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
rows. 699 providers produce 828 rows.

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

- **Provider identity is the normalised domain of `source_url`**, not the provider name, because the
  same provider is named differently across collection passes. 699 providers, 849 rows.
- **"Publishes a price"** means the provider has at least one row where `price_low` or `price_high`
  is non-null. Providers with only null rows do not count. This yields 90 providers.
- **"Confirmed"** additionally requires `verification` to be `browser_verified` or `first_party`.
  Since the 2026-08-20 verification pass the two counts coincide: all 90 are confirmed.
- **Percentages** are over the 699 providers in the dataset unless the line states otherwise.
- **The retainer band and median** are computed over rows that are confirmed, priced,
  `unit = per_month` and `currency = USD`, **excluding four rows whose own notes state they are not
  executive rates** (bookkeeping, monitoring-only support, developer hours and a non-executive
  specialist rate). That leaves 82 rows from 44 providers, a median floor of $5,499 and a band of
  $397–$30,000. Including the excluded rows moves the floor to $375 and the median to $5,350; both
  figures are reported here so the exclusion is visible rather than silent.
- **Currencies are never pooled and never converted.** Every band and median is computed within a
  single currency, and the currency is named in the finding.
- **Role and offering-type rates** count distinct providers per group. A provider appearing under two
  roles is counted in each.

Anyone can reproduce every figure from `data/rates-2026-08.csv` alone.

---

## 5b. Cohort B — the Apollo-derived cohort (2026-08-20)

`data/rates-2026-08.csv` is a **separate cohort**, collected differently from v1.0.
It is published as its own file, and its figures are reported separately in `FINDINGS.md`, because
pooling the two would silently mix sampling frames and capture dates.

**Provenance.** A commercial contact-database export of 1,003 records of individuals whose job title
contains "fractional". **All personal data was discarded before anything entered this repository**:
no names, no email addresses, no personal LinkedIn URLs, no cities. Only the company name and company
domain were retained, and only in-scope providers were carried forward into `data/`. The source export
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
subscription and a physiotherapy clinic. Of the 330 in scope, **one was dropped because its only web
presence was a personal LinkedIn profile rather than a first-party business site, leaving 329 in
`data/`.** Carrying the out-of-scope companies through would have corrupted the denominator of every
disclosure rate in this repository.

**The screening list itself is not published.** It recorded 616 companies that turned out to have
nothing to do with fractional services, which is a fact about a contact export rather than a fact
about this market, and it named those businesses without telling a reader anything they could use.
The test applied to each is stated above and is reproducible against any provider's live site.

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

## 5c. The merged dataset

`data/rates-2026-08.csv` is the **dataset**. It merges every collection pass into one file so that
provider counts are correct. The per-pass files have been **deleted**: they double-counted 79
providers and published 8 providers in contradictory states, so keeping them alongside the merged
file invited exactly the error the merge fixed. They remain in git history, and the `source_pass`
column records which pass produced every row.

**Why merging was necessary.** 57 providers appeared in more than one pass. Adding the per-file
counts together produced 778 providers where there are 699, and 99 price-publishers where there are
89. Worse, 8 providers were published in two contradictory states at once, priced in one file and
recorded as having no published price in another.

**Merge rules, applied mechanically and logged:**

1. **Identity is the normalised domain of `source_url`**, not the provider name. The same provider is
   named differently across passes; the domain is stable.
2. **Every priced row is kept.** A provider with four published tiers keeps four rows.
3. **A null row is dropped when another pass found a price for that provider** and the null came from
   a pass that found none. 10 such stale nulls were removed. This resolves all 8 contradictions in
   favour of the pass that found a figure.
4. **A null row is kept when it sits beside prices from the same pass**, because it documents a
   genuinely unpriced tier. A provider publishing three figures and one "Custom Pricing" tier is
   correctly recorded as four rows. 11 such rows were kept.
5. **Exact-duplicate offerings collapse**, keeping the row with the strongest verification. 39
   duplicates were removed.
6. **One provider name per domain**, taken from the best-verified priced row.

**Two columns were added, and the first matters more than anything else in this file:**

| Column | Values |
|---|---|
| `verification` | `browser_verified`, `first_party`, `screened_only`, `blocked`, `unreachable`, `rejected`. `fetch_only` is retired: no row carries it since the 2026-08-20 pass |
| `source_pass` | Which collection pass produced the row |

**`fetch_only` was the label for a problem this merge exposed, and it has since been cleared.** The
merge found that 43 of the 89 apparent price-publishers rested on an automated fetch, 21 of them
saying "WebFetch-verified" in their own notes. Under section 3.1 a summarizing fetch is not a
capture, so none of those figures could be asserted.

**All affected providers were then checked in a browser on 2026-08-20**, in two batches: 49 surfaced
by targeted pricing-page discovery, and 31 surfaced from the contact export. 48 were confirmed and
their figures recorded verbatim; 32 did not survive and their prices were removed.

**The rejection rate depends on how the candidate was found.** 16 of 49 failed (32.7%) in the
discovery batch, but 16 of 31 failed (51.6%) in the contact-export batch, because a contact export
surfaces companies whose pages talk about revenue bands and client outcomes rather than prices.
Across all four passes the range is 25% to 52%. **No unconfirmed price remains in the dataset**, and
the confirmed rate settled at 90 of 699 (12.9%).

Two classification errors were found and fixed during that pass, both worth recording. A regular
expression written to catch HTTP status 999 also matched any price ending in ",999", which wrongly
marked two confirmed prices as bot-blocked. And one provider's pre-existing rows survived a
supersession sweep because they carried a different label, briefly duplicating that provider until
the overlap was resolved by capture date.

**Correction to earlier scope statements.** v1.0 recorded USD only. The dataset now contains
confirmed published prices in **7 currencies**: USD, GBP, EUR, AUD, SGD, NZD and CHF. The "USD only"
limitation stated for v1.0 no longer describes the dataset. `currency` carries the code per row and
**prices are not converted**: no exchange rate is applied anywhere, and rows in different currencies
must not be pooled into a single band.

**Three capture dates** are present (2026-08-17, 2026-08-19, 2026-08-20). `capture_date` is per row.

---

## 6. Known limitations

- **Small confirmed sample.** 699 providers establish a disclosure pattern, but only 90 publish a
  price. That is **not enough to state market rates** for any role. No row in this dataset should be
  read as a market range.
- **Point-in-time.** Three capture dates across four days. Provider pages change: Go Fractional
  described "over 1,200 fractional executives" on 2026-08-16 and "15,000 operators" on 2026-08-17.
  Four days cannot show stability.
- **Role coverage is uneven.** CPO is the thinnest at 5 confirmed publishers out of 106 providers,
  so the CPO figure rests on very little and should not be compared confidently against CTO.
- **A published price is not a transacted price.** This records what providers publish, not what
  clients pay, and the gap between the two is unmeasured here.
- **Monthly figures are not comparable without hours.** `hours_included` is frequently null because
  providers frequently omit it.
- **Selection is not random.** The candidate pool came from discovery research, not from a sampling
  frame, so the disclosure rate describes the providers checked and is not a population estimate.
- **English-language sources, US and UK-weighted.** Seven currencies appear; USD dominates.

---

Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
