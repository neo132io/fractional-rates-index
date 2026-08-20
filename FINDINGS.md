# Findings

**The Fractional Rates Index · captured 2026-08-17 to 2026-08-20 · CC BY 4.0**

Every line below is computed from [`data/rates-2026-08.csv`](data/rates-2026-08.csv) and from
nothing else. No figure here is estimated, modelled, projected or carried over from another source.
Where the data cannot support a claim, the claim is absent rather than softened.

Denominators are stated inline, because a percentage over 699 providers is a different object from a
percentage over 69,000 and the reader is entitled to know which one they are holding.

---

## Read this before quoting any number

**"Publishes a price" and "confirmed to publish a price" are different counts, and the gap is large.**

| | Providers | Share of 699 |
|---|---|---|
| Appear to publish a price | 89 | 12.7% |
| **Confirmed against the browser-rendered page** | **46** | **6.6%** |
| Reported by automated fetch only, not yet confirmed | 43 | 6.2% |

The `verification` column carries this per row. `browser_verified` and `first_party` rows meet the
stage-two standard. **`fetch_only` rows do not** — their figure was reported by an automated fetch
and has not been confirmed in a browser. Under this repository's own protocol, a summarizing fetch is
not a capture, so those figures are labelled rather than counted.

**The defensible headline is 46 of 699.** The measured stage-one error rate is 30% in the first pass
and 25% in the second, so expect roughly a quarter of the 43 unconfirmed providers to fail browser
confirmation.

---

## Headline findings

**1. Disclosure**

> Of 699 fractional executive providers, 46 are confirmed to publish a price — 6.6%, about one in fifteen. A further 43 appear to, on evidence not yet confirmed. (Fractional Rates Index, Aug 2026)

**2. Spread**

> Among confirmed USD monthly retainers, published figures run from $397 to $30,000 — a 75-fold spread across 44 tiers from 23 providers. (Fractional Rates Index, Aug 2026)

**3. Central tendency**

> The median confirmed USD monthly retainer floor is $6,250, and the median confirmed USD hourly rate is $200. (Fractional Rates Index, Aug 2026)

---

## All findings

### Coverage

> The index covers 699 distinct fractional executive providers across 835 provider-offering rows, captured between 2026-08-17 and 2026-08-20. (Fractional Rates Index, Aug 2026)

> 647 of 835 rows — 77.5% — record a published absence of price rather than a figure. The nulls are the dataset's main result, not a gap in it. (Fractional Rates Index, Aug 2026)

### Why providers publish nothing

> Of 647 rows with no published figure: 574 publish nothing resembling a price, 58 direct the reader to a quote or a call, 8 were unreachable at capture, and 7 blocked automated access. (Fractional Rates Index, Aug 2026)

> 58 providers state that pricing exists and then withhold it behind a call or a form. Withheld pricing is a deliberate choice, and it is distinguishable in this dataset from silence. (Fractional Rates Index, Aug 2026)

### Disclosure by role

> Confirmed price disclosure by role: CMO 13.8% (22 of 159), COO 11.2% (16 of 143), multi-function 4.8% (2 of 42), CTO 2.8% (4 of 145), CPO 1.9% (2 of 106), CFO 0.7% (1 of 136). (Fractional Rates Index, Aug 2026)

> Only 1 of 136 fractional CFO providers has a confirmed published price — the least transparent role in the index by a wide margin. (Fractional Rates Index, Aug 2026)

> Fractional CTO is where claimed and confirmed disclosure diverge most: 48 CTO providers appear to publish a price, but only 4 are browser-confirmed. That gap is a verification backlog, not a finding about CTOs. (Fractional Rates Index, Aug 2026)

### Confirmed pricing

> Across 44 confirmed USD monthly retainer tiers from 23 providers, the median floor is $6,250 and the full band runs $397 to $30,000. (Fractional Rates Index, Aug 2026)

> Confirmed USD hourly rates for fractional executive work run $100 to $399 across 9 published rates, with a median of $200. (Fractional Rates Index, Aug 2026)

### Currency

> Published fractional pricing is not a USD-only phenomenon. Confirmed rows appear in 4 currencies (USD, EUR, GBP, AUD) and the full priced set spans 8 (adding SGD, NZD, DKK, CHF). (Fractional Rates Index, Aug 2026)

> No exchange rate is applied anywhere in this dataset. Rows in different currencies are not pooled, and any cross-currency band would be an artifact of whoever chose the rate. (Fractional Rates Index, Aug 2026)

### Verification

> Across two measured passes, automated screening reported prices that failed browser confirmation 30% and 25% of the time. Any pricing dataset built on automated fetching alone should be assumed to carry an error rate in that range. (Fractional Rates Index, Aug 2026)

> Documented stage-two rejections include a "$1,500/hr" figure that turned out to be a claim about competitors, a "$9,000/month" figure that was a rival's column in a comparison table, and two figures that do not occur anywhere in the rendered page. (Fractional Rates Index, Aug 2026)

---

## What this dataset cannot tell you

Stated explicitly so the lines above are not quoted past their evidence.

- **These are not market rates.** 699 providers establish a disclosure pattern. The 46 confirmed
  price-publishers are too few, and too self-selected, to state a market rate for any role.
- **Selection is not random.** The candidate pool came from discovery research and a commercial
  contact export, not from a sampling frame. The disclosure rate describes the providers checked.
- **A floor is not a range.** Many providers publish "starting at" with no ceiling, so `price_high`
  is null by design. Reading a lone floor as a range fabricates a ceiling.
- **A published price is not a transacted price.** This records what providers publish, not what
  clients pay, and the gap between the two is unmeasured here.
- **Monthly figures are not comparable without hours.** `hours_included` is frequently null because
  providers frequently omit it.
- **Do not pool currencies.** See above.
- **Point-in-time.** Three capture dates across four days. Nothing here measures change over time.
- **English-language sources, US and UK-weighted.**

---

Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
