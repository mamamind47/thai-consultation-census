# What the census shows

All figures below are the 5,371 **closed** consultations (of 5,572 pulled), December 2020 –
September 2026. Reproduce with `scripts/analyze.py` and `scripts/explain.py`.

## 1. Participation is rising sharply

This is the first thing to say, because it contradicts the assumption the project started
from — that the mechanism sits unused.

| Year closed | n | median comments | zero comments | total comments |
|---|---:|---:|---:|---:|
| 2021 | 69 | 3 | 27.5% | 16,264 |
| 2022 | 386 | 2 | 34.2% | 31,488 |
| 2023 | 1,153 | 4 | 27.6% | 111,877 |
| 2024 | 1,285 | 4 | 29.6% | 199,720 |
| 2025 | 1,168 | 8 | 10.8% | 438,144 |
| 2026 | 1,310 | 11 | **9.2%** | 982,956 |

Consultations receiving nothing at all fell from about one in three to about one in eleven.
Annual comment volume grew roughly 31×. Any claim that Thailand's consultation mechanism is
dormant is false on this data.

## 2. But participation is extraordinarily concentrated

| | |
|---|---|
| Gini coefficient | **0.967** |
| Top 1% (53 consultations) | **82.0%** of all comments |
| Top 5% (268) | 91.9% |
| Single largest consultation | **39.3%** of all comments |
| The 48.3% with ≤5 comments | **0.20%** of all comments |
| median 6 | mean 331.5 |

One lead agency, **สำนักงานประกันสังคม** (Social Security Office), accounts for **49.3%**
of every comment in the system — 877,075 of 1,780,449.

Restricted to primary legislation (ร่างกฎหมาย, n=941): Gini 0.922, median 13,
11.7% zero, top 1% hold 53.4%.

So both statements are true at once: the mechanism is being used more every year, and
almost all of that use is a handful of consultations.

## 3. Benchmark against Norway

| | zero submissions |
|---|---|
| Thailand, primary legislation (n=941) | **11.7%** |
| Norway, all consultations (n=4,062) — Bunea et al. 2025 | 6.28% |

Roughly 1.9×, not the order-of-magnitude gap an earlier sample suggested.

## 4. What the mega-consultations have in common

The eight largest are all rules that change money reaching individuals who already belong
to an organised mass constituency:

| Comments | Agency | Subject |
|---:|---|---|
| 699,927 | สำนักงานประกันสังคม | ministerial regulation on contributions |
| 111,201 | อย. | drug listing notification |
| 97,062 | สำนักงานประกันสังคม | pension calculation formula |
| 77,789 | สำนักงานเศรษฐกิจการคลัง | draft primary legislation |
| 55,584 | สำนักงานประกันสังคม | wage ceiling for contributions |
| 53,754 | กรมสนับสนุนบริการสุขภาพ | village health volunteer (อสม.) bill |
| 29,588 | กรมสนับสนุนบริการสุขภาพ | อสม. bill, earlier round |
| 23,015 | กรมบัญชีกลาง | civil servant medical benefits |

## 5. Agency variation is the largest untold story

Among agencies running 50 or more consultations:

| Agency | n | median | zero |
|---|---:|---:|---:|
| ก.ล.ต. (SEC) | 257 | **0** | 50.2% |
| คปภ. (OIC) | 214 | **0** | 53.7% |
| สำนักงานปรมาณูเพื่อสันติ | 51 | 0 | 56.9% |
| กรมเจ้าท่า | 67 | 0 | 50.7% |
| ธนาคารแห่งประเทศไทย | 104 | 1 | 44.2% |
| … | | | |
| กรมประมง | 559 | 18 | 4.5% |
| กรมศุลกากร | 110 | 27 | 12.7% |
| กรมทรัพยากรทางทะเลและชายฝั่ง | 64 | 44 | **0.0%** |
| กรมการปกครอง | 89 | 74 | 12.4% |
| กรมการขนส่งทางราง | 57 | **135** | 1.8% |

Financial-sector regulators consult constantly into near-silence. The SEC has run 257
consultations at a median of zero comments. Fisheries has run 559 at a median of 18.

## 6. What correlates with participation

Spearman rho against log(1 + comments), n=5,371:

| Predictor | rho |
|---|---:|
| `view_count` | **+0.742** |
| `duration_day` | +0.161 |
| `n_invited` (stakeholder agencies listed) | **+0.025** |
| `question_count` | −0.025 |

**Visibility dominates.** Consultations that received no comments have a median of
**62 page views**; those receiving more than 100 comments have a median of **1,645**.
Silence is mostly a matter of nobody arriving, not of visitors declining to write.

| Comments | n | median views |
|---|---:|---:|
| zero | 1,095 | 62 |
| 1–5 | 1,499 | 140 |
| 6–20 | 1,010 | 274 |
| 21–100 | 1,051 | 469 |
| >100 | 716 | 1,645 |

**Naming the public as affected matters.** Where `affected_person` lists ประชาชน:
median 13 comments, 13.1% zero. Where it does not: median 3, 25.1% zero.

**The invitation lever is missing.** In Bunea et al.'s Norwegian data, the number of
invitations issued is a central driver of participation. The Thai analogue barely moves
anything (rho = +0.025) — because the field is usually empty. **3,555 of 5,371
consultations (66%) list no stakeholder agencies at all.**

This is worth stating carefully. Section 14 paragraph 2 of the 2019 Act provides that where
a state agency knows the contact details of affected persons, it **shall** notify them;
section 15 requires the Office of the Council of State to register stakeholders through the
central system and requires agencies to compile and submit stakeholder lists. What the data
shows is that the public record carries no listed stakeholders for two thirds of
consultations. It does **not** show that notification failed to occur — `stackholders_agency`
holds agency identifiers, not individuals, and individual registrations may not surface in
the public payload.

## 7. One thing that is *not* a finding

323 consultations (6.0%) ran for fewer than 15 days, and 35% of those received nothing.
That is **not** a breach of any statutory minimum: sections 13–15 of the 2019 Act set no
minimum consultation period. Section 14 requires only that the start and end dates be
announced. Checked against the Gazette text (เล่ม ๑๓๖ ตอนที่ ๗๒ ก, 31 May 2019).

## Sources

- Bunea, A., Chrisp, J. & Vrangbæk, K. (2025). Do government invitations to consultations
  shape stakeholder participation in public policymaking? *European Journal of Political
  Research*. doi:10.1111/1475-6765.70027
- OECD (2025). *Regulatory Reform in Thailand*. Box 3.3.
- Thananithichot, S., Satidporn, W. & Tangthavorn, C. (2026). Institutionalizing Public
  Consultation in Thai Health Legislation. *Asia-Pacific Social Science Review* 26(2).
- TDRI (2024). การมีส่วนร่วมของประชาชนในการออกกฎหมายตามมาตรา 77 ของรัฐธรรมนูญฯ 2560.
- พระราชบัญญัติหลักเกณฑ์การจัดทำร่างกฎหมายและการประเมินผลสัมฤทธิ์ของกฎหมาย พ.ศ. ๒๕๖๒,
  ราชกิจจานุเบกษา เล่ม ๑๓๖ ตอนที่ ๗๒ ก (๓๑ พฤษภาคม ๒๕๖๒).
