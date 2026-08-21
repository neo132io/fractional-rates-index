# The Fractional Rates Index

**v1.0 · captured 2026-08-17 · CC BY 4.0**

An open dataset of **publicly published pricing for fractional executive services**. Every figure in
this repository carries the provider's own URL and the date it was captured. Nothing is estimated,
modelled or inferred.

The index exists because the fractional market discusses its own pricing almost entirely through
numbers with no traceable origin. This repository takes the opposite position: a number is worth
citing only when a reader can follow it back to the page it came from and check it. Where the data
cannot support a claim, this repository says so rather than filling the gap.

Website: **https://saasfractionalcpo.com** — the `/data/` page goes live **24 August 2026**.

---

## The three headline findings

**1.** Across **736 providers**, only **129 publish a price** — **17.5%**, about one in six. Every one
was confirmed against the provider's own rendered page, and every provider in the index was opened
in a browser — not a sample, all 736.

**2.** Confirmed USD monthly executive retainers run from **$299 to $50,000** — a 167-fold spread
across 122 tiers from 61 providers. Sterling runs **£699 to £18,000** across 23 tiers; the euro band is
now reportable at **€1,200 to €25,000** across 12 tiers.

**3.** The **median confirmed USD monthly retainer floor is $5,000**, the median confirmed USD hourly
rate is **$200**, and the median confirmed USD project fee is **$2,500**.

Full set with denominators: **[FINDINGS.md](FINDINGS.md)**.

---

## What is in here

| Path | What it is |
|---|---|
| [`FINDINGS.md`](FINDINGS.md) | Every finding v1.0 supports, each with its denominator |
| **[`data/rates-2026-08.csv`](data/rates-2026-08.csv)** | **The dataset.** 938 rows, 736 providers, 129 with a browser-confirmed published price |
| [`methodology.md`](methodology.md) | Inclusion criteria, collection protocol, limitations |
| [`analysis/market-size-reality-check.md`](analysis/market-size-reality-check.md) | Citation-genealogy audit of the market's four most-cited statistics |
| [`standard/services-agreement.md`](standard/services-agreement.md) | The Fractional CPO Engagement Standard, open template v1.1 |
| [`standard/scope-of-work.md`](standard/scope-of-work.md) | Open scope-of-work template, v1.1. Attaches to the agreement |
| [`research/verification-queue-raw.csv`](research/verification-queue-raw.csv) | 315 unverified provider candidates. **Not data.** See below |
| [`LICENSE`](LICENSE) | CC BY 4.0 full legal code |
| [`NOTICE.md`](NOTICE.md) | Attribution line and what the license does and does not cover |

### A note on the dataset scope

One file, cross-role: CFO, CMO, CTO, COO, CPO and multi-function marketplaces. The disclosure
pattern is only visible by comparison, and separate per-role files turned out to double-count
providers who serve more than one role. The `role` and `source_pass` columns preserve everything
those files carried.

### A note on `research/`

`research/verification-queue-raw.csv` holds **315 unverified provider candidates** produced by two
independent discovery passes. It is deliberately outside `data/` because **not one row in it has been
verified**, and it contains raw research artifacts: markdown fragments, search-tool citation markers
and unparsed notes. No number in it may be cited. It is published for transparency about how the
candidate pool was built, and it is the input queue for the v1.1 per-role editions, which require
browser verification of each candidate before any of it becomes data.

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
boundary, and commercial terms. Precedence between them is explicit: **the scope of work governs
what is delivered, the agreement governs everything legal, and the agreement wins any conflict.**

---

## Methodology in brief

**Published prices only.** A figure enters the dataset from the provider's own page or not at all.
Third-party estimates of a provider's rates are excluded even where they look authoritative — this
release contains a clean demonstration of why, in which a third-party estimate of one provider's
floor is off by a factor of two against that provider's own published figure.

**Two-stage verification.** Stage one screens a page with an automated fetch. Stage two confirms
every price-bearing row against the browser-rendered page. **A summarizing fetch is not a capture.**
In this run, 3 of 10 stage-one price reports failed stage-two verification and were dropped.

**Nulls are results.** Providers publishing no price are included as rows, not omitted. 68.8% of the
rows in this index are a published absence of price, and that is the index's main finding rather than
a gap in it.

**Every price here is confirmed, and every provider has been opened.** The `verification` column
records how each row was established. There are no unconfirmed prices left in the dataset: 94
provider prices reported by automated screening were each opened in a browser and read, and the 41
that did not survive were removed rather than softened — a 43.6% rejection rate.

**Then the other direction was checked too.** A full browser pass over all 736 providers, completed
2026-08-21, found a published price on 34 providers the dataset had recorded as publishing none — a
5.3% false-negative rate. On 14 of those 34 the price was on a `/pricing` page no earlier pass had
opened. Screening errs both ways, and only opening the page distinguishes "publishes nothing" from
"publishes elsewhere".

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
The Fractional Rates Index, captured 2026-08-17 to 2026-08-21. saasfractionalcpo.com. CC BY 4.0.
```

BibTeX:

```bibtex
@dataset{fractional_rates_index_2026,
  title   = {The Fractional Rates Index},
  author  = {Kadosh, Sivan},
  year    = {2026},
  version = {1.0},
  url     = {https://saasfractionalcpo.com},
  note    = {Captured 2026-08-17},
  license = {CC BY 4.0}
}
```

Please cite the version and capture date. Provider pages change, and a figure with no capture date is
the problem this index was built to address.

---

## Roadmap

**Every provider has now been opened in a browser — all 736, not a sample.** That full pass moved the
confirmed disclosure rate from 12.9% to 17.5% and overturned the file's sharpest claim: fractional
CPO had been the least transparent role at 4.7%, and is now 13.5%. The old figure was an artifact of
unopened pricing pages, not a fact about CPOs. Fractional CFO is now the least transparent role at
12.5%.

**Every candidate list this project holds has now been worked through.** The 315-row research queue
yielded 198 distinct domains, 142 of which were already covered; the remaining 56 were screened and
35 were in scope, adding 5 confirmed price publishers.

**Next:** a second capture pass, to establish which published prices are stable over time. One
provider already changed a published figure inside the four-day capture window, which is recorded
with both dates. Beyond that, the index needs new discovery rather than more verification.

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

Corrections are published with the version that carries them, and the changelog records what changed.
**Removal requests are honoured without argument** — the dataset's value does not depend on any single
provider being in it. A dataset that is never contradicted is usually one nobody checked.

---

## License

**CC BY 4.0.** Use, adapt and redistribute, including commercially, with attribution.

The license covers this compilation — the selection, verification and arrangement of the rows. It
does not assert ownership of the underlying published facts, which belong to the providers who
published them.

Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
