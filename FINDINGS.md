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

## Cohort B — Apollo-derived discovery, captured 2026-08-20

A second cohort, collected and screened separately from the v1.0 dataset. **Its figures are not
comparable to the v1.0 figures above** and must not be pooled with them: different sampling frame,
different capture date, and a far lower browser-verification rate. Reported separately for that reason.

> A 1,003-record commercial contact export yielded 967 distinct companies, of which only 330 (34.1%) offer fractional executive services at all — 616 never mention the word "fractional". (Fractional Rates Index, Aug 2026)

> Contact-database exports are a poor sampling frame for provider research: 63.7% of the companies in one 967-company export were out of scope on inspection. (Fractional Rates Index, Aug 2026)

> Of 329 in-scope fractional providers screened, 6 publish a browser-verified price — 1.8%. A further 35 (10.6%) show a price-shaped string awaiting browser verification, so the disclosure rate for this cohort sits between 1.8% and a ceiling of 12.5%. (Fractional Rates Index, Aug 2026)

> 34 of 329 in-scope providers (10.3%) publish no figure but direct the reader to a quote or a call — pricing exists and is deliberately withheld. (Fractional Rates Index, Aug 2026)

> 251 of 329 in-scope fractional providers (76.3%) publish nothing resembling a price on their homepage or any pricing-linked page. (Fractional Rates Index, Aug 2026)

> Of 8 stage-one price reports taken to browser verification in this cohort, 2 were rejected — a 25% rejection rate, consistent with the 30% measured in v1.0. (Fractional Rates Index, Aug 2026)

**Verified price rows in this cohort**, all captured 2026-08-20: fractional CTO retainers at $1,800,
$2,800, $5,000 and $9,500 per month from one provider; fractional CTO hourly rates of $150, $200 and
$300 against published monthly hour bands; an executive-collective subscription table running $397 to
$3,697 per month by expert count and hours; fractional operations retainers at $4,000, $9,600 and
$20,000 per month; a fractional CMO retainer from $15,000 per month; and a fractional CMO hourly rate
of $200.

**Two stage-two rejections, documented.** One provider's "$1,500/hr" turned out to be a claim about
*competitors*, not its own rate. Another's "$8,000 retainer" did not occur anywhere in the
browser-rendered page. Both were dropped, and both are recorded in the dataset's `notes`.

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
