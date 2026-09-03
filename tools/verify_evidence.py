#!/usr/bin/env python3
"""Deterministic evidence verifier for the Fractional Rates Index.

Pure code, zero LLM. Every priced row is checked against the quote that was
captured with it. A row is published only if the number, the currency and the
unit term can all be found in that quote, the number is not a calendar year,
the value is inside a plausibility band, and the row carries a provider's own
price rather than a market commentary.

Rules (RATES-PIPE-V3-PLAN, layer 1):
  1. every numeric value must appear in the price evidence, with format
     variants (8,000 / 8000 / 8k / $8K)            -> REJECT value_not_in_evidence
  2. the currency symbol or code must appear         -> REJECT currency_not_in_evidence
  3. the unit term must appear                       -> REJECT unit_not_in_evidence
  4. year guard: a 4-digit 2020-2030 number that
     only ever occurs in a year context is a year,
     not a price                                     -> REJECT year_read_as_price
  5. plausibility bands, coarse USD-equivalent:
     hourly 25-1000, daily 200-8000,
     monthly 500-60000                               -> QUARANTINE implausible_*
  6. own-price gate: context_verdict own AND
     dual_agreement == agree AND strict_pass == true -> REJECT not_own_price

Verdict precedence: any REJECT reason -> REJECT; else any QUARANTINE reason ->
QUARANTINE; else PASS.

CLI:
    python verify_evidence.py --input core-staging.csv \
        --out verdicts.csv --summary summary.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path

csv.field_size_limit(2 ** 31 - 1)

# --------------------------------------------------------------------------
# population definition
# --------------------------------------------------------------------------

# The audited population (STAT-QA-RATES-INDEX-20260903): a row counts as
# "priced" when price_low or price_high is numeric, the currency is one of the
# three the index reports in, and the unit is one of the three cadences the
# index models. On core-staging.csv md5 7a45392c27bfe11b1d80fae1a4b33872 this
# yields exactly 579 rows, matching the audit.
REPORTED_CURRENCIES = ("USD", "GBP", "EUR")
REPORTED_UNITS = ("per_month", "per_day", "per_hour")

_NUMERIC = re.compile(r"\d+(?:\.\d+)?")


def parse_amount(raw: str | None) -> Decimal | None:
    """Return the numeric value of a price cell, or None if it is not a number."""
    if raw is None:
        return None
    s = raw.strip().replace(",", "").replace(" ", "")
    if not s or not _NUMERIC.fullmatch(s):
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def is_priced(row: dict) -> bool:
    """True when the row belongs to the priced population the index publishes."""
    has_value = parse_amount(row.get("price_low")) is not None or \
        parse_amount(row.get("price_high")) is not None
    return (
        has_value
        and row.get("currency") in REPORTED_CURRENCIES
        and row.get("unit") in REPORTED_UNITS
    )


# --------------------------------------------------------------------------
# evidence pools
# --------------------------------------------------------------------------

# Strict pool: the quotes the extractor attached to the price fields themselves.
# A published number has to come from here.
VALUE_EVIDENCE_KEYS = ("price_low", "price_high")

# Wide pool: everything the extractor captured for this offer, plus the
# cadence column. Used only to report how much the strict pool costs us.
WIDE_EVIDENCE_KEYS = (
    "price_low", "price_high", "currency", "unit", "hours_included",
    "cadence_published", "offering_type", "minimum_term",
)


def _load_evidence(row: dict) -> dict:
    raw = (row.get("evidence_json") or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def evidence_quotes(row: dict, wide: bool = False) -> list[str]:
    """The distinct evidence strings that may support this row's price."""
    ev = _load_evidence(row)
    keys = WIDE_EVIDENCE_KEYS if wide else VALUE_EVIDENCE_KEYS
    parts = []
    for k in keys:
        v = ev.get(k)
        if isinstance(v, str) and v.strip():
            parts.append(v.strip())
    if wide:
        cad = (row.get("cadence_published") or "").strip()
        if cad and cad != "none-published":
            parts.append(cad)
    # dedupe while preserving order: the extractor repeats the same prose across
    # price_high / currency / unit (finding F27) and duplicates only add noise.
    seen, out = set(), []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def evidence_pool(row: dict, wide: bool = False) -> str:
    """All of this row's evidence quotes joined into one searchable blob."""
    return "  ||  ".join(evidence_quotes(row, wide=wide))


