#!/usr/bin/env python3
"""Generate a blog post using an LLM service and write to `src/content/blog`.

This script expects the following environment variables to be set (the workflow will
supply them when `GEMIAI_KEY` is configured):

- `GEMIAI_KEY` (required): API key for the LLM service.
- `GEMIAI_API_URL` (optional): full URL of the text-generation endpoint. If not set,
  the script will try a sensible default placeholder; update it to match your provider.
- `GEMIAI_MODEL` (optional): model name to request (default: "gemini-1.0").

The script reads an input JSON (path passed as `--input` or default
`scripts/generate_input.json`) which should follow the prompt template schema.
It then builds a prompt using `scripts/blog_prompt_template.md`, sends it to the
LLM, and writes the returned MDX to `src/content/blog/<slug>.mdx`.

Important: The script attempts to be tolerant of different API response shapes
(OpenAI-like `choices[].text`, or Gemini-style `output`), but you should verify
the provider's response format and adapt the parsing block below.
"""
import os
import sys
import json
import argparse
import re
import requests
import time
from typing import Optional
try:
    # Prefer official Google GenAI client when available
    from google import genai
    HAVE_GENAI = True
except Exception:
    HAVE_GENAI = False
from pathlib import Path


def slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^a-z0-9\- ]", "", s)
    s = s.replace(" ", "-")
    return s[:80]


def load_input(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_prompt(template_path: Path, input_json: dict) -> str:
    tpl = template_path.read_text(encoding="utf-8")
    # The template includes a marker '<PASTE_JSON_HERE>' where the JSON should go.
    json_blob = json.dumps(input_json, ensure_ascii=False, indent=2)
    if "<PASTE_JSON_HERE>" in tpl:
        return tpl.replace("<PASTE_JSON_HERE>", json_blob)
    # Fallback: append input JSON at the end
    return tpl + "\n\nINPUT:\n" + json_blob


def call_llm(api_url: str, api_key: str, model: str, prompt: str, timeout=120) -> dict:
    """Call LLM. Prefer google-genai client; otherwise fall back to a raw HTTP POST.

    Implements simple retry/backoff for 429 rate-limit responses.
    """
    max_retries = 5
    backoff = 2

    if HAVE_GENAI:
        client = genai.Client(api_key=api_key)
        for attempt in range(1, max_retries + 1):
            try:
                # Using the user's suggested call shape. Providers may differ.
                resp = client.models.generate_content(model=model, contents=prompt)
                # genai response often has `text` attribute on the returned object
                return {"genai": True, "response": resp}
            except Exception as exc:
                if attempt == max_retries:
                    raise
                wait = backoff * attempt
                print(f"genai client error, retrying in {wait}s: {exc}")
                time.sleep(wait)

    # Fallback HTTP path
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "prompt": prompt, "max_tokens": 3000}
    for attempt in range(1, max_retries + 1):
        resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code == 429:
            if attempt == max_retries:
                resp.raise_for_status()
            wait = backoff * attempt
            print(f"Rate limited (429). Backing off {wait}s (attempt {attempt}).")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()


def extract_text_from_response(resp_json: dict) -> str:
    # Try common shapes: genai client object, OpenAI-like -> resp['choices'][0]['text']
    # If we received the genai client object wrapper, normalize it first
    if isinstance(resp_json, dict) and resp_json.get("genai"):
        resp_obj = resp_json.get("response")
        # Try to use .text if present
        try:
            text = getattr(resp_obj, "text", None)
            if text:
                return text
        except Exception:
            pass
        # Some genai responses serialize to dict-like structures
        try:
            j = resp_obj.__dict__
        except Exception:
            j = None
        if j:
            # try common keys
            for k in ("output", "outputs", "text"):
                if k in j:
                    return j[k]
    # Try previous heuristics
    if isinstance(resp_json, dict):
        if "choices" in resp_json and isinstance(resp_json["choices"], list):
            first = resp_json["choices"][0]
            if isinstance(first, dict) and "text" in first:
                return first["text"]
            if isinstance(first, dict) and "message" in first and "content" in first["message"]:
                return first["message"]["content"]
        # Gemini-style: 'output' or 'outputs'
        if "output" in resp_json and isinstance(resp_json["output"], str):
            return resp_json["output"]
        if "outputs" in resp_json and isinstance(resp_json["outputs"], list):
            # Join textual content fragments
            parts = []
            for o in resp_json["outputs"]:
                if isinstance(o, dict):
                    if "content" in o and isinstance(o["content"], str):
                        parts.append(o["content"])
                    elif "text" in o and isinstance(o["text"], str):
                        parts.append(o["text"])
            return "\n".join(parts)
    # Last resort: stringify entire response
    return json.dumps(resp_json, ensure_ascii=False, indent=2)


def find_slug_from_content(text: str) -> str:
    m = re.search(r"<!--\s*slug:\s*([a-z0-9\-]+)\s*-->", text, re.IGNORECASE)
    if m:
        return m.group(1)
    # Try to extract title from frontmatter
    m2 = re.search(r"title:\s*\"([^\"]+)\"", text)
    if m2:
        return slugify(m2.group(1))
    return "generated-post-" + datetime_now_slug()


def datetime_now_slug() -> str:
    from datetime import datetime

    return datetime.utcnow().strftime("%Y%m%d%H%M%S")


def write_output(content: str, out_dir: Path, slug: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = "mdx" if "---" in content else "md"
    path = out_dir / f"{slug}.{ext}"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote generated post: {path}")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="scripts/generate_input.json", help="Path to input JSON")
    parser.add_argument("--template", default="scripts/blog_prompt_template.md", help="Prompt template path")
    parser.add_argument("--out", default="src/content/blog", help="Output blog directory")
    args = parser.parse_args(argv)

    api_key = os.getenv("GEMIAI_KEY")
    if not api_key:
        print("GEMIAI_KEY not set. Aborting.")
        sys.exit(2)

    api_url = os.getenv("GEMIAI_API_URL", "https://api.gemini.example/v1/generate")
    # Default to the highest free-tier throughput model. Override with GEMIAI_MODEL env var.
    # Recommended choices:
    # - gemini-2.5-flash-lite : highest free-tier request limits (1,000/day)
    # - gemini-3-pro-preview : latest reasoning capabilities (use if available)
    model = os.getenv("GEMIAI_MODEL", "gemini-2.5-flash-lite")

    input_json = load_input(Path(args.input))
    prompt = build_prompt(Path(args.template), input_json)

    print("Calling LLM service at:", api_url)
    resp = call_llm(api_url, api_key, model, prompt)
    text = extract_text_from_response(resp)

    # Determine slug and write file
    slug = find_slug_from_content(text)
    write_output(text, Path(args.out), slug)


if __name__ == "__main__":
    main()
