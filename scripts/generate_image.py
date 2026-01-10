#!/usr/bin/env python3
"""Generate an image from a prompt and save to `src/assets/generated/`.

This script accepts `--input` JSON containing:
- `imagePrompt`: the text prompt for the image model
- `slug`: base filename to write (without extension)

It prefers the `google.genai` client if available; otherwise it will POST to
`GEMIAI_API_URL_IMAGE` (if set). It writes a PNG file and prints the path.
"""
import os
import sys
import json
import argparse
import base64
import time
import requests
from pathlib import Path
try:
    from google import genai
    HAVE_GENAI = True
except Exception:
    HAVE_GENAI = False
from io import BytesIO
from PIL import Image


def load_input(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_image_bytes(b: bytes, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(b)
    print(f"Wrote image: {out_path}")


def call_image_api_genai(api_key: str, model: str, prompt: str):
    client = genai.Client(api_key=api_key)
    # Use models.generate_content to get candidates with inline bytes
    resp = client.models.generate_content(model=model, contents=prompt)
    return resp


def call_image_api_http(api_url: str, api_key: str, model: str, prompt: str, timeout=120):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "prompt": prompt, "size": "1536x1024", "format": "png"}
    resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def save_first_image_from_genai_response(resp, out_path: Path):
    # Walk resp.candidates -> candidate.content.parts and find inline_data
    candidates = getattr(resp, "candidates", None) or (resp.get("candidates") if isinstance(resp, dict) else None)
    if not candidates:
        raise ValueError("No candidates in genai response")
    for cand in candidates:
        content = getattr(cand, "content", None) or (cand.get("content") if isinstance(cand, dict) else None)
        if not content:
            continue
        parts = getattr(content, "parts", None) or (content.get("parts") if isinstance(content, dict) else None)
        if not parts:
            continue
        for part in parts:
            inline = getattr(part, "inline_data", None) or (part.get("inline_data") if isinstance(part, dict) else None)
            if not inline:
                continue
            data = getattr(inline, "data", None) or (inline.get("data") if isinstance(inline, dict) else None)
            if not data:
                continue
            if isinstance(data, (bytes, bytearray)):
                img_bytes = bytes(data)
            elif isinstance(data, str):
                img_bytes = base64.b64decode(data)
            else:
                img_bytes = bytes(data)
            image = Image.open(BytesIO(img_bytes))
            out_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(out_path)
            print(f"Wrote image: {out_path}")
            return out_path


def extract_image_bytes_from_http_response(resp_json):
    if isinstance(resp_json, dict):
        if "data" in resp_json and isinstance(resp_json["data"], list) and resp_json["data"]:
            first = resp_json["data"][0]
            if isinstance(first, dict) and "b64" in first:
                return base64.b64decode(first["b64"])
        for k in ("b64", "image"):
            if k in resp_json and isinstance(resp_json[k], str):
                return base64.b64decode(resp_json[k])
    raise ValueError("Could not extract image bytes from HTTP response")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=".tmp_trend_inputs/image_input.json")
    args = parser.parse_args(argv)

    data = load_input(Path(args.input))
    prompt = data.get("imagePrompt")
    slug = data.get("slug") or "trend-image"

    api_key = os.getenv("GEMIAI_KEY")
    if not api_key:
        print("GEMIAI_KEY not set. Aborting image generation.")
        sys.exit(2)

    model = os.getenv("GEMIAI_MODEL_IMAGE", "gemini-image-1")
    api_url = os.getenv("GEMIAI_API_URL_IMAGE", os.getenv("GEMIAI_API_URL", "https://api.gemini.example/v1/images"))

    max_retries = 4
    for attempt in range(1, max_retries + 1):
        try:
            if HAVE_GENAI:
                resp = call_image_api_genai(api_key, model, prompt)
                img_bytes = extract_image_bytes_from_response(resp)
            else:
                resp_json = call_image_api_http(api_url, api_key, model, prompt)
                img_bytes = extract_image_bytes_from_response(resp_json)
            break
        except Exception as exc:
            if attempt == max_retries:
                print("Image generation failed:", exc)
                raise
            wait = attempt * 2
            print(f"Image generation error, retrying in {wait}s: {exc}")
            time.sleep(wait)

    out_dir = Path("src") / "assets" / "generated"
    out_path = out_dir / f"{slug}.png"
    save_image_bytes(img_bytes, out_path)


if __name__ == "__main__":
    main()
