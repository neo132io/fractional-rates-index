#!/usr/bin/env python3
"""Cut the test fixture out of the frozen staging snapshot.

Run once against core-staging.csv md5 7a45392c27bfe11b1d80fae1a4b33872 (the same
bytes the statistical audit used). The fixture is committed so the tests never
depend on D:\\ or on the live staging file, which the collector rewrites.

    python tools/tests/make_fixtures.py --input D:/index-v2/staging/core-staging.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_evidence import is_priced  # noqa: E402

csv.field_size_limit(2 ** 31 - 1)

REGION = {"USD": "US", "GBP": "UK", "EUR": "EU"}
MODEL = {"per_month": "Monthly", "per_day": "Day", "per_hour": "Hourly"}

# The six groups the release agent reproduced digit for digit against the live
# v2.0 page (RELEASE-V21-CHECKPOINT sec 6b). They are the regression surface:
# the verifier must run over them without crashing and hold a stable verdict
# split, so that any later change to the rules shows up as a diff here.
REGRESSION_GROUPS = {
    ("CFO", "US", "Hourly"),
    ("CMO", "US", "Hourly"),
    ("COO", "US", "Hourly"),
    ("CPO", "US", "Hourly"),
    ("CTO", "UK", "Day"),
    ("CPO", "UK", "Day"),
}

# Named rows the report calls out by finding number. The last element is an
# optional substring the row's evidence_json must contain, used where a host
# carries two near-identical extractions of the same offer.
NAMED = [
    ("fractional-csuite.com", "83", "", "EUR", "per_hour", None),      # F3 phantom
    ("fractional-csuite.com", "700", "2026", "EUR", "per_day", None),  # F2 year-as-euro
    ("512financial.com", "9000", "21000", "USD", "per_month", None),   # clean PASS
    ("gigx.com", "39", "", "USD", "per_month", None),                  # SaaS product
    # same offer captured twice, once with the currency in the quote and once
    # without. Both are kept: the pair is the test for rule 2.
    ("paqanyway.com", "3350", "", "EUR", "per_month", '"price_low": "EUR 3,350 per month"'),
    ("paqanyway.com", "3350", "", "EUR", "per_month", '"price_low": "3,350 per month"'),
    ("kledigital.com", "127.5", "", "USD", "per_hour", None),          # value + unit unquoted
    ("saasfractionalcpo.com", "8000", "", "USD", "per_month", None),   # self-inclusion
]


def group_of(row: dict) -> tuple[str, str, str]:
    return (
        row.get("role") or "",
        REGION.get(row.get("currency", ""), ""),
        MODEL.get(row.get("unit", ""), ""),
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).with_name("fixtures") / "priced-fixture.csv")
    args = ap.parse_args(argv)

    digest = hashlib.md5(args.input.read_bytes()).hexdigest()
    with args.input.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames
        rows = list(reader)

    priced = [r for r in rows if is_priced(r)]
    keep, seen = [], set()

    for r in priced:
        if group_of(r) in REGRESSION_GROUPS:
            keep.append(r)
            seen.add(id(r))

    # one F27-signature row: evidence_json repeats the same prose in the
    # price_high / currency / unit slots instead of typed values.
    for r in priced:
        if id(r) in seen:
            continue
        ev = r.get("evidence_json") or ""
        if '"currency": "$' in ev and '"unit": "$' in ev and len(ev) > 200:
            keep.append(r)
            seen.add(id(r))
            break

    for host, lo, hi, cur, unit, ev_contains in NAMED:
        for r in priced:
            if id(r) in seen:
                continue
            if (r["host"] == host and r["price_low"] == lo
                    and r["price_high"] == hi and r["currency"] == cur
                    and r["unit"] == unit
                    and (ev_contains is None
                         or ev_contains in (r["evidence_json"] or ""))):
                keep.append(r)
                seen.add(id(r))
                break
        else:
            raise SystemExit(f"named fixture row not found: {host} {lo}-{hi} {ev_contains}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(keep)

    print(f"source        : {args.input}")
    print(f"source md5    : {digest}")
    print(f"rows total    : {len(rows)}")
    print(f"rows priced   : {len(priced)}")
    print(f"fixture rows  : {len(keep)} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
