#!/usr/bin/env python3
"""Read the time commitment a priced offer states, out of the text that was captured with it.

v2.1 verified the numerator of the hourly axis word for word and never checked
the denominator. The adversarial statistical review of 2026-09-03
(PROF-STAT-QA-V21, finding C1) measured the cost: the manual hours audit had
100% precision and 56% recall, and 29 published records carried the measured
default divisor while the provider's own captured words said something else.
The published hourly figure on those rows was wrong by a factor of two on
average, and by 3.7x on the publisher's own listing.

This module is the recall half. It reads a time commitment - hours per week,
hours per month, days per week, days per month - out of the quotes the
collector attached to *this* offer, and refuses to read one out of anything
else.

Three rules keep it honest, and each of them was written against a case that
broke a naive scan of the same data:

  1. Whitelisted fields only. `conversion_terms_published`, `delivery_model`,
     `equity_accepted` and friends talk about other things. golosnichenko.com
     publishes "$4,400/month" with "~6 hours per week of dedicated time" as its
     cadence, and separately mentions an "Executive CTO Custom pricing Full
     executive commitment, 3-5 days per week" tier that has no price at all. A
     scan that reads every field takes 3-5 days/week and prices the $4,400
     retainer at $32/h.

  2. Offer-scoped strings only. The collector copies host-wide fields onto every
     offer of that host. talpaperin.com carries "About 3 hours a week Advisor
     $2,000 /mo" in `cadence_published` on all six of its offers, including the
     $22,000 one. A string that appears verbatim on another priced offer of the
     same host describes the host, not this offer, and is discarded. The same
     rule is what keeps "20 to 25 hours a month" - offer one's allowance on
     saasfractionalcpo.com - off offer two.

  3. The manual audit outranks the scan. Where retainer_hours.AUDIT has read a
     row and rejected the reading, that row is not scanned at all:
     marketingeyedallas.com's "Free 3 Hours Per Month Intern Graphic Design"
     matches the pattern perfectly and belongs to a bundled intern.

Conversions are the ones already declared in retainer_hours.py: hours per week
x 52/12, days x 8 hours, ranges at their midpoint, an open-ended "3+" at its
floor. A days-per-week statement therefore multiplies by 8 x 52/12 = 34.667.

Deliberately not read: "about 2 hours a day", which needs a days-per-month
assumption the page does not give. That is the same call the manual audit made
on talpaperin.com, kept consistent here.

    python tools/hours_evidence.py --input <snapshot.csv> --out <audit.csv>
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retainer_hours import AUDIT_INDEX, BASIS_FACTOR, REJECT  # noqa: E402

csv.field_size_limit(2 ** 31 - 1)

# --------------------------------------------------------------------------
# rule 1 - the fields that describe this offer's price and cadence
# --------------------------------------------------------------------------

SCANNED_FIELDS = (
    "price_low", "price_high", "offering_type",
    "hours_included", "cadence_published", "unit", "currency",
)

# --------------------------------------------------------------------------
# the patterns
# --------------------------------------------------------------------------

_NUM = r"\d+(?:[.,]\d+)?"

# "10-20", "1 to 4", "3+", "~1", "1.5 to 3.5"
_RANGE = (
    r"(?P<lo>" + _NUM + r")"
    r"(?:\s*(?P<plus>\+)"
    r"|\s*(?:-|–|—|to|or|up\s+to|and|bis|a|à|hasta)\s*(?P<hi>" + _NUM + r"))?"
)

_SEP = r"\s*(?:/|per|a|an|each|every|pro|par|por|al|a\s+la|/\s*)\s*"

# Unit tails, English first and then the languages that actually occur in an
# EU/UK/US price page: German, French, Spanish, Italian, Dutch, Portuguese.
# The index reports in USD/GBP/EUR, so a euro-zone provider writing in its own
# language is a live case, not a hypothetical.
_HOUR = r"(?:hours?|hrs?|h|stunden|stunde|std|heures?|horas?|ore|uur|uren)"
_DAY = r"(?:days?|tage?n?|jours?|d[ií]as?|giorni|giorno|dagen|dag)"
_WEEK = r"(?:weeks?|wk|woche|wochen|semaines?|semanas?|settimana|settimane|week)"
_MONTH = r"(?:months?|mo|mth|monat|monats|monate|mois|mes(?:es)?|mese|maand)"

_UNIT_TAILS = {
    "hours_per_week": _HOUR + _SEP + _WEEK,
    "hours_per_month": _HOUR + _SEP + _MONTH,
    "days_per_week": _DAY + _SEP + _WEEK,
    "days_per_month": _DAY + _SEP + _MONTH,
}

PATTERNS = {
    basis: re.compile(_RANGE + r"\s*" + tail + r"(?![A-Za-z])", re.IGNORECASE)
    for basis, tail in _UNIT_TAILS.items()
}

# the conversions live in retainer_hours.py, so the audit and the scan cannot
# drift apart
BASIS_FACTOR_EXT = BASIS_FACTOR


@dataclass(frozen=True)
class Reading:
    """One time commitment found in one captured string."""
    basis: str
    low: Decimal
    high: Decimal | None
    open_ended: bool
    quote: str
    field: str

    @property
    def midpoint(self) -> Decimal:
        return self.low if self.high is None else (self.low + self.high) / 2

    @property
    def hours_per_month(self) -> Decimal:
        return self.midpoint * BASIS_FACTOR_EXT[self.basis]

    @property
    def label(self) -> str:
        if self.high is not None:
            span = f"{_t(self.low)}-{_t(self.high)} midpoint {_t(self.midpoint)}"
        elif self.open_ended:
            span = f"{_t(self.low)}+ (read at floor)"
        else:
            span = _t(self.low)
        return f"{self.basis} {span}"


def _t(v: Decimal) -> str:
    return format(v.normalize(), "f")


def _dec(raw: str) -> Decimal:
    return Decimal(raw.replace(",", "."))


def scan_text(text: str, field: str = "") -> list[Reading]:
    """Every time commitment written in one string."""
    out: list[Reading] = []
    for basis, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            hi = m.group("hi")
            out.append(Reading(
                basis=basis,
                low=_dec(m.group("lo")),
                high=_dec(hi) if hi else None,
                open_ended=bool(m.group("plus")),
                quote=m.group(0).strip(),
                field=field,
            ))
    return out


# --------------------------------------------------------------------------
# rule 2 - offer-scoped strings only
# --------------------------------------------------------------------------

def _evidence(row: dict) -> dict:
    raw = (row.get("evidence_json") or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def candidate_strings(row: dict) -> dict[str, str]:
    """The scannable text this row carries, field -> string."""
    ev = _evidence(row)
    out: dict[str, str] = {}
    for f in SCANNED_FIELDS:
        v = ev.get(f)
        if isinstance(v, str) and v.strip():
            out[f] = v.strip()
    for col in ("hours_included", "cadence_published"):
        v = (row.get(col) or "").strip()
        if v and v not in ("none-published", "none", "null", "n/a") and col not in out:
            out[col] = v
    return out


def host_shared_strings(host_rows: list[dict]) -> dict[str, int]:
    """How many of a host's priced offers carry each distinct string."""
    counts: dict[str, int] = {}
    for r in host_rows:
        for s in set(candidate_strings(r).values()):
            counts[s] = counts.get(s, 0) + 1
    return counts


