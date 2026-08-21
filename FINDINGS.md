# Findings

**The Fractional Rates Index · v1.1 · captured 2026-08-17 to 2026-08-21 · CC BY 4.0**

Every line below is computed from [`data/rates-2026-08.csv`](data/rates-2026-08.csv) and from
nothing else. No figure here is estimated, modelled, projected or carried over from another source.
Where the data cannot support a claim, the claim is absent rather than softened.

Denominators are stated inline, because a percentage over 736 providers is a different object from a
percentage over 69,000 and the reader is entitled to know which one they are holding.

**v1.1 corrected several figures published in v1.0**, including the headline disclosure rate and the
role table. If you cited an earlier version, [`CHANGELOG.md`](CHANGELOG.md) states what changed and
what to do about it.

**Every provider in this index was opened in a browser.** Not a sample — all 736. 700 of them
rendered and were read; the remaining 36 returned a bot check, an empty body or a dead domain, and
carry no observation in either direction rather than being recorded as publishing no price. Nothing
here rests on an automated fetch. That full pass is also what produced the most useful finding in
this file: screening had missed a published price on 34 providers, and on 14 of those the price was
sitting on a `/pricing` page nobody had opened.

---

## Headline findings

**1. Disclosure**

> Of 736 fractional executive providers, 129 publish a price — 17.5%, about one in six. Every one was confirmed against the provider's own rendered page. (Fractional Rates Index, Aug 2026)

> Every row in this index now carries a browser observation or an explicit failure to obtain one. 899 of 938 rows are browser-verified; the remaining 39 are recorded as blocked, unreachable or out of scope. No row rests on automated screening alone. (Fractional Rates Index, Aug 2026)

**2. Spread**

> Confirmed USD monthly executive retainers run from $299 to $50,000 — a 167-fold spread across 122 published tiers from 61 providers. (Fractional Rates Index, Aug 2026)

**3. Central tendency**

> The median confirmed USD monthly retainer floor is $5,000; the median confirmed USD hourly rate is $200; the median confirmed USD project fee is $2,500. (Fractional Rates Index, Aug 2026)

---

## All findings

### Coverage

> The index covers 736 distinct fractional executive providers across 938 provider-offering rows, captured between 2026-08-17 and 2026-08-21. (Fractional Rates Index, Aug 2026)

> 645 of 938 rows — 68.8% — record a published absence of price rather than a figure. The nulls are the dataset's main result, not a gap in it. (Fractional Rates Index, Aug 2026)

### Disclosure by role

> Confirmed price disclosure by role: CTO 24.3% (35 of 144), CMO 19.4% (31 of 160), COO 16.1% (23 of 143), multi-function 15.8% (9 of 57), CPO 13.5% (14 of 104), CFO 12.5% (19 of 152). (Fractional Rates Index, Aug 2026)

> Fractional CTO is the most price-transparent role in the index at 24.3%, roughly twice the fractional CFO rate of 12.5%. (Fractional Rates Index, Aug 2026)

> Fractional CFO is the least transparent role measured, with 19 published prices across 152 providers — and it is the most crowded role in the index, so the buyer with the most providers to choose from has the least to compare them on. (Fractional Rates Index, Aug 2026)

Roles with fewer than 10 providers — CRO (5), CEO (2) — are recorded in the data but are too small to
report a rate for, and are omitted here rather than quoted at a spurious precision.

### Confirmed pricing

> Across 122 confirmed USD monthly executive retainer tiers from 61 providers, the median floor is $5,000 and the band runs $299 to $50,000. (Fractional Rates Index, Aug 2026)

> Half of confirmed USD monthly retainer floors fall between $2,500 and $8,000. The quartiles are tighter than the 167-fold headline range suggests: the extremes are real but rare. (Fractional Rates Index, Aug 2026)

> Sterling pricing: 23 confirmed GBP monthly tiers from 12 providers run £699 to £18,000, with a median floor of £4,000. (Fractional Rates Index, Aug 2026)

> Euro pricing is now large enough to report separately: 12 confirmed EUR monthly tiers from 7 providers run €1,200 to €25,000, with a median floor of €5,450. (Fractional Rates Index, Aug 2026)

