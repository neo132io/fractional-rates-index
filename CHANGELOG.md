# Changelog

Every published figure that this index later corrected is recorded here, with what it said, what it
says now, and why it changed.

This file exists for the same reason the index exists. A statistic whose revisions are invisible
cannot be audited, and a dataset that is never contradicted is usually one nobody checked. Anyone who
cited an earlier version should be able to find out, from this file alone, whether the number they
quoted still holds.

---

## v1.1 — 2026-08-21

**Headline: the confirmed disclosure rate moved from 12.9% to 17.5%, and it moved because the method
was tested against itself rather than because more data arrived.**

### What changed, and what to do if you cited v1.0

| v1.0 published | v1.1 publishes | If you cited the old figure |
|---|---|---|
| 95 of 738 providers publish a price (12.9%) | **129 of 736 (17.5%)** | Correct it. The old rate understated disclosure by about a third |
| CPO is the least transparent role, 4.7% (5 of 106) | **CPO 13.5% (14 of 104); CFO is now least at 12.5%** | Correct it. The 4.7% was an artifact of unopened pricing pages |
| "CTO is roughly 5× more transparent than CPO" | **CTO 24.3%, roughly 2× CFO at 12.5%** | Withdraw the claim. It does not survive |
| 893 rows, 738 providers | **938 rows, 736 providers** | Update denominators |
| 681 rows record an absence (76.3%) | **645 of 938 (68.8%)** | Update |
| USD monthly band $299–$27,200, n=86 | **$299–$50,000, 122 tiers from 61 providers** | Update |
| Stage-one error rate 30% (3 of 10) | **43.6% (41 of 94)**, measured on a far larger sample | Use the new figure |
| "All USD" | **7 currencies:** USD, GBP, EUR, AUD, SGD, NZD, CHF | The USD-only limitation no longer describes the dataset |
| 218 rows browser-verified | **899 of 938**, and no row rests on screening alone | Update |

### Why it changed

Every verification pass before this one checked prices that automated screening had **reported**.
None of them tested the opposite failure: a provider recorded as publishing nothing that in fact
publishes something. On 2026-08-21 all 736 providers were opened in a browser.

**34 of the 643 providers previously recorded as unpriced turned out to publish a price** — a 5.3%
false-negative rate. **14 of those 34 had their price on a `/pricing` page no earlier pass had ever
opened.** That is a sampling error, not a parsing one: the tool read the page it was given,
correctly, and the price was somewhere else.

The result is that this project can now state both of its error rates rather than only the flattering
one. Screening reported prices that were not there on **43.6%** of what it flagged, and missed prices
that were there on **5.3%** of what it cleared.

### Corrections made to the file itself

- **The `verification` column was rewritten to match what was actually established.** 616 rows had
  carried `screened_only`, meaning no browser had confirmed them, while the prose claimed every
  provider had been opened. 599 absence rows confirmed read became `browser_verified`; 17 whose pages
  never rendered became `blocked` or `unreachable`. `screened_only` no longer appears in the dataset.
- **An overstatement was corrected in the same pass.** "All 736 opened and read" became **"700
  rendered and were read; 36 did not"** — a bot check, an empty body or a dead domain. Those 36 are
  counted in the denominator as publishing nothing, which makes **17.5% the floor of a 17.5–22.4%
  interval**, and the documents now say so.
- **Two providers were removed as defunct.** `coalescemanagement.com` now serves a domain-for-sale
  listing and `k2p.com` a hosting placeholder. Neither can support an observation in either
  direction, so the provider count fell from 738 to 736.
- **The maintainer's own row was corrected.** It recorded `8000–8000` while the page publishes a full
  range of **$5,000–$15,000** with $8,000 as the standard tier. The row now carries an explicit
  maintainer-disclosure note. No published band changed as a result.
- **The role-counting rule was stated exactly.** Methodology had described the denominator rule but
  not the numerator rule, and the two defensible readings disagree: crediting a provider to every role
  it appears under, rather than only to roles its priced row carries, moves CTO from 24.3% to 25.7%
  and CPO from 13.5% to 14.4%. The published table uses the narrower rule.
- **Two files that the pass had not reached were swept.** `analysis/market-size-reality-check.md` and
  `standard/scope-of-work.md` still asserted 95 of 738 (12.9%) as current, and the analysis file still
  carried the CPO rate at 5 of 106 — the exact claim the pass overturned, inside the document whose
  purpose is auditing other people's unsourced statistics.

### Found by a deep QA pass, after the v1.1 documents were written

