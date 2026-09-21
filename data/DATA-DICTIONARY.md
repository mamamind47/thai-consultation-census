# Data dictionary — `consultations.csv`

One row per consultation published on Thailand's Central Law Portal
(ระบบกลางทางกฎหมาย, `law.go.th`). 5,572 rows, 21 columns, UTF-8, comma-separated,
header row present. Collected 21 September 2026; see `fetch-meta.json` for the
endpoint, page log, timing and SHA-256 of the raw payload.

Columns marked **derived** are computed in `scripts/make_dataset.py`; all others
are copied unchanged from the portal's listing endpoint.

| Column | Type | Description |
|---|---|---|
| `survey_id` | integer | Portal identifier. Primary key. Retrieve the notice at `https://law.go.th/listeningDetail?survey_id=<id>`. |
| `survey_name` | text (Thai) | Title of the consultation as posted. |
| `survey_type_name` | categorical (Thai) | One of four: `ร่างกฎหมาย` primary legislation; `กม.ลำดับรองอื่นๆ` subordinate regulation; `ประเมินผลสัมฤทธิ์` ex post evaluation; `หลักการ` consultation at the stage of principles. **Note:** this does not cleanly separate instrument types — bills also appear under `หลักการ`. |
| `agency_name` | text (Thai) | Lead agency. 294 distinct values across all rows, 293 among closed rows. |
| `agency_id` | integer | Portal's agency identifier. |
| `ministry_id` | integer | Portal's parent-ministry identifier. Not independently validated. |
| `start_date` | date `YYYY-MM-DD` | Opening date. Range 2020-12-27 to 2026-09-20. |
| `end_date` | date `YYYY-MM-DD` | Closing date. |
| `duration_day` | integer | **Nominal** duration as the portal reports it. Does not always reconcile with an inclusive calendar-day count of `start_date`–`end_date`; see Limitations. |
| `closed` | 0/1 | **Derived.** 1 if `end_date` precedes the collection timestamp. 5,371 closed, 201 still open. Analysis uses closed rows only. |
| `close_year` | integer | **Derived** calendar year of `end_date`. 2026 is year-to-date. |
| `answer_count` | integer | Recorded responses. See *Unit* below. |
| `view_count` | integer | Page views. Counting basis undocumented; disagrees with the OECD's figure for at least one consultation. Treat as weaker evidence than `answer_count`. |
| `question_count` | integer | Number of questions in the response form. |
| `n_invited` | integer | **Derived** count of identifiers in the portal's `stackholders_agency` field. See *Stakeholders* below. |
| `affects_prachachon` | 0/1 | **Derived.** 1 if `affected_person` contains `ประชาชน` (the general public). |
| `affected_person` | text (Thai) | Free-text, comma-separated list of who the draft is said to affect. **Blank in 1,484 closed rows** — report blanks as their own category, not merged with either other state. |
| `tags` | text (Thai) | Free-text, comma-separated keywords set by the agency. |
| `isconclude` | text | Publication status of the summary of results. `P` indicates published: 2,632 closed rows, of which 2,247 also recorded at least one response. |
| `law_group_id` | integer | Portal's subject-area grouping. Labels are in the detail endpoint, not here. |
| `url` | text | **Derived** permalink to the consultation notice. |

## Unit of `answer_count`

The field counts responses to the portal consultation. Two checks were made and
both have limits, set out in full in the manuscript:

- The OECD's 2025 review names one consultation as having received 55,591
  comments; this field gives 55,584 for that record. This establishes order of
  magnitude, not unit.
- For 82 consultations whose published summary states a respondent count in
  prose, 66% match exactly. That exercise covers only consultations that both
  published a summary *and* recorded at least one response, cannot validate zeros,
  and selects the closest stated number where a document states several.

The dataset therefore uses **recorded responses**. It is not established that one
unit equals one unique person, and the field is not a comment-per-question tally.

## Stakeholders (`n_invited`)

This counts agency identifiers attached to a consultation. It is **not** a measure
of the statutory duties in ss.14–15 of the 2019 Act: it does not record stakeholder
registrations, invitations issued, notifications delivered, or recipients reached.
Section 14 paragraph 2 expressly permits direct notification, which leaves no trace
here. 3,555 closed rows list none; in the raw payload 3,331 of those are `null` and
224 are an empty string, a distinction whose meaning is undocumented and which the
CSV flattens to `0`.

## What the dataset does not contain

Respondent identities or categories; response texts; notification or registration
records; consultations conducted through the other channels s.13 permits; the
parliamentary consultation site; and any denominator of drafting exercises that
should have been consulted on but were not.

## Reproduction

`python3 scripts/reproduce.py` regenerates every figure stated in the manuscript
from this file alone, labelled by the table or section where it appears. It does
not use the network. Re-running `scripts/fetch.py` would not reproduce these
counters: the portal's response and view counts continue to move.
