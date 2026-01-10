#!/usr/bin/env python3
"""Generate blog posts from the latest Google Trends JSON.

Reads `data/trends/latest.json`, builds prompt-input JSON for the top trends per
region using the project's prompt template schema, then calls
`scripts/generate_blog.py --input <temp.json>` for each trend. It respects a
delay between calls to avoid rate limits.
"""
import json
import os
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime


ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "trends" / "latest.json"
GENERATOR = ROOT / "scripts" / "generate_blog.py"


def read_trends(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Trends file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_input_for(trend: str, region: str):
    title = f"Why {trend} is Trending in {region} Today"
    today = datetime.utcnow().date().isoformat()
    inp = {
        "title": title,
        "description": f"Why {trend} is trending in {region} and what to watch next.",
        "pubDate": today,
        "heroImage": {"src": "../../assets/auto-trend.png", "alt": f"{trend} trending"},
        "tags": [trend.lower().replace(' ', '-'), region.lower()],
        "framework": "H-I-P",
        "tone": "informative",
        "audience": "general",
        "length": "short",
        "outlineHints": ["H2: Hook", "H2: Why it's trending", "H2: Impact", "H2: What next"]
    }
    return inp


def run_generator(input_json: dict, tmp_path: Path, env: dict):
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(input_json, f, ensure_ascii=False, indent=2)
    cmd = ["python", str(GENERATOR), "--input", str(tmp_path)]
    print("Running generator:", " ".join(cmd))
    return subprocess.Popen(cmd, env=env)


def run_image_generator(image_prompt: str, slug: str, tmp_path: Path, env: dict):
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"imagePrompt": image_prompt, "slug": slug}
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    image_script = ROOT / "scripts" / "generate_image.py"
    cmd = ["python", str(image_script), "--input", str(tmp_path)]
    print("Running image generator:", " ".join(cmd))
    return subprocess.Popen(cmd, env=env)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=1, help="Top N trends per region")
    parser.add_argument("--delay", type=int, default=6, help="Delay between calls (seconds)")
    args = parser.parse_args()

    data = read_trends(DATA_PATH)
    regions = data.get("regions", {})
    if not regions:
        print("No regions found in trends data.")
        return

    env = os.environ.copy()
    tmpdir = Path(".tmp_trend_inputs")
    tmpdir.mkdir(exist_ok=True)

    for region_code, info in regions.items():
        trends = info.get("trends", [])
        if not trends:
            continue
        for i, trend in enumerate(trends[: args.top]):
            input_json = build_input_for(trend, region_code)
            ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            tmp_path = tmpdir / f"input_{region_code}_{i}_{ts}.json"
            # Build a compact slug for filenames
            slug = (trend.lower().replace(" ", "-") + "-" + region_code.lower())[:80]

            # Build an image prompt derived from the trend data
            image_prompt = (
                f"Create a high-resolution, attention-grabbing hero image representing the trending topic '{trend}' "
                f"in {region_code}. Style: modern editorial, clean composition, strong focal point that evokes the subject; "
                "color palette: neutral with one accent color; include space on the upper third for a headline; deliver as PNG. size 1536*1024"
            )

            # Launch both generators in parallel and wait for both to finish
            blog_proc = None
            img_proc = None
            try:
                blog_proc = run_generator(input_json, tmp_path, env)
            except Exception as e:
                print("Failed to start blog generator for", trend, region_code, e)

            img_tmp = tmpdir / f"image_{region_code}_{i}_{ts}.json"
            try:
                img_proc = run_image_generator(image_prompt, slug, img_tmp, env)
            except Exception as e:
                print("Failed to start image generator for", trend, region_code, e)

            # Wait for both processes to complete, with timeout per process
            procs = [p for p in (blog_proc, img_proc) if p]
            for p in procs:
                try:
                    p.wait(timeout=300)
                except subprocess.TimeoutExpired:
                    print("Process timed out, killing:", p.pid)
                    p.kill()

            time.sleep(args.delay)


if __name__ == "__main__":
    main()