A structural audit of the dataset — invariants the reproduction check does not test — found two
defects. Both were fixed, and the checks that would have caught them earlier are now part of the
suite.

- **One row was labelled `blocked` and was not blocked.** toptal.com rendered normally in the
  full-coverage pass (13,063 characters); what returned HTTP 404 was a role-specific path that does
  not exist. A missing page is evidence that a rate is not published, not a failure to observe the
  site — and the sibling row on the same URL was already `browser_verified`. Corrected to
  `browser_verified`, which moves `browser_verified` from 898 to 899 and `blocked` from 16 to 15.
- **Five rows carried no price yet asserted a currency**, two of them a unit as well. A currency is
  an observation about a price; where there is no price there is nothing for it to describe, and the
  published wording was already preserved verbatim in `notes`. The schema documents `currency` as
  "null on unpriced rows", which those five rows made false. Cleared. `USD` moves from 210 to 205 and
  `per_month` from 173 to 172 in the schema table.

Neither defect touched a headline figure: rows, providers, priced providers, the disclosure rate, the
read/unread split and all six currency bands are unchanged.

**Four other QA flags were examined and are correct as they stand**, recorded here so they are not
re-raised: three priced rows carry no unit because the provider attaches no period to the figure
(documented in methodology §5); two pairs of rows share a price because one provider sells four
distinct fixed-fee products at two price points; one marketplace publishes a $15/hour floor, which is
real and is excluded from the executive hourly band by the `offering_type` filter; and two domains
hold both readable and unreadable rows because different pages of the same site had different fates.

### Added

- [`CHANGELOG.md`](CHANGELOG.md) — this file.
- [`research/detector-gaps.md`](research/detector-gaps.md) — the five defects found in the
  price-detection tooling, each with a damage assessment established rather than assumed.

### Restructured

`methodology.md` had grown by accretion into a pass-by-pass narrative with sections numbered 5, 5b,
5c and 5e — there was no 5d — and it contained statements that contradicted each other: section 3 said
every row was captured on 2026-08-17 while section 5c listed four capture dates, and section 4 said
"All USD" while section 5c listed seven currencies. It is now a single clean document describing the
dataset as it stands, with the historical narrative moved here.

---

## v1.0 — 2026-08-17

First publication. 893 rows, 738 providers, one capture date, USD only.

Figures published in v1.0 that v1.1 supersedes are listed in the table above. The v1.0 tag remains in
this repository and its figures remain reproducible from the CSV as it stood at that tag.

### Known problems in v1.0, identified afterwards

- **The disclosure rate was too low**, because pricing pages linked from homepages were never opened.
- **The role table was wrong**, for the same reason, most severely for CPO.
- **The stage-one error rate rested on 10 observations.** It has since been measured on 94.
- **The dataset was described as USD-only.** It was not.

### Labels retired before or during v1.1

- **`rejected`** described the wrong party. It marked a row where a figure reported by automated
  screening was not found in the browser — but the reported figure came from **our screening tool**,
  not from the provider, so a row saying "reported figure rejected" read as a finding against a named
  business when it was a finding about our own tooling. Those rows now record the observation plainly.
  No factual content was removed in the rewording.
- **`fetch_only`** marked rows resting on an automated fetch. A merge found 43 of the then-89 apparent
  price-publishers in this state, 21 of them describing themselves as "WebFetch-verified" in their own
  notes. All were re-checked in a browser; the label is retired and no row carries it.
- **`screened_only`** marked rows no browser had confirmed. Cleared by the full-coverage pass.

### The merge that produced the single dataset

Per-role files were merged into one because they double-counted 57 providers and published 8
providers in contradictory states — priced in one file, recorded as unpriced in another. Adding the
per-file counts gave 778 providers where there were 699. The per-role files were deleted rather than
kept alongside the merged file, since keeping them invited exactly the error the merge fixed. They
remain in git history, and `source_pass` records which pass produced each row.

Merge rules, applied mechanically: identity is the normalised domain, not the provider name; every
priced row is kept; a null row is dropped when another pass found a price for that provider (10 stale
nulls removed); a null row is kept when it sits beside prices from the same pass, because it documents
a genuinely unpriced tier (11 kept); exact-duplicate offerings collapse to the strongest verification
(39 removed); one provider name per domain.

### Two classification bugs found and fixed

- A regular expression written to catch HTTP status 999 also matched any price ending in `,999`,
  wrongly marking two confirmed prices as bot-blocked.
- One provider's pre-existing rows survived a supersession sweep because they carried a different
  label, briefly duplicating that provider until the overlap was resolved by capture date.

---

Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
