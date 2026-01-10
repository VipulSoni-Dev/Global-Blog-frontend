#!/usr/bin/env python3
"""Fetch Google Trends for configured regions and write JSON files to data/trends/.

This script uses the `pytrends` package to fetch daily trending searches
for a set of regions and writes a dated JSON file plus a `latest.json`.

Regions and their pytrends 'pn' identifiers can be adjusted in REGIONS.
"""
import json
import os
import logging
import time
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
# Retry configuration for transient failures when fetching trends
MAX_RETRIES = 5
RETRY_DELAY = 3  # seconds


def fetch_trends_for_regions(regions):
    # Use a browser-like User-Agent to reduce the likelihood of Google returning
    # 404s or blocking automated clients. `requests_args` is passed to the
    # underlying requests.Session used by pytrends.
    REQUESTS_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    pytrends = TrendReq(hl="en-US", tz=0, requests_args={"headers": REQUESTS_HEADERS})
    results = {}
    for code, pn in regions.items():
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                LOG.info("Fetching trending searches for %s (%s) — attempt %d/%d", code, pn, attempt, MAX_RETRIES)
                df = pytrends.trending_searches(pn=pn)
                # `trending_searches` returns a DataFrame with one column of queries
                trends = df.iloc[:, 0].dropna().astype(str).tolist()
                results[code] = {"pn": pn, "trends": trends}
                break
            except Exception as exc:
                last_exc = exc
                # If the exception has an HTTP response, log detailed info
                extra = ""
                try:
                    resp = getattr(exc, 'response', None)
                    if resp is not None:
                        extra = f" (status={getattr(resp, 'status_code', 'n/a')} body={getattr(resp, 'text', '')[:200]})"
                except Exception:
                    extra = ""
                LOG.warning("Attempt %d failed for %s (%s): %s%s", attempt, code, pn, exc, extra)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    # All attempts failed
                    LOG.error("All %d attempts failed for %s (%s). Last error: %s", MAX_RETRIES, code, pn, last_exc)
                    # Try a small set of fallback 'pn' variants when Google returns 404
                    fallbacks = [code.lower(), pn]
                    fallback_success = False
                    for alt in fallbacks:
                        if alt == pn:
                            continue
                        try:
                            LOG.info("Trying fallback pn '%s' for %s", alt, code)
                            df = pytrends.trending_searches(pn=alt)
                            trends = df.iloc[:, 0].dropna().astype(str).tolist()
                            results[code] = {"pn": alt, "trends": trends}
                            fallback_success = True
                            LOG.info("Fallback succeeded for %s using pn=%s", code, alt)
                            break
                        except Exception as exc2:
                            LOG.warning("Fallback pn '%s' failed for %s: %s", alt, code, exc2)
                    if not fallback_success:
                        results[code] = {"pn": pn, "error": str(last_exc), "trends": []}
                    break
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
