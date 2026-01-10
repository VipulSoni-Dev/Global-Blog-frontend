#!/usr/bin/env python3
"""Fetch Google Trends for configured regions and write JSON files to data/trends/.

This script uses the `pytrends` package to fetch daily trending searches
for a set of regions and writes a dated JSON file plus a `latest.json`.

Regions and their pytrends 'pn' identifiers can be adjusted in REGIONS.
"""
import json
import os
import logging
from datetime import datetime, timezone

try:
    from pytrends.request import TrendReq
except Exception as e:
    raise RuntimeError("pytrends is required. Install with 'pip install pytrends'") from e

LOG = logging.getLogger("fetch_trends")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Regions mapping: short code -> pytrends 'pn' value
REGIONS = {
    "US": "united_states",
    "UK": "united_kingdom",
    "UAE": "united_arab_emirates",
    "EU": "europe",
}

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "trends")


def fetch_trends_for_regions(regions):
    pytrends = TrendReq(hl="en-US", tz=0)
    results = {}
    for code, pn in regions.items():
        try:
            LOG.info("Fetching trending searches for %s (%s)", code, pn)
            df = pytrends.trending_searches(pn=pn)
            # `trending_searches` returns a DataFrame with one column of queries
            trends = df.iloc[:, 0].dropna().astype(str).tolist()
            results[code] = {"pn": pn, "trends": trends}
        except Exception as exc:
            LOG.exception("Failed to fetch trends for %s (%s): %s", code, pn, exc)
            results[code] = {"pn": pn, "error": str(exc), "trends": []}
    return results


def write_output(data, out_dir=OUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    now = datetime.now(timezone.utc)
    date_str = now.date().isoformat()
    payload = {"fetched_at": now.isoformat(), "date": date_str, "regions": data}

    dated_path = os.path.join(out_dir, f"{date_str}.json")
    latest_path = os.path.join(out_dir, "latest.json")

    with open(dated_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    LOG.info("Wrote trends to %s and %s", dated_path, latest_path)
    return dated_path, latest_path


def main():
    LOG.info("Starting Google Trends fetch")
    data = fetch_trends_for_regions(REGIONS)
    dated, latest = write_output(data)
    LOG.info("Done: %s", dated)


if __name__ == "__main__":
    main()
