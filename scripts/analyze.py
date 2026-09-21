"""Analyse the law.go.th consultation census.

Reads data/surveys.jsonl and reports the participation distribution.

Two methodological choices are made explicit here because they change the numbers:

1. Only CLOSED consultations are counted. A consultation still open for comment
   has not finished collecting, so including it would understate participation.
   Closure is determined from end_date against the fetch date, not from
   date_balance, because date_balance is computed server-side at request time.

2. answer_count is treated as the comment count. This is validated externally:
   OECD, *Regulatory Reform in Thailand* (2025), Box 3.3 names the largest
   consultation as 55,591 comments; this field gives 55,584 for that record.
"""

import json
import statistics as st
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "surveys.jsonl"
META = ROOT / "data" / "fetch-meta.json"


def load():
    # NOT splitlines(): the HTML content fields contain U+2028/U+2029, which
    # str.splitlines() treats as line breaks but json.dumps does not escape.
    # Splitting on those characters tears records in half.
    text = SRC.read_text(encoding="utf-8")
    return [json.loads(l) for l in text.split("\n") if l.strip()]


def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def gini(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0 or sum(xs) == 0:
        return float("nan")
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return (2 * cum) / (n * sum(xs)) - (n + 1) / n


def dist(rows, label):
    a = sorted((r.get("answer_count") or 0) for r in rows)
    n = len(a)
    if n == 0:
        print(f"\n{label}: no rows")
        return
    tot = sum(a)
    desc = a[::-1]
    print(f"\n=== {label} (n={n}) ===")
    print(f"  total comments {tot:,}   median {st.median(a):.0f}   mean {tot/n:.1f}   max {a[-1]:,}")
    buckets = [(0, 0), (1, 5), (6, 20), (21, 100), (101, 10**9)]
    names = ["zero", "1-5", "6-20", "21-100", ">100"]
    for (lo, hi), nm in zip(buckets, names):
        c = sum(1 for x in a if lo <= x <= hi)
        print(f"    {nm:>7}: {c:>5} ({100*c/n:5.1f}%)")
    for k in (1, 5, 10):
        c = max(1, n * k // 100)
        print(f"  top {k:>2}% ({c:>4} consultations) hold {100*sum(desc[:c])/tot:5.1f}% of all comments")
    print(f"  single largest alone: {100*desc[0]/tot:.1f}%")
    le5 = [x for x in a if x <= 5]
    print(f"  the {len(le5)} consultations with <=5 comments ({100*len(le5)/n:.1f}%) hold {100*sum(le5)/tot:.2f}% of comments")
    print(f"  Gini {gini(a):.3f}")


def main():
    rows = load()
    meta = json.loads(META.read_text(encoding="utf-8"))
    fetched = parse_dt(meta["fetch_finished_utc"])
    print(f"census: {len(rows)} consultations, fetched {meta['fetch_finished_utc']}")

    closed, open_now, undated = [], [], []
    for r in rows:
        ed = parse_dt(r.get("end_date"))
        if ed is None:
            undated.append(r)
        elif ed < fetched:
            closed.append(r)
        else:
            open_now.append(r)
    print(f"  closed {len(closed)} | still open {len(open_now)} | no end_date {len(undated)}")
    print("  (all figures below use CLOSED consultations only)")

    by_type = {}
    for r in closed:
        by_type.setdefault(r.get("survey_type_name") or "(none)", []).append(r)
    print("\ntypes among closed:")
    for t, v in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(v):>5}  {t}")

    dist(closed, "ALL CLOSED CONSULTATIONS")
    for t in ("ร่างกฎหมาย", "กม.ลำดับรองอื่นๆ", "ประเมินผลสัมฤทธิ์", "หลักการ"):
        if t in by_type:
            dist(by_type[t], f"TYPE: {t}")

    # View funnel
    print("\n=== views vs responses (closed) ===")
    z = [r for r in closed if (r.get("answer_count") or 0) == 0]
    zv = sorted((r.get("view_count") or 0) for r in z)
    if zv:
        print(f"  zero-comment consultations n={len(zv)}: views median {st.median(zv):.0f}, "
              f"mean {st.mean(zv):.0f}, max {zv[-1]:,}")
        print(f"    of those, {sum(1 for v in zv if v > 1000)} had >1000 views yet no comments")
    rates = [r["answer_count"] / r["view_count"] for r in closed
             if (r.get("view_count") or 0) > 0 and (r.get("answer_count") or 0) > 0]
    if rates:
        print(f"  comment/view rate where both >0 (n={len(rates)}): median {st.median(rates):.4f}, "
              f"mean {st.mean(rates):.4f}")

    # By year of close
    print("\n=== by year consultation closed ===")
    by_year = {}
    for r in closed:
        ed = parse_dt(r.get("end_date"))
        by_year.setdefault(ed.year, []).append(r.get("answer_count") or 0)
    for y in sorted(by_year):
        v = by_year[y]
        zc = sum(1 for x in v if x == 0)
        print(f"  {y}: n={len(v):>5}  median {st.median(v):>6.0f}  total {sum(v):>8,}  zero {zc:>4} ({100*zc/len(v):4.1f}%)")

    # Agencies
    print("\n=== top agencies by consultation count (closed) ===")
    by_ag = {}
    for r in closed:
        by_ag.setdefault(r.get("agency_name") or "(none)", []).append(r.get("answer_count") or 0)
    for ag, v in sorted(by_ag.items(), key=lambda kv: -len(kv[1]))[:12]:
        zc = sum(1 for x in v if x == 0)
        print(f"  {len(v):>4} consultations  median {st.median(v):>6.0f}  zero {zc:>3} ({100*zc/len(v):4.1f}%)  {ag[:48]}")
    print(f"\n  distinct agencies: {len(by_ag)}")

    # Norway benchmark
    draft = by_type.get("ร่างกฎหมาย", [])
    if draft:
        dz = sum(1 for r in draft if (r.get("answer_count") or 0) == 0)
        print(f"\n=== benchmark ===")
        print(f"  Thailand draft laws (closed): {100*dz/len(draft):.2f}% zero  (n={len(draft)})")
        print(f"  Norway (Bunea et al. 2025, n=4,062):       6.28% zero")


if __name__ == "__main__":
    main()
