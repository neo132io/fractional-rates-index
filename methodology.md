# Methodology

**The Fractional Rates Index · v1.0 · captured 2026-08-17 · CC BY 4.0**

---

## 1. The rule

**Published prices only.** A figure enters this dataset from the provider's own published page, or it
does not enter at all.

This single rule generates most of the dataset's shape, including the fact that most of it is null.
Three consequences follow, and all three are deliberate:

1. **Third-party estimates are excluded**, including estimates that look authoritative and estimates
   published by other providers in the same market. This release contains a clean demonstration of
   why. One provider's pricing article estimates Go Fractional at "typically $10K-$22K" per month.
   Go Fractional's own page publishes a **$5,000 per month** starting rate. The estimate is off by a
   factor of two at the floor. Only the first-party figure is recorded.
2. **"Custom pricing" is not a price**, and is recorded as a null with the wording in `notes`. A
   provider that states pricing exists but is not published is a meaningfully different observation
   from one that says nothing, and the `notes` column preserves the difference.
3. **No figure is recalled from memory or inferred from context.** If it was not read off the page at
   capture, it is not here.

---

## 2. Inclusion criteria

A provider is in scope if it:

- offers **fractional, interim or part-time executive services** in a C-suite function (CFO, CMO,
  CTO, COO, CPO), or operates a **marketplace** matching such executives; and
- has a reachable, first-party web presence at capture.

A provider is included **as a row whether or not it publishes a price.** This is the most important
methodological choice in the index. A dataset of only the providers that publish pricing would show a
price distribution and conceal the disclosure rate, which is the actual finding. Non-publishing
providers are the majority of the file by design.

**Row granularity: one row per provider-offering.** A provider publishing three tiers produces three
rows. 34 providers produce 43 rows.

**Excluded from the dataset:**

- Third-party estimates of any provider's rates.
- Comparative marketing claims that are not prices (cost-saving percentages, acceptance rates).
- Full-time salary benchmarks, which are market claims rather than a provider's price.
- **DataForSEO-derived figures, excluded entirely on rights grounds.** DataForSEO's Terms of Service
  (read 2026-08-17) is silent on redistribution: no clause permits or prohibits redistributing data
  obtained through the service, none addresses whether derived or aggregated data may be published
  under an open license, and none states ownership of derived works. Silence is not permission.
  Publishing under CC BY 4.0 would grant downstream recipients a redistribution right not clearly
  granted to us, so search-volume and CPC figures are excluded rather than included with a caveat.

---

## 3. Collection protocol

**Access dates: every row in v1.0 was captured on 2026-08-17.** There is one capture date in this
release, so nothing in it measures change over time.

### 3.1 Two-stage verification

**Stage one — screening.** An automated fetch of the provider's pricing-relevant pages.

**Stage two — browser confirmation.** Every price-bearing row is confirmed against the
browser-rendered page, and the published wording is recorded verbatim in `notes`.

**A summarizing fetch is not a capture.** Stage-one figures that fail stage two are **dropped, not
softened**. Providers screened but not browser-confirmed before the cutoff carry no asserted price
row; they are marked pending verification and are the first work item for v1.1.

### 3.2 Rules learned in this run

1. **JavaScript counters do not survive a server fetch.** Animated count-up statistics return as `0+`
   or a bare `+`. Any headline statistic needs a browser capture.
2. **A price in the DOM is not a price for the service you are looking at.** Pilot's monthly tiers
   are present in the page DOM but attach to bookkeeping plans, not to the CFO service, so they are
   not recorded as a CFO rate. The published CFO price is $399/hr.
3. **Bot-blocking is recorded as such.** HTTP 403 is not "no published price". Go Fractional blocks
   server fetches and was captured in a browser instead.
4. **Unreachable is its own state.** The CFO Centre failed DNS resolution at capture and is recorded
   as unreachable, not as publishing no price.
5. **Marketplace fees are not executive rates.** Bolster's "$2,500 upfront + 20% markup" is the
   platform's fee, not what the executive charges. The `unit` column carries the distinction.
6. **A floor is not a range.** Where a provider publishes "starting at", `price_low` is populated and
   `price_high` is left null. Reading a lone floor as a range would fabricate a ceiling.

### 3.3 Verification failures in v1.0

Documented because a dataset that only shows what survived tells you nothing about its own error rate.

| Provider | Reported by stage-one screening | What browser verification found |
|---|---|---|
| CMOx | "Rates range between $3,000 and $15,000 per month" | The strings `3,000` and `15,000` do not occur anywhere in the rendered page. The only published figure is a full-time CMO salary benchmark — a market claim, not this provider's price. |
| Burkland | "Accounting from $495/month"; "fractional CFO at $1,600/month" | Neither string appears in the rendered page, and the site has no pricing page. |
| Pilot | Monthly tiers presented as CFO pricing | The tiers exist in the DOM but attach to bookkeeping plans. The published CFO price is $399/hr. |

**Rate: 3 of 10 stage-one price reports did not survive — a 30% error rate.** Any dataset built on
automated fetching alone should be assumed to carry an error rate in this range. This is the single
strongest argument for the two-stage protocol, and it is why no price row in this release rests on a
summarizing fetch.

---

## 4. Schema