> Confirmed USD hourly rates for fractional executive work run $60 to $500 across 17 published rates from 14 providers, with a median of $200 — an 8-fold spread in what an hour of fractional executive time costs. (Fractional Rates Index, Aug 2026)

> Confirmed USD project and diagnostic fees run $97 to $30,000 across 40 published fees from 27 providers, with a median of $2,500. The cheap end is a paid entry point, not a discount: providers sell a fixed-fee audit to open a retainer conversation. (Fractional Rates Index, Aug 2026)

> Confirmed GBP day rates run £600 to £2,500 across 8 published rates from 7 providers, with a median of £1,125 — the tightest band in the dataset, and the only unit where the top of the range is under 5× the bottom. (Fractional Rates Index, Aug 2026)

### What a published price leaves out

> 212 of 293 priced rows — 72% — are open-ended floors: a "starting at" figure with no ceiling. Reading a lone floor as a range fabricates a ceiling the provider did not publish. (Fractional Rates Index, Aug 2026)

> Only 96 of 293 priced rows — 33% — state the hours or day commitment the price buys. A monthly figure without hours is not comparable to another monthly figure. (Fractional Rates Index, Aug 2026)

> Providers who publish a price rarely publish only one: 56 of 129 publish three or more tiers, and two publish seven. Publishing a price is usually a decision to publish a whole card. (Fractional Rates Index, Aug 2026)

### Currency

> Published fractional pricing is not a USD-only phenomenon. Confirmed prices appear in 7 currencies: USD, EUR, GBP, AUD, SGD, NZD and CHF. (Fractional Rates Index, Aug 2026)

> No exchange rate is applied anywhere in this dataset. Rows in different currencies are not pooled, and any cross-currency band would be an artifact of whoever chose the rate. (Fractional Rates Index, Aug 2026)

### Verification

Two separate error rates are reported below, because they measure opposite failures. The first is
screening reporting a price that was not there. The second is screening missing a price that was.

> Of 94 provider prices reported by automated screening and then checked in a browser, 41 did not survive — a 43.6% rejection rate. (Fractional Rates Index, Aug 2026)

> The rejection rate depends on how the candidates were found: 16 of 49 failed (32.7%) among providers surfaced by targeted pricing-page discovery, 9 of 14 (64.3%) among AI-discovery candidates, and 16 of 31 (51.6%) among providers surfaced from a commercial contact export. (Fractional Rates Index, Aug 2026)

> A full browser pass over all 736 providers found a published price on 34 that the dataset had recorded as publishing none — a 5.3% false-negative rate against the 643 providers previously recorded as unpriced. (Fractional Rates Index, Aug 2026)

> 14 of those 34 prices — 41% — were on a `/pricing` page that no earlier pass had opened. Checking a provider's homepage and concluding it publishes no price is the single most reproducible way to get this measurement wrong. (Fractional Rates Index, Aug 2026)

> Screening error runs in both directions. It reported prices that did not exist on 43.6% of the candidates it flagged, and it missed prices that did exist on 5.3% of the providers it cleared. Neither number is knowable without opening the page. (Fractional Rates Index, Aug 2026)

### How automated screening gets prices wrong

Documented because a dataset that only shows what survived tells you nothing about its own error rate.

**These are failure modes of our screening tool, not of the providers.** Every example below is a page
doing something perfectly normal — publishing an article, a comparison, a calculator, a case study —
which an automated pass misread as a price. No provider is named in this table, and none of these
is a finding about a provider's conduct.