def offer_scoped(row: dict, shared: dict[str, int]) -> dict[str, str]:
    """Only the strings that belong to this offer and not to the whole host."""
    return {f: s for f, s in candidate_strings(row).items() if shared.get(s, 0) <= 1}


@dataclass(frozen=True)
class HostContext:
    """What a host's priced offers say, taken together."""
    shared: dict[str, int]
    single_monthly_product: bool
    host_readings: tuple[Reading, ...]

    def sole_cadence(self) -> Reading | None:
        """The host's one time statement, when it has exactly one."""
        hours = {r.hours_per_month for r in self.host_readings}
        if len(hours) != 1:
            return None
        return max(self.host_readings, key=lambda r: len(r.quote))


def host_context(host_rows: list[dict]) -> HostContext:
    """Assemble the host-level facts the scan needs.

    `single_monthly_product` is the guard on the host-wide path. A cadence that
    the collector copied onto every offer can only be attached to a price when
    the host has one monthly price to attach it to. fractionalcoo.net publishes
    "$15K-$40K/month" twice and "2-3 days per week" once, and the two belong
    together. contineofy.com publishes five monthly tiers and copies "20 hours
    per month" - tier one's allowance - onto all of them; oshricohen.me
    publishes three and copies "~1 day a week", which is tier one's. Requiring
    one monthly price separates the first case from the other two without
    anyone having to judge which is which.
    """
    shared = host_shared_strings(host_rows)
    monthly_prices = {
        ((r.get("price_low") or "").strip(), (r.get("price_high") or "").strip())
        for r in host_rows if r.get("unit") == "per_month"
    }
    readings: list[Reading] = []
    for r in host_rows:
        for field, text in candidate_strings(r).items():
            readings.extend(scan_text(text, field))
    return HostContext(shared, len(monthly_prices) == 1, tuple(readings))


# --------------------------------------------------------------------------
# the reading for one row
# --------------------------------------------------------------------------

NO_READING = "none"
FOUND = "found"
FOUND_HOST_CADENCE = "found_host_cadence"
AMBIGUOUS = "ambiguous"
AUDIT_REJECTED = "audit_rejected"
AUDIT_DECLARED = "audit_declared"

