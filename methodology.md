# Methodology

**The Fractional Rates Index · v1.1 · captured 2026-08-17 to 2026-08-21 · CC BY 4.0**

This document describes the dataset as it stands. Where a figure in it superseded an earlier
published figure, [`CHANGELOG.md`](CHANGELOG.md) records what changed and why. Nothing here is a
patch note; the corrections live in one place so this file can be read straight through.

---

## 1. The rule

**Published prices only.** A figure enters this dataset from the provider's own published page, or it
does not enter at all.

This single rule generates most of the dataset's shape, including the fact that most of it is null.
Three consequences follow, and all three are deliberate:

1. **Third-party estimates are excluded**, including estimates that look authoritative and estimates
   published by other providers in the same market. This repository contains a clean demonstration of
   why. One provider's pricing article estimates Go Fractional at "typically $10K–$22K" per month.
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
rows. **736 providers produce 938 rows.**

**Excluded from the dataset:**

- Third-party estimates of any provider's rates.
- Comparative marketing claims that are not prices (cost-saving percentages, acceptance rates).
- Full-time salary benchmarks, which are market claims rather than a provider's price.
- Platform, placement, matching and subscription fees where they are the intermediary's charge rather
  than the executive's rate. The `unit` column carries the distinction where such rows are kept.
- **DataForSEO-derived figures, excluded entirely on rights grounds.** DataForSEO's Terms of Service
  (read 2026-08-17) is silent on redistribution: no clause permits or prohibits redistributing data
  obtained through the service, none addresses whether derived or aggregated data may be published
  under an open license, and none states ownership of derived works. Silence is not permission.
  Publishing under CC BY 4.0 would grant downstream recipients a redistribution right not clearly
  granted to us, so search-volume and CPC figures are excluded rather than included with a caveat.

**On the contact-export cohort.** Part of the candidate pool came from a commercial contact-database
export of 1,003 records of individuals whose job title contains "fractional". **All personal data was
discarded before anything entered this repository**: no names, no email addresses, no personal
LinkedIn URLs, no cities. Only company name and company domain were retained. The source export is
not published and will not be — publishing it would distribute roughly a thousand individuals'
contact details under an open licence this repository has no right to grant.

A contact export is not a provider list: the company column is frequently the person's *employer*
rather than a fractional services business. Screening the 967 distinct companies found **330 in scope
(34.1%)**, 21 weak, and **616 out of scope (63.7%)** with zero mentions of "fractional" anywhere on
the site — among them a mattress retailer, a pet-portrait shop, a coffee roaster and a
physiotherapy clinic. Carrying those through would have corrupted the denominator of every disclosure
rate in this repository. The screening list itself is not published: it names businesses that turn
out to have nothing to do with this market, which is a fact about a contact export rather than a fact
about the market.

---

## 3. Schema

`data/rates-2026-08.csv`, 13 columns, 938 rows.

| Column | Values as they actually occur in the file |
|---|---|
| `provider` | Provider or marketplace name, one per domain |
| `role` | `CMO` 205, `CTO` 183, `CFO` 177, `COO` 165, `CPO` 120, `multi` 77, `CRO` 8, `CEO` 2, `other` 1 |
| `offering_type` | `retainer` 747, `marketplace_match` 109, `project` 73, `day_rate` 9 |
| `price_low` | Null where nothing is published. A lone `price_low` is a published floor with no ceiling |
| `price_high` | Null where the provider publishes a floor only. Two rows carry a high with no low: a published ceiling |
| `currency` | ISO code, null on unpriced rows. `USD` 210, `GBP` 46, `EUR` 29, `AUD` 6, `SGD` 3, `NZD` 3, `CHF` 1 |
| `unit` | Null on unpriced rows. `per_month` 173, `fixed_fee_per_project` 64, `per_hour` 22, `per_day` 9, and nine long-tail units |
| `hours_included` | Nullable. Published hours or days per week where the provider states them |
| `source_url` | The provider's own page. Never a third party |
| `capture_date` | ISO date of capture, per row: 2026-08-17, -19, -20 or -21 |
| `verification` | `browser_verified` 898, `unreachable` 23, `blocked` 16, `out_of_scope` 1 |
| `source_pass` | Which collection pass produced the row |
| `notes` | Verbatim published wording, verification status, and any exclusion reason |

**`verification` is the column that matters most.** Every row in the published file either carries a
browser observation or an explicit statement that one could not be obtained. **No row rests on
automated screening alone.** `out_of_scope` marks a provider publishing a real, browser-confirmed
price for something this index does not cover, such as fractional sales roles below C-suite level —
the price is excluded by section 2, not because anything is wrong with it.

**The dataset contains no personal data beyond public business information**: business names,
business URLs and publicly published business prices. The one row naming an individual is the index
maintainer's own practice, included under the same rules as every other provider and read in the same
browser pass, so the maintainer's pricing is subject to the index rather than exempt from it.

---

