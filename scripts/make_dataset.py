"""Derive a tidy, publishable dataset from the raw census.

The raw pull (data/surveys.jsonl, ~207 MB) carries the full HTML body of every
consultation notice. That bulk is not needed for analysis and is awkward to
distribute, so this writes data/consultations.csv with one row per consultation
and only the fields the analysis uses.

Nothing here is inferred or imputed. Every column is either copied straight from
the API payload or is a mechanical transformation of it, noted in the comments.
"""

import csv
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "surveys.jsonl"
META = ROOT / "data" / "fetch-meta.json"
OUT = ROOT / "data" / "consultations.csv"

PORTAL = "https://law.go.th/listeningDetail?survey_id="

COLUMNS = [
    "survey_id",
    "survey_name",
    "survey_type_name",      # ร่างกฎหมาย / กม.ลำดับรองอื่นๆ / ประเมินผลสัมฤทธิ์ / หลักการ
    "agency_name",
    "agency_id",
    "ministry_id",
    "start_date",
    "end_date",
    "duration_day",
    "closed",                # derived: end_date < fetch time
    "close_year",            # derived
    "answer_count",          # comments; validated against OECD 2025 Box 3.3
    "view_count",
    "question_count",
    "n_invited",             # derived: count of ids in stackholders_agency
    "affects_prachachon",    # derived: 'ประชาชน' appears in affected_person
    "affected_person",
    "tags",
    "isconclude",            # whether a summary of results has been published
    "law_group_id",
    "url",                   # derived: portal permalink
]


def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def main():
    # Not splitlines(): the HTML fields contain U+2028, which str.splitlines()
    # treats as a line break but json.dumps does not escape.
    rows = [json.loads(l) for l in SRC.read_text(encoding="utf-8").split("\n") if l.strip()]
    fetched = parse_dt(json.loads(META.read_text(encoding="utf-8"))["fetch_finished_utc"])

    n_closed = 0
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            ed = parse_dt(r.get("end_date"))
            closed = bool(ed and ed < fetched)
            n_closed += closed
            stake = str(r.get("stackholders_agency") or "")
            affected = r.get("affected_person") or ""
            w.writerow({
                "survey_id": r.get("survey_id"),
                "survey_name": (r.get("survey_name") or "").strip(),
                "survey_type_name": r.get("survey_type_name"),
                "agency_name": r.get("agency_name"),
                "agency_id": r.get("agency_id"),
                "ministry_id": r.get("ministry_id"),
                "start_date": (r.get("start_date") or "")[:10],
                "end_date": (r.get("end_date") or "")[:10],
                "duration_day": r.get("duration_day"),
                "closed": int(closed),
                "close_year": ed.year if ed else "",
                "answer_count": r.get("answer_count") or 0,
                "view_count": r.get("view_count") or 0,
                "question_count": r.get("question_count"),
                "n_invited": len([x for x in stake.split(",") if x.strip()]),
                "affects_prachachon": int("ประชาชน" in affected),
                "affected_person": affected,
                "tags": r.get("tags") or "",
                "isconclude": r.get("isconclude") or "",
                "law_group_id": r.get("law_group_id"),
                "url": PORTAL + str(r.get("survey_id")),
            })

    size_mb = OUT.stat().st_size / 1e6
    print(f"wrote {len(rows)} rows ({n_closed} closed) -> {OUT}  [{size_mb:.1f} MB]")


if __name__ == "__main__":
    main()