_BARE_MONEY = re.compile(
    r"^\s*(?:\$|£|€|US\$|USD|GBP|EUR)?\s*[\d][\d,.\s]*\s*(?:USD|GBP|EUR)?\s*$",
    re.IGNORECASE,
)


def is_bare_money_quote(text: str) -> bool:
    """True when a 'quote' is nothing but a currency marker and a number.

    Such a string restates the extracted value instead of quoting the page, so
    it cannot corroborate anything. This is the fingerprint of the phantom
    EUR 83 row (finding F3), where the extractor wrote its own answer into the
    evidence field.
    """
    return bool(text.strip()) and bool(_BARE_MONEY.match(text))


# --------------------------------------------------------------------------
# rule 1 - value in evidence, with format variants
# --------------------------------------------------------------------------

_GROUP_SEP = r"[,   . ]"


def format_variants(value: Decimal) -> list[str]:
    """Literal spellings a page may use for `value`, longest first.

    8000 -> 8000, 8,000, 8.000, 8 000, 8k, 8K, 8 000.00 ...
    8500 -> 8500, 8,500, 8.5k, 8,5k ...
    """
    out: list[str] = []
    q = value.normalize()
    is_int = q == q.to_integral_value()
    n = int(q) if is_int else None

    if is_int:
        plain = str(n)
        out.append(plain)
        if len(plain) > 3:
            # grouped by thousands with any of the separators
            head = plain[: len(plain) % 3 or 3]
            rest = [plain[i:i + 3] for i in range(len(head), len(plain), 3)]
            for sep in (",", ".", " ", " ", " ", " "):
                out.append(sep.join([head] + rest))
        # trailing .00 forms
        out.append(plain + ".00")
        if len(plain) > 3:
            head = plain[: len(plain) % 3 or 3]
            rest = [plain[i:i + 3] for i in range(len(head), len(plain), 3)]
            out.append(",".join([head] + rest) + ".00")
        # k / m shorthand
        if n >= 1000:
            k = Decimal(n) / 1000
            k_str = format(k.normalize(), "f")
            if "." not in k_str or len(k_str.split(".")[1]) <= 2:
                out.append(k_str + "k")
                out.append(k_str + "K")
                if "." in k_str:
                    out.append(k_str.replace(".", ",") + "k")
                    out.append(k_str.replace(".", ",") + "K")
        if n >= 1_000_000:
            m = Decimal(n) / 1_000_000
            m_str = format(m.normalize(), "f")
            if "." not in m_str or len(m_str.split(".")[1]) <= 2:
                out += [m_str + "m", m_str + "M", m_str + "mm"]
    else:
        s = format(q, "f")
        out.append(s)
        out.append(s.replace(".", ","))
        # pages write cents in full: 127.5 is printed as 127.50
        two = format(q.quantize(Decimal("0.01")), "f")
        out.append(two)
        out.append(two.replace(".", ","))

    seen, uniq = set(), []
    for v in sorted(out, key=len, reverse=True):
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


def _variant_pattern(variant: str) -> re.Pattern:
    """Boundary-guarded pattern so 8000 does not match inside 18000 or 80005."""
    body = re.escape(variant)
    if variant[-1] in "kKmM":
        tail = r"(?![A-Za-z0-9])"
    else:
        tail = r"(?![0-9])"
    return re.compile(r"(?<![0-9A-Za-z])" + body + tail)


def find_value(value: Decimal, text: str) -> list[tuple[int, int]]:
    """Spans in `text` where `value` is written, in any recognised format."""
    spans: list[tuple[int, int]] = []
    for variant in format_variants(value):
        for m in _variant_pattern(variant).finditer(text):
            span = (m.start(), m.end())
            if not any(s <= span[0] and span[1] <= e for s, e in spans):
                spans.append(span)
    return spans


# --------------------------------------------------------------------------
# rule 2 - currency in evidence
# --------------------------------------------------------------------------

CURRENCY_TOKENS = {
    "USD": ("$", "US$", "USD", "US dollar", "dollars"),
    "GBP": ("£", "GBP", "pound sterling", "pounds"),
    "EUR": ("€", "EUR", "euro", "euros"),
}

_CURRENCY_PREFIX = re.compile(
    r"(?:\$|£|€|US\$|USD|GBP|EUR)\s*$", re.IGNORECASE
)


