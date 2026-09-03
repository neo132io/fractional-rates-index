#!/usr/bin/env python3
"""Put every rate on one axis: US dollars per hour.

Sivan's ruling of 2026-09-03. The raw capture is never touched; two computed
columns are added beside it.

    rate_hourly_usd       the number
    normalization_basis   the whole chain that produced it, in one string

Conversion rules, all declared:

    per_hour    value                       as captured
    per_day     value / 8                   an 8-hour day, corroborated three
                                            times on sackermanconsulting.com,
                                            which prices 4h as a half-day, 8h as
                                            a full day and 12h as a day and a half
    per_month   value / hours_per_month     the provider's own published hours
                                            where it has them (see
                                            retainer_hours.py), otherwise the
                                            measured default

    currency    x USD per unit, from the release's fx-lock file

The value entering the chain is the one the index publishes: the midpoint of a
published range, labelled `midpoint`, else the single endpoint, labelled
`published`.

A basis string reads end to end, so any published figure can be checked by
hand:

    midpoint(8000,10000)=9000 USD | per_month / 32.5h (default:measured median)
    | FX USD 1 @2026-09-03 | = 276.92 USD/h

    python tools/normalize_rates.py --input <snapshot.csv> \
        --fx-lock <fx-lock-YYYYMMDD.json> --out <normalized.csv>
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hours_evidence as he  # noqa: E402
from fx_rates import load_lock, rate_of  # noqa: E402
from retainer_hours import (  # noqa: E402
    DEFAULT_HOURS_SOURCE, HOURS_PER_DAY, declared_hours,
    default_hours_per_month,
)
from verify_evidence import is_priced, parse_amount, representative_value  # noqa: E402

csv.field_size_limit(2 ** 31 - 1)

NORMALIZED_COLUMNS = ["rate_hourly_usd", "normalization_basis",
                      "hours_per_month_used", "hours_source", "fx_usd_per_unit",
                      # v2.1.1: what the offer's own captured words say about
                      # time, written down separately so the divisor can be
                      # checked against the evidence the way the price already is
                      "hours_evidence_hours", "hours_evidence_basis",
                      "hours_evidence_quote", "hours_evidence_status"]

UNIT_LABEL = {"per_hour": "per_hour", "per_day": "per_day", "per_month": "per_month"}


def _round(value: Decimal, places: str = "0.01") -> Decimal:
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def _trim(value: Decimal) -> str:
    """Decimal without trailing zeros, for readable basis strings."""
    s = format(value.normalize(), "f")
    return s


def value_and_label(row: dict) -> tuple[Decimal | None, str]:
    """The value the index publishes, and how it was arrived at."""
    lo = parse_amount(row.get("price_low"))
    hi = parse_amount(row.get("price_high"))
    v = representative_value(row)
    if v is None:
        return None, ""
    if lo is not None and hi is not None and lo != hi:
        return v, f"midpoint({_trim(lo)},{_trim(hi)})={_trim(v)}"
    return v, f"published({_trim(v)})"


def hours_for(row: dict, default: Decimal,
              ctx: "he.HostContext" = he.EMPTY_CONTEXT) -> tuple[Decimal, str, str]:
    """(hours per month, short source tag, human note) for a monthly retainer.

    The order of precedence, and the reason for each step:

      declared          the manual audit read the page and accepted a figure
      evidence_offer    the offer's own captured words state a commitment
      evidence_host_..  the host publishes one retainer and one cadence
      default           nothing was published; the measured median is used

    v2.1 had only the first and the last, and the review of 2026-09-03 found
    the cost: 25 published records whose own captured words state a commitment
    were divided by the default anyway, overstating the hourly figure by a
    factor of two on average.
    """
    declared, detail = declared_hours(row.get("host", ""),
                                      row.get("offer_seq", ""))
    if declared is not None and declared > 0:
        return declared, "declared", detail

    outcome = he.read_offer_hours(row, ctx)
    if outcome.status in he.USES_EVIDENCE and outcome.hours and outcome.hours > 0:
        r = outcome.reading
        return outcome.hours, outcome.source, f'{r.label} from "{r.quote}"'

    if detail:
        # the row did carry an hours reading, and the audit threw it out
        return default, "default_after_rejected_reading", detail
    if outcome.status == he.AMBIGUOUS:
        return default, "default_after_ambiguous_evidence", outcome.note
    return default, "default", "no hours published"


def normalize_row(row: dict, lock: dict, default_hours: Decimal,
                  ctx: "he.HostContext" = he.EMPTY_CONTEXT) -> dict:
    """The two computed columns, plus the inputs that produced them."""
    blank = {c: "" for c in NORMALIZED_COLUMNS}
    if not is_priced(row):
        return blank

    value, value_label = value_and_label(row)
    if value is None:
        return blank

    currency = row.get("currency") or ""
    unit = row.get("unit") or ""
    fx = rate_of(lock, currency)
    usd = value * fx

    parts = [f"{value_label} {currency}"]
    hours_used = ""
    hours_src = ""

    if unit == "per_hour":
        hourly = usd
        parts.append("per_hour as captured")
    elif unit == "per_day":
        hourly = usd / HOURS_PER_DAY
        parts.append(f"per_day / {_trim(HOURS_PER_DAY)}h (declared 8-hour day)")
    elif unit == "per_month":
        hours, src, note = hours_for(row, default_hours, ctx)
        hours_used, hours_src = _trim(_round(hours)), src
        hourly = usd / hours
        parts.append(f"per_month / {_trim(_round(hours))}h ({src}: {note})")
    else:
        return blank

    parts.append(f"FX {currency} {_trim(fx)} USD @{lock['rate_date']}")
    parts.append(f"= {_round(hourly)} USD/h")

    outcome = he.read_offer_hours(row, ctx) if unit == "per_month" else None
    ev_hours = ev_basis = ev_quote = ""
    ev_status = outcome.status if outcome else ""
    if outcome and outcome.reading is not None:
        ev_hours = _trim(_round(outcome.hours))
        ev_basis = outcome.reading.basis
        ev_quote = outcome.reading.quote

    return {
        "rate_hourly_usd": str(_round(hourly)),
        "normalization_basis": " | ".join(parts),
        "hours_per_month_used": hours_used,
        "hours_source": hours_src,
        "fx_usd_per_unit": _trim(fx),
        "hours_evidence_hours": ev_hours,
        "hours_evidence_basis": ev_basis,
        "hours_evidence_quote": ev_quote,
        "hours_evidence_status": ev_status,
    }


def run(input_path: Path, fx_lock_path: Path, out_path: Path | None) -> dict:
    lock = load_lock(fx_lock_path)
    default_hours = default_hours_per_month()

    with input_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        columns = list(reader.fieldnames or [])
        rows = list(reader)

    from collections import Counter
    counts: Counter = Counter()
    ctx_by_host = he.index_by_host(rows)
    out_rows = []
    for r in rows:
        extra = normalize_row(r, lock, default_hours,
                              ctx_by_host.get(r.get("host", ""), he.EMPTY_CONTEXT))
        if extra["rate_hourly_usd"]:
            counts[f"unit:{r.get('unit')}"] += 1
            counts[f"currency:{r.get('currency')}"] += 1
            if r.get("unit") == "per_month":
                counts[f"hours:{extra['hours_source']}"] += 1
            counts["normalized"] += 1
        merged = dict(r)
        merged.update(extra)
        out_rows.append(merged)

    if out_path:
        added = [c for c in NORMALIZED_COLUMNS if c not in columns]
        with out_path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=columns + added,
                               lineterminator="\n", extrasaction="ignore")
            w.writeheader()
            w.writerows(out_rows)

    return {
        "input": str(input_path),
        "fx_lock": str(fx_lock_path),
        "fx_rate_date": lock["rate_date"],
        "default_hours_per_month": str(default_hours),
        "default_hours_source": DEFAULT_HOURS_SOURCE,
        "hours_per_day": str(HOURS_PER_DAY),
        "rows": len(rows),
        "counts": dict(counts.most_common()),
        "out": str(out_path) if out_path else None,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--fx-lock", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    json.dump(run(args.input, args.fx_lock, args.out), sys.stdout,
              ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
