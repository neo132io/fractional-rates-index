#!/usr/bin/env python3
"""Population hygiene for the Fractional Rates Index.

Three deterministic classifiers, no LLM and no network:

  scope    - is this a fractional-executive engagement, or a software
             subscription / bookkeeping plan that wandered into the sample?
             (findings F4, F15)
  country  - a real country from the ccTLD, kept separate from currency, which
             is what "region" has actually been measuring all along (F9)
  dedup    - the same offer captured more than once (F16)

Nothing here deletes a row. Each classifier writes its verdict into a new
column so the raw capture stays intact and every exclusion is auditable.

    python tools/scope_filter.py --input core-staging.csv --out scope-report.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_evidence import (  # noqa: E402
    PASS, QUARANTINE, _load_evidence, is_priced, parse_amount, verify_row,
)

csv.field_size_limit(2 ** 31 - 1)

# --------------------------------------------------------------------------
# scope: accounting and bookkeeping shops inside the CFO group (F4)
# --------------------------------------------------------------------------

# Sivan's ruling of 2026-09-03 named eight hosts to take out of the CFO group.
# Six of them are corroborated by evidence already in the capture, quoted here
# so the exclusion can be checked without re-fetching anything.
BOOKKEEPING_HOSTS = {
    "daxhive.com": "captured page /fractional-coo-cfo-back-office; productised back-office plans from $299/mo",
    "escalon.services": "captured page /services/tax-operations",
    "kruzeconsulting.com": "captured page /cost-accounting-startup/",
    "graphitefinancial.com": "captured pages /services-payroll and /services-tax-compliance",
    "beyondaccounting.info": "provider name is Beyond Accounting",
    "burklandassociates.com": "evidence quote: payroll services start at $500/month",
}

# The other two were named in the ruling but our capture carries no evidence of
# a bookkeeping offering, and autocfo.com's evidence says the opposite
# ("a team of fractional CFOs"). They go to the manual queue rather than being
# removed on an unverified basis. One line from Sivan releases them.
RULING_PENDING_EVIDENCE = {
    "pilot.com": "named in the ruling; captured evidence holds pricing pages only, no bookkeeping wording",
    "autocfo.com": "named in the ruling; captured evidence says 'a team of fractional CFOs', contradicting the bookkeeping classification",
}

# --------------------------------------------------------------------------
# scope: software subscriptions (F15)
# --------------------------------------------------------------------------

SEAT_TERMS = re.compile(
    r"(?:per\s*(?:user|seat|person|doc\s*maker|member|editor)"
    r"|/\s*(?:user|seat|person)"
    r"|\b(?:user|seat)\s*/\s*(?:month|mo)"
    r"|\bseat\s*/?\s*month\b"
    r"|\bper\s+active\s+user\b)",
    re.IGNORECASE,
)

PRODUCT_TERMS = re.compile(
    r"(?:\bbookkeep(?:ing|er)\b|\bbook-keeping\b"
    r"|\baccounting\s+(?:subscription|plan|package|services?)\b"
    r"|\bsoftware\s+plan\b|\bsubscription\s+plan\b"
    r"|\bfree\s+to\s+start\b|\bfree\s+tier\b|\bfree\s+plan\b"
    r"|\bminimum\s+usage\b)",
    re.IGNORECASE,
)

# A firm that lists bookkeeping among its services is not thereby a bookkeeping
# subscription. When the disqualifying word turns up in site-wide text but the
# retainer is executive-sized, the row is queued at low confidence so a human
# reads it first instead of it being treated as settled.
EXECUTIVE_MONTHLY = Decimal(2000)

# Rule of thumb from the audit: a monthly retainer under $300, or an hourly
# rate under $25, is a product price until a human says otherwise.
MONTHLY_SUSPECT_FLOOR = Decimal(300)
HOURLY_SUSPECT_FLOOR = Decimal(25)

INCLUDE, QUEUE, EXCLUDE = "include", "quarantine", "exclude"


def scope_evidence_text(row: dict) -> str:
    ev = _load_evidence(row)
    parts = [v for v in ev.values() if isinstance(v, str)]
    for col in ("provider", "offering_type", "cadence_published", "notes"):
        v = (row.get(col) or "").strip()
        if v and v != "none-published":
            parts.append(v)
    parts.append(row.get("coverage_manifest") or "")
    return " ".join(parts)


def price_quote_text(row: dict) -> str:
    ev = _load_evidence(row)
    return " ".join(
        ev.get(k) for k in ("price_low", "price_high") if isinstance(ev.get(k), str)
    )


def classify_scope(row: dict) -> tuple[str, str, str, str]:
    """Return (scope_verdict, scope_class, scope_reason, confidence)."""
    host = (row.get("host") or "").lower()

    if host in BOOKKEEPING_HOSTS:
        return EXCLUDE, "bookkeeping_subscription", BOOKKEEPING_HOSTS[host], "high"
    if host in RULING_PENDING_EVIDENCE:
        return QUEUE, "ruling_named_unevidenced", RULING_PENDING_EVIDENCE[host], "high"

    text = scope_evidence_text(row)
    quote = price_quote_text(row)
    value = parse_amount(row.get("price_low"))
    unit = row.get("unit") or ""

    m = SEAT_TERMS.search(text)
    if m:
        conf = "high" if SEAT_TERMS.search(quote) else "low"
        return QUEUE, "seat_licence", f"per-seat pricing in evidence: {m.group(0)!r}", conf

    m = PRODUCT_TERMS.search(text)
    if m:
        in_quote = bool(PRODUCT_TERMS.search(quote))
        small = value is not None and unit == "per_month" and value < EXECUTIVE_MONTHLY
        conf = "high" if (in_quote or small) else "low"
        where = "price quote" if in_quote else "site text"
        return (QUEUE, "product_subscription",
                f"disqualifying term in {where}: {m.group(0)!r}", conf)

    if value is not None:
        if unit == "per_month" and value < MONTHLY_SUSPECT_FLOOR:
            return (QUEUE, "product_suspected",
                    f"monthly retainer {value} below the {MONTHLY_SUSPECT_FLOOR} floor", "high")
        if unit == "per_hour" and value < HOURLY_SUSPECT_FLOOR:
            return (QUEUE, "product_suspected",
                    f"hourly rate {value} below the {HOURLY_SUSPECT_FLOOR} floor", "high")

    return INCLUDE, "fractional_exec", "", "high"


# --------------------------------------------------------------------------
# country from ccTLD (F9)
# --------------------------------------------------------------------------

# Two-letter TLDs sold and used as generic names. A .io or .ai domain says
# nothing about where the provider is, so these resolve to no country rather
# than to the British Indian Ocean Territory.
GENERIC_TWO_LETTER = {
    "io", "ai", "co", "me", "tv", "cc", "ly", "so", "gg", "sh", "is", "to",
    "fm", "am", "im", "st", "ws", "vc", "mn", "ninja",
}

MULTI_LEVEL = {
    "co.uk": "GB", "org.uk": "GB", "gov.uk": "GB", "ac.uk": "GB", "me.uk": "GB",
    "com.au": "AU", "net.au": "AU", "org.au": "AU",
    "co.nz": "NZ", "net.nz": "NZ",
    "com.sg": "SG", "com.my": "MY", "com.hk": "HK",
    "co.il": "IL", "co.za": "ZA", "co.in": "IN", "com.br": "BR",
    "com.mx": "MX", "com.ar": "AR", "com.tr": "TR", "co.jp": "JP",
    "com.cn": "CN", "com.ph": "PH", "co.th": "TH", "com.pl": "PL",
    "co.ke": "KE", "com.ua": "UA", "com.pt": "PT", "com.es": "ES",
}

# ccTLDs whose ISO code differs from the label.
TLD_TO_ISO = {"uk": "GB", "eu": "", "su": "", "ac": ""}


def country_from_host(host: str) -> tuple[str, str]:
    """Return (country_iso2, source). Empty country means: not derivable."""
    h = (host or "").strip().lower().rstrip(".")
    if not h or "." not in h:
        return "", ""
    parts = h.split(".")
    tail2 = ".".join(parts[-2:])
    if tail2 in MULTI_LEVEL:
        return MULTI_LEVEL[tail2], "cctld"
    tld = parts[-1]
    if len(tld) != 2:
        return "", ""
    if tld in GENERIC_TWO_LETTER:
        return "", ""
    iso = TLD_TO_ISO.get(tld, tld.upper())
    return (iso, "cctld") if iso else ("", "")


def country_evidence(row: dict) -> str:
    """Location wording already captured on the page. Recorded, never inferred from."""
    v = (row.get("remote_geo") or "").strip()
    if v and v != "none-published":
        return v
    ev = _load_evidence(row)
    v = ev.get("remote_geo")
    return v.strip() if isinstance(v, str) else ""


# --------------------------------------------------------------------------
# duplicate offers (F16)
# --------------------------------------------------------------------------

DUP_KEY = ("host", "role", "price_low", "price_high", "currency", "unit")

_RANK = {PASS: 0, QUARANTINE: 1}


def dup_key(row: dict) -> tuple:
    return tuple((row.get(k) or "") for k in DUP_KEY)


def rank_duplicate(row: dict) -> tuple:
    """Sort key for choosing which capture of an offer to keep.

    Best verdict first, then the longest evidence quote, then the newest
    capture. The verdict has to lead: the same $8,000 is captured both as a
    bare "$8,000" (which cannot be verified) and as "$8,000 / month" (which
    can), and dropping the wrong twin would throw away the only publishable
    record of that price.
    """
    v = verify_row(row)
    ev = _load_evidence(row)
    quote_len = sum(len(ev.get(k) or "") for k in ("price_low", "price_high"))
    return (_RANK.get(v.status, 2), -quote_len, row.get("capture_date", ""))


def mark_duplicates(rows: list[dict]) -> dict[int, tuple[str, int]]:
    """id(row) -> (keep|drop, group index) for rows sharing a DUP_KEY."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        groups[dup_key(r)].append(r)
    out: dict[int, tuple[str, int]] = {}
    gi = 0
    for key, members in groups.items():
        if len(members) < 2:
            continue
        gi += 1
        ordered = sorted(members, key=lambda r: (rank_duplicate(r), id(r)))
        for i, r in enumerate(ordered):
            out[id(r)] = ("keep" if i == 0 else "drop", gi)
    return out


