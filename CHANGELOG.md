# Changelog

Every published figure that this index later corrected is recorded here, with what it said, what it
says now, and why it changed.

This file exists for the same reason the index exists. A statistic whose revisions are invisible
cannot be audited, and a dataset that is never contradicted is usually one nobody checked. Anyone who
cited an earlier version should be able to find out, from this file alone, whether the number they
quoted still holds.

---

## v2.1 — 2026-09-03

**Sites belonging to one operator are now one provider, every published figure has to match a quote
captured from the provider's own page, and each record ships with that quote beside it.**

### Figures that changed

| Group | v2.0 | v2.1 | Why |
|---|---|---|---|
| Providers tracked | 1,127 | **1,774** | Collection continued, and 65 sites in one operator's network folded into one provider |
| Publish a price | 211 (18.7% of tracked) | **175 (11.1% of the 1,577 sites read)** | The gate tightened, and the denominator now counts only sites actually read |
| Median US monthly retainer | $5,000 | **$5,625** | Sits inside the old figure's interval and the old figure inside the new one, so this is the same finding measured on more providers, not a correction |
| CFO / US / monthly | $1,499 (n=15) | **$2,500 (n=6, below the reporting floor)** | Six outsourced-bookkeeping subscriptions were being counted as fractional CFO retainers |
| CPO / EU / day rate | €1,363 (n=1) | **withdrawn** | Built from the sentence "day rates in Europe in 2026 range from €700 to €1,900": a market summary, not the provider's own price, with the year read as the top of the range |
| CPO / EU / hourly | €83 (n=1) | **withdrawn** | The figure appears in no captured quote. The page said "€100-320 per hour" |
| COO / EU / monthly, COO / US / day | €6,000, $2,000 (n=1 each) | **withdrawn** | Neither figure could be matched to a quote |

**If you cited $5,000 as the median US monthly retainer, it still holds.** Its 95% interval was
$3,250 to $6,250; the new figure is $5,625 with an interval of $4,750 to $7,750. Thirteen of the 30
groups that exist in both releases have a median delta of exactly zero and three more move by under
0.2%, so the collection is measuring the same market it was measuring before.

**If you cited a CPO euro figure, a CFO US monthly figure, or "19% of providers publish a price",
change it.** The first is withdrawn, the second was measuring bookkeeping subscriptions, and the
third counted sites that were never successfully read as sites that publish nothing.

### What changed in how the index is made

A figure is published only when it is found word for word in a quote captured from the provider's own
page, together with its currency and its cadence, and sits inside a plausibility band for its unit.
All three have to appear in the *same* quote: a number in one place and the word "hour" in another do
not, together, establish an hourly rate. That single rule is what withdrew the four groups above.

A number is also no longer published just because a group exists. A group needs eight providers
before it carries a figure. 31 of the 38 groups fall below that line; they are named and counted in
`data/groups-v2.1.csv` with empty median cells, so a group of one can never be mistaken for a
finding. That floor is why no UK figure appears in this release: sterling providers are in the data,
25 of them, but no UK group reaches eight.

SaaS seat pricing and outsourced bookkeeping subscriptions are excluded from the population. A $4
per-seat licence is not a fractional executive retainer, and 26 such products were being counted.

Every record now carries one comparison column: USD per hour. Hourly rates are used as captured, day
rates divided by eight hours, monthly retainers divided by the hours the provider publishes or by
32.5 hours where it publishes none. The 32.5 comes from reading all 51 stated hour figures in the
data and keeping the 41 that survived: the raw column was mixing hours per month, hours per week,
days per month, support SLA response times and plan names. The original currency and unit stay in
every row; the hourly column sits beside them.

The divisor is checked against the data rather than assumed. Providers who state an hourly rate
publish a median of $200; day rates over eight hours give $250; retainers over 32.5 hours give
$154. A retainer buying volume ought to price below spot, and it does. At the 12 hours the unaudited
column suggested, retainers would imply $417 an hour, twice what the market charges by the hour.

Currency conversion uses one ECB reference rate locked at release time and published with the data
(`data/fx-lock-20260903.json`), so any figure can be recomputed exactly.

