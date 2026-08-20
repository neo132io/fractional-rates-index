# Findings

**The Fractional Rates Index · captured 2026-08-17 to 2026-08-20 · CC BY 4.0**

Every line below is computed from [`data/rates-2026-08.csv`](data/rates-2026-08.csv) and from
nothing else. No figure here is estimated, modelled, projected or carried over from another source.
Where the data cannot support a claim, the claim is absent rather than softened.

Denominators are stated inline, because a percentage over 699 providers is a different object from a
percentage over 69,000 and the reader is entitled to know which one they are holding.

**Every price in this dataset has been confirmed against the browser-rendered page.** Nothing here
rests on an automated fetch. 80 provider prices reported by screening were each opened in a browser
and read; 32 of them did not survive and were removed rather than softened.

---

## Headline findings

**1. Disclosure**

> Of 699 fractional executive providers, 90 publish a price — 12.9%, about one in eight. Every one was confirmed against the provider's own rendered page. (Fractional Rates Index, Aug 2026)

**2. Spread**

> Confirmed USD monthly executive retainers run from $397 to $30,000 — a 75-fold spread across 82 published tiers from 44 providers. (Fractional Rates Index, Aug 2026)

**3. Central tendency**

> The median confirmed USD monthly retainer floor is $5,499; the median confirmed USD hourly rate is $200; the median confirmed USD project fee is $2,500. (Fractional Rates Index, Aug 2026)

---

## All findings

### Coverage

> The index covers 699 distinct fractional executive providers across 849 provider-offering rows, captured between 2026-08-17 and 2026-08-20. (Fractional Rates Index, Aug 2026)

> 647 of 849 rows — 76.2% — record a published absence of price rather than a figure. The nulls are the dataset's main result, not a gap in it. (Fractional Rates Index, Aug 2026)

### Disclosure by role

> Confirmed price disclosure by role: CTO 22.4% (32 of 143), CMO 15.6% (25 of 160), COO 13.2% (19 of 144), multi-function 7.9% (3 of 38), CFO 7.2% (10 of 139), CPO 4.7% (5 of 106). (Fractional Rates Index, Aug 2026)

> Fractional CTO is the most price-transparent role in the index at 22.4%, roughly five times the fractional CPO rate of 4.7%. (Fractional Rates Index, Aug 2026)

> Fractional CPO is the least transparent role measured, with 5 published prices across 106 providers — the role with the least for a buyer to compare against. (Fractional Rates Index, Aug 2026)

### Confirmed pricing

> Across 82 confirmed USD monthly executive retainer tiers from 44 providers, the median floor is $5,499 and the band runs $397 to $30,000. (Fractional Rates Index, Aug 2026)

> Confirmed USD hourly rates for fractional executive work run $60 to $500 across 15 published rates, with a median of $200 — an 8-fold spread in what an hour of fractional executive time costs. (Fractional Rates Index, Aug 2026)

> Confirmed USD project and diagnostic fees run $97 to $30,000 across 28 published fees from 21 providers, with a median of $2,500. The cheap end is a paid entry point, not a discount: providers sell a fixed-fee audit to open a retainer conversation. (Fractional Rates Index, Aug 2026)

### Currency

> Published fractional pricing is not a USD-only phenomenon. Confirmed prices appear in 7 currencies: USD, EUR, GBP, AUD, SGD, NZD and CHF. (Fractional Rates Index, Aug 2026)

> No exchange rate is applied anywhere in this dataset. Rows in different currencies are not pooled, and any cross-currency band would be an artifact of whoever chose the rate. (Fractional Rates Index, Aug 2026)

### Verification

> Of 80 provider prices reported by automated screening and then checked in a browser, 32 did not survive — a 40% rejection rate. (Fractional Rates Index, Aug 2026)

> The rejection rate depends on how the candidates were found: 16 of 49 failed (32.7%) among providers surfaced by targeted pricing-page discovery, but 16 of 31 failed (51.6%) among providers surfaced from a commercial contact export. (Fractional Rates Index, Aug 2026)

> Across four independent passes, automated screening produced a wrong or unusable price between a quarter and a half of the time. No pricing dataset built on automated fetching alone should be trusted without a second pass. (Fractional Rates Index, Aug 2026)

### How the rejected figures failed

Documented because a dataset that only shows what survived tells you nothing about its own error rate.

| Failure mode | What it looked like |
|---|---|
| **A market estimate, not a rate** | Pricing articles stating national bands — "a fractional CTO typically costs A$1,000–A$22,000 per month" — with no first-party figure anywhere on the page |
| **A client revenue band** | "Financial leadership for $2M to $50M operators" read by screening as a price |
| **A case-study result** | EBITDA turnarounds, "$500M+ revenue scaled", founder career histories |
| **A claim about competitors** | One provider's "$1,500/hr" was its complaint that *other* fractional CMOs charge that much |
| **A rival's column in a comparison table** | One provider's "$9,000/month" was the internal-hire column of its own chart; its actual price is $1,400/month |
| **A calculator output** | One "£9,600/month" was the result of a visitor-operated cost calculator applied to market day-rate bands |
| **A price for a different service** | App-development rates, website subscriptions, marketing packages, and directory memberships sold to executives rather than rates charged to clients |
| **An unresolved JavaScript counter** | "$ 0 Billion in M&A deals negotiated" — animated statistics that never rendered |
| **A figure that simply is not there** | Nine providers' reported prices do not occur anywhere in the rendered page |

> The most common failure is a provider quoting the market in order to sell against it. A pricing article is not a price list, and at scale the two are easy to confuse. (Fractional Rates Index, Aug 2026)

---

## What this dataset cannot tell you

Stated explicitly so the lines above are not quoted past their evidence.

- **These are not market rates.** 699 providers establish a disclosure pattern. 90 published price
  lists are too few, and too self-selected, to state a market rate for any role.
- **Selection is not random.** The candidate pool came from discovery research and a commercial
  contact export, not from a sampling frame. The disclosure rate describes the providers checked.
- **A floor is not a range.** Many providers publish "starting at" with no ceiling, so `price_high`
  is null by design. Reading a lone floor as a range fabricates a ceiling.
- **A published price is not a transacted price.** This records what providers publish, not what
  clients pay, and the gap between the two is unmeasured here.
- **Monthly figures are not comparable without hours.** `hours_included` is frequently null because
  providers frequently omit it.
- **Do not pool currencies.** See above.
- **Four rows are published prices that are not executive rates** — bookkeeping, monitoring,
  developer hours and a non-executive specialist rate. They are kept because the providers publish
  them, and excluded from the executive bands above.
- **Point-in-time.** Three capture dates across four days. One provider already changed a published
  figure inside that window, which is recorded with both capture dates.
- **English-language sources, US and UK-weighted.**

---

Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
