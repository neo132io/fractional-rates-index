# Findings

**The Fractional Rates Index · v1.0 · captured 2026-08-17 · CC BY 4.0**

Every line below is computed from `data/rates-cpo-2026-08.csv` and from nothing else. No figure here
is estimated, modelled, projected or carried over from another source. Where the dataset cannot
support a claim, the claim is absent rather than softened.

Denominators are stated inline, because a percentage over 34 providers is a different object from a
percentage over 3,400 and the reader is entitled to know which one they are holding.

---

## Headline findings

**1. Disclosure**

> Only 8 of 34 fractional executive providers publish a price at all — 23.5%, fewer than one in four. (Fractional Rates Index, Aug 2026)

**2. Spread**

> Published fractional executive monthly retainers run from $500 to $30,000, a 60-fold spread across 7 published tiers. (Fractional Rates Index, Aug 2026)

**3. Central tendency**

> The median published monthly retainer floor is $8,000, unchanged whether or not the one out-of-band support tier is excluded. (Fractional Rates Index, Aug 2026)

---

## All findings

### Coverage and collection

> The v1.0 index checked 34 fractional executive providers and marketplaces on a single capture date, 2026-08-17, producing 43 provider-offering rows. (Fractional Rates Index, Aug 2026)

> 33 of 34 providers were reachable at capture; 1 (The CFO Centre) failed DNS resolution and is recorded as unreachable, which is a different state from publishing no price. (Fractional Rates Index, Aug 2026)

### Price disclosure

> 8 of 34 providers (23.5%) publish at least one figure; measured against the 33 reachable providers the rate is 24.2%. (Fractional Rates Index, Aug 2026)

> 14 of 43 provider-offering rows carry a figure — 67.4% of all rows in the index are a published absence of price. (Fractional Rates Index, Aug 2026)

> Of the 8 providers publishing a figure, 6 were confirmed against the browser-rendered page, 1 is a first-party row, and 1 (Fractionus) was screened only and carries no verification stamp. (Fractional Rates Index, Aug 2026)

### Disclosure by role

> Price disclosure is uneven by role: fractional CTO providers publish at 50.0% (2 of 4), multi-function benches at 40.0% (2 of 5), CPO at 33.3% (3 of 9), CFO at 11.1% (1 of 9), and neither of the CMO (0 of 6) nor COO (0 of 1) providers checked publishes a price. (Fractional Rates Index, Aug 2026)

> Not one of the 6 fractional CMO providers checked publishes a price, the largest fully opaque role group in the index. (Fractional Rates Index, Aug 2026)

### Disclosure by offering type

> Disclosure barely moves with commercial structure: 30.0% of marketplace providers (3 of 10), 25.0% of project providers (1 of 4) and 23.8% of retainer providers (5 of 21) publish a figure. (Fractional Rates Index, Aug 2026)

### Retainer pricing

> Across the 7 published monthly retainer tiers in the index, the median floor is $8,000 and the full band runs $500 to $30,000. (Fractional Rates Index, Aug 2026)

> Excluding the single tier the provider itself states is not executive-level leadership, the published retainer band narrows to $3,000-$30,000 across 6 tiers, and the median floor stays at $8,000. (Fractional Rates Index, Aug 2026)

> Published fractional CPO retainer floors — $6,000 and $8,000 per month across 2 providers — sit below the published fractional CTO band of $3,000 to $30,000 across 5 tiers. Two data points do not make a rate; this is recorded as an observation. (Fractional Rates Index, Aug 2026)

### Verification

> 3 of 10 prices reported by automated screening did not survive browser verification and were dropped rather than softened — a 30% stage-one error rate in this run. (Fractional Rates Index, Aug 2026)

---

## What this dataset cannot tell you

Stated explicitly so the lines above are not quoted past their evidence.

- **These are not market rates.** 34 providers establish a disclosure pattern. They do not size a market or set a rate, and no line above should be quoted as either.
- **A floor is not a range.** Several providers publish "starting at" with no ceiling. `price_high` is null for those rows by design.
- **A published price is not a transacted price.** The index records what providers publish, not what clients pay.
- **A monthly figure without an hours figure is not comparable** to another monthly figure. The `hours_included` column carries this and is frequently null because providers frequently omit it.
- **One capture date.** Every row was captured on 2026-08-17. Nothing here measures change over time.
- **US/UK-centric, English-language, USD only.**

---

Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
