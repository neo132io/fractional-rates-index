#!/usr/bin/env python3
"""Build the hygiene sidecar and the enriched release snapshot.

Why this is a sidecar and not an edit to core-staging.csv
---------------------------------------------------------
The collector owns core-staging.csv and rewrites it whole on every host it
touches:

    store.py:189  csv.DictWriter(sio, fieldnames=STAGING_COLUMNS,
                                 extrasaction="ignore", ...)

`extrasaction="ignore"` means any column that is not in STAGING_COLUMNS is
dropped without a word. A hygiene column written into that file survives only
until the next host is collected. Editing the collector's schema while it runs
is somebody else's territory, so the hygiene lives beside the data instead,
keyed on (host, offer_seq) - the collector's own row key, unique across all
2,397 rows of the audited snapshot.

Outputs
-------
  hygiene-<md5>.csv          key + hygiene columns, joinable onto any snapshot
  snapshot-hygienic-<md5>.csv the input plus those columns, for the generator
  manual-queue-<md5>.csv     rows a human has to look at, with the reason

    python tools/build_release_snapshot.py --input <staging.csv> --outdir <dir>
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scope_filter import (  # noqa: E402
    EXCLUDE, INCLUDE, QUEUE, classify_scope, country_evidence,
    country_from_host, mark_duplicates,
)
from verify_evidence import (  # noqa: E402
    is_priced, parse_amount, representative_value, verify_row,
)

csv.field_size_limit(2 ** 31 - 1)

KEY = ("host", "offer_seq")

HYGIENE_COLUMNS = [
    "host", "offer_seq",
    "is_priced",
    "verify_verdict", "verify_reasons", "verify_details",
    "value_basis", "value_published",
    "scope_verdict", "scope_class", "scope_confidence", "scope_reason",
    "country", "country_source", "country_evidence",
    "dup_keep", "dup_group",
    "regex_net_flag_status",
    "publishable",
]

# F25, corrected. The audit read regex_net_flag as a detector that returns zero
# on every row. It does not: it is empty on all 579 priced rows *by
# construction* - schema.py:131 defines it as "money found on a page the model
# called none-published", so it can only fire where no price was extracted. On
# the 1,818 unpriced rows it fires 569 times. The detector works; the column is
# simply not informative on the slice the audit sampled. Recorded, not fixed.
REGEX_NET_FLAG_NOTE = "not-applicable-on-priced-rows-by-construction"


def value_basis(row: dict) -> tuple[str, str]:
    """Sivan's ruling: the published value is the midpoint, labelled as such."""
    lo = parse_amount(row.get("price_low"))
    hi = parse_amount(row.get("price_high"))
    value = representative_value(row)
    if value is None:
        return "", ""
    if lo is not None and hi is not None and lo != hi:
        return "midpoint", str(value)
    return "published", str(value)


def build(input_path: Path, outdir: Path) -> dict:
    digest = hashlib.md5(input_path.read_bytes()).hexdigest()
    with input_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        source_columns = list(reader.fieldnames or [])
        rows = list(reader)

    priced = [r for r in rows if is_priced(r)]
    dups = mark_duplicates(priced)

    hygiene: list[dict] = []
    queue: list[dict] = []
    stats = Counter()

    for r in rows:
        priced_flag = is_priced(r)
        scope_v, scope_c, scope_r, scope_conf = classify_scope(r)
        country, csrc = country_from_host(r.get("host", ""))
        keep, group = dups.get(id(r), ("keep", 0))
        basis, published = value_basis(r) if priced_flag else ("", "")

        if priced_flag:
            v = verify_row(r)
            verdict, reasons, details = v.status, v.reason, json.dumps(
                v.details, ensure_ascii=False)
        else:
            verdict, reasons, details = "", "", ""

        publishable = (
            priced_flag
            and verdict == "PASS"
            and scope_v == INCLUDE
            and keep == "keep"
        )
        stats["publishable"] += int(publishable)
        if priced_flag:
            stats[f"verdict:{verdict}"] += 1
            stats[f"scope:{scope_v}"] += 1

        hygiene.append({
            "host": r.get("host", ""), "offer_seq": r.get("offer_seq", ""),
            "is_priced": "yes" if priced_flag else "no",
            "verify_verdict": verdict, "verify_reasons": reasons,
            "verify_details": details,
            "value_basis": basis, "value_published": published,
            "scope_verdict": scope_v, "scope_class": scope_c,
            "scope_confidence": scope_conf, "scope_reason": scope_r,
            "country": country, "country_source": csrc,
            "country_evidence": country_evidence(r),
            "dup_keep": keep, "dup_group": group or "",
            "regex_net_flag_status": REGEX_NET_FLAG_NOTE,
            "publishable": "yes" if publishable else "no",
        })

        if priced_flag and (scope_v == QUEUE or verdict == "QUARANTINE"
                            or scope_conf == "low"):
            queue.append({
                "host": r.get("host", ""), "offer_seq": r.get("offer_seq", ""),
                "provider": r.get("provider", ""), "role": r.get("role", ""),
                "price_low": r.get("price_low", ""),
                "price_high": r.get("price_high", ""),
                "currency": r.get("currency", ""), "unit": r.get("unit", ""),
                "source_url": r.get("source_url", ""),
                "why": "; ".join(x for x in [
                    f"scope={scope_c} ({scope_conf})" if scope_v == QUEUE else "",
                    f"verify={reasons}" if verdict == "QUARANTINE" else "",
                ] if x),
                "detail": scope_r,
            })
            stats["manual_queue"] += 1

    outdir.mkdir(parents=True, exist_ok=True)
    side = outdir / f"hygiene-{digest}.csv"
    snap = outdir / f"snapshot-hygienic-{digest}.csv"
    mq = outdir / f"manual-queue-{digest}.csv"

    _write(side, HYGIENE_COLUMNS, hygiene)

    added = [c for c in HYGIENE_COLUMNS if c not in KEY]
    merged = []
    for r, h in zip(rows, hygiene):
        assert r.get("host", "") == h["host"] and r.get("offer_seq", "") == h["offer_seq"]
        row = dict(r)
        row.update({c: h[c] for c in added})
        merged.append(row)
    _write(snap, source_columns + added, merged)

    if queue:
        _write(mq, list(queue[0].keys()), queue)

    return {
        "input": str(input_path),
        "input_md5": digest,
        "rows": len(rows),
        "rows_priced": len(priced),
        "stats": dict(stats.most_common()),
        "outputs": {"sidecar": str(side), "snapshot": str(snap),
                    "manual_queue": str(mq) if queue else None},
    }


def _write(path: Path, columns: list[str], records: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n",
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(records)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    args = ap.parse_args(argv)
    if args.input.name == "core-staging.csv":
        raise SystemExit(
            "refusing to read the live staging file: the collector rewrites it "
            "mid-run. Point --input at a frozen backup under staging/backups/."
        )
    json.dump(build(args.input, args.outdir), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