| Failure mode | What it looked like |
|---|---|
| **A market estimate, not a rate** | Pricing articles stating national bands — "a fractional CTO typically costs A$1,000–A$22,000 per month" — with no first-party figure anywhere on the page |
| **A client revenue band** | "Financial leadership for $2M to $50M operators" read by screening as a price |
| **A case-study result** | EBITDA turnarounds, "$500M+ revenue scaled", founder career histories |
| **A figure describing other firms** | A "$1,500/hr" that the page attributed to *other* fractional CMOs, not to itself |
| **The wrong column of a comparison table** | A "$9,000/month" that was the internal-hire column of a cost comparison; the provider's own published price on the same page is $1,400/month |
| **A calculator output** | Visitor-operated estimators — a "£9,600/month" built from market day-rate bands, and a "$9,000/mo" returned as "YOUR ESTIMATE" after selecting a revenue band |
| **A price for a different service** | App-development rates, website subscriptions, marketing packages, and directory memberships sold to executives rather than rates charged to clients |
| **An unresolved JavaScript counter** | "$ 0 Billion in M&A deals negotiated" — animated statistics captured mid-animation at zero |
| **A dashboard mockup** | Sample client figures in a "Live Dashboard" graphic — revenue, runway, net cash flow — read as prices |
| **A figure that simply is not there** | Twelve providers' reported prices do not occur anywhere in the rendered page |

> The most common way automated screening goes wrong is on pages that quote the market rather than state a price. A pricing article is not a price list, and at scale the two are easy to confuse. (Fractional Rates Index, Aug 2026)

### How automated screening misses prices

The mirror image of the table above, from the full browser pass.

| Miss mode | What happened |
|---|---|
| **The price is on another page** | The homepage states no figure; a linked `/pricing` page states three. 14 of 34 recoveries |
| **The currency follows the number** | A page writing `USD 10,000` rather than `$10,000` is invisible to a symbol-anchored pattern |
| **The page had not finished rendering** | A capture taken before client-side render returns an empty body; the same page read seconds later carries a full rate card |
| **An interstitial stood in front** | A bot check or cookie wall returned in place of the page, and the miss was recorded as an absence rather than as a block |
| **A separator the pattern did not expect** | Swiss pricing written `CHF 2'900` truncates at the apostrophe under a comma-and-period number class |

> Four of these five miss modes are invisible to the tool that caused them: the fetch succeeds, returns text, and the text genuinely contains no price. Only opening the page distinguishes "publishes nothing" from "publishes elsewhere". (Fractional Rates Index, Aug 2026)

---

## What this dataset cannot tell you

Stated explicitly so the lines above are not quoted past their evidence.

- **These are not market rates.** 736 providers establish a disclosure pattern. 129 published price
  lists are too few, and too self-selected, to state a market rate for any role.
- **Selection is not random.** The candidate pool came from discovery research, two AI-discovery
  passes and a commercial contact export, not from a sampling frame. The disclosure rate describes
  the providers checked.
- **Out-of-scope companies are excluded, not counted.** Businesses that turned out not to offer
  fractional executive services at all never enter the denominator. Sales roles such as fractional
  SDR and account executive are also out of scope, even where the provider publishes a real price.
- **A floor is not a range.** 72% of priced rows publish "starting at" with no ceiling, so
  `price_high` is null by design. Reading a lone floor as a range fabricates a ceiling.
- **One row is a ceiling, not a floor.** A single provider publishes "for less than $25,000" with no
  lower bound. It is stored as `price_high` with a null `price_low` and must not be read as a
  starting price.
- **A published price is not a transacted price.** This records what providers publish, not what
  clients pay, and the gap between the two is unmeasured here.
- **Monthly figures are not comparable without hours.** `hours_included` is null on 67% of priced
  rows because providers frequently omit it.
- **Some published figures are exclusive of tax.** Several UK and EU rows are published "+VAT" and
  one Australian row "+GST". They are recorded as published, tax-exclusive, and are not grossed up.
- **Do not pool currencies.** See above.
- **Some priced rows are not executive rates** — bookkeeping, recruiting retainers, platform
  markups, developer hours and bundled service packages in which a fractional executive is one line
  item. They are kept because the providers publish them, flagged in `notes`, and excluded from the
  executive bands above.
- **Point-in-time.** Four capture dates across five days. One provider already changed a published
  figure inside that window, which is recorded with both capture dates.
- **The maintainer is in the dataset.** saasfractionalcpo.com is the practice of the person who
  maintains this index. It publishes a price, and is recorded on the same basis as every other
  provider and read in the same browser pass, so the maintainer's pricing is subject to the index
  rather than exempt from it. It is one row of 938 and moves no figure in this file, but readers
  should discount it accordingly.
- **English-language sources, US and UK-weighted.**

---

Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
