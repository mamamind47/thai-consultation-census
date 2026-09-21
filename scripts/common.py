"""Shared loading and statistics for the analysis scripts.

Everything reads data/consultations.csv, the published dataset, so that the
figures in the manuscript can be reproduced without re-running the collection.
The raw API payload (data/surveys.jsonl) is needed only to rebuild the CSV, and
re-fetching it would not reproduce historical counters in any case, since the
portal's response and view counts move.
"""

import csv
import math
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "consultations.csv"

TYPES = ("ร่างกฎหมาย", "กม.ลำดับรองอื่นๆ", "ประเมินผลสัมฤทธิ์", "หลักการ")
SSO = "สำนักงานประกันสังคม"


class Row(dict):
    """A consultation, with the numeric fields already parsed."""

    @property
    def responses(self):
        return int(self["answer_count"])

    @property
    def views(self):
        return int(self["view_count"])

    @property
    def duration(self):
        return int(self["duration_day"] or 0)

    @property
    def invited(self):
        return int(self["n_invited"])

    @property
    def questions(self):
        return int(self["question_count"] or 0)


def load(closed_only=True):
    with DATA.open(encoding="utf-8") as fh:
        rows = [Row(r) for r in csv.DictReader(fh)]
    if closed_only:
        rows = [r for r in rows if r["closed"] == "1"]
    return rows


def gini(xs):
    """Gini over non-negative values; zeros are permitted and meaningful here."""
    xs = sorted(xs)
    n = len(xs)
    if n == 0 or sum(xs) == 0:
        return float("nan")
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return (2 * cum) / (n * sum(xs)) - (n + 1) / n


def top_share(xs, pct):
    """Share of the total held by the top `pct` per cent, and how many that is.

    The count is floor(n * pct / 100), floored at one, which is the convention
    the manuscript states: 53 of 5,371 at one per cent.
    """
    xs = sorted(xs, reverse=True)
    k = max(1, len(xs) * pct // 100)
    return 100 * sum(xs[:k]) / sum(xs), k


def spearman(xs, ys):
    """Spearman's rho with average ranks for ties.

    Note that rho on log(1+x) equals rho on x: a monotonic transform preserves
    ranks. The manuscript reports rho on the raw counts for that reason.
    """
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


def describe(values, label, width=26):
    z = sum(1 for x in values if x == 0)
    n = len(values)
    return (f"{label:<{width}} n={n:>5}  median {st.median(values):>6.0f}  "
            f"mean {st.mean(values):>9.1f}  zero {100*z/n:>5.1f}%")
