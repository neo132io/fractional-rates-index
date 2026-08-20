# Findings

**The Fractional Rates Index · captured 2026-08-17 to 2026-08-20 · CC BY 4.0**

Every line below is computed from [`data/rates-2026-08.csv`](data/rates-2026-08.csv) and from
nothing else. No figure here is estimated, modelled, projected or carried over from another source.
Where the data cannot support a claim, the claim is absent rather than softened.

Denominators are stated inline, because a percentage over 699 providers is a different object from a
percentage over 69,000 and the reader is entitled to know which one they are holding.

**Every price in this dataset has been confirmed against the browser-rendered page.** There is no
gap between "appears to publish a price" and "confirmed to publish a price": the verification
backlog was cleared on 2026-08-20, and 16 figures that did not survive that check were removed
rather than softened.

---

## Headline findings

**1. Disclosure**

> Of 699 fractional executive providers, 75 publish a price — 10.7%, about one in nine. Every one of those 75 was confirmed against the provider's own rendered page. (Fractional Rates Index, Aug 2026)

**2. Spread**

> Confirmed USD monthly retainers run from $397 to $30,000 — a 75-fold spread across 63 published tiers from 34 providers. (Fractional Rates Index, Aug 2026)

**3. Central tendency**

> The median confirmed USD monthly retainer floor is $6,750, and the median confirmed USD hourly rate is $175. (Fractional Rates Index, Aug 2026)

---

## All findings

### Coverage

> The index covers 699 distinct fractional executive providers across 828 provider-offering rows, captured between 2026-08-17 and 2026-08-20. (Fractional Rates Index, Aug 2026)

> 663 of 828 rows — 80.1% — record a published absence of price rather than a figure. The nulls are the dataset's main result, not a gap in it. (Fractional Rates Index, Aug 2026)

### Disclosure by role

> Confirmed price disclosure by role: CTO 21.7% (31 of 143), CMO 13.8% (22 of 159), COO 11.2% (16 of 143), multi-function 7.1% (3 of 42), CPO 4.7% (5 of 106), CFO 1.5% (2 of 137). (Fractional Rates Index, Aug 2026)

> Fractional CTO is the most price-transparent role in the index at 21.7%, roughly fourteen times the fractional CFO rate of 1.5%. (Fractional Rates Index, Aug 2026)

> Only 2 of 137 fractional CFO providers publish a price — the least transparent role in the index by a wide margin, and the one where buyers have least to compare against. (Fractional Rates Index, Aug 2026)

### Confirmed pricing

> Across 63 confirmed USD monthly retainer tiers from 34 providers, the median floor is $6,750 and the full band runs $397 to $30,000. (Fractional Rates Index, Aug 2026)

> Confirmed USD hourly rates for fractional executive work run $60 to $399 across 14 published rates, with a median of $175 — a 6.7-fold spread in what an hour of fractional executive time costs. (Fractional Rates Index, Aug 2026)

### Currency

> Published fractional pricing is not a USD-only phenomenon. Confirmed prices appear in 7 currencies: USD, EUR, GBP, AUD, SGD, NZD and CHF. (Fractional Rates Index, Aug 2026)

> No exchange rate is applied anywhere in this dataset. Rows in different currencies are not pooled, and any cross-currency band would be an artifact of whoever chose the rate. (Fractional Rates Index, Aug 2026)

### Verification

> Of 49 providers whose prices were reported by automated screening and then checked in a browser, 16 did not survive — a 32.7% rejection rate, consistent with the 30% and 25% measured in earlier passes. (Fractional Rates Index, Aug 2026)

> Across three independent passes, automated screening produced a wrong or unusable price between a quarter and a third of the time. Any pricing dataset built on automated fetching alone should be assumed to carry an error rate in that range. (Fractional Rates Index, Aug 2026)

### How the rejected figures failed

Documented because a dataset that only shows what survived tells you nothing about its own error rate.

| Failure mode | Example |
|---|---|
| **A claim about competitors** | One provider's "$1,500/hr" was its complaint that *other* fractional CMOs charge that much |
| **A rival's column in a comparison table** | One provider's "$9,000/month" was the cost of an internal hire in its own comparison chart; its actual price is $1,400/month |
| **A market estimate, not a rate** | Several pricing articles state national market bands and publish no first-party figure at all |
| **A calculator output** | One "£9,600/month" was the result of a visitor-operated cost calculator applied to market day-rate bands |
| **A price for a different service** | App-development day rates, website subscriptions, and directory memberships sold to executives rather than rates charged to clients |
| **A figure that simply is not there** | Six providers' reported prices do not occur anywhere in the rendered page |

> The single most common failure is a provider quoting the market to sell against it. A pricing article is not a price list, and the two are easy to confuse at scale. (Fractional Rates Index, Aug 2026)

---

## What this dataset cannot tell you

Stated explicitly so the lines above are not quoted past their evidence.

- **These are not market rates.** 699 providers establish a disclosure pattern. 75 published price
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
- **Point-in-time.** Three capture dates across four days. One provider already changed a published
  figure inside that window, which is recorded with both capture dates.
- **English-language sources, US and UK-weighted.**

---

Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
