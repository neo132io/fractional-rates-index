# The Fractional Rates Index

**v2.1.1-live · collection in progress · CC BY 4.0** (v1.2, captured 2026-08-17 to 2026-08-21, remains the last fully browser-audited release below)

An open dataset of **publicly published pricing for fractional executive services**. Every figure in
this repository carries the provider's own URL and the date it was captured. Nothing is estimated,
modelled or inferred.

The index exists because the fractional market discusses its own pricing almost entirely through
numbers with no traceable origin. This repository takes the opposite position: a number is worth
citing only when a reader can follow it back to the page it came from and check it. Where the data
cannot support a claim, this repository says so rather than filling the gap.

Website: **https://saasfractionalcpo.com/data** — the same snapshot, rendered.


---

## v2.1.1 — the live index (collection in progress)

The index is collected by a calibrated extraction pipeline rather than a one-off browser audit. The
live snapshot in this repository is the same one that renders **https://saasfractionalcpo.com/data**
— the site and this repository update together.

Current snapshot: **1,774 providers tracked · 168 publish a verifiable price (10.7% of the 1,577
sites read) · median published US monthly retainer $5,750, middle half $3,000 to $10,000 · median
across the whole index $172 an hour** · 7 roles · USD, GBP, EUR.

Both headlines carry an interval: $5,750 sits inside $5,000 to $8,000, and $172 inside $125 to $209.
The second of those is a joint interval. It resamples the providers **and** the hours divisor
together, because most of the hourly column is a retainer divided by an estimated number, and an
interval that only covers sampling error would understate the uncertainty by a factor of two.

### The rule that decides what gets published

A figure appears in this index only when it is found **word for word in a quote captured from the
provider's own page**, together with its currency and its cadence, and sits inside a plausibility
band for its unit. All three have to appear in the same quote. A number in one place and the word
"hour" in another do not, together, establish an hourly rate.

That rule is the reason four groups that v2.0 published are withdrawn in v2.1, including one built
from a market-summary sentence whose year, 2026, had been read as the top of a euro range.
`data/records-v2.1.1.csv` carries the quote beside every figure, so any row can be checked against
the page it came from.

The band now runs on the derived USD-per-hour column as well as on the price as captured. A $300 a
month retainer is a plausible monthly price and an implausible executive rate once it is divided by
the default divisor, and v2.1 published seven such records. They are held back in v2.1.1 and named
in `data/quarantine-v2.1.1.csv` rather than dropped in silence.

A group needs **eight providers** before it carries a figure at all. 32 of the 38 groups fall below
that line; they are named and counted with empty median cells rather than hidden, so a group of one
can never be mistaken for a finding. COO / US / monthly crossed that line downwards between v2.1 and
v2.1.1: it held eight providers and $3,938, it holds seven now, and it is withdrawn. Anyone who
cited $3,938 will find the withdrawal in [`CHANGELOG.md`](CHANGELOG.md) rather than a gap.

### Files

| File | What it is |
|---|---|
| **[`data/records-v2.1.1.csv`](data/records-v2.1.1.csv)** | **Record level, 347 rows.** Every published figure with its evidence quote, the page it came from, its normalisation chain and a confidence tier |
| [`data/portal-rates-v2.1.1.csv`](data/portal-rates-v2.1.1.csv) | The 6 groups that clear the reporting floor: median, p25/p75, USD-per-hour equivalents, providers and prices counted separately, and the confidence mix behind each |
| [`data/groups-v2.1.1.csv`](data/groups-v2.1.1.csv) | All 38 groups, including the 32 below the floor, which carry no figures |
| [`data/portal-metrics-v2.1.1.json`](data/portal-metrics-v2.1.1.json) | Headlines with bootstrap intervals, the publication funnel, the FX lock, the full methodology, the known limitations and the numeric changes against v2.1 |
| [`data/portal-distribution-v2.1.1.csv`](data/portal-distribution-v2.1.1.csv) | Histogram of published US monthly retainers |
| [`data/quarantine-v2.1.1.csv`](data/quarantine-v2.1.1.csv) | The 27 records that cleared the evidence rules and then fell outside a plausibility band, each with its reason and its quote |
| [`data/hours-evidence-v2.1.1.csv`](data/hours-evidence-v2.1.1.csv) | Every time commitment read out of an offer's own words, with the quote and the field it came from |
| [`data/hours-audit-v2.1.1.csv`](data/hours-audit-v2.1.1.csv) | All 51 stated hour figures, each with its quote and the verdict on it |
| [`data/delta-vs-v2-v2.1.1.csv`](data/delta-vs-v2-v2.1.1.csv) · [`data/delta-vs-v2.1-v2.1.1.csv`](data/delta-vs-v2.1-v2.1.1.csv) | Group by group against v2.0 and against v2.1, with a reason for every move |
| [`data/approved-shrinkage-v2.1.1.json`](data/approved-shrinkage-v2.1.1.json) | The signed authorisation for the one count that falls by more than the release gate allows, with its decomposition |
| [`data/fx-lock-20260903.json`](data/fx-lock-20260903.json) | The ECB reference rates this release converted with |
| [`data/acceptance-gate-v2.1.1.json`](data/acceptance-gate-v2.1.1.json) | 40 published records and all 20 hours citations re-fetched from their live pages before release |
| [`tools/`](tools/) | The generator, the evidence verifier and their tests |

