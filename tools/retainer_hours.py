#!/usr/bin/env python3
"""How many hours a monthly retainer actually buys.

Sivan's ruling of 2026-09-03 normalises everything to an hourly axis. Hourly
rates pass through, day rates divide by eight, and monthly retainers divide by
the hours the retainer contains. That last divisor is the whole ballgame: it
sets the number the index will be read on, and only 51 of the 479 priced
monthly rows say anything about hours at all.

So the ruling also says: read those 51 by hand, throw out the misreads, and
take the default from what survives instead of picking a round number.

This module is the written-down result of that reading. Every row is listed
with the string the collector captured, what that string actually means, and
the verdict. Ten rows were thrown out. The reasons are in the table, not in a
footnote, because two of them are systematic and will come back:

  * lucrumconsulting.com - "24 Hours", "8 Hours", "4 Hours" are cells in a
    plan-comparison table, and the price *rises* as the number falls
    ($899 -> 24, $1,599 -> 8, $3,400 -> 4). That is a support response-time
    SLA read as an hours allowance. Three rows.
  * digitalapplied.com - "20 units", "30 units", "40 units". Units of what is
    never said on the page. Three rows.

Unit conversions, all declared:
  hours per week -> per month   x 52/12 = 4.3333   (calendar, not 4)
  days per month -> per month   x 8                (the same 8h day the day-rate
                                                    rule uses; corroborated on
                                                    sackermanconsulting.com,
                                                    which prints "4 hours/month
                                                    (half-day)" and "8
                                                    hours/month (full-day)")
Ranges collapse to their midpoint, matching the midpoint rule used for prices.
An open-ended "20+" is read as its floor, which understates hours and therefore
overstates the hourly rate - the conservative direction for a rate index.

    python tools/retainer_hours.py --input <snapshot.csv>
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from decimal import Decimal
from pathlib import Path

csv.field_size_limit(2 ** 31 - 1)

HOURS_PER_DAY = Decimal(8)
WEEKS_PER_MONTH = Decimal(52) / Decimal(12)   # 4.3333...

ACCEPT, REJECT = "accept", "reject"

# basis -> multiplier onto hours per month
BASIS_FACTOR = {
    "hours_per_month": Decimal(1),
    "hours_per_week": WEEKS_PER_MONTH,
    "days_per_month": HOURS_PER_DAY,
    # a days-per-week commitment goes through both declared conversions:
    # 8 hours a day, 52/12 weeks a month. Added in v2.1.1, when the evidence
    # scan (hours_evidence.py) found that "2 days a week" is the single most
    # common way a retainer states its size and v2.1 had no way to read it.
    "days_per_week": HOURS_PER_DAY * WEEKS_PER_MONTH,
}


class HoursRow:
    """One audited hours_included reading."""

    __slots__ = ("host", "offer_seq", "captured", "quote", "verdict", "basis",
                 "low", "high", "open_ended", "note")

    def __init__(self, host, offer_seq, captured, quote, verdict,
                 basis="", low=None, high=None, open_ended=False, note=""):
        self.host = host
        self.offer_seq = str(offer_seq)
        self.captured = Decimal(str(captured))
        self.quote = quote
        self.verdict = verdict
        self.basis = basis
        self.low = None if low is None else Decimal(str(low))
        self.high = None if high is None else Decimal(str(high))
        self.open_ended = open_ended
        self.note = note

    @property
    def key(self) -> tuple[str, str]:
        return (self.host, self.offer_seq)

    @property
    def stated_midpoint(self) -> Decimal | None:
        if self.verdict != ACCEPT or self.low is None:
            return None
        hi = self.high if self.high is not None else self.low
        return (self.low + hi) / 2

    @property
    def hours_per_month(self) -> Decimal | None:
        mid = self.stated_midpoint
        if mid is None:
            return None
        return mid * BASIS_FACTOR[self.basis]

    def as_dict(self) -> dict:
        h = self.hours_per_month
        return {
            "host": self.host,
            "offer_seq": self.offer_seq,
            "captured_hours_included": str(self.captured),
            "evidence_quote": self.quote,
            "verdict": self.verdict,
            "basis": self.basis,
            "stated_low": "" if self.low is None else str(self.low),
            "stated_high": "" if self.high is None else str(self.high),
            "open_ended": "yes" if self.open_ended else "no",
            "hours_per_month": "" if h is None else str(round(h, 2)),
            "note": self.note,
        }


# --------------------------------------------------------------------------
# the audit: all 51 priced monthly rows that carry an hours_included value
# --------------------------------------------------------------------------

AUDIT: list[HoursRow] = [
    # -- rejected: the captured number is not an hours allowance ------------
    HoursRow("scaleupexec.com", 0, 1.0, "The 1-hour plan is strategy-focused",
             REJECT, note="plan name, not a monthly allowance; the page never "
                          "states hours per month"),
    HoursRow("marketingeyedallas.com", 0, 3.0,
             "Free 3 Hours Per Month Intern Graphic Design & Web",
             REJECT, note="the 3 hours belong to a free graphic-design intern "
                          "bundled with the plan, not to the fractional CMO"),
    HoursRow("lucrumconsulting.com", 3, 4.0,
             "Starting at $ 3,400 / Month ... Comprehensive 4 Hours Unlimited",
             REJECT, note="comparison-table cell. Price rises as the number "
                          "falls across the three plans ($899/24h, $1,599/8h, "
                          "$3,400/4h): this is a support response-time SLA"),
    HoursRow("lucrumconsulting.com", 2, 8.0,
             "$ 1,599 / Month ... Advanced 8 Hours 3",
             REJECT, note="same SLA column as offer 3"),
    HoursRow("lucrumconsulting.com", 1, 24.0,
             "$ 899 / Month ... Basic 24 Hours 1",
             REJECT, note="same SLA column as offer 3"),
    HoursRow("digitalapplied.com", 0, 20.0, "20 units",
             REJECT, note="'units' is never defined on the page; not hours"),
    HoursRow("digitalapplied.com", 1, 30.0, "30 units",
             REJECT, note="'units' is never defined on the page; not hours"),
    HoursRow("digitalapplied.com", 2, 40.0, "40 units",
             REJECT, note="'units' is never defined on the page; not hours"),
    HoursRow("talpaperin.com", 1, 2.0, "about 2 hours a day",
             REJECT, note="intensity per working day. Converting needs a "
                          "days-per-month assumption the page does not give"),
    HoursRow("talpaperin.com", 2, 4.0, "about 4-5 hours a day",
             REJECT, note="intensity per working day, as offer 1"),

    # -- accepted: hours per month, stated ----------------------------------
    HoursRow("sackermanconsulting.com", 0, 4.0,
             "Block of hours for ad hoc work - 4 hours/month (half-day)",
             ACCEPT, "hours_per_month", 4,
             note="also fixes the day length: half-day = 4h, so a day is 8h"),
    HoursRow("trailmarktech.com", 0, 4.0, "4-8 hrs/month",
             ACCEPT, "hours_per_month", 4, 8),
    HoursRow("fractionalcmopartners.com", 0, 8.0, "8 hours per month",
             ACCEPT, "hours_per_month", 8),
    HoursRow("sackermanconsulting.com", 1, 8.0,
             "Block of hours for ad hoc work - 8 hours/month (full-day)",
             ACCEPT, "hours_per_month", 8, note="full-day = 8h"),
    HoursRow("solunapartners.com", 0, 10.0, "10-15 hours per month",
             ACCEPT, "hours_per_month", 10, 15),
    HoursRow("sackermanconsulting.com", 2, 12.0,
             "Block of hours for ad hoc work - 12 hours/month (one & a half-days)",
             ACCEPT, "hours_per_month", 12, note="1.5 days = 12h, so a day is 8h"),
    HoursRow("trailmarktech.com", 1, 12.0, "12-24 hrs/month",
             ACCEPT, "hours_per_month", 12, 24),
    HoursRow("luminspiregroup.com", 0, 15.0,
             "Most CFO engagements: $3,000-$6,000/month (15-30 hours at $200/hour)",
             ACCEPT, "hours_per_month", 15, 30,
             note="the page does the arithmetic itself: $4,500 / 22.5h = $200/h"),
    HoursRow("luminspiregroup.com", 1, 15.0,
             "Most advisory partnerships: $3,000-$4,000/month (15-20 hours at $200/hour)",
             ACCEPT, "hours_per_month", 15, 20,
             note="$3,500 / 17.5h = $200/h, self-consistent"),
    HoursRow("shashankshalabh.com", 0, 16.0,
             "16-20 hours per month per engagement",
             ACCEPT, "hours_per_month", 16, 20),
    HoursRow("contineofy.com", 0, 20.0, "20 hours per month",
             ACCEPT, "hours_per_month", 20),
    # Corrected in v2.1.1. v2.1 read "20 to 25 hours a month" from a capture
    # that the live page contradicts: saasfractionalcpo.com/ says "Offer one
    # Fractional CPO Partner $8,000 /mo 25 hours a month", and /standard/ says
    # "$8,000 for 25 hours a month". Re-fetched 2026-09-03; a regex for
    # r"\d+\s*(to|-)\s*\d+\s*hours" returns nothing on the live home page.
    # This is the one row in the index with an absolute ground truth, and it
    # was 11% wrong.
    HoursRow("saasfractionalcpo.com", 0, 25.0, "25 hours a month",
             ACCEPT, "hours_per_month", 25,
             note="our own listing, re-read against the live page on "
                  "2026-09-03; kept in, and declared as self-inclusion"),
    HoursRow("trailmarktech.com", 2, 20.0, "20+ hrs/month",
             ACCEPT, "hours_per_month", 20, open_ended=True,
             note="open-ended; read at the floor"),
    HoursRow("aaronzakowski.com", 2, 25.0,
             "$7000/month About 25 hours per month inside your business",
             ACCEPT, "hours_per_month", 25),
    HoursRow("solunapartners.com", 1, 25.0, "25-40 hours per month",
             ACCEPT, "hours_per_month", 25, 40),
    HoursRow("tucksoftwaregroup.com", 3, 35.0,
             "Fixed hours of consultation (35 hours)",
             ACCEPT, "hours_per_month", 35),
    HoursRow("contineofy.com", 1, 40.0, "40 hours per month",
             ACCEPT, "hours_per_month", 40),
    HoursRow("solunapartners.com", 2, 50.0, "Up to 50-70 hours per month",
             ACCEPT, "hours_per_month", 50, 70),
    HoursRow("tucksoftwaregroup.com", 4, 55.0,
             "Fixed hours of consultation (55 hours)",
             ACCEPT, "hours_per_month", 55),
    HoursRow("tucksoftwaregroup.com", 5, 60.0,
             "Unfixed, prioritized hours of consultation (60+ hours)",
             ACCEPT, "hours_per_month", 60, open_ended=True),
    HoursRow("contineofy.com", 2, 80.0, "80 hours per month",
             ACCEPT, "hours_per_month", 80),
    HoursRow("contineofy.com", 3, 120.0, "120 hours per month",
             ACCEPT, "hours_per_month", 120),

    # -- accepted: hours per week, converted x 52/12 ------------------------
    HoursRow("talpaperin.com", 0, 3.0, "About 3 hours a week",
             ACCEPT, "hours_per_week", 3),
    HoursRow("gofractional.com", 0, 5.0, "5-10 hrs/week",
             ACCEPT, "hours_per_week", 5, 10),
    HoursRow("hypernestlabs.com", 0, 5.0, "5-10 hrs/week",
             ACCEPT, "hours_per_week", 5, 10),
    HoursRow("hypernestlabs.com", 1, 5.0,
             "Strategic Advisory $3K-$8K /month 5-10 hrs/week",
             ACCEPT, "hours_per_week", 5, 10),
    HoursRow("misnomer.co", 0, 6.0, "Board-ready 6 to 9 hrs / week",
             ACCEPT, "hours_per_week", 6, 9),
    HoursRow("erikalpurcell.com", 0, 10.0, "10 hours per week",
             ACCEPT, "hours_per_week", 10),
    HoursRow("flexexec.io", 0, 10.0, "10-20 hours/week typical",
             ACCEPT, "hours_per_week", 10, 20),
    HoursRow("fractionalleader.io", 1, 10.0, "10-20 h / wk",
             ACCEPT, "hours_per_week", 10, 20),
    HoursRow("misnomer.co", 1, 10.0, "10 to 15 hrs / week",
             ACCEPT, "hours_per_week", 10, 15),
    HoursRow("rankedcmo.com", 0, 10.0, "10-20 hours per week",
             ACCEPT, "hours_per_week", 10, 20),
    HoursRow("thefractionalproductmanager.com", 0, 10.0,
             "Approximately 10 hours per week",
             ACCEPT, "hours_per_week", 10),
    HoursRow("hypernestlabs.com", 2, 15.0,
             "Embedded CTO $8K-$15K /month 15-20 hrs/week",
             ACCEPT, "hours_per_week", 15, 20),
    HoursRow("misnomer.co", 2, 16.0, "16 to 25 hrs / week",
             ACCEPT, "hours_per_week", 16, 25),
    HoursRow("thefractionalproductmanager.com", 1, 20.0,
             "Approximately 20 hours per week",
             ACCEPT, "hours_per_week", 20),
    HoursRow("kore1.com", 1, 25.0, "15 to 25 hours per week",
             ACCEPT, "hours_per_week", 15, 25),
    HoursRow("misnomer.co", 3, 25.0, "25+ hrs / week",
             ACCEPT, "hours_per_week", 25, open_ended=True),

    # -- accepted: days per month, converted x 8 ----------------------------
    HoursRow("prodevel.co.uk", 0, 2.0, "2 days/month",
             ACCEPT, "days_per_month", 2),
    HoursRow("prodevel.co.uk", 1, 4.0, "4 days/month",
             ACCEPT, "days_per_month", 4),
    HoursRow("prodevel.co.uk", 2, 6.0, "6 days/month",
             ACCEPT, "days_per_month", 6),
]

AUDIT_INDEX: dict[tuple[str, str], HoursRow] = {r.key: r for r in AUDIT}


def declared_hours(host: str, offer_seq: str) -> tuple[Decimal | None, str]:
    """(hours per month, why) for one row, from the audit. None means 'no reading'."""
    row = AUDIT_INDEX.get((host, str(offer_seq)))
    if row is None:
        return None, ""
    if row.verdict != ACCEPT:
        return None, f"declared hours rejected: {row.note}"
    h = row.hours_per_month
    detail = row.basis
    if row.high is not None and row.high != row.low:
        detail += f" {row.low}-{row.high} midpoint {row.stated_midpoint}"
    else:
        detail += f" {row.low}"
        if row.open_ended:
            detail += "+ (read at floor)"
    return h, f"declared:{detail}"


# --------------------------------------------------------------------------
# the default: the median of what survived
# --------------------------------------------------------------------------

def _median(values: list[Decimal]) -> Decimal:
    return Decimal(str(statistics.median(sorted(float(v) for v in values))))


def accepted_rows() -> list[HoursRow]:
    return [r for r in AUDIT if r.verdict == ACCEPT]


def hours_distribution() -> dict:
    """Offer-level and host-level views of the surviving readings."""
    rows = accepted_rows()
    per_offer = [r.hours_per_month for r in rows]

    by_host: dict[str, list[Decimal]] = {}
    for r in rows:
        by_host.setdefault(r.host, []).append(r.hours_per_month)
    per_host = [_median(v) for v in by_host.values()]

    def describe(values: list[Decimal]) -> dict:
        f = sorted(float(v) for v in values)
        return {
            "n": len(f),
            "min": round(f[0], 2),
            "p25": round(_quantile(f, 0.25), 2),
            "median": round(statistics.median(f), 2),
            "mean": round(sum(f) / len(f), 2),
            "p75": round(_quantile(f, 0.75), 2),
            "max": round(f[-1], 2),
        }

    stated = [r.hours_per_month for r in rows if r.basis == "hours_per_month"]
    weekly = [r.hours_per_month for r in rows if r.basis == "hours_per_week"]
    daily = [r.hours_per_month for r in rows if r.basis == "days_per_month"]

    return {
        "audited_rows": len(AUDIT),
        "rejected_rows": len(AUDIT) - len(rows),
        "accepted_rows": len(rows),
        "per_offer": describe(per_offer),
        "per_host": describe(per_host),
        "hosts": len(by_host),
        "by_basis": {
            "hours_per_month": describe(stated),
            "hours_per_week": describe(weekly),
            "days_per_month": describe(daily),
        },
        "rejections": [
            {"host": r.host, "offer_seq": r.offer_seq,
             "captured": str(r.captured), "quote": r.quote, "why": r.note}
            for r in AUDIT if r.verdict == REJECT
        ],
    }


def _quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def host_level_hours() -> list[Decimal]:
    """The sample the default divisor is the median of: one figure per host.

    Exposed so the bootstrap can resample it. An interval that holds this
    estimate fixed measures the smaller of the two unknowns in the hourly axis.
    """
    rows = accepted_rows()
    by_host: dict[str, list[Decimal]] = {}
    for r in rows:
        by_host.setdefault(r.host, []).append(r.hours_per_month)
    return sorted(_median(v) for v in by_host.values())


def default_hours_per_month() -> Decimal:
    """The divisor for a retainer that does not say how many hours it buys.

    Host-level median, so that contineofy.com's four tiers and misnomer.co's
    four tiers do not outvote the twenty-odd providers that publish one number.
    Measured, not chosen: see hours_distribution().
    """
    rows = accepted_rows()
    by_host: dict[str, list[Decimal]] = {}
    for r in rows:
        by_host.setdefault(r.host, []).append(r.hours_per_month)
    return _median([_median(v) for v in by_host.values()])


DEFAULT_HOURS_SOURCE = (
    "host-level median of the 41 hours_included readings that survived the "
    "manual audit of all 51 (10 rejected: 3 SLA cells, 3 undefined 'units', "
    "2 per-working-day intensities, 1 plan name, 1 bundled intern allowance)"
)


# --------------------------------------------------------------------------
# CLI - prints the audit and cross-checks it against a snapshot
# --------------------------------------------------------------------------

def cross_check(input_path: Path) -> dict:
    """Confirm the audit still covers exactly the rows that carry hours."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from verify_evidence import is_priced  # noqa: E402

    rows = list(csv.DictReader(input_path.open(newline="", encoding="utf-8")))
    found = {
        (r.get("host", ""), str(r.get("offer_seq", "")))
        for r in rows
        if is_priced(r) and r.get("unit") == "per_month"
        and (r.get("hours_included") or "").strip()
        not in ("", "none-published", "none", "null", "n/a")
    }
    audited = set(AUDIT_INDEX)
    return {
        "snapshot_rows_with_hours": len(found),
        "audited": len(audited),
        "in_snapshot_not_audited": sorted(found - audited),
        "audited_not_in_snapshot": sorted(audited - found),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", type=Path, help="snapshot to cross-check against")
    ap.add_argument("--out", type=Path, help="write the audit table as CSV")
    args = ap.parse_args(argv)

    report = {
        "default_hours_per_month": str(default_hours_per_month()),
        "default_source": DEFAULT_HOURS_SOURCE,
        "distribution": hours_distribution(),
    }
    if args.input:
        report["cross_check"] = cross_check(args.input)
    if args.out:
        records = [r.as_dict() for r in AUDIT]
        with args.out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(records[0].keys()),
                               lineterminator="\n")
            w.writeheader()
            w.writerows(records)
        report["audit_csv"] = str(args.out)

    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
