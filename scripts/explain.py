"""What explains variation in participation across consultations?

Descriptive and correlational only. Nothing here identifies a causal effect:
agencies choose what to consult on and how to promote it, so every predictor
below is entangled with topic choice.

Predictors available in the listing payload:
  duration_day          how long the consultation stayed open
  n_invited             len(stackholders_agency) -- the agencies OCS/the lead
                        agency listed as stakeholders. This is the closest
                        analogue to Bunea et al. (2025)'s "invitations" variable.
  question_count        number of questions in the response form
  view_count            page views (a mediator, not an exogenous predictor)
  affected_person       free-text list of who the draft is said to affect
  agency_name           the lead agency
  survey_type_name      primary law / subordinate / ex post review / principles
"""

import json
import math
import statistics as st
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "surveys.jsonl"
META = ROOT / "data" / "fetch-meta.json"


def load_closed():
    text = SRC.read_text(encoding="utf-8")
    rows = [json.loads(l) for l in text.split("\n") if l.strip()]
    fetched = datetime.fromisoformat(
        json.loads(META.read_text(encoding="utf-8"))["fetch_finished_utc"]
    )
    out = []
    for r in rows:
        ed = r.get("end_date")
        if not ed:
            continue
        if datetime.fromisoformat(ed.replace("Z", "+00:00")) < fetched:
            out.append(r)
    return out


def n_invited(r):
    s = r.get("stackholders_agency")
    if not s:
        return 0
    return len([x for x in str(s).split(",") if x.strip()])


def spearman(xs, ys):
    """Spearman rho without scipy: Pearson on ranks, average ranks for ties."""
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


def bucket_report(rows, keyfn, label, min_n=25):
    groups = defaultdict(list)
    for r in rows:
        k = keyfn(r)
        if k is not None:
            groups[k].append(r.get("answer_count") or 0)
    print(f"\n--- {label} ---")
    for k in sorted(groups, key=lambda k: (str(type(k)), k)):
        v = groups[k]
        if len(v) < min_n:
            continue
        z = sum(1 for x in v if x == 0)
        print(f"  {str(k):<22} n={len(v):>5}  median {st.median(v):>6.0f}  "
              f"zero {100*z/len(v):>5.1f}%  mean {st.mean(v):>8.1f}")


def main():
    rows = load_closed()
    print(f"closed consultations: {len(rows)}")

    y = [r.get("answer_count") or 0 for r in rows]
    ly = [math.log1p(v) for v in y]

    print("\n=== Spearman rho with comment count ===")
    for name, fn in [
        ("duration_day", lambda r: r.get("duration_day") or 0),
        ("n_invited (stakeholder agencies)", n_invited),
        ("question_count", lambda r: int(r.get("question_count") or 0)),
        ("view_count", lambda r: r.get("view_count") or 0),
    ]:
        xs = [fn(r) for r in rows]
        print(f"  {name:<34} rho={spearman(xs, ly):+.3f}   "
              f"(median {st.median(xs):.0f}, max {max(xs)})")

    # Is n_invited doing anything once you look inside bands?
    bucket_report(rows, lambda r: (
        "0 invited" if n_invited(r) == 0 else
        "1-5" if n_invited(r) <= 5 else
        "6-20" if n_invited(r) <= 20 else
        "21-50" if n_invited(r) <= 50 else ">50"), "by number of stakeholder agencies listed")

    bucket_report(rows, lambda r: (
        "<=7 days" if (r.get("duration_day") or 0) <= 7 else
        "8-15" if (r.get("duration_day") or 0) <= 15 else
        "16-30" if (r.get("duration_day") or 0) <= 30 else ">30"), "by consultation length")

    # Who is said to be affected
    def affects_public(r):
        s = r.get("affected_person") or ""
        if not s:
            return None
        return "lists ประชาชน" if "ประชาชน" in s else "does not list ประชาชน"
    bucket_report(rows, affects_public, "by whether ประชาชน is listed as affected")

    bucket_report(rows, lambda r: r.get("survey_type_name"), "by consultation type")

    # Agency-level: separate the quiet regulators from the busy ones
    print("\n--- agencies with >=50 consultations, ranked by median comments ---")
    by_ag = defaultdict(list)
    for r in rows:
        by_ag[r.get("agency_name") or "(none)"].append(r.get("answer_count") or 0)
    big = {k: v for k, v in by_ag.items() if len(v) >= 50}
    for ag, v in sorted(big.items(), key=lambda kv: st.median(kv[1])):
        z = sum(1 for x in v if x == 0)
        print(f"  median {st.median(v):>6.0f}  zero {100*z/len(v):>5.1f}%  n={len(v):>4}  {ag[:46]}")

    # How much of the total is one policy family?
    print("\n--- concentration by lead agency ---")
    tot = sum(y)
    ag_tot = sorted(((sum(v), k) for k, v in by_ag.items()), reverse=True)
    for s, k in ag_tot[:8]:
        print(f"  {100*s/tot:>5.1f}% of all comments  ({s:>9,})  {k[:46]}")

    # Views as the funnel: do quiet consultations get seen at all?
    print("\n--- views by comment bucket ---")
    for lo, hi, nm in [(0, 0, "zero"), (1, 5, "1-5"), (6, 20, "6-20"),
                       (21, 100, "21-100"), (101, 10**9, ">100")]:
        v = [r.get("view_count") or 0 for r in rows if lo <= (r.get("answer_count") or 0) <= hi]
        if v:
            print(f"  {nm:>7}: n={len(v):>5}  median views {st.median(v):>8.0f}")


if __name__ == "__main__":
    main()