## 4. Collection protocol

### 4.1 Two-stage verification

**Stage one — screening.** An automated fetch of the provider's pricing-relevant pages.

**Stage two — browser confirmation.** Every price-bearing row is confirmed against the
browser-rendered page, and the published wording is recorded verbatim in `notes`.

**A summarizing fetch is not a capture.** Stage-one figures that fail stage two are **dropped, not
softened**.

### 4.2 The full-coverage pass

Stage two, as described above, only ever tests prices that screening *reported*. It cannot detect the
opposite failure: a provider recorded as publishing nothing that in fact publishes something. On
2026-08-21 that second direction was tested.

**All 736 providers were opened in a browser**, in risk order — providers never previously opened
first, then providers whose earlier check returned nothing, then providers already carrying a
confirmed price. Each was navigated, given three seconds to render, and read with a detector that
strips known non-price contexts (revenue, funding, savings, salary, portfolio, valuation) before
reporting a figure. Where the page exposed a link matching `pricing|price|rates|cost|fees|packages|plans`,
that link was followed before any "no price" observation was recorded.

**700 of the 736 rendered and were read. 36 did not** — a bot check or consent wall stood in front of
the page, the body came back empty after retry, or the domain no longer serves content. Those 36 are
recorded as `blocked` or `unreachable`, **not** as publishing no price. They remain in the
denominator and carry no observation in either direction.

That treatment is conservative in a specific and measurable way: **if every one of those 36 published
a price, the disclosure rate would be 22.4% rather than 17.5%.** 17.5% should be read as the floor of
that interval, not as a point estimate.

### 4.3 Rules learned in this project

1. **JavaScript counters do not survive a server fetch.** Animated count-up statistics return as `0+`
   or a bare `+`. Any headline statistic needs a browser capture.
2. **A price in the DOM is not a price for the service you are looking at.** Pilot's monthly tiers are
   present in the page DOM but attach to bookkeeping plans, not to the CFO service, so they are not
   recorded as a CFO rate. The published CFO price is $399/hr.
3. **Bot-blocking is recorded as such.** HTTP 403 is not "no published price".
4. **Unreachable is its own state.** A DNS failure is recorded as unreachable, not as publishing no
   price.
5. **Marketplace fees are not executive rates.** A "$2,500 upfront + 20% markup" is the platform's
   fee, not what the executive charges.
6. **A floor is not a range.** Where a provider publishes "starting at", `price_low` is populated and
   `price_high` is left null. Reading a lone floor as a range would fabricate a ceiling.
7. **Hedged figures are treated consistently or not at all.** Three providers publish figures hedged
   with "typically" on their own service pages. Treating one as first-party and another as market
   would make the rule arbitrary, so all three are recorded as publishing no price and the figures are
   quoted in `notes` so a reader can disagree with the call on the evidence.

---

## 5. How the figures in FINDINGS.md are computed

- **Provider identity is the normalised domain of `source_url`**, not the provider name, because the
  same provider is named differently across collection passes. 736 providers, 938 rows.
- **"Publishes a price"** means the provider has at least one row where `price_low` or `price_high`
  is non-null. Providers with only null rows do not count. This yields 129 providers.
- **"Confirmed"** additionally requires `verification` to be `browser_verified` or `first_party`. The
  two counts coincide: all 129 are confirmed, and no priced row carries any other verification value.
  That invariant is checkable in one pass over the file.
- **Percentages** are over the 736 providers in the dataset unless the line states otherwise.
- **Bands and medians** are computed over rows that are priced and filtered to one `currency`, one
  `unit` and one `offering_type`. The `offering_type` filter is what excludes marketplace and platform
  rows, whose own notes state they are not executive rates. On this basis the USD monthly retainer
  band is 122 rows from 61 providers, median floor $5,000, range $299–$50,000.
- **Band endpoints use both columns.** The low end is the minimum `price_low`; the high end is the
  maximum of `price_high` where set and `price_low` where it is not. A provider publishing only a
  floor therefore contributes to the low end and cannot inflate the high end. This is why the USD
  band tops at $50,000 while the *floor* histogram in `FINDINGS.md` tops out lower: the histogram
  plots floors, the band reports published endpoints.
- **Medians are medians of the published floor**, so that a provider publishing a range and a provider
  publishing "starting at" contribute the same kind of number.
- **Rows with no stated period are excluded from every per-period band.** Three rows carry a currency
  and an amount but no unit, because the provider's page attaches no period to the figure. They are
  not assumed monthly.
- **Currencies are never pooled and never converted.** Every band and median is computed within a
  single currency, and the currency is named in the finding. No exchange rate is applied anywhere in
  this repository.