### The comparison column

Every record keeps the currency and unit its provider published, and gains one derived column: USD
per hour. Hourly rates as captured, day rates over eight hours, monthly retainers over the hours the
provider publishes or over 32.5 hours where it publishes none.

Where a provider states how many hours its retainer buys, that number is now read from the offer's
own words and shipped with its quote. Four published monthly records in five still use the default,
and the record-level file says which is which. **The word-for-word guarantee covers the captured
price. It does not cover the divisor**, and no reading of the rules should suggest otherwise.

The 32.5 is measured, not assumed. All 51 stated hour figures in the data were read one by one; 10
were rejected because the column was mixing hours per month, hours per week, days per month, support
SLA response times and plan names. The 41 readings that survived come from **21 providers**, and the
median across those 21 is 32.5. The divisor is then checked against the data from outside: providers
stating an hourly rate publish a median of $200, day rates over eight hours give $250, and retainers
over 32.5 hours give $169 — a retainer buying volume priced below spot, which is what should happen.

**A monthly retainer is not literally a block of hours.** Treat the hourly column as a device for
comparing rows, not as a rate to quote. Across the offers that state both a price and their hours,
hours rise almost in step with the retainer, so part of what the quartiles of the hourly column
measure is the size of an engagement rather than its price.

### Reproducing a release

`tools/generate_release.py` takes one frozen snapshot and one locked FX rate and emits every v2.1.1
file in `data/`. The snapshot's md5 is recorded in `data/portal-metrics-v2.1.1.json`. The snapshot
itself is 5 MB of raw collection and is not in this repository, so a reader can check every shipped
figure against its quote but cannot yet re-run the build. Run `python -m pytest tools/tests` for the
evidence rules, the normalisation and the release build.

### Honesty notes

Collection is in progress toward a 10,000-provider target, so n grows continuously. Region is the
currency a provider quotes in, not where the provider is: a US firm quoting in euros lands in EU. The
hours default is measured on the 21 hosts that publish hours, and providers who publish hours are not
typical of those who do not: on this snapshot they are the more expensive tail. That is the largest
assumption left in the index, and it is stated in the metrics file rather than buried in a footnote.
**saasfractionalcpo.com, which publishes this index, is one of the sampled providers** at $8,000 a
month for 25 hours and $15,000 a month at three to four days a week. It is one host out of 168, its
median of $221.81 an hour sits at the 63rd percentile, and it is not excluded.

---

## The three headline findings (v1.2, 2026-08)

**1.** Across **736 providers**, only **129 publish a price** — **17.5%**, about one in six. Every
provider in the index was opened in a browser: not a sample, all 736. 700 rendered and were read; 36
could not be read and are recorded as such rather than counted as publishing nothing.

**2.** Confirmed USD monthly executive retainers run from **$299 to $50,000** — a 167-fold spread
across 122 tiers from 61 providers. Sterling runs **£699 to £18,000** across 23 tiers; the euro band
is now reportable at **€1,200 to €25,000** across 12 tiers.