### Verification

Before release, 40 published records were drawn at random from `data/records-v2.1.csv` and their
source pages re-fetched: 30 of the 30 that could be read carried the number, its currency and its
cadence. A second draw at a different seed returned 34 of 35. Combined, 64 of 65, against a 95%
threshold. Both reports are in `data/acceptance-gate-v2.1.json` and
`data/acceptance-gate-v2.1-confirm.json`, listing every page checked and every page that could not be.

### Reproducing this release

v2.0 was generated once, by hand, on a server, and could not be reproduced afterwards. The generator
is now a script in this repository. `tools/generate_release.py` takes one frozen snapshot and one
locked FX rate and emits every file in `data/` that carries a v2.1 suffix. `python -m pytest
tools/tests` covers the evidence rules, the normalisation and the release build.

---

## v2.0 — 2026-09-02

**The index moved from a one-off browser audit to continuous, calibrated machine collection, and the
public site at saasfractionalcpo.com/data now renders this repository's snapshot directly.**

What changed: coverage expanded from CPO-centric to 7 executive roles (COO, CRO and Chief of Staff
added); providers tracked 736 -> 1,127 and growing; day-rate normalisation revised; per-group
aggregates are deduplicated per (host, role) and groups below n=8 are flagged low-n; records from any
uncalibrated extraction run are quarantined and excluded until re-extracted. The v1.2 files are
unchanged and remain in `data/` for anyone who cited them.

No previously published v1.2 figure is corrected by this release; v2.0 is a new, larger snapshot on a
new collection basis, not a restatement of the old one.

---

## v1.2 — 2026-08-24

**No figure in this release changed. v1.2 corrects how one figure was worded, removes a stray contact
detail, and writes down the counting rule that an audit of this release got wrong.**

Every number published in v1.1 was recomputed from the shipped file during this pass and every one
reproduced exactly: 736 providers, 938 rows, 129 publishing a price, 17.5%, the 17.5–22.4% interval,
and the full role table down to CFO at 12.5% (19 of 152). **Anyone who cited v1.1 needs to change
nothing.**

### What changed

| Was | Is now | If you cited it |
|---|---|---|
| "Of 736 providers, 129 publish a price — 17.5%" | **"At least 17.5% publish a price (129 of 736) — the floor of a 17.5–22.4% interval"** | No figure changed. The floor framing was already in `README.md` and `methodology.md`; `FINDINGS.md` stated the rate bare and now matches |
| A provider row carried a business phone number | **Removed** | Nothing depended on it |
| Counting rule stated once, in passing | **Stated with the failure mode named** | See below |

### The denominator that looks wrong and is not

An audit of the live release counted **734** distinct providers against the **736** the documents
claim, and reported the documents as stale. The documents were right and the audit's counting rule was
wrong.

Provider identity in this index is the **normalised domain of `source_url`**, not the `provider`
string. Two providers run two domains each — `aspirecfo.com`/`aspirecfo.net` and
`cfocentre.com`/`thecfocentre.com` — so 734 names span 736 identities. Counting names yields 734,
17.6%, and CFO 12.6% (19 of 151); **none of those reproduce a published figure.**

The rule was already in `methodology.md`. It is now stated with the specific way it gets missed, the
two providers that cause it, and the normalisation needed to reproduce the file, because a counting
rule that a careful reader can trip on is not documented well enough.

### The CPO flip

Unchanged in this release and still documented in the **v1.1** entry below: CPO moved from 4.7%
(5 of 106) to **13.5% (14 of 104)** when every provider was opened in a browser, and CFO became the
least transparent role at 12.5%. The 4.7% was an artifact of unopened pricing pages.

### Bidirectional screening error

Also unchanged and carried forward from v1.1: screening reported prices that were not there on
**43.6%** of what it flagged (41 of 94) and missed prices that were there on **5.3%** of what it
cleared (34 of 643). Both directions remain published in `FINDINGS.md`, `README.md`, `methodology.md`
and `research/detector-gaps.md`. Neither is knowable without opening the page.

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