def currency_in_text(currency: str, text: str) -> bool:
    tokens = CURRENCY_TOKENS.get(currency)
    if not tokens:
        return False
    low = text.lower()
    for t in tokens:
        if len(t) == 1 or not t.isalpha():
            if t in text:
                return True
        elif re.search(r"(?<![A-Za-z])" + re.escape(t.lower()) + r"(?![A-Za-z])", low):
            return True
    return False


def other_currencies_in_text(currency: str, text: str) -> list[str]:
    return [c for c in CURRENCY_TOKENS if c != currency and currency_in_text(c, text)]


# --------------------------------------------------------------------------
# rule 3 - unit term in evidence
# --------------------------------------------------------------------------

UNIT_TERMS = {
    "per_hour": (r"hours?", r"hourly", r"hrs?", r"p/?h"),
    "per_day": (r"days?", r"daily", r"diem", r"day\s*rate"),
    "per_month": (r"months?", r"monthly", r"mo", r"mth", r"pcm", r"retainer", r"p/?m"),
}


def unit_in_text(unit: str, text: str) -> bool:
    terms = UNIT_TERMS.get(unit)
    if not terms:
        return False
    pattern = r"(?<![A-Za-z])(?:" + "|".join(terms) + r")(?![A-Za-z])"
    return re.search(pattern, text, re.IGNORECASE) is not None


# --------------------------------------------------------------------------
# rule 4 - year guard
# --------------------------------------------------------------------------

YEAR_MIN, YEAR_MAX = 2020, 2030

_YEAR_LEAD = re.compile(
    r"(?:\b(?:in|for|since|by|during|through|until|till|of|from|as\s+of|copyright)\s+"
    r"|©\s*|\(\s*|\[\s*)$",
    re.IGNORECASE,
)
_YEAR_TRAIL = re.compile(
    r"^\s*(?:\)|\]|,|\.|:|;|-|–)?\s*"
    r"(?:range|ranges|rates?|pricing|prices?|benchmark|report|survey|data|edition|"
    r"update|guide|market|salary|salaries|study|index|forecast|outlook)\b",
    re.IGNORECASE,
)


def year_verdict(value: Decimal, text: str) -> str:
    """'not_a_year' | 'price' | 'year'.

    A 2020-2030 integer counts as a price only when at least one occurrence is
    money-shaped: preceded by a currency marker. Otherwise, if any occurrence
    sits in a year context, the number is a calendar year.
    """
    if value != value.to_integral_value():
        return "not_a_year"
    n = int(value)
    if not (YEAR_MIN <= n <= YEAR_MAX):
        return "not_a_year"
    spans = find_value(value, text)
    if not spans:
        return "not_a_year"  # rule 1 handles absence
    year_hit = False
    for start, end in spans:
        before = text[max(0, start - 12):start]
        after = text[end:end + 24]
        if _CURRENCY_PREFIX.search(before):
            return "price"
        if _YEAR_LEAD.search(before) or _YEAR_TRAIL.match(after):
            year_hit = True
    return "year" if year_hit else "price"


# --------------------------------------------------------------------------
# rule 5 - plausibility bands
# --------------------------------------------------------------------------

# Coarse FX, bounds checking only. Real normalisation happens in stage 4 via
# frankfurter.app and never uses these numbers.
COARSE_USD = {"USD": Decimal("1.00"), "GBP": Decimal("1.27"), "EUR": Decimal("1.08")}

PLAUSIBILITY = {
    "per_hour": (Decimal(25), Decimal(1000)),
    "per_day": (Decimal(200), Decimal(8000)),
    "per_month": (Decimal(500), Decimal(60000)),
}


def representative_value(row: dict) -> Decimal | None:
    """The value the index would publish: midpoint of the range, else the endpoint."""
    lo = parse_amount(row.get("price_low"))
    hi = parse_amount(row.get("price_high"))
    if lo is not None and hi is not None:
        return (lo + hi) / 2
    return lo if lo is not None else hi


def plausibility_check(value: Decimal, unit: str, currency: str) -> str | None:
    band = PLAUSIBILITY.get(unit)
    if band is None:
        return None
    usd = value * COARSE_USD.get(currency, Decimal("1.00"))
    low, high = band
    if usd < low:
        return "implausible_below_floor"
    if usd > high:
        return "implausible_above_ceiling"
    return None


# --------------------------------------------------------------------------
# rule 6 - own-price gate
# --------------------------------------------------------------------------

