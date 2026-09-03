#!/usr/bin/env python3
"""Release acceptance gate (RATES-PIPE-V3-PLAN layer 5, item 4).

Draws a deterministic random sample of published records, re-fetches the pages
the collector actually read, and checks that the published number, its currency
and its unit term all appear together on one of those pages as served today.

Why the page list and not source_url: source_url is the crawl seed. The offer
may have been extracted from another page of the same host. The snapshot keeps
the real page in `page_source` and the full list in
`coverage_manifest.pages_read`. Checking only the seed measures the gate, not
the data (221 of 579 priced rows have page_source != source_url).

Rules:
  * seed is fixed, so the sample is reproducible from the same input file
  * one request per URL, generous timeout, no aggressive retry
  * a host whose pages cannot be read today is recorded but drops out of the
    denominator. "Cannot be read" means every page errored, was blocked, or
    returned far less visible text than the collector recorded for it - a page
    that needs JavaScript to paint its prices is not evidence of a missing
    price.
  * pass threshold is 95 percent of the reachable sample

Second gate, added for v2.1.1: the hours citations, in full and not by sample.
v2.1.1's one new class of evidence is the time commitment read out of an
offer's own words, which moved 20 records off the measured 32.5-hour default
and onto a quoted figure. Those 20 quotes are the load-bearing new evidence of
the release, so they are all re-fetched, not sampled: a released divisor that
nobody has looked at since it was typed is exactly the failure the price gate
was built to stop, one column over. The quote has to appear on a page the
collector read, allowing only whitespace and dash-glyph variation.

Usage:
    python tools/acceptance_gate.py --records <records.csv> --snapshot <snap.csv> --out <report.json>
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import time
from decimal import Decimal
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_evidence import (  # noqa: E402
    currency_in_text,
    find_value,
    parse_amount,
    unit_in_text,
)

SEED = 20260903
SAMPLE_SIZE = 40
THRESHOLD = 0.95
TIMEOUT = 25
MAX_PAGES = 4
# A live fetch that yields less than this share of the text the collector
# recorded for the host did not render. It is a fetch failure, not evidence.
RENDER_RATIO = 0.20
MIN_TEXT = 800

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

_SCRIPT = re.compile(r"(?is)<(script|style|noscript|template)[^>]*>.*?</\1>")
_TAG = re.compile(r"(?s)<[^>]+>")
_WS = re.compile(r"\s+")
_CHARS_NOTE = re.compile(r"chars=(\d+)")


def page_text(html: str) -> str:
    text = _SCRIPT.sub(" ", html)
    text = _TAG.sub(" ", text)
    text = unescape(text)
    return _WS.sub(" ", text).strip()


def fetch(url: str, session) -> tuple[str | None, str]:
    try:
        resp = session.get(
            url,
            timeout=TIMEOUT,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            allow_redirects=True,
        )
    except Exception as exc:
        return None, f"{type(exc).__name__}: {str(exc)[:120]}"
    if resp.status_code != 200:
        return None, f"HTTP {resp.status_code}"
    if resp.encoding is None:
        resp.encoding = resp.apparent_encoding or "utf-8"
    body = resp.text
    if not body.strip():
        return None, "empty body"
    return page_text(body), f"HTTP 200"


def pages_for(snap_row: dict) -> list[str]:
    """Pages the collector read, evidence page first."""
    urls: list[str] = []
    primary = (snap_row.get("page_source") or "").strip()
    if primary:
        urls.append(primary)
    try:
        cm = json.loads(snap_row.get("coverage_manifest") or "{}")
    except Exception:
        cm = {}
    for u in cm.get("pages_read") or []:
        u = (u or "").strip()
        if u and u not in urls:
            urls.append(u)
    seed = (snap_row.get("source_url") or "").strip()
    if seed and seed not in urls:
        urls.append(seed)
    return urls[:MAX_PAGES]


def collector_chars(snap_row: dict) -> int | None:
    m = _CHARS_NOTE.search(snap_row.get("notes") or "")
    return int(m.group(1)) if m else None


def check_page(row: dict, text: str) -> dict:
    currency = (row.get("currency") or "").strip()
    unit = (row.get("unit") or "").strip()
    wanted = []
    for field in ("price_low", "price_high"):
        amount = parse_amount(row.get(field))
        if amount is not None:
            wanted.append((field, amount))
    found = [f for f, amount in wanted if find_value(amount, text)]
    return {
        "value_ok": bool(found),
        "value_fields_found": found,
        "currency_ok": currency_in_text(currency, text) if currency else False,
        "unit_ok": unit_in_text(unit, text) if unit else False,
    }


HOURS_FROM_EVIDENCE = ("evidence_offer", "evidence_host_cadence")

_DASHES = "-‐‑‒–—−"


def quote_pattern(quote: str) -> re.Pattern | None:
    """The quote as a regex: literal words, tolerant whitespace and dashes.

    The collector normalises whitespace and the page may hyphenate with an en
    dash where the extract kept a hyphen. Nothing else is allowed to differ:
    this is a word-for-word check, not a fuzzy one.
    """
    quote = (quote or "").strip()
    if not quote:
        return None
    parts = []
    for ch in quote:
        if ch.isspace():
            parts.append(r"\s+")
        elif ch in _DASHES:
            parts.append(r"\s*[" + re.escape(_DASHES) + r"]\s*")
        else:
            parts.append(re.escape(ch))
    # a \s+ next to a dash class is already covered by the class's own \s*,
    # so "1-2", "1 - 2" and "1 – 2" all hit the same pattern
    pattern = "".join(parts)
    pattern = pattern.replace(r"\s+\s*[", r"\s*[").replace(r"]\s*\s+", r"]\s*")
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error:
        return None


def hours_evidence_rows(rows: list[dict]) -> list[dict]:
    """Every published record whose divisor was read out of a quote."""
    return [r for r in rows
            if (r.get("hours_source") or "") in HOURS_FROM_EVIDENCE
            and (r.get("hours_evidence_quote") or "").strip()]


def load_snapshot_index(path: Path) -> dict:
    csv.field_size_limit(10 ** 9)
    index: dict[tuple, dict] = {}
    by_host: dict[str, dict] = {}
    with path.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("is_priced") != "yes":
                continue
            key = (
                row.get("host", ""),
                row.get("currency", ""),
                row.get("unit", ""),
                (row.get("price_low") or "").strip(),
                (row.get("price_high") or "").strip(),
            )
            index.setdefault(key, row)
            by_host.setdefault(row.get("host", ""), row)
    return {"exact": index, "by_host": by_host}


def run_hours_gate(rows: list[dict], snap: dict, session, sleep: float) -> dict:
    """Re-read every hours citation in the release against the live pages."""
    targets = hours_evidence_rows(rows)
    results = []
    cache: dict[str, tuple[str | None, str]] = {}

    for i, row in enumerate(targets, 1):
        host = row.get("host", "")
        quote = (row.get("hours_evidence_quote") or "").strip()
        rx = quote_pattern(quote)
        key = (
            host,
            row.get("currency", ""),
            row.get("unit", ""),
            (row.get("price_low") or "").strip(),
            (row.get("price_high") or "").strip(),
        )
        snap_row = snap["exact"].get(key) or snap["by_host"].get(host) or {}

        urls: list[str] = []
        page = (row.get("evidence_page") or "").strip()
        if page:
            urls.append(page)
        for u in pages_for(snap_row):
            if u not in urls:
                urls.append(u)
        urls = urls[:MAX_PAGES]

        want_chars = collector_chars(snap_row)
        pages, live_chars, hit_url = [], 0, None
        for url in urls:
            if url in cache:
                text, note = cache[url]
            else:
                text, note = fetch(url, session)
                cache[url] = (text, note)
                time.sleep(sleep)
            rec = {"url": url, "fetch": note, "chars": len(text) if text else 0}
            if text:
                live_chars += len(text)
                rec["quote_ok"] = bool(rx and rx.search(text))
                if rec["quote_ok"]:
                    hit_url = url
            pages.append(rec)
            if hit_url:
                break

        rendered = live_chars >= MIN_TEXT and (
            want_chars is None or live_chars >= RENDER_RATIO * want_chars)
        entry = {
            "n": i,
            "host": host,
            "hours_source": row.get("hours_source"),
            "hours_per_month_used": row.get("hours_per_month_used"),
            "hours_evidence_quote": quote,
            "price_low": row.get("price_low"),
            "price_high": row.get("price_high"),
            "currency": row.get("currency"),
            "unit": row.get("unit"),
            "collector_chars": want_chars,
            "live_chars": live_chars,
            "found_on": hit_url,
            "pages": pages,
            "reachable": bool(rendered or hit_url),
        }
        if hit_url:
            entry["pass"] = True
        elif not rendered:
            entry["pass"] = None
            entry["unreachable_reason"] = (
                "all pages errored/blocked" if live_chars == 0
                else f"page did not render for a plain HTTP client "
                     f"(live {live_chars} chars vs collector {want_chars})")
        else:
            entry["pass"] = False
        results.append(entry)
        state = "OK" if entry["pass"] else ("MISS" if entry["reachable"] else "SKIP")
        print(f"[hours {i:>2}/{len(targets)}] {host:<32} {state:<4} "
              f"{quote!r}", flush=True)

    reachable = [r for r in results if r["reachable"]]
    passed = [r for r in reachable if r["pass"]]
    rate = (len(passed) / len(reachable)) if reachable else 0.0
    return {
        "scope": ("every published record whose divisor was read out of a "
                  "quote, not a sample"),
        "records": len(targets),
        "reachable": len(reachable),
        "unreachable": len(results) - len(reachable),
        "passed": len(passed),
        "accuracy_on_reachable": round(rate, 4),
        "threshold": THRESHOLD,
        "verdict": "PASS" if reachable and rate >= THRESHOLD else "FAIL",
        "failures": [
            {k: v for k, v in r.items() if k != "pages"}
            | {"pages": [p["url"] + " -> " + p["fetch"] for p in r["pages"]]}
            for r in results if r["pass"] is not True
        ],
        "results": results,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True, type=Path)
    ap.add_argument("--snapshot", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--sample", type=int, default=SAMPLE_SIZE)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--sleep", type=float, default=0.4)
    ap.add_argument("--no-hours-gate", action="store_true",
                    help="skip the full re-read of the hours citations")
    args = ap.parse_args(argv)

    # utf-8-sig, not utf-8. v2.1.1 gave the record file a BOM so Excel would
    # stop mangling the pound and euro signs, and a plain utf-8 read turns the
    # first column name into "﻿host". Every host lookup then misses, the
    # snapshot join returns nothing, and the gate silently falls back to
    # checking the crawl seed instead of the page the price was read from -
    # which is the exact failure this gate was rewritten to stop.
    with args.records.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if rows and "host" not in rows[0]:
        raise SystemExit("records file has no 'host' column: "
                         f"{sorted(rows[0])[:5]}")

    snap = load_snapshot_index(args.snapshot)

    rng = random.Random(args.seed)
    sample = rng.sample(rows, min(args.sample, len(rows)))

    import requests

    session = requests.Session()
    results = []
    for i, row in enumerate(sample, 1):
        host = row.get("host", "")
        key = (
            host,
            row.get("currency", ""),
            row.get("unit", ""),
            (row.get("price_low") or "").strip(),
            (row.get("price_high") or "").strip(),
        )
        snap_row = snap["exact"].get(key) or snap["by_host"].get(host) or {}
        urls = pages_for(snap_row) or [(row.get("source_url") or "").strip()]
        want_chars = collector_chars(snap_row)

        page_reports = []
        live_chars = 0
        best = None
        for url in urls:
            text, note = fetch(url, session)
            rec = {"url": url, "fetch": note, "chars": len(text) if text else 0}
            if text:
                live_chars += len(text)
                res = check_page(row, text)
                rec.update(res)
                score = sum((res["value_ok"], res["currency_ok"], res["unit_ok"]))
                if best is None or score > best[0]:
                    best = (score, res)
                if res["value_ok"] and res["currency_ok"] and res["unit_ok"]:
                    page_reports.append(rec)
                    break
            page_reports.append(rec)
            time.sleep(args.sleep)

        entry = {
            "n": i,
            "host": host,
            "role": row.get("role"),
            "currency": row.get("currency"),
            "unit": row.get("unit"),
            "price_low": row.get("price_low"),
            "price_high": row.get("price_high"),
            "confidence_tier": row.get("confidence_tier"),
            "evidence_quote": row.get("evidence_quote"),
            "collector_chars": want_chars,
            "live_chars": live_chars,
            "pages": page_reports,
        }

        rendered = live_chars >= MIN_TEXT and (
            want_chars is None or live_chars >= RENDER_RATIO * want_chars
        )
        if not rendered:
            entry["reachable"] = False
            entry["unreachable_reason"] = (
                "all pages errored/blocked"
                if live_chars == 0
                else f"page did not render for a plain HTTP client "
                     f"(live {live_chars} chars vs collector {want_chars})"
            )
            entry["pass"] = None
        else:
            entry["reachable"] = True
            res = best[1] if best else {
                "value_ok": False, "currency_ok": False, "unit_ok": False}
            entry.update(res)
            entry["pass"] = bool(res["value_ok"] and res["currency_ok"] and res["unit_ok"])

        results.append(entry)
        state = "OK" if entry.get("pass") else ("MISS" if entry["reachable"] else "SKIP")
        print(f"[{i:>2}/{len(sample)}] {host:<32} {state:<4} "
              f"live={live_chars} collector={want_chars}", flush=True)

    reachable = [r for r in results if r["reachable"]]
    passed = [r for r in reachable if r["pass"]]
    unreachable = [r for r in results if not r["reachable"]]
    rate = (len(passed) / len(reachable)) if reachable else 0.0

    hours_gate = None
    if not args.no_hours_gate:
        print()
        hours_gate = run_hours_gate(rows, snap, session, args.sleep)

    price_verdict = "PASS" if rate >= THRESHOLD else "FAIL"
    verdict = price_verdict
    if hours_gate is not None and hours_gate["verdict"] != "PASS":
        verdict = "FAIL"

    report = {
        "records_file": str(args.records),
        "snapshot_file": str(args.snapshot),
        "seed": args.seed,
        "sample_size": len(sample),
        "reachable": len(reachable),
        "unreachable": len(unreachable),
        "passed": len(passed),
        "accuracy_on_reachable": round(rate, 4),
        "threshold": THRESHOLD,
        "price_verdict": price_verdict,
        "hours_evidence_gate": hours_gate,
        "verdict": verdict,
        "unreachable_records": [
            {"host": r["host"], "reason": r["unreachable_reason"],
             "pages": [p["url"] + " -> " + p["fetch"] for p in r["pages"]]}
            for r in unreachable
        ],
        "failures": [
            {k: v for k, v in r.items() if k != "pages"} | {
                "pages": [p["url"] + " -> " + p["fetch"] for p in r["pages"]]}
            for r in reachable if not r["pass"]
        ],
        "results": results,
    }
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"price sample: reachable {len(reachable)}/{len(sample)}  "
          f"passed {len(passed)}  accuracy {rate:.1%}  verdict {price_verdict}")
    if hours_gate is not None:
        print(f"hours citations: reachable {hours_gate['reachable']}/"
              f"{hours_gate['records']}  passed {hours_gate['passed']}  "
              f"accuracy {hours_gate['accuracy_on_reachable']:.1%}  "
              f"verdict {hours_gate['verdict']}")
    print(f"release verdict {report['verdict']}")
    return 0 if report["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
