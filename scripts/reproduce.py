"""Regenerate every figure stated in the manuscript, labelled by where it appears.

Run:  python3 scripts/reproduce.py

Reads only data/consultations.csv. Nothing here touches the network, so the
output is stable: re-fetching the portal would not reproduce historical counters,
because response and view counts continue to move.

Each block prints the manuscript location, so a reader can check any number
against the text without reading the code.
"""

import statistics as st
from collections import defaultdict

from common import load, gini, top_share, spearman, SSO


def head(loc, what):
    print(f"\n{'-'*78}\n{loc}  |  {what}\n{'-'*78}")


def main():
    allrows = load(closed_only=False)
    rows = load()
    R = lambda r: r.responses

    head("Abstract, sec. 3.2", "populations, reported separately")
    for lab, s in (("all records", allrows), ("closed", rows)):
        print(f"  {lab:<12} n={len(s):>5}  agencies={len({r['agency_name'] for r in s}):>4}"
              f"  responses={sum(R(r) for r in s):>10,}")
    print(f"  still open: {len(allrows)-len(rows)}")
    ds = sorted(r["start_date"] for r in allrows if r["start_date"])
    print(f"  date range: {ds[0]} to {ds[-1]}")

    head("Sec. 3.3", "response-field validation denominators")
    p = [r for r in rows if r["isconclude"] == "P"]
    print(f"  closed with published summary: {len(p)}")
    print(f"  ... of which recorded >0 responses: {sum(1 for r in p if R(r) > 0)}")

    head("Table 1", "recorded participation by year of closure")
    by_year = defaultdict(list)
    for r in rows:
        by_year[r["close_year"]].append(R(r))
    for y in sorted(by_year):
        v = by_year[y]
        z = sum(1 for x in v if x == 0)
        print(f"  {y}  n={len(v):>5}  median {st.median(v):>3.0f}  "
              f"zero {100*z/len(v):>5.1f}%  total {sum(v):>9,}")

    head("Sec. 4", "2026 depends on one case; 2026 is year-to-date")
    y26 = [r for r in rows if r["close_year"] == "2026"]
    t26, big = sum(R(r) for r in y26), max(y26, key=R)
    t25 = sum(R(r) for r in rows if r["close_year"] == "2025")
    print(f"  2026 total {t26:,}; largest single {R(big):,} = {100*R(big)/t26:.1f}%")
    print(f"  2026 excluding it {t26-R(big):,}  vs full-year 2025 {t25:,}")

    head("Table 2", "composition and median responses by type, 2025 vs 2026")
    for t in ("ร่างกฎหมาย", "กม.ลำดับรองอื่นๆ", "หลักการ", "ประเมินผลสัมฤทธิ์"):
        a = [R(r) for r in rows if r["close_year"] == "2025" and r["survey_type_name"] == t]
        b = [R(r) for r in rows if r["close_year"] == "2026" and r["survey_type_name"] == t]
        print(f"  {t:<22} n {len(a):>4} -> {len(b):<4}  median "
              f"{st.median(a) if a else 0:>3.0f} -> {st.median(b) if b else 0:<3.0f}")

    head("Sec. 4", "sample bias: census vs convenience samples")
    d = [R(r) for r in rows if r["survey_type_name"] == "ร่างกฎหมาย"]
    print(f"  primary legislation n={len(d)}  zero {100*sum(1 for x in d if x==0)/len(d):.2f}%")
    print("  (convenience samples of 1,212 and 1,661 gave 14.7% and 19.7%)")

    head("Sec. 5, Table 3", "concentration and its sensitivity")
    a = [R(r) for r in rows]
    le5 = [x for x in a if x <= 5]
    print(f"  median {st.median(a):.0f}  mean {st.mean(a):.1f}  total {sum(a):,}")
    print(f"  <=5 responses: {len(le5)} ({100*len(le5)/len(a):.1f}%) holding "
          f"{100*sum(le5)/sum(a):.2f}% of responses")
    order = sorted(rows, key=lambda r: -R(r))
    for lab, v in (
        ("all closed", a),
        ("excluding largest", [R(r) for r in order[1:]]),
        ("excluding 8 largest", [R(r) for r in order[8:]]),
        ("excluding Social Security Office", [R(r) for r in rows if r["agency_name"] != SSO]),
        ("positive responses only", [x for x in a if x > 0]),
    ):
        s1, k = top_share(v, 1)
        print(f"  {lab:<34} n={len(v):>5}  Gini {gini(v):.4f}  top1% ({k:>2}) {s1:5.1f}%")
    print(f"  largest single share: {100*max(a)/sum(a):.1f}%")
    d = [R(r) for r in rows if r["survey_type_name"] == "ร่างกฎหมาย"]
    s1, k = top_share(d, 1)
    print(f"  primary legislation: n={len(d)} Gini {gini(d):.3f} median {st.median(d):.0f} "
          f"top1% ({k}) {s1:.1f}%")

    head("Table 4", "the eight largest consultations")
    for r in order[:8]:
        print(f"  {R(r):>7,}  id={r['survey_id']:>5}  [{r['survey_type_name']}] "
              f"{r['agency_name'][:24]}")
        print(f"           {r['survey_name'][:88]}")

    head("Sec. 5.2", "Norway comparison is a choice of scope")
    for lab, s in (("primary legislation only",
                    [r for r in rows if r["survey_type_name"] == "ร่างกฎหมาย"]),
                   ("all closed types", rows)):
        z = 100 * sum(1 for r in s if R(r) == 0) / len(s)
        print(f"  {lab:<26} zero {z:5.2f}%   ratio to Norway 6.28%: {z/6.28:.2f}x")

    head("Table 5", "Spearman rho with recorded responses")
    y = [R(r) for r in rows]
    for lab, xs in (("view count", [r.views for r in rows]),
                    ("duration in days", [r.duration for r in rows]),
                    ("stakeholder agencies listed", [r.invited for r in rows]),
                    ("questions in the form", [r.questions for r in rows])):
        print(f"  {lab:<30} {spearman(xs, y):+.3f}")
    ly = [__import__("math").log1p(v) for v in y]
    print(f"  (check) rho on log(1+responses) for view count: "
          f"{spearman([r.views for r in rows], ly):+.3f}  -- identical, ranks preserved")

    head("Sec. 6.1", "views: funnel is not stable")
    rr = sorted(R(r) / r.views for r in rows if r.views > 0 and R(r) > 0)
    q1, q3 = rr[len(rr) // 4], rr[3 * len(rr) // 4]
    print(f"  n={len(rr)} median {st.median(rr):.4f}  IQR {q1:.4f}-{q3:.4f}  max {rr[-1]:.2f}")
    for r in order[:3]:
        print(f"    id={r['survey_id']}: {R(r):,}/{r.views:,} = {R(r)/r.views:.2f}")
    for r in rows:
        if r.views and R(r) > r.views:
            print(f"    more responses than views: id={r['survey_id']} "
                  f"{R(r):,} responses, {r.views:,} views")
    print("  median views by response bucket:")
    for lo, hi, nm in ((0, 0, "0"), (1, 5, "1-5"), (6, 20, "6-20"),
                       (21, 100, "21-100"), (101, 10**9, ">100")):
        v = [r.views for r in rows if lo <= R(r) <= hi]
        print(f"    {nm:>7}: n={len(v):>5}  median {st.median(v):>6.0f}")

    head("Sec. 6.2, Table 6", "stakeholder field")
    empt = [r for r in rows if r.invited == 0]
    print(f"  listing none: {len(empt)} ({100*len(empt)/len(rows):.1f}%)")
    print("  (null vs empty string requires the raw payload; 3,331 null / 224 empty)")
    g = defaultdict(list)
    for r in rows:
        n = r.invited
        g["0" if n == 0 else "1-5" if n <= 5 else "6-20" if n <= 20
          else "21-50" if n <= 50 else ">50"].append(R(r))
    for k in ("0", "1-5", "6-20", "21-50", ">50"):
        v = g[k]
        print(f"    {k:>6}: n={len(v):>5}  median {st.median(v):>4.0f}  "
              f"zero {100*sum(1 for x in v if x==0)/len(v):5.1f}%")
    nz = [r for r in rows if r.invited > 0]
    print(f"  rho among non-empty lists (n={len(nz)}): "
          f"{spearman([r.invited for r in nz], [R(r) for r in nz]):+.3f}")

    head("Table 7", "description of affected persons, three states")
    groups = {
        "names ประชาชน": [R(r) for r in rows if r["affects_prachachon"] == "1"],
        "blank": [R(r) for r in rows if not r["affected_person"].strip()],
        "names others": [R(r) for r in rows
                         if r["affected_person"].strip() and r["affects_prachachon"] == "0"],
    }
    for k, v in groups.items():
        print(f"  {k:<18} n={len(v):>5}  median {st.median(v):>4.0f}  "
              f"zero {100*sum(1 for x in v if x==0)/len(v):5.1f}%")

    head("Sec. 6.4", "duration against the advised periods")
    dur = [r.duration for r in rows]
    print(f"  median {st.median(dur):.0f} days")
    for thr in (15, 30):
        c = sum(1 for x in dur if x < thr)
        print(f"  shorter than {thr} days: {c} ({100*c/len(dur):.1f}%)")
    for t in ("ร่างกฎหมาย", "กม.ลำดับรองอื่นๆ"):
        v = [r.duration for r in rows if r["survey_type_name"] == t]
        print(f"  {t:<22} median {st.median(v):>3.0f}d  "
              f"under 30d {100*sum(1 for x in v if x<30)/len(v):.1f}%")
    wk = [R(r) for r in rows if r.duration <= 7]
    print(f"  running 7 days or fewer: n={len(wk)} median {st.median(wk):.0f} responses")

    head("Table 8", "agencies with 50 or more closed consultations")
    by_ag = defaultdict(list)
    for r in rows:
        by_ag[r["agency_name"]].append(R(r))
    big_ag = {k: v for k, v in by_ag.items() if len(v) >= 50}
    print(f"  qualifying agencies: {len(big_ag)}   distinct agencies overall: {len(by_ag)}")
    for ag, v in sorted(big_ag.items(), key=lambda kv: st.median(kv[1])):
        print(f"    n={len(v):>4} median {st.median(v):>5.0f} "
              f"zero {100*sum(1 for x in v if x==0)/len(v):5.1f}%  {ag[:44]}")
    tot = sum(R(r) for r in rows)
    print(f"  Social Security Office share of all responses: "
          f"{100*sum(by_ag[SSO])/tot:.1f}% ({sum(by_ag[SSO]):,})")


if __name__ == "__main__":
    main()