def own_price_gate(row: dict) -> list[str]:
    """Sub-reasons for failing the own-price gate; empty list means it passed."""
    failed = []
    if not (row.get("context_verdict") or "").startswith("own"):
        failed.append("context_not_own")
    if (row.get("dual_agreement") or "") != "agree":
        failed.append("dual_not_agree")
    if (row.get("strict_pass") or "") != "true":
        failed.append("strict_pass_false")
    return failed


# --------------------------------------------------------------------------
# verdict
# --------------------------------------------------------------------------

PASS, REJECT, QUARANTINE = "PASS", "REJECT", "QUARANTINE"


@dataclass
class Verdict:
    status: str
    reasons: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)
    # Plausibility findings are recorded whatever the headline verdict says.
    # Verdict precedence hides them behind a REJECT, and the publication gate
    # has to see them: a row can fail rule 6 *and* be out of band, and the gate
    # ignores rule 6.
    quarantines: list[str] = field(default_factory=list)

    @property
    def reason(self) -> str:
        return ";".join(self.reasons)

    def __str__(self) -> str:
        return self.status if not self.reasons else f"{self.status}({self.reason})"


GROUNDING_REASONS = (
    "value_not_in_evidence", "currency_not_in_evidence", "unit_not_in_evidence",
)

# The publication gate, as ruled by Sivan on 2026-09-03: evidence and
# plausibility decide what gets published; `strict_pass` and `dual_agreement`
# become confidence columns on the record rather than a veto. Rule 6 is the
# only reason excluded here, so this is "everything the verifier found wrong
# with the evidence itself".
POLICY_ONLY_REASONS = frozenset({"not_own_price"})


def gate_pass(verdict: "Verdict") -> bool:
    """True when a row clears evidence and plausibility, ignoring rule 6."""
    if verdict.quarantines:
        return False
    return not any(r not in POLICY_ONLY_REASONS for r in verdict.reasons)


CONFIDENCE_TIERS = ("high", "medium", "low")


def confidence_tier(row: dict) -> str:
    """How much corroboration the pipeline's own flags give this row.

    high   both independent extractions agreed and the strict parse passed
    medium one of the two
    low    neither
    """
    score = int((row.get("dual_agreement") or "") == "agree") + \
        int((row.get("strict_pass") or "") == "true")
    return {2: "high", 1: "medium"}.get(score, "low")


def _ground_value(value: Decimal, currency: str, unit: str,
                  quotes: list[str], own_quote: str | None) -> tuple[str | None, list[str]]:
    """Find one quote that carries the value, the currency and the unit together.

    Returns (supporting_quote, missing_components). Co-located grounding is the
    point: a number in one string and the word "hour" in a different string do
    not, between them, establish an hourly rate. That split is what let the
    phantom EUR 83 through (F3).

    Candidates are tried own-quote first, then the row's other price quotes, so
    a single range quote ("EUR 700 to EUR 1,900 per day") can legitimately
    ground both endpoints.
    """
    candidates: list[str] = []
    if own_quote and own_quote.strip():
        candidates.append(own_quote)
    for q in quotes:
        if q not in candidates:
            candidates.append(q)
    if not candidates:
        return None, ["value", "currency", "unit"]

    best_missing: list[str] | None = None
    for q in candidates:
        missing = []
        if not find_value(value, q):
            missing.append("value")
        if not currency_in_text(currency, q):
            missing.append("currency")
        if not unit_in_text(unit, q):
            missing.append("unit")
        if not missing:
            return q, []
        if best_missing is None or len(missing) < len(best_missing):
            best_missing = missing
    return None, best_missing or ["value"]