**3.** The **median confirmed USD monthly retainer floor is $5,000**, the median confirmed USD hourly
rate is **$200**, and the median confirmed USD project fee is **$2,500**.

Full set with denominators: **[FINDINGS.md](FINDINGS.md)**.

---

## What is in here

| Path | What it is |
|---|---|
| [`FINDINGS.md`](FINDINGS.md) | Every finding this release supports, each with its denominator |
| **[`data/rates-2026-08.csv`](data/rates-2026-08.csv)** | **The dataset.** 938 rows, 736 providers, 129 with a browser-confirmed published price |
| [`methodology.md`](methodology.md) | Inclusion criteria, collection protocol, how each figure is computed, limitations |
| [`CHANGELOG.md`](CHANGELOG.md) | What this index published before, what it publishes now, and why it changed |
| [`research/detector-gaps.md`](research/detector-gaps.md) | The five defects found in our own price-detection tooling, each with a damage assessment |
| [`analysis/market-size-reality-check.md`](analysis/market-size-reality-check.md) | Citation-genealogy audit of the market's four most-cited statistics |
| [`standard/services-agreement.md`](standard/services-agreement.md) | The Fractional CPO Engagement Standard, open template v1.1 |
| [`standard/scope-of-work.md`](standard/scope-of-work.md) | Open scope-of-work template, v1.1. Attaches to the agreement |
| [`research/verification-queue-raw.csv`](research/verification-queue-raw.csv) | 315 raw provider candidates. **Not data.** See below |
| [`LICENSE`](LICENSE) | CC BY 4.0 full legal code |
| [`NOTICE.md`](NOTICE.md) | Attribution line and what the license does and does not cover |

### A note on the dataset scope

One file, cross-role: CFO, CMO, CTO, COO, CPO and multi-function marketplaces. The disclosure pattern
is only visible by comparison, and separate per-role files turned out to double-count providers who
serve more than one role. The `role` and `source_pass` columns preserve everything those files
carried.

### A note on `research/`

`research/verification-queue-raw.csv` holds **315 raw provider candidates** produced by two
independent discovery passes. It is deliberately outside `data/` because it contains raw research
artifacts: markdown fragments, search-tool citation markers and unparsed notes. **No number in it may
be cited.** It is published for transparency about how the candidate pool was built. That queue has
since been worked through in full — it yielded 198 distinct domains, 142 already covered, and of the
remaining 56 screened, 35 were in scope and added 5 confirmed price publishers.

### A note on `standard/`

`standard/` holds two reusable engagement documents under CC BY 4.0: the Fractional CPO Engagement
Standard and the scope of work that attaches to it. **They are working templates, not legal advice.**
Have a lawyer review **the whole agreement**, not selected sections: employment status, data
protection, restraint of trade and limitation of liability all vary sharply by country, and a clause
that is standard in one jurisdiction is void in another.

The agreement exists because fractional engagements keep failing on the same four points: undefined
decision rights, hours treated as a meter, scope documents that quietly become performance
guarantees, and no plan for how the engagement ends. Its **Commentary** blocks explain the reasoning
and are expressly not part of the agreement.

Bracketed values in them are **template fields for the parties to set, not published market data.**
The agreement states no rates, bands or market figures at all — commercial terms are for the parties.
No figure from the index appears in either document, and neither asserts a market norm. Where market
practice genuinely varies, the templates say so instead of inventing a standard: there is no single
standard notice period in this market, and any document claiming otherwise is asserting rather than
measuring.

Both documents are **fully sourced — no field is left pending.** The scope of work carries the five
sections that decide whether an engagement holds: outcomes, decision rights, cadence, the execution
boundary, and commercial terms. Precedence between them is explicit: **the scope of work governs what
is delivered, the agreement governs everything legal, and the agreement wins any conflict.**

---

## Methodology in brief

**Published prices only.** A figure enters the dataset from the provider's own page or not at all.
Third-party estimates are excluded even where they look authoritative — this release contains a clean
demonstration of why, in which a third-party estimate of one provider's floor is off by a factor of
two against that provider's own published figure.

**Nulls are results.** Providers publishing no price are included as rows, not omitted. **68.8% of
the rows in this index are a published absence of price**, and that is the index's main finding
rather than a gap in it.