# --------------------------------------------------------------------------
# CLI report
# --------------------------------------------------------------------------

def run(input_path: Path, out_path: Path | None) -> dict:
    rows = list(csv.DictReader(input_path.open(newline="", encoding="utf-8")))
    priced = [r for r in rows if is_priced(r)]
    dups = mark_duplicates(priced)

    verdicts, classes, countries, conf = Counter(), Counter(), Counter(), Counter()
    records = []
    for r in priced:
        verdict, klass, reason, confidence = classify_scope(r)
        country, src = country_from_host(r.get("host", ""))
        keep, group = dups.get(id(r), ("keep", 0))
        verdicts[verdict] += 1
        classes[klass] += 1
        countries[country or "(unknown)"] += 1
        if verdict != INCLUDE:
            conf[f"{klass}:{confidence}"] += 1
        records.append({
            "host": r.get("host", ""), "role": r.get("role", ""),
            "currency": r.get("currency", ""), "unit": r.get("unit", ""),
            "price_low": r.get("price_low", ""), "price_high": r.get("price_high", ""),
            "scope_verdict": verdict, "scope_class": klass,
            "scope_confidence": confidence, "scope_reason": reason,
            "country": country, "country_source": src,
            "country_evidence": country_evidence(r),
            "dup_keep": keep, "dup_group": group or "",
        })

    if out_path:
        with out_path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(records[0].keys()))
            w.writeheader()
            w.writerows(records)

    return {
        "rows_priced": len(priced),
        "scope_verdict": dict(verdicts),
        "scope_class": dict(classes.most_common()),
        "queued_by_confidence": dict(conf.most_common()),
        "duplicate_rows_dropped": sum(1 for v in dups.values() if v[0] == "drop"),
        "duplicate_groups": len({g for _, g in dups.values()}),
        "country_top": dict(countries.most_common(12)),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    json.dump(run(args.input, args.out), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
