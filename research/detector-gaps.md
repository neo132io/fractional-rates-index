# Detector gaps

Defects found in the price-detection tooling during the full-coverage browser pass of
2026-08-21, recorded because a dataset that only shows what its tools caught tells you
nothing about what they missed.

Each entry states the defect, whether it damaged the published data, and how that was
established. "No damage" here means checked, not assumed.

---

## 1. Currency written after the number

**Defect.** The detector anchored on a currency symbol preceding a number (`$10,000`).
A page writing `USD 10,000` was invisible to it.

**Damage.** One provider (`8figurecpo.com`) was recorded as publishing no price on this
basis. The same page, read minutes later with a pattern that also matches a
number-then-code form, yielded a three-month engagement priced per month.

**Fix.** A second alternation was added mid-pass:
`\d[\d,.]*\s?[kKmM]?\s?(?:CHF|USD|EUR|GBP|AUD|NZD|CAD|SGD|ILS)\b`.

**Residual risk.** Roughly the first 33 providers in the pass were read before the fix.
They have not been re-read.

---

## 2. Extraction ran before the page rendered

**Defect.** A capture taken before client-side rendering completed returns an empty body
or a shell of a few hundred characters. The fetch succeeds, so the miss looks like an
absence rather than a failure.

**Damage.** At least four providers returned an empty or near-empty body on first attempt
and rendered normally after a further 3–5 seconds — `wellspentconsulting.com`,
`smartgrowthcfo.com`, `paramgrowth.com`, `madelynvictoriaco.com`. Of those,
`madelynvictoriaco.com` turned out to publish two priced tiers.

**Fix.** Every empty or suspiciously short body was retried with a longer wait before any
"no price" observation was recorded.

**Residual risk.** A single-attempt "no price" is weaker evidence than a retried one. Rows
whose note does not mention a retry rest on one capture.

---

## 3. Swiss apostrophe thousands separator

**Defect.** The number class was `\d[\d,.]*`, which stops at an apostrophe. Swiss sites
write `CHF 2'900`, so the detector would capture `CHF 2` — a hit is still raised, so
nothing is silently dropped, but the captured **value** is wrong by three orders of
magnitude.

**Damage: none.** Established rather than assumed. All three Swiss and Liechtenstein
domains in the dataset were re-read on 2026-08-21: `flossels.ch` publishes
`from CHF 2'900/month` and is recorded correctly at 2900; `cro2go.ch` and
`productrocket.ch` publish no figure. The single CHF row in the file is correct.

**Fix.** The apostrophe was added to the number class for the remainder of the pass.

---

## 4. The price is on a page the pass never opened

**Defect.** Not a parsing bug — a sampling one. The tool read the URL it was given,
correctly, and the provider's price was on a different page.

**Damage.** The largest single source of error in this project. 14 of the 34 providers
recovered by the full-coverage pass published their price on a `/pricing`, `/packages` or
similar path linked from a homepage that itself states no figure.

**Fix.** The detector was extended to return any link whose `href` matches
`pricing|price|rates|cost|fees|packages|plans`, and every such link was followed before a
"no price" observation was recorded.

**Residual risk.** A provider whose pricing page is linked only from a nav menu rendered
after capture, or labelled with a word outside that pattern, would still be missed.

---

## 5. Interstitials recorded as absence

**Defect.** A bot check or consent wall returns HTTP 200 with body text. Read naively that
is a page with no price on it.

**Damage.** None known in the published data — such responses are recorded with
`verification = blocked`, not as an absence. `lucrumconsulting.com` is the clear case: its
homepage sits behind a Cloudflare interstitial, it had been recorded as blocked, and its
`/fractional-cfo-pricing/` page carries three tiers.

**Residual risk.** 12 rows remain `blocked` and 10 `unreachable`. Those providers are
counted in the denominator and carry no observation in either direction, which is the
honest treatment but does mean the disclosure rate is computed over some providers whose
pages were never read.

---

## What this list is for

Two of these five defects — 1 and 3 — corrupt a value while still producing a hit. Three —
2, 4 and 5 — produce a clean, confident, wrong "no price". The second kind is more
dangerous, because nothing about the output signals that anything went wrong.

That asymmetry is the reason the full-coverage pass was run at all, and the reason its
false-negative rate (5.3%) is published in `FINDINGS.md` alongside the more flattering
false-positive rate (43.6%).

---

Source: The Fractional Rates Index, maintained by Sivan Kadosh (saasfractionalcpo.com). License: CC BY 4.0.
