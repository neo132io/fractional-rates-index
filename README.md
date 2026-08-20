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

**1.** Across **699 providers**, only **75 publish a price** — **10.7%**, about one in nine. Every one
of those 75 was confirmed against the provider's own rendered page.

**2.** Confirmed USD monthly retainers run from **$397 to $30,000** — a 75-fold spread across 63
tiers from 34 providers.

**3.** The **median confirmed USD monthly retainer floor is $6,750**, and the median confirmed USD
hourly rate is **$175**.

Full set with denominators: **[FINDINGS.md](FINDINGS.md)**.

---

## What is in here

| Path | What it is |
|---|---|
| [`FINDINGS.md`](FINDINGS.md) | Every finding v1.0 supports, each with its denominator |
| **[`data/rates-2026-08.csv`](data/rates-2026-08.csv)** | **The dataset.** 828 rows, 699 providers, 75 with a browser-confirmed published price |
| [`methodology.md`](methodology.md) | Inclusion criteria, collection protocol, limitations |
| [`analysis/market-size-reality-check.md`](analysis/market-size-reality-check.md) | Citation-genealogy audit of the market's four most-cited statistics |
| [`standard/services-agreement.md`](standard/services-agreement.md) | Open services agreement template, v1.0 |
| [`standard/scope-of-work.md`](standard/scope-of-work.md) | Open scope-of-work template, v1.0. Attaches to the agreement |
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

`standard/` holds two reusable engagement documents under CC BY 4.0: a services agreement template
and the scope of work that attaches to it. **They are working templates, not legal advice**, and
§§7-11 of the agreement need adapting to your jurisdiction by a lawyer.

Bracketed values in them — `[30] days`, `[20-25] hours` — are **template fields for the parties to
set, not published market data.** No figure from the index appears in either document, and neither
asserts a market norm. Where market practice genuinely varies, the templates say so instead of
inventing a standard: there is no single standard notice period in this market, and any document
claiming otherwise is asserting rather than measuring.

Both documents are **fully sourced — no field is left pending.** The scope of work is built from
the scope-of-work source content and from the agreement it attaches to, and it carries the five
sections that decide whether an engagement holds: outcomes, decision rights, cadence, the execution
boundary, and commercial terms.

---

## Methodology in brief

**Published prices only.** A figure enters the dataset from the provider's own page or not at all.
Third-party estimates of a provider's rates are excluded even where they look authoritative — this
release contains a clean demonstration of why, in which a third-party estimate of one provider's
floor is off by a factor of two against that provider's own published figure.

**Two-stage verification.** Stage one screens a page with an automated fetch. Stage two confirms
every price-bearing row against the browser-rendered page. **A summarizing fetch is not a capture.**
In this run, 3 of 10 stage-one price reports failed stage-two verification and were dropped.

**Nulls are results.** Providers publishing no price are included as rows, not omitted. 80.1% of the
rows in this index are a published absence of price, and that is the index's main finding rather than
a gap in it.

**Every price here is confirmed.** The `verification` column records how each row was established.
As of 2026-08-20 there are no unconfirmed prices left in the dataset: 49 provider prices reported by
automated screening were each checked in a browser, and the 16 that did not survive were removed
rather than softened.

Full protocol, inclusion criteria and limitations: **[methodology.md](methodology.md)**.

---

## How to cite

Copy this line exactly:

```
Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
```

For a specific finding, cite the figure with its denominator and the index version:

```
75 of 699 fractional executive providers have a browser-confirmed published price (10.7%).
The Fractional Rates Index, captured 2026-08-17 to 2026-08-20. saasfractionalcpo.com. CC BY 4.0.
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

**The verification backlog is cleared.** Every price in the dataset has been confirmed in a browser.
Clearing it moved the confirmed rate from 6.6% to 10.7% and changed one finding outright: fractional
CTO went from apparently the least-verified role to the most price-transparent one at 21.7%.

**Next:** browser verification of the remaining candidates in `research/`, and a second capture pass
to establish which published prices are stable over time. One provider already changed a published
figure inside the four-day capture window, which is recorded with both dates.

---

## Corrections

If a figure here is wrong, or a provider's page has changed, open an issue with the URL and what it
says now. Corrections are published with the version that carries them. A dataset that is never
contradicted is usually one nobody checked.

---

## License

**CC BY 4.0.** Use, adapt and redistribute, including commercially, with attribution.

The license covers this compilation — the selection, verification and arrangement of the rows. It
does not assert ownership of the underlying published facts, which belong to the providers who
published them.

Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
