# Thailand Central Law Portal — consultation participation census

A complete census of public consultations posted to Thailand's Central Law Portal
(ระบบกลางทางกฎหมาย, law.go.th), the portal mandated by the *Act on Legislative Drafting
and Evaluation of Law B.E. 2562 (2019)* implementing s.77 of the 2017 Constitution.

**5,572 consultations, December 2020 – September 2026, 293 lead agencies, 1,780,449 comments.**

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

The comparison point is **Bunea, Chrisp & Vrangbæk (2025)**, *European Journal of Political
Research*, which does exactly this for Norway: 4,062 consultations, 2009–2023, of which
**6.28% received zero submissions**.

## Layout

```
scripts/fetch.py         full census pull + provenance record
scripts/make_dataset.py  raw JSONL -> tidy CSV
scripts/analyze.py       participation distribution, concentration, benchmark
scripts/explain.py       what correlates with participation
data/consultations.csv   the dataset (5,572 rows, 21 columns)  <- published
data/fetch-meta.json     endpoint, timing, page log, sha256    <- published
data/surveys.jsonl       raw API payloads, ~207 MB             <- gitignored
```

Reproduce with:

```
python3 scripts/fetch.py && python3 scripts/make_dataset.py
python3 scripts/analyze.py && python3 scripts/explain.py
```

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
   zero-comment draft laws and a 1,661-row sample gave 19.7%; the census says **11.7%**.
   Participation has risen sharply over time, so any sample weighted toward recent or
   toward old records is wrong in a predictable direction. Take the census.

5. **Open consultations are not finished collecting.** 201 of 5,572 were still open at
   fetch time. All analysis here uses the 5,371 closed ones. Determine closure from
   `end_date` against your fetch timestamp, not from `date_balance`, which the server
   computes at request time.

6. **`answer_count` is comments, externally validated.** OECD (2025) Box 3.3 names the
   largest consultation as **55,591 comments**; this field gives **55,584** for that record
   (ร่างกฎกระทรวงกำหนดค่าจ้างขั้นต่ำและขั้นสูงฯ, closed 2023-02-27). Whether one comment
   equals one person is still **not** established — see Limitations.

## Limitations

- **Unit of `answer_count` is unresolved.** OECD calls these "comments", which does not
  settle whether the field counts submissions or unique respondents.
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

## Data licence

The underlying records are public documents published by Thai state agencies. The derived
dataset and the code are released under the terms in [LICENSE](LICENSE).