| Column | Notes |
|---|---|
| `provider` | Provider or marketplace name |
| `role` | CFO, CMO, CTO, COO, CPO, or `multi` for multi-function benches |
| `offering_type` | `retainer`, `day_rate`, `project`, `marketplace_match` |
| `price_low` | Null where nothing is published. A lone `price_low` is a published floor with no ceiling |
| `price_high` | Null where the provider publishes a floor only |
| `currency` | ISO code. All USD in v1.0 |
| `unit` | `per_month`, `per_hour`, `per_project`, `fixed_fee_per_project`, `per_search`, `upfront_plus_markup`, `percent_of_first_year_salary`, `placement_fee` |
| `hours_included` | Nullable. Published hours or days per week where the provider states them |
| `source_url` | The provider's own page. Never a third party |
| `capture_date` | ISO date of capture |
| `notes` | Verbatim published wording, verification status, and any exclusion reason |

**Cleaning applied at publication.** One `notes` field containing a literal comma was unquoted in the working file and made that row parse as 12 fields instead of 11. It is quoted here. No value was altered and no computed figure changes; that row carries no price. This is the only edit made to the working dataset for publication.

The dataset contains **no personal data beyond public business information**: business names,
business URLs and publicly published business prices. The one row naming an individual is the index
maintainer's own practice, included under the same rules as every other provider so that the
maintainer's pricing is subject to the index rather than exempt from it.

---

## 5. How the numbers in FINDINGS.md are computed

- **Provider counts** are of distinct `provider` values, not of rows. 34 providers, 43 rows.
- **"Publishes a price"** means the provider has at least one row where `price_low` or `price_high`
  is non-null. Providers with only null rows do not count.
- **Percentages** are over the 34 providers checked unless the line states otherwise. Where a rate
  over the 33 reachable providers differs materially, both are given.
- **The retainer band and median** are computed over rows where `offering_type = retainer` and
  `unit = per_month` and a figure is present — 7 rows. The **median floor** is the median of the
  non-null `price_low` values. Both the median floor and the median of all endpoints are $8,000, and
  the median floor stays $8,000 when the one tier its provider states is not executive-level
  leadership is excluded. The figure is reported because it is stable under that exclusion, not
  despite it.
- **Role and offering-type rates** count distinct providers per group. A provider appearing under two
  roles is counted in each.

Anyone can reproduce every figure from `data/rates-cpo-2026-08.csv` alone.

---

## 5b. Cohort B — the Apollo-derived cohort (2026-08-20)

`data/rates-fractional-cohort-2026-08.csv` is a **separate cohort**, collected differently from v1.0.
It is published as its own file, and its figures are reported separately in `FINDINGS.md`, because
pooling the two would silently mix sampling frames and capture dates.

**Provenance.** A commercial contact-database export of 1,003 records of individuals whose job title
contains "fractional". **All personal data was discarded before anything entered this repository**:
no names, no email addresses, no personal LinkedIn URLs, no cities. Only the company name and company
domain were retained, and only those appear in `research/apollo-company-queue.csv`. The source export
is not published, and will not be — publishing it would distribute roughly a thousand individuals'
contact details under an open licence, which the licence in this repository has no right to grant and
which the rule in §4 forbids.

**A contact export is not a provider list.** The export names people with fractional titles; the
company column is frequently their *employer*, not a fractional services business. Screening the 967
distinct companies for whether they offer fractional executive services at all produced:

| Scope verdict | Companies | Test |
|---|---|---|
| **In scope** | 330 (34.1%) | Offers a named fractional/interim executive role, or mentions "fractional" three or more times |
| Weak | 21 (2.2%) | One or two passing mentions, no role offered |
| **Out of scope** | 616 (63.7%) | Zero mentions of "fractional" anywhere on the site |

Out-of-scope companies included a mattress retailer, a pet-portrait shop, a coffee roaster, a chess
subscription and a physiotherapy clinic. Of those 330, **one was dropped because its only web presence was a personal LinkedIn profile rather
than a first-party business site, leaving 329 in `data/`.** Including
the rest would corrupt the denominator of every disclosure rate in this repository. All 967 remain in
`research/apollo-company-queue.csv` with their `scope_verdict`, so the exclusion is auditable.

**Verification status is the honest limitation of this cohort.** Stage one screened all 329. Stage two
— browser confirmation — was completed for 8 providers, of which **6 were confirmed and 2 rejected.**
The remaining 35 price candidates are marked pending in `notes` and carry **no asserted price.**
The cohort's measured disclosure rate is therefore **1.8% verified, with a ceiling of 12.5%** if every
pending candidate later confirms. Both numbers are stated in `FINDINGS.md`; neither is presented alone.

**Rights.** Only company names and domains were retained, which are bare facts rather than a
protectable compilation, and the source export itself is not republished. This is a narrower position
than the DataForSEO exclusion in §2, which concerned publishing *derived figures* under an open
licence. No figure in this cohort comes from the contact database: every price was read off the
provider's own page.

---

## 6. Known limitations

- **Small sample.** 34 providers is enough to establish a disclosure pattern and **not enough to
  state market rates.** No row in this dataset should be read as a market range.
- **Point-in-time, single capture.** Provider pages change; Go Fractional described "over 1,200
  fractional executives" on 2026-08-16 and "15,000 operators" on 2026-08-17. Capture dates matter,
  and one capture date cannot show stability.
- **Roles are unevenly covered.** COO is the thinnest: 1 provider checked, none publishing.
- **A published price is not a transacted price.** This records what providers publish, not what
  clients pay, and the gap between the two is unmeasured here.
- **Monthly figures are not comparable without hours.** `hours_included` is frequently null because
  providers frequently omit it.
- **Selection is not random.** The candidate pool came from discovery research, not from a sampling
  frame, so the disclosure rate describes the providers checked and is not a population estimate.
- **US and UK-centric, English-language, USD only.**

---

Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