**No row rests on automated screening alone.** The `verification` column records how each row was
established: 899 of 938 rows are `browser_verified`, and the other 39 carry an explicit `blocked`,
`unreachable` or `out_of_scope` label. A summarizing fetch is not a capture.

**Both error rates are published, not just the flattering one.** Automated screening was tested in
both directions:

- It **reported prices that were not there** on 43.6% of the candidates it flagged — 41 of 94 were
  removed after a browser check rather than softened.
- It **missed prices that were there** on 5.3% of the providers it cleared — 34 of 643. On 14 of
  those 34 the price sat on a `/pricing` page no earlier pass had opened.

Neither number is knowable without opening the page. That is the whole argument for the protocol.

**The maintainer is in the dataset.** saasfractionalcpo.com publishes a price and is recorded as a row
like any other, checked in the same browser pass, so the maintainer's own pricing is subject to this
index rather than exempt from it. Readers should discount that row accordingly.

**17.5% is a floor, not a point estimate.** 36 providers could not be read and are counted as
publishing nothing. If every one of them published a price the rate would be 22.4%.

Full protocol, inclusion criteria and limitations: **[methodology.md](methodology.md)**.

---

## How to cite

Copy this line exactly:

```
Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
```

For a specific finding, cite the figure with its denominator and the index version:

```
129 of 736 fractional executive providers have a browser-confirmed published price (17.5%).
The Fractional Rates Index v1.2, captured 2026-08-17 to 2026-08-21. saasfractionalcpo.com. CC BY 4.0.
```

BibTeX:

```bibtex
@dataset{fractional_rates_index_2026,
  title   = {The Fractional Rates Index},
  author  = {Kadosh, Sivan},
  year    = {2026},
  version = {1.1},
  url     = {https://saasfractionalcpo.com},
  note    = {Captured 2026-08-17 to 2026-08-21},
  license = {CC BY 4.0}
}
```

**Please cite the version.** v1.1 corrected several figures published in v1.0, including the headline
disclosure rate and the role table. [`CHANGELOG.md`](CHANGELOG.md) lists what changed and what to do
if you cited an earlier figure. A figure with no capture date and no version is the problem this index
was built to address.

---

## Roadmap

**Every provider has now been opened in a browser — all 736, not a sample**, and every candidate list
this project holds has been worked through. That leaves verification largely complete and puts the
open work elsewhere.

**Next:** a second capture pass, to establish which published prices are stable over time. One
provider already changed a published figure inside the five-day capture window, which is recorded with
both dates. Nothing in this release measures change, and a repeated-measure pass is the only way to
get there.

**Also open:** the 36 providers whose pages could not be read, which are the difference between a
17.5% floor and a 22.4% ceiling; and new discovery, since the index now needs more providers rather
than more verification of the ones it has.

---

## What a row does and does not say

Every row records **one observation of one page on one date**. It says what was on that page at
capture, and nothing else.

A row that records no published price is **not** a statement that the provider has no price, hides
its pricing, or behaves badly. Most providers price on enquiry, which is a normal commercial choice
and the majority behaviour in this market. Where an automated screening pass flagged a figure that a
browser capture did not find, the note says so and attributes the discrepancy to **our screening
tool**, not to the provider.

Nothing here is a statement about the conduct, quality or good faith of any provider or any person.

## Corrections

**If you are a provider named here and something is wrong, we will fix it.** Open an issue with the
URL and what the page says now, or write to us. That includes:

- a price we recorded that is wrong, out of date, or was never yours
- a page we read incorrectly
- a "no published price" row where you do publish one
- a request to be removed from the dataset entirely

Corrections are published with the version that carries them, and [`CHANGELOG.md`](CHANGELOG.md)
records what changed. **Removal requests are honoured without argument** — the dataset's value does
not depend on any single provider being in it. A dataset that is never contradicted is usually one
nobody checked.

---

## License

**CC BY 4.0.** Use, adapt and redistribute, including commercially, with attribution.

The license covers this compilation — the selection, verification and arrangement of the rows. It
does not assert ownership of the underlying published facts, which belong to the providers who
published them.

Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
