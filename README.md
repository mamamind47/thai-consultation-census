# Thailand Central Law Portal — consultation participation census

A complete census of public consultations posted to Thailand's Central Law Portal
(ระบบกลางทางกฎหมาย, law.go.th), the portal mandated by the *Act on Legislative Drafting
and Evaluation of Law B.E. 2562 (2019)* implementing s.77 of the 2017 Constitution.

**5,572 consultations, December 2020 – September 2026, 293 lead agencies, 1,780,449 responses.**

Pulled 2026-09-21. See [FINDINGS.md](FINDINGS.md) for what the data shows.

## Why this exists

Everyone writing about Thai public consultation says participation is thin, and nobody
publishes the numbers:

- **TDRI (2024)**, *การมีส่วนร่วมของประชาชนในการออกกฎหมายตามมาตรา 77* — a monitoring study
  that concludes there is a lack of genuine participation by affected stakeholders. No counts.
- **Thananithichot, Satidporn & Tangthavorn (2026)**, *Asia-Pacific Social Science Review* —
  qualitative comparative case study of three health laws. No portal data.
- **OECD (2025)**, *Regulatory Reform in Thailand*, Box 3.3 — reports aggregate totals only
  (877 projects Oct 2021–Sep 2022; ~94,000 comments in 2023), sourced from the Thai
  government's own questionnaire response, and notes elsewhere that data on RIA adoption
  rates "are not yet able to be ascertained by the Office of the Council of State".

The portal's own listing endpoint answers the question directly, so this repository
just asks it and publishes the result.

The comparison point is **Bunea & Nørbech (2025)**, *European Journal of Political
Research*, which does exactly this for Norway: 4,062 consultations, 2009–2023, of which
**6.28% received zero submissions**.

## Layout

```
scripts/common.py          shared loading, Gini, Spearman
scripts/reproduce.py       every figure in the manuscript, labelled by table
scripts/validate_unit.py   response field vs agencies' own published summaries
scripts/fetch.py           census pull + provenance record
scripts/make_dataset.py    raw JSONL -> tidy CSV
data/consultations.csv     the dataset, 5,572 rows x 21 columns   <- published
data/DATA-DICTIONARY.md    every column, and what the data omit   <- published
data/fetch-meta.json       endpoint, timing, page log, sha256     <- published
data/surveys.jsonl         raw API payloads, ~207 MB              <- gitignored
paper/                     manuscript source
```

## Reproducing the manuscript

Every number stated in the paper comes from the published CSV and nothing else:

```
python3 scripts/reproduce.py
```

No network access, no raw payload, no dependencies beyond the standard library.
Output is labelled by the table or section where each figure appears.

**Re-fetching does not reproduce these figures.** `scripts/fetch.py` rebuilds the raw
payload and `scripts/make_dataset.py` derives the CSV from it, but the portal's response
and view counters continue to move, so a fresh pull gives a later snapshot rather than
this one. The CSV is the archival artefact; treat the fetch scripts as documentation of
how it was made.

`scripts/validate_unit.py` re-runs the response-field check. It does use the network,
downloading agencies' published summary documents, and needs `pdftotext` on the path.

## Source

Unauthenticated public endpoint, the same one the law.go.th front end calls:

```
POST https://apig.law.go.th/dga-user-service-survey/surveys
{"searchText": "", "size": 200, "page": <n>, "sort": "desc"}
```

Each consultation is viewable at `https://law.go.th/listeningDetail?survey_id=<id>`.

## Traps, all of which cost us something

1. **`lastPage` lies.** The endpoint reports `lastPage: 27`; there are really 31 pages.
   Paginate until a page comes back empty, and deduplicate on `survey_id`.
   (This pull found 0 duplicates across 31 pages.)

2. **Page sizes vary.** Requesting `size: 200` returns anywhere from 73 to 200 rows.
   Do not infer the total from page count × page size.

3. **`str.splitlines()` tears records in half.** The HTML content fields contain U+2028,
   which Python's `splitlines()` treats as a line break but `json.dumps` does not escape.
   Read the JSONL with `split("\n")`.

4. **The listing is recency-sorted, so samples are biased.** A 1,212-row sample gave 14.7%
   zero-response draft laws and a 1,661-row sample gave 19.7%; the census says **11.7%**.
   Participation has risen sharply over time, so any sample weighted toward recent or
   toward old records is wrong in a predictable direction. Take the census.

5. **Open consultations are not finished collecting.** 201 of 5,572 were still open at
   fetch time. All analysis here uses the 5,371 closed ones. Determine closure from
   `end_date` against your fetch timestamp, not from `date_balance`, which the server
   computes at request time.

6. **`answer_count` counts respondents, validated two ways.** OECD (2025) Box 3.3 names
   the largest consultation as **55,591 comments**; this field gives **55,584** for that
   record (ร่างกฎกระทรวงกำหนดค่าจ้างขั้นต่ำและขั้นสูงฯ, closed 2023-02-27). Separately,
   `scripts/validate_unit.py` compares the field against the respondent counts agencies
   state in their own published summaries ("ผู้จัดส่งความคิดเห็น จำนวน ๓๑ ราย"): **68%
   exact agreement** on the unbiased subset. See Limitations for the residual 32%.

7. **Normalise the pattern, not just the text.** Thai PDF extraction drops combining marks,
   so phrase matching runs on a mark-stripped string — but the search literals must be put
   through the same normaliser. `"จำนวน"` normalises to `"จานวน"`; matching the raw literal
   against normalised text returns nothing, silently, with no error.

## Limitations

- **`answer_count` agrees with agencies' own figures about two thirds of the time.**
  Across 82 consultations whose summary states a respondent count, 66% match exactly;
  on the 22 documents stating exactly one number (no selection bias) the rate is 68%.
  Of the remainder, 18% state fewer than the field (agencies often report only those
  giving substantive comments, excluding "ไม่แสดงความคิดเห็น") and 16% state more
  (summaries may cover the meetings, interviews and surveys that s.13 also permits).
  So the field is a respondent count, with roughly a third of cases diverging for
  reasons that are directional and explicable rather than random.
- **View counts disagree with OECD.** OECD reports 373,000 views for the 2023 wage-ceiling
  consultation; the API gives 197,695. Unexplained.
- **A second portal is not covered.** The Secretariat of the Parliament runs its own
  s.77 consultation site (parliament.go.th/section77) with 225+ legislative proposals.
  This census covers only the Central Law Portal.
- **`stackholders_agency` holds agency ids, not individuals.** Individual stakeholder
  registrations under s.15 may exist without appearing in the public payload. Claims
  about notification must be limited to what the public record shows.
- **Nothing here is causal.** Agencies choose what to consult on, how long to leave it
  open, and how hard to promote it. Every correlation reported is entangled with that choice.

## Archiving

The CSV, `fetch-meta.json` and `DATA-DICTIONARY.md` are the citable artefacts.
`CITATION.cff` carries the metadata. For a permanent identifier, deposit a tagged
release to Zenodo and record the DOI here and in the manuscript's data availability
statement; a GitHub URL alone does not satisfy most journals' data policies.

## Data licence

The underlying records are public documents published by Thai state agencies. The derived
dataset and the code are released under the terms in [LICENSE](LICENSE).
