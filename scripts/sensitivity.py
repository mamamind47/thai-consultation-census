"""Sensitivity checks and the figures the revised paper reports.

Every number the manuscript states should come from here or from analyze.py, so
that the two cannot drift apart. Written after an external review found that the
original draft mixed populations (all records vs closed records), misread the
subjects of the largest consultations, and reported a single Gini without showing
how much of it one case supplies.
"""

import csv
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "consultations.csv"


def load():
    return list(csv.DictReader(SRC.open(encoding="utf-8")))


def gini(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0 or sum(xs) == 0:
        return float("nan")
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return (2 * cum) / (n * sum(xs)) - (n + 1) / n


def topshare(xs, pct):
    xs = sorted(xs, reverse=True)
    k = max(1, len(xs) * pct // 100)
    return 100 * sum(xs[:k]) / sum(xs), k


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    n = len(rx)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def main():
    rows = load()
    closed = [r for r in rows if r["closed"] == "1"]
    A = lambda r: int(r["answer_count"])
    V = lambda r: int(r["view_count"])

    print("=== POPULATIONS (state these separately, never mixed) ===")
    for lab, s in (("all records", rows), ("closed", closed)):
        print(f"  {lab:<12} n={len(s):>5}  agencies={len({r['agency_name'] for r in s}):>4}  "
              f"responses={sum(A(r) for r in s):>10,}")

    print("\n=== LARGEST CONSULTATIONS: full titles ===")
    for r in sorted(closed, key=lambda r: -A(r))[:8]:
        print(f"  id={r['survey_id']:>5} {A(r):>7,}  [{r['survey_type_name']}] {r['agency_name'][:28]}")
        print(f"        {r['survey_name']}")

    a = [A(r) for r in closed]
    print("\n=== GINI SENSITIVITY (closed) ===")
    order = sorted(closed, key=lambda r: -A(r))
    sso = "สำนักงานประกันสังคม"
    variants = [
        ("all closed", a),
        ("excl. largest", [A(r) for r in order[1:]]),
        ("excl. 8 largest", [A(r) for r in order[8:]]),
        ("excl. Social Security Office", [A(r) for r in closed if r["agency_name"] != sso]),
        ("positive responses only", [x for x in a if x > 0]),
    ]
    for lab, v in variants:
        s1, k1 = topshare(v, 1)
        print(f"  {lab:<30} n={len(v):>5}  Gini {gini(v):.4f}  top1% ({k1}) {s1:5.1f}%")

    print("\n=== 2026 DEPENDS ON ONE CASE ===")
    y26 = [r for r in closed if r["close_year"] == "2026"]
    t26 = sum(A(r) for r in y26)
    big = max(y26, key=A)
    print(f"  2026 total {t26:,}; largest single {A(big):,} = {100*A(big)/t26:.1f}%")
    print(f"  2026 excluding it: {t26-A(big):,}  vs full-year 2025: "
          f"{sum(A(r) for r in closed if r['close_year']=='2025'):,}")
    print("  NB 2026 is year-to-date (census taken 21 Sep 2026)")

    print("\n=== COMPOSITION SHIFT 2025 -> 2026 ===")
    for t in ("ร่างกฎหมาย", "กม.ลำดับรองอื่นๆ", "หลักการ", "ประเมินผลสัมฤทธิ์"):
        c25 = [A(r) for r in closed if r["close_year"] == "2025" and r["survey_type_name"] == t]
        c26 = [A(r) for r in closed if r["close_year"] == "2026" and r["survey_type_name"] == t]
        print(f"  {t:<22} n {len(c25):>4} -> {len(c26):<4}   "
              f"median {st.median(c25) if c25 else 0:>5.0f} -> {st.median(c26) if c26 else 0:<5.0f}")

    print("\n=== STAKEHOLDER FIELD: all groups ===")
    def bucket(n):
        return ("0" if n == 0 else "1-5" if n <= 5 else "6-20" if n <= 20
                else "21-50" if n <= 50 else ">50")
    g = defaultdict(list)
    for r in closed:
        g[bucket(int(r["n_invited"]))].append(A(r))
    for k in ("0", "1-5", "6-20", "21-50", ">50"):
        v = g[k]
        z = sum(1 for x in v if x == 0)
        print(f"  {k:>6}: n={len(v):>5}  median {st.median(v):>5.0f}  zero {100*z/len(v):5.1f}%")
    nz = [r for r in closed if int(r["n_invited"]) > 0]
    print(f"  Spearman among nonempty lists only (n={len(nz)}): "
          f"{spearman([int(r['n_invited']) for r in nz], [A(r) for r in nz]):+.3f}")
    print("  NB Spearman on log(1+x) equals Spearman on x: ranks are preserved.")

    print("\n=== RESPONSE/VIEW RATIO: not a stable funnel ===")
    rr = sorted(A(r) / V(r) for r in closed if V(r) > 0 and A(r) > 0)
    q1, q3 = rr[len(rr)//4], rr[3*len(rr)//4]
    print(f"  n={len(rr)}  median {st.median(rr):.4f}  IQR {q1:.4f}-{q3:.4f}  max {rr[-1]:.2f}")
    print("  ratios of the three largest consultations:")
    for r in sorted(closed, key=lambda r: -A(r))[:3]:
        if V(r):
            print(f"    id={r['survey_id']}: {A(r):,}/{V(r):,} = {A(r)/V(r):.2f}")
    over = [r for r in closed if V(r) > 0 and A(r) > V(r)]
    print(f"  consultations with MORE responses than views: {len(over)}")
    for r in sorted(over, key=lambda r: -A(r))[:3]:
        print(f"    id={r['survey_id']}: {A(r):,} responses, {V(r):,} views")

    print("\n=== affected_person: report blanks separately ===")
    blank = [A(r) for r in closed if not r["affected_person"].strip()]
    named = [A(r) for r in closed if r["affects_prachachon"] == "1"]
    other = [A(r) for r in closed
             if r["affected_person"].strip() and r["affects_prachachon"] == "0"]
    for lab, v in (("blank", blank), ("names ประชาชน", named), ("named, not ประชาชน", other)):
        z = sum(1 for x in v if x == 0)
        print(f"  {lab:<22} n={len(v):>5}  median {st.median(v):>5.0f}  zero {100*z/len(v):5.1f}%")

    print("\n=== Norway benchmark depends entirely on scope ===")
    nor = 6.28
    for lab, s in (("primary legislation only",
                    [r for r in closed if r["survey_type_name"] == "ร่างกฎหมาย"]),
                   ("all closed types", closed)):
        z = sum(1 for r in s if A(r) == 0)
        print(f"  {lab:<26} zero {100*z/len(s):5.2f}%  ratio to Norway {100*z/len(s)/nor:.2f}x")


if __name__ == "__main__":
    main()