- **Role rates** count distinct providers per group, and the two sides of the fraction use different
  rules, so it is worth being exact. The **denominator** for role X is every distinct provider with
  any row carrying role X; a provider appearing under two roles is counted in both denominators. The
  **numerator** is every distinct provider with a *priced* row carrying role X — not merely a provider
  that publishes a price somewhere and happens also to appear under X. The distinction matters for
  three multi-role marketplaces whose published price sits under one role while they also appear under
  others; crediting them to every role they touch would inflate CTO from 35 to 37 and CPO from 14 to
  15. Because providers can appear under several roles, the role numerators sum to 131 rather than 129.
- **Roles below 10 providers are not reported as a rate.** CRO (5 providers) and CEO (2) appear in the
  data and are omitted from the role table rather than quoted at a spurious precision.

**Every figure published in this repository reproduces from `data/rates-2026-08.csv` alone.** That is
not a claim of intent: it is checked. A 69-assertion reproduction script recomputes every published
count, percentage, band, median, quartile, histogram bucket and domain tally from the CSV and compares
it to the published value. It passes at 69 of 69.

---

## 6. What the tooling got wrong

Documented because a dataset that only shows what its tools caught tells you nothing about what they
missed. **These are failure modes of our screening, not of the providers.** No provider is named here
in connection with a failure mode.

**Screening error runs in both directions, and the two rates are measured separately.**

### 6.1 False positives — prices reported that were not there

Of **94 provider prices reported by automated screening** and then opened in a browser, **41 did not
survive — a 43.6% rejection rate.** Their figures were removed rather than softened.

**The rejection rate depends on how the candidate was found**, which is the most transferable finding
in this project:

| Discovery method | Rejected |
|---|---|
| Targeted pricing-page search | 32.7% (16 of 49) |
| Commercial contact export | 51.6% (16 of 31) |
| AI discovery | 64.3% (9 of 14) |

The better the discovery method models "a page that states a price", the less of the verification
budget is wasted on pages that never had one.

**What the false positives actually were:** market estimates in pricing articles; client revenue
qualification bands; case-study outcomes and EBITDA turnarounds; figures a page attributed to *other*
firms; the internal-hire column of a provider's own cost-comparison table; visitor-operated calculator
outputs; prices for a different service entirely; unresolved JavaScript counters captured mid-animation
at zero; sample figures in dashboard mockups; and twelve figures that do not occur anywhere in the
rendered page.

### 6.2 False negatives — prices missed that were there

The full-coverage pass found a published price on **34 providers the dataset had recorded as
publishing none — a 5.3% false-negative rate** against the 643 providers previously recorded as
unpriced.

**14 of those 34 — 41% — had their price on a page nobody had opened**, a `/pricing`, `/packages` or
`/fractional-cfo-pricing` path linked from a homepage that itself states no figure. That is the single
largest source of error found in this project, and it is a **sampling** error rather than a parsing
one: the tool read the page it was given, correctly, and the price was on a different page.

The remaining miss modes, and the detector defects behind them, are recorded in
[`research/detector-gaps.md`](research/detector-gaps.md) with an explicit damage assessment for each —
including one, a Swiss apostrophe thousands separator, that was checked for damage and found to have
caused none rather than being assumed harmless.

**Four of the five miss modes are invisible to the tool that caused them:** the fetch succeeds,
returns text, and the text genuinely contains no price. Only opening the page distinguishes "publishes
nothing" from "publishes elsewhere". This is why the full-coverage pass was run at all.

---

## 7. Known limitations

- **Small confirmed sample.** 736 providers establish a disclosure pattern, but only 129 publish a
  price. That is **not enough to state market rates** for any role. No row in this dataset should be
  read as a market range.
- **Selection is not random.** The candidate pool came from discovery research, two AI-discovery
  passes and a commercial contact export, not from a sampling frame. The disclosure rate describes the
  providers checked and is not a population estimate.
- **36 providers were never read.** They are counted in the denominator as publishing nothing, which
  makes 17.5% the floor of a 17.5–22.4% interval rather than a point estimate.
- **Point-in-time.** Four capture dates across five days. Provider pages change: one provider altered
  a published figure inside the capture window, which is recorded with both capture dates. Five days
  cannot show stability.
- **Role coverage is uneven.** CRO (5 providers) and CEO (2) are too thin to report a rate for. Among
  the six reportable roles the thinnest is CPO at 14 confirmed publishers out of 104 providers.
- **A published price is not a transacted price.** This records what providers publish, not what
  clients pay, and the gap between the two is unmeasured here.
- **Monthly figures are not comparable without hours.** `hours_included` is null on 67% of priced rows
  because providers frequently omit it.
- **Some published figures are exclusive of tax.** Several UK and EU rows are published "+VAT" and one
  Australian row "+GST". They are recorded as published, tax-exclusive, and are not grossed up.
- **Some priced rows are not executive rates** — bookkeeping, recruiting retainers, platform markups,
  developer hours and bundled packages in which a fractional executive is one line item. They are kept
  because the providers publish them, flagged in `notes`, and excluded from the executive bands.
- **English-language sources, US and UK-weighted.** Seven currencies appear; USD dominates.

---

Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