def verify_row(row: dict) -> Verdict:
    """Apply the six rules to one priced row."""
    rejects: list[str] = []
    quarantines: list[str] = []
    details: dict = {}

    unit = row.get("unit") or ""
    currency = row.get("currency") or ""
    ev = _load_evidence(row)
    quotes = evidence_quotes(row)
    pool = "  ||  ".join(quotes)
    wide = evidence_pool(row, wide=True)
    details["evidence_chars"] = len(pool)

    if not quotes:
        rejects.append("no_price_evidence")

    # rules 1-3 (co-located) + rule 4, per endpoint
    missing_by_component: dict[str, list[str]] = {}
    years: list[str] = []
    unsupported: list[str] = []
    bare: list[str] = []

    for fieldname in ("price_low", "price_high"):
        value = parse_amount(row.get(fieldname))
        if value is None:
            continue
        own_quote = ev.get(fieldname) if isinstance(ev.get(fieldname), str) else None
        if own_quote and is_bare_money_quote(own_quote):
            bare.append(fieldname)
        support, missing = _ground_value(value, currency, unit, quotes, own_quote)
        if support is None:
            unsupported.append(fieldname)
            for comp in missing:
                missing_by_component.setdefault(comp, []).append(fieldname)
            continue
        # rule 4 runs against the quote that actually grounded the value
        if year_verdict(value, support) == "year":
            years.append(fieldname)

    for comp in ("value", "currency", "unit"):
        if comp in missing_by_component:
            rejects.append(f"{comp}_not_in_evidence")
            details[f"{comp}_missing_for"] = ",".join(missing_by_component[comp])
    if unsupported:
        details["unsupported_fields"] = ",".join(unsupported)
        # would the whole evidence blob have carried it? reporting only.
        pooled_ok = [
            f for f in unsupported
            if find_value(parse_amount(row.get(f)), wide)
            and currency_in_text(currency, wide) and unit_in_text(unit, wide)
        ]
        if pooled_ok:
            details["grounded_only_when_pooled"] = ",".join(pooled_ok)
    if bare:
        details["bare_money_quote"] = ",".join(bare)
    if years:
        rejects.append("year_read_as_price")
        details["year_fields"] = ",".join(years)

    others = other_currencies_in_text(currency, pool)
    if others:
        details["other_currencies_in_evidence"] = ",".join(others)

    # rule 5
    value = representative_value(row)
    if value is not None:
        details["representative_value"] = str(value)
        bad = plausibility_check(value, unit, currency)
        if bad:
            quarantines.append(bad)

    # rule 6
    gate = own_price_gate(row)
    if gate:
        rejects.append("not_own_price")
        details["own_price_gate_failed"] = ",".join(gate)

    if rejects:
        return Verdict(REJECT, rejects, details, quarantines)
    if quarantines:
        return Verdict(QUARANTINE, quarantines, details, quarantines)
    return Verdict(PASS, [], details, [])


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

OUT_FIELDS = [
    "host", "provider", "role", "currency", "unit",
    "price_low", "price_high", "representative_value",
    "verdict", "reasons", "details",
    "evidence_price_quote", "source_url", "capture_date",
]


def run(input_path: Path, out_path: Path | None, summary_path: Path | None) -> dict:
    from collections import Counter

    rows = list(csv.DictReader(input_path.open(newline="", encoding="utf-8")))
    priced = [r for r in rows if is_priced(r)]

    status_counts: Counter = Counter()
    reason_counts: Counter = Counter()
    gate_counts: Counter = Counter()
    records = []

    for r in priced:
        v = verify_row(r)
        status_counts[v.status] += 1
        for reason in v.reasons:
            reason_counts[reason] += 1
        for sub in (v.details.get("own_price_gate_failed") or "").split(","):
            if sub:
                gate_counts[sub] += 1
        records.append({
            "host": r.get("host", ""),
            "provider": r.get("provider", ""),
            "role": r.get("role", ""),
            "currency": r.get("currency", ""),
            "unit": r.get("unit", ""),
            "price_low": r.get("price_low", ""),
            "price_high": r.get("price_high", ""),
            "representative_value": v.details.get("representative_value", ""),
            "verdict": v.status,
            "reasons": v.reason,
            "details": json.dumps(v.details, ensure_ascii=False),
            "evidence_price_quote": evidence_pool(r)[:600],
            "source_url": r.get("source_url", ""),
            "capture_date": r.get("capture_date", ""),
        })

    if out_path:
        with out_path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=OUT_FIELDS)
            w.writeheader()
            w.writerows(records)

    summary = {
        "input": str(input_path),
        "rows_total": len(rows),
        "rows_priced": len(priced),
        "status": dict(status_counts),
        "reasons": dict(reason_counts.most_common()),
        "own_price_gate_subreasons": dict(gate_counts.most_common()),
    }
    if summary_path:
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out", type=Path, help="per-row verdict CSV")
    ap.add_argument("--summary", type=Path, help="summary JSON")
    args = ap.parse_args(argv)
    summary = run(args.input, args.out, args.summary)
    json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
