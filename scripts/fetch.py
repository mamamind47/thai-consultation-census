"""Full census of Thailand's Central Law Portal (law.go.th) consultations.

Pulls every page of the public listing endpoint and writes one JSON object per
consultation to data/surveys.jsonl, plus a provenance record to data/fetch-meta.json.

The listing endpoint is the same one the law.go.th React front end calls. It is
public and unauthenticated. We record enough provenance that the pull can be
audited or repeated: endpoint, request body, wall-clock time, HTTP status, page
sizes, and the number of duplicate survey_ids seen while paginating.
"""

import json
import time
import hashlib
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ENDPOINT = "https://apig.law.go.th/dga-user-service-survey/surveys"
PAGE_SIZE = 200
MAX_PAGES = 200          # generous ceiling; we stop when a page comes back empty
SLEEP = 0.4              # be polite to a government server
RETRIES = 4

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "surveys.jsonl"
META = ROOT / "data" / "fetch-meta.json"


def post(page, size=PAGE_SIZE):
    """One listing request. Returns (rows, http_status, last_page)."""
    body = {"searchText": "", "size": size, "page": page, "sort": "desc"}
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    last_err = None
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                payload = json.load(resp)
                return payload.get("data", []), resp.status, payload.get("lastPage")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"page {page} failed after {RETRIES} attempts: {last_err}")


def main():
    started = datetime.now(timezone.utc).isoformat()
    seen = {}
    dup_count = 0
    page_log = []
    last_page_reported = None

    for page in range(1, MAX_PAGES + 1):
        rows, status, last_page = post(page)
        if last_page is not None:
            last_page_reported = last_page
        page_log.append({"page": page, "status": status, "n_rows": len(rows)})
        if not rows:
            break
        new = 0
        for r in rows:
            sid = r.get("survey_id")
            if sid in seen:
                dup_count += 1
                continue
            seen[sid] = r
            new += 1
        print(f"page {page:>3}: {len(rows):>3} rows, {new:>3} new, total {len(seen)}")
        # The endpoint reports lastPage; keep going a page past it only if rows keep coming.
        if last_page_reported is not None and page >= last_page_reported and new == 0:
            break
        time.sleep(SLEEP)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for sid in sorted(seen, key=lambda s: int(s) if str(s).isdigit() else 0):
            fh.write(json.dumps(seen[sid], ensure_ascii=False) + "\n")

    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    meta = {
        "endpoint": ENDPOINT,
        "request_body_template": {"searchText": "", "size": PAGE_SIZE, "page": "<n>", "sort": "desc"},
        "fetch_started_utc": started,
        "fetch_finished_utc": datetime.now(timezone.utc).isoformat(),
        "last_page_reported_by_api": last_page_reported,
        "pages_requested": len(page_log),
        "page_log": page_log,
        "n_unique_surveys": len(seen),
        "n_duplicate_rows_seen": dup_count,
        "output_file": str(OUT.relative_to(ROOT)),
        "output_sha256": digest,
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {len(seen)} unique consultations -> {OUT}")
    print(f"sha256 {digest}")
    print(f"duplicates seen while paginating: {dup_count}")


if __name__ == "__main__":
    main()
