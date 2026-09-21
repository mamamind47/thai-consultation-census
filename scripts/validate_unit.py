"""Does answer_count count people, or submitted comments?

OECD (2025) Box 3.3 calls these "comments", and the field matches their figure for
the largest consultation (55,584 vs 55,591). That settles the magnitude but not the
unit, which is the thing a reviewer will ask about.

Agencies that publish a summary of results (isconclude == 'P') frequently state the
respondent count in prose: "มีผู้แสดงความคิดเห็น จำนวน ๘ ราย". This script downloads
those summary PDFs, extracts every stated count, and compares it to answer_count.

Reading the result:
  stated == answer_count            -> the field counts respondents
  stated  < answer_count            -> the field counts something more granular
                                       (e.g. one row per answered question)
  stated  > answer_count            -> the summary covers channels beyond the portal
                                       (s.13 permits meetings, interviews, surveys)

Thai PDF text extraction routinely drops combining marks, so phrase matching is done
on a normalised string with marks stripped; digits are unaffected.
"""

import csv
import json
import re
import subprocess
import urllib.parse
import urllib.request
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_IN = ROOT / "data" / "consultations.csv"
CACHE = ROOT / "data" / "summaries"
OUT = ROOT / "data" / "unit-validation.csv"

DETAIL = "https://apig.law.go.th/dga-user-service-survey/surveys/"

_MARKS = re.compile(r"[ัิ-ฺ็-๎]")
THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")


def norm(t):
    """Strip combining marks and whitespace so phrase matching survives extraction loss."""
    t = t.replace("ำ", "า")          # SARA AM -> SARA AA
    return _MARKS.sub("", re.sub(r"\s+", "", t))


# Phrases that introduce a respondent count. These are stored ALREADY NORMALISED,
# because the text they are matched against is normalised. Matching a raw literal
# against normalised text silently returns nothing -- "จำนวน" normalises to "จานวน".
CUES = [norm(s) for s in (
    "ผู้จัดส่งความคิดเห็น",
    "ผู้แสดงความคิดเห็น",
    "ผู้ร่วมแสดงความคิดเห็น",
    "ผู้เข้าร่วมแสดงความคิดเห็น",
    "ผู้ตอบแบบสอบถาม",
    "มีผู้แสดงความเห็น",
    "ผู้เข้าร่วมประชุม",
)]

# "จำนวน 31 ราย" -> normalised "จานวน31ราย"; also accept a bare "31ราย".
_JAMNUAN = norm("จำนวน")
COUNT_RE = re.compile(r"(?:" + _JAMNUAN + r")?([0-9][0-9,]*)(?:" + "|".join(
    norm(u) for u in ("ราย", "คน", "ท่าน", "หน่วยงาน")) + r")")

def fetch_detail(sid):
    enc = base64.b64encode(str(sid).encode()).decode()
    req = urllib.request.Request(DETAIL + enc, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["data"]


def summary_urls(detail):
    out = []
    for f in detail.get("content_files") or []:
        name = f.get("file_name") or ""
        typ = (f.get("type") or "").lower()
        # Only the summary-of-results document; skip the impact analysis (RIA).
        if "conclu" in typ and ("สรุปผล" in name or "สรุป" in name) and "วิเคราะห" not in name:
            out.append(f["file_path"])
    if not out:  # fall back to any conclude file
        out = [f["file_path"] for f in (detail.get("content_files") or [])
               if "conclu" in (f.get("type") or "").lower()]
    return out


def pdf_text(url, sid, idx):
    CACHE.mkdir(parents=True, exist_ok=True)
    pdf = CACHE / f"{sid}-{idx}.pdf"
    txt = CACHE / f"{sid}-{idx}.txt"
    if not txt.exists():
        if not pdf.exists():
            safe = urllib.parse.quote(url, safe=":/?=&%")
            req = urllib.request.Request(safe, headers={"User-Agent": "Mozilla/5.0"})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    pdf.write_bytes(r.read())
            except Exception as e:
                return None, f"download failed: {e}"
        try:
            subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)],
                           check=True, capture_output=True, timeout=120)
        except Exception as e:
            return None, f"pdftotext failed: {e}"
    try:
        return txt.read_text(encoding="utf-8", errors="replace"), None
    except Exception as e:
        return None, f"read failed: {e}"


def stated_counts(text):
    """Return counts appearing within 120 normalised chars after a respondent cue."""
    t = norm(text.translate(THAI_DIGITS))
    hits = []
    for cue in CUES:
        for m in re.finditer(re.escape(cue), t):
            window = t[m.end():m.end() + 120]
            for c in COUNT_RE.finditer(window):
                hits.append(int(c.group(1).replace(",", "")))
    return hits


def main(limit=60):
    rows = [r for r in csv.DictReader(CSV_IN.open(encoding="utf-8"))
            if r["closed"] == "1" and r["isconclude"] == "P" and int(r["answer_count"]) > 0]
    rows.sort(key=lambda r: int(r["survey_id"]))
    step = max(1, len(rows) // limit)
    sample = rows[::step][:limit]
    print(f"{len(rows)} closed consultations with a published summary; testing {len(sample)}\n")

    results = []
    for r in sample:
        sid = r["survey_id"]
        ac = int(r["answer_count"])
        try:
            detail = fetch_detail(sid)
        except Exception as e:
            print(f"  {sid}: detail failed ({e})")
            continue
        urls = summary_urls(detail)
        found = []
        for i, u in enumerate(urls[:2]):
            text, err = pdf_text(u, sid, i)
            if text:
                found += stated_counts(text)
        if not found:
            continue
        best = min(found, key=lambda v: abs(v - ac))
        verdict = ("exact" if best == ac else
                   "stated<count" if best < ac else "stated>count")
        results.append({"survey_id": sid, "answer_count": ac,
                        "stated": best, "all_stated": ";".join(map(str, sorted(set(found)))),
                        "verdict": verdict, "url": r["url"]})
        print(f"  {sid:>5}  answer_count={ac:>6}  stated={best:>6}  {verdict}")

    if results:
        with OUT.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
            w.writeheader()
            w.writerows(results)
        n = len(results)
        ex = sum(1 for x in results if x["verdict"] == "exact")
        lo = sum(1 for x in results if x["verdict"] == "stated<count")
        hi = sum(1 for x in results if x["verdict"] == "stated>count")
        print(f"\n  usable comparisons: {n}")
        print(f"    exact match      {ex:>4} ({100*ex/n:.0f}%)")
        print(f"    stated < count   {lo:>4} ({100*lo/n:.0f}%)")
        print(f"    stated > count   {hi:>4} ({100*hi/n:.0f}%)")
        print(f"  wrote {OUT}")
    else:
        print("\n  no usable comparisons -- summaries do not state counts in a parseable form")


if __name__ == "__main__":
    main()