USES_EVIDENCE = (FOUND, FOUND_HOST_CADENCE)

# hours_source tags written onto the record
SOURCE_OF_STATUS = {
    FOUND: "evidence_offer",
    FOUND_HOST_CADENCE: "evidence_host_cadence",
}


@dataclass(frozen=True)
class Outcome:
    status: str
    reading: Reading | None = None
    note: str = ""

    @property
    def hours(self) -> Decimal | None:
        return self.reading.hours_per_month if self.reading else None

    @property
    def source(self) -> str:
        return SOURCE_OF_STATUS.get(self.status, "")


def read_offer_hours(row: dict, ctx: HostContext) -> Outcome:
    """What this offer's own captured words say about time, if anything.

    Precedence: the manual audit outranks the scan on any row it has read, then
    the offer's own strings, then - only under the single-monthly-product guard
    - the host's sole cadence statement.
    """
    key = (row.get("host", ""), str(row.get("offer_seq", "")))
    audited = AUDIT_INDEX.get(key)
    if audited is not None:
        if audited.verdict == REJECT:
            return Outcome(AUDIT_REJECTED, None, audited.note)
        return Outcome(AUDIT_DECLARED, None, "read by the manual hours audit")

    readings: list[Reading] = []
    for field, text in offer_scoped(row, ctx.shared).items():
        readings.extend(scan_text(text, field))

    if readings:
        hours = {r.hours_per_month for r in readings}
        if len(hours) > 1:
            labels = "; ".join(sorted({f"{r.quote} = {_t(r.hours_per_month)}h"
                                       for r in readings}))
            return Outcome(AMBIGUOUS, None,
                           "the offer's own text states more than one "
                           f"commitment: {labels}")
        # identical hours from several spellings: keep the longest quote
        return Outcome(FOUND, max(readings, key=lambda r: (len(r.quote), r.field)))

    if row.get("unit") == "per_month" and ctx.single_monthly_product:
        sole = ctx.sole_cadence()
        if sole is not None:
            return Outcome(FOUND_HOST_CADENCE, sole,
                           "the host publishes one monthly retainer and one "
                           "cadence for it")
    return Outcome(NO_READING)


def index_by_host(rows: list[dict]) -> dict[str, HostContext]:
    """host -> the host-level facts, over the host's priced rows."""
    from verify_evidence import is_priced
    by_host: dict[str, list[dict]] = {}
    for r in rows:
        if is_priced(r):
            by_host.setdefault(r.get("host", ""), []).append(r)
    return {h: host_context(rs) for h, rs in by_host.items()}


EMPTY_CONTEXT = HostContext({}, False, ())


# --------------------------------------------------------------------------
# CLI - the recall audit the v2.1 review asked for
# --------------------------------------------------------------------------

AUDIT_FIELDS = [
    "host", "offer_seq", "currency", "unit", "price_low", "price_high",
    "status", "basis", "hours_per_month", "matched_quote", "matched_field",
    "hours_source_v21", "hours_used_v21", "note",
]


def audit(rows: list[dict]) -> list[dict]:
    """Every priced monthly row, and what its own words say about time."""
    from verify_evidence import is_priced
    ctx_by_host = index_by_host(rows)
    out = []
    for r in rows:
        if not is_priced(r) or r.get("unit") != "per_month":
            continue
        o = read_offer_hours(r, ctx_by_host.get(r.get("host", ""), EMPTY_CONTEXT))
        if o.status in (NO_READING, AUDIT_DECLARED):
            continue
        out.append({
            "host": r.get("host", ""),
            "offer_seq": r.get("offer_seq", ""),
            "currency": r.get("currency", ""),
            "unit": r.get("unit", ""),
            "price_low": r.get("price_low", ""),
            "price_high": r.get("price_high", ""),
            "status": o.status,
            "basis": o.reading.basis if o.reading else "",
            "hours_per_month": (f"{o.hours:.2f}" if o.hours is not None else ""),
            "matched_quote": o.reading.quote if o.reading else "",
            "matched_field": o.reading.field if o.reading else "",
            "hours_source_v21": r.get("hours_source", ""),
            "hours_used_v21": r.get("hours_per_month_used", ""),
            "note": o.note,
        })
    out.sort(key=lambda d: (d["status"], d["host"], str(d["offer_seq"])))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)

    rows = list(csv.DictReader(args.input.open(newline="", encoding="utf-8")))
    records = audit(rows)
    if args.out:
        with args.out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=AUDIT_FIELDS, lineterminator="\n")
            w.writeheader()
            w.writerows(records)
    from collections import Counter
    json.dump({
        "rows": len(rows),
        "monthly_rows_with_a_time_statement": len(records),
        "by_status": dict(Counter(r["status"] for r in records)),
        "hosts": len({r["host"] for r in records}),
        "out": str(args.out) if args.out else None,
    }, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
