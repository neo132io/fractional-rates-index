#!/usr/bin/env python3
"""Build a full release of the Fractional Rates Index from one frozen snapshot.

One script, run once, everything it emits archived together. v2.0 was generated
by hand on the server and could not be reproduced afterwards; that is the hole
this closes.

Inputs
  --input     a normalized snapshot (hygiene columns + rate_hourly_usd)
  --fx-lock   the fx-lock-YYYYMMDD.json used to normalise it

Outputs, all into --outdir
  portal-rates-<version>.csv     the groups that clear the reporting floor,
                                 in their own currency and in USD per hour
  portal-metrics-<version>.json  headline with interval, fx lock, methodology,
                                 quality flags, the whole funnel
  records-<version>.csv          every published record with its evidence
                                 quote and its normalisation chain - the part
                                 nobody else publishes
  delta-vs-v2-<version>.csv      group by group against the live v2.0 tables
  hours-audit-<version>.csv      the 51 hours_included readings and their verdicts

    python tools/generate_release.py --input <normalized.csv> \
        --fx-lock <fx-lock.json> --outdir <dir> --version v2.1
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import group_stats as gs  # noqa: E402
import hours_evidence as he  # noqa: E402
import retainer_hours as rh  # noqa: E402
from fx_rates import load_lock  # noqa: E402
from normalize_rates import value_and_label  # noqa: E402
from verify_evidence import (  # noqa: E402
    CONFIDENCE_REASONS, clean_pass, confidence_tier, evidence_quotes, gate_pass,
    is_priced, verify_row,
)

csv.field_size_limit(2 ** 31 - 1)

ROLE_LABEL = {
    "CPO": "Fractional CPO", "CTO": "Fractional CTO", "CMO": "Fractional CMO",
    "CFO": "Fractional CFO", "COO": "Fractional COO", "CRO": "Fractional CRO",
    "multi": "Fractional multi-role", "(none)": "Role not specified",
}
MODEL_LABEL = {"Monthly": "Monthly retainer", "Day": "Day rate", "Hourly": "Hourly"}
SYMBOL = {"USD": "$", "GBP": "£", "EUR": "€"}


# The leading byte of a UTF-8 sequence, seen through cp1252: Â for two-byte
# symbols (£ -> Â£), Ã for accented letters, â for three-byte ones (€ -> â‚¬).
_MOJIBAKE_MARKERS = ("Â", "Ã", "â", "Å", "Ð")


def repair_mojibake(text: str) -> str:
    """Undo one round of UTF-8-read-as-cp1252 in a captured quote.

    Eight of the captured quotes carry "Â£1,500" where the page said "£1,500".
    The collector wrote UTF-8 bytes that were then read back as cp1252. The
    repair is applied only when it is provably safe: the round trip has to
    succeed, it has to remove the marker, and it must not change a single
    digit. Anything else is left exactly as captured, because a wrong repair
    to an evidence quote is worse than an ugly one.
    """
    if not text or not any(m in text for m in _MOJIBAKE_MARKERS):
        return text
    try:
        fixed = text.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    if any(m in fixed for m in _MOJIBAKE_MARKERS):
        return text
    if [c for c in fixed if c.isdigit()] != [c for c in text if c.isdigit()]:
        return text
    return fixed


def money(currency: str, value) -> str:
    if value in ("", None):
        return ""
    return f"{SYMBOL.get(currency, '')}{float(value):,.0f}"


# --------------------------------------------------------------------------
# v2.0 baseline, read off the shipped release files
# --------------------------------------------------------------------------

def load_v2(repo_data: Path, version: str = "v2") -> tuple[dict, dict]:
    """The group table and metrics of an already-shipped release."""
    rates_path = repo_data / f"portal-rates-{version}.csv"
    metrics_path = repo_data / f"portal-metrics-{version}.json"
    rates: dict[tuple[str, str, str], dict] = {}
    reverse_role = {v: k for k, v in ROLE_LABEL.items()}
    reverse_model = {v: k for k, v in MODEL_LABEL.items()}
    with rates_path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            key = (reverse_role.get(row["role"], row["role"]),
                   row["region"],
                   reverse_model.get(row["model"], row["model"]))
            rates[key] = {
                "median": _demoney(row["median"]),
                "p25": _demoney(row["p25"]),
                "p75": _demoney(row["p75"]),
                "n": int(row.get("n") or row.get("n_hosts") or 0),
                "publish": row.get("publish", ""),
            }
    metrics = json.loads(metrics_path.read_text(encoding="utf-8-sig"))
    return rates, metrics


def _demoney(s: str) -> float | None:
    s = (s or "").strip().lstrip("$£€").replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


# --------------------------------------------------------------------------
# outputs
# --------------------------------------------------------------------------

PORTAL_FIELDS = [
    "role", "region", "model", "currency",
    "median", "p25", "p75",
    "median_hourly_usd", "p25_hourly_usd", "p75_hourly_usd",
    "n_hosts", "n_offers",
    "confidence_high", "confidence_medium", "confidence_low", "confidence_flag",
    "bar_left", "bar_right", "bar_median",
]

# The quartile bar is drawn as a share of the widest value in its own
# (region, model) block, capped at 92.6% so the widest bar still has a right
# margin. Same geometry as v2.0, so the two releases chart identically.
BAR_SCALE = 92.6

RECORD_FIELDS = [
    "host", "provider", "role", "region", "model",
    "currency", "unit", "price_low", "price_high",
    "value_basis", "value_published",
    "rate_hourly_usd", "normalization_basis",
    "hours_per_month_used", "hours_source",
    "hours_evidence_quote", "hours_evidence_basis",
    "confidence_tier", "strict_pass", "dual_agreement",
    "evidence_verdict", "evidence_reasons", "confidence_reasons",
    "scope_verdict", "country", "country_source",
    "evidence_quote", "evidence_page", "source_url", "capture_date",
]

DISTRIBUTION_FIELDS = ["bucket", "count", "height_pct", "is_median"]

# The buckets the v2.0 chart used. Kept identical so the two releases can be
# read against each other. Upper bound is exclusive.
DIST_BUCKETS = [
    ("<2k", 0, 2000), ("2-3k", 2000, 3000), ("3-4k", 3000, 4000),
    ("4-5k", 4000, 5000), ("5-6k", 5000, 6000), ("6-8k", 6000, 8000),
    ("8-10k", 8000, 10000), ("10-15k", 10000, 15000),
    ("15k+", 15000, float("inf")),
]

DELTA_FIELDS = [
    "role", "region", "model",
    "v2_n", "v21_n_hosts", "n_delta",
    "v2_median", "v21_median_native", "median_delta", "median_delta_pct",
    "v21_median_hourly_usd", "v21_published",
    "note",
]


def build_portal(groups: dict) -> list[dict]:
    out = []
    for key in sorted(groups):
        g = groups[key]
        if not g["meets_floor"]:
            continue
        role, region, model = key
        cur = gs.CURRENCY_OF_REGION.get(region, "")
        native, hourly = g["native"], g["hourly_usd"]
        out.append({
            "role": ROLE_LABEL.get(role, role),
            "region": region,
            "model": MODEL_LABEL.get(model, model),
            "currency": cur,
            "median": money(cur, native["median"]),
            "p25": money(cur, native["p25"]),
            "p75": money(cur, native["p75"]),
            "median_hourly_usd": f"${hourly['median']:,.0f}" if hourly else "",
            "p25_hourly_usd": f"${hourly['p25']:,.0f}" if hourly else "",
            "p75_hourly_usd": f"${hourly['p75']:,.0f}" if hourly else "",
            "n_hosts": g["n_hosts"],
            "n_offers": g["n_offers"],
            "confidence_high": g["confidence"].get("high", 0),
            "confidence_medium": g["confidence"].get("medium", 0),
            "confidence_low": g["confidence"].get("low", 0),
            # One column the template can read without arithmetic. A group with
            # no corroborated record at all is the case the confidence tier was
            # kept for, so it is flagged in the artifact and not left to the
            # theme to notice.
            "confidence_flag": ("no_high_confidence_record"
                                if not int(g["confidence"].get("high", 0))
                                else ""),
            "_p25": native["p25"], "_median": native["median"],
            "_p75": native["p75"],
        })
    return add_bar_geometry(out)


def add_bar_geometry(rows: list[dict]) -> list[dict]:
    """Percentage offsets for the quartile bar, scaled within (region, model)."""
    widest: dict[tuple[str, str], float] = {}
    for row in rows:
        block = (row["region"], row["model"])
        widest[block] = max(widest.get(block, 0.0), float(row["_p75"] or 0))
    for row in rows:
        top = widest[(row["region"], row["model"])] or 1.0
        pos = lambda v: round(min(float(v or 0) / top, 1.0) * BAR_SCALE, 1)
        row["bar_left"] = pos(row["_p25"])
        row["bar_median"] = pos(row["_median"])
        row["bar_right"] = round(100.0 - pos(row["_p75"]), 1)
        for k in ("_p25", "_median", "_p75"):
            row.pop(k)
    return rows


def build_records(rows: list[dict]) -> list[dict]:
    verdicts = {id(r): verify_row(r) for r in rows}
    out = []
    for r in rows:
        _, label = value_and_label(r)
        quote = repair_mojibake(" || ".join(evidence_quotes(r)))[:800]
        role, region, model = gs.group_key(r)
        out.append({
            "host": r.get("host", ""),
            "provider": r.get("provider", ""),
            "role": role, "region": region, "model": model,
            "currency": r.get("currency", ""), "unit": r.get("unit", ""),
            "price_low": r.get("price_low", ""),
            "price_high": r.get("price_high", ""),
            "value_basis": r.get("value_basis", "") or label.split("(")[0],
            "value_published": r.get("value_published", ""),
            "rate_hourly_usd": r.get("rate_hourly_usd", ""),
            "normalization_basis": r.get("normalization_basis", ""),
            "hours_per_month_used": r.get("hours_per_month_used", ""),
            "hours_source": r.get("hours_source", ""),
            "hours_evidence_quote": r.get("hours_evidence_quote", ""),
            "hours_evidence_basis": r.get("hours_evidence_basis", ""),
            "confidence_tier": confidence_tier(r),
            "strict_pass": r.get("strict_pass", ""),
            "dual_agreement": r.get("dual_agreement", ""),
            # Recomputed here, never copied from the snapshot. The snapshot's
            # own verify_verdict column was written by an earlier pass that
            # still treated the two confidence checks as a veto, and it labels
            # 215 of these 362 records REJECT / not_own_price when every one of
            # them is context_verdict=own. A published label has to be produced
            # by the rules that were actually applied.
            "evidence_verdict": verdicts[id(r)].status,
            "evidence_reasons": ";".join(
                x for x in verdicts[id(r)].reasons if x not in CONFIDENCE_REASONS),
            "confidence_reasons": ";".join(
                x for x in verdicts[id(r)].reasons if x in CONFIDENCE_REASONS),
            "scope_verdict": r.get("scope_verdict", ""),
            "country": r.get("country", ""),
            "country_source": r.get("country_source", ""),
            "evidence_quote": quote,
            # The page the quote was read from. source_url is the crawl seed
            # and differs from it on 221 of the 579 priced rows, so a reader
            # who only had source_url could not find the quote.
            "evidence_page": r.get("page_source", "") or r.get("source_url", ""),
            "source_url": r.get("source_url", ""),
            "capture_date": r.get("capture_date", ""),
        })
    out.sort(key=lambda d: (d["role"], d["region"], d["model"], d["host"]))
    return out


def us_monthly_host_medians(published: list[dict]) -> list[float]:
    """One value per host: the median of that host's US monthly retainers."""
    import statistics
    from verify_evidence import representative_value
    per_host: dict[str, list[float]] = {}
    for r in published:
        if r.get("currency") != "USD" or r.get("unit") != "per_month":
            continue
        v = representative_value(r)
        if v is not None:
            per_host.setdefault(r.get("host", ""), []).append(float(v))
    return sorted(statistics.median(sorted(v)) for v in per_host.values())


def build_distribution(published: list[dict]) -> list[dict]:
    """The US monthly retainer histogram, one observation per host.

    Same buckets and the same bar geometry as v2.0: heights are a share of the
    tallest bucket, so the chart reads as shape rather than as counts.
    """
    import statistics
    values = us_monthly_host_medians(published)
    counts = []
    for label, low, high in DIST_BUCKETS:
        counts.append(sum(1 for v in values if low <= v < high))
    tallest = max(counts) if counts else 0
    median = statistics.median(values) if values else None
    out = []
    for (label, low, high), count in zip(DIST_BUCKETS, counts):
        is_median = (median is not None and low <= median < high)
        out.append({
            "bucket": label,
            "count": count,
            "height_pct": round(100.0 * count / tallest, 1) if tallest else 0.0,
            "is_median": "1" if is_median else "0",
        })
    return out


def build_portal_contract(all_rows, published, groups, distribution,
                          headline, publish_rate, version, dates) -> dict:
    """The flat key set the site templates read.

    The templates used to carry these figures as literals in six PHP files.
    They now read this block and nothing else, so a release changes numbers on
    the site by shipping a file, never by editing markup. Every key here is
    derived; none is typed.
    """
    import statistics

    at_floor = {k: g for k, g in groups.items() if g["meets_floor"]}
    hosts_tracked = len({r.get("host") for r in all_rows})
    hosts_published = len({r.get("host") for r in published})

    # GBP counts. Counts are not subject to the reporting floor - a count of
    # providers is measured directly, unlike a median of too few of them.
    def gbp_hosts(unit=None):
        return len({r.get("host") for r in published
                    if r.get("currency") == "GBP"
                    and (unit is None or r.get("unit") == unit)})

    roles_priced = len({gs.group_key(r)[0] for r in published} - {"(none)", "multi"})
    roles_tracked = len({r.get("role") for r in all_rows
                         if (r.get("role") or "").strip()
                         not in ("", "(none)", "none", "multi", "other")})

    us_month = headline.get("us_monthly_native") or {}
    hourly = headline.get("hourly_usd_all") or {}

    dist_n = sum(int(b["count"]) for b in distribution)
    band = next((b["bucket"] for b in distribution if b["is_median"] == "1"), "")

    return {
        "version": version,
        "reporting_floor_n": gs.REPORTING_FLOOR,

        # sample frame
        "tracked": hosts_tracked,
        "published": hosts_published,
        "share_pct": round(100.0 * hosts_published / hosts_tracked, 1)
                     if hosts_tracked else 0.0,

        # the continuity headline, in the currency providers quote.
        # The *_exact keys carry the unrounded value: v2.1 published
        # us_monthly_p25 as 2562 for a p25 of 2562.50, which is a truncation
        # presented as a price. The integer keys stay for template
        # compatibility; a template that wants to be right reads the exact one.
        "us_monthly_median": int(round(us_month.get("median") or 0)),
        "us_monthly_p25": int(round(us_month.get("p25") or 0)),
        "us_monthly_p75": int(round(us_month.get("p75") or 0)),
        "us_monthly_median_exact": round(us_month.get("median") or 0, 2),
        "us_monthly_p25_exact": round(us_month.get("p25") or 0, 2),
        "us_monthly_p75_exact": round(us_month.get("p75") or 0, 2),
        "us_monthly_providers": int(us_month.get("n_hosts") or 0),
        "us_monthly_ci_low": int(round(us_month.get("ci95_low") or 0)),
        "us_monthly_ci_high": int(round(us_month.get("ci95_high") or 0)),

        # the unified axis, new in v2.1
        "hourly_usd_median": round(hourly.get("median") or 0, 2),
        "hourly_usd_p25": round(hourly.get("p25") or 0, 2),
        "hourly_usd_p75": round(hourly.get("p75") or 0, 2),
        # The interval that carries the divisor's uncertainty as well as the
        # sample's. v2.1 published the sampling-only pair as if it were the
        # whole answer; both are here now, and the wide one is the default so
        # that a template cannot quietly pick the flattering one.
        "hourly_usd_ci_low": round(hourly.get("ci95_low") or 0, 2),
        "hourly_usd_ci_high": round(hourly.get("ci95_high") or 0, 2),
        "hourly_usd_ci_sampling_only_low": round(
            hourly.get("ci95_sampling_only_low") or 0, 2),
        "hourly_usd_ci_sampling_only_high": round(
            hourly.get("ci95_sampling_only_high") or 0, 2),
        "hourly_usd_divisor": (hourly.get("divisor") or {}).get("divisor_point"),
        "hourly_usd_divisor_ci_low": (hourly.get("divisor") or {}).get("divisor_ci95_low"),
        "hourly_usd_divisor_ci_high": (hourly.get("divisor") or {}).get("divisor_ci95_high"),
        "hourly_usd_providers": int(hourly.get("n_hosts") or 0),

        # GBP frame: counts only. No UK group clears the floor in v2.1, so no
        # UK median is published. The site must not quote one either.
        "uk_providers": gbp_hosts(),
        "uk_monthly_providers": gbp_hosts("per_month"),
        "uk_day_providers": gbp_hosts("per_day"),
        "uk_day_median": 0,
        "uk_groups_published": len([k for k in at_floor if k[1] == "UK"]),

        # roles and table shape
        "roles_tracked": roles_tracked,
        "roles_priced": roles_priced,
        "table_groups": len(at_floor),
        "table_records": sum(g["n_hosts"] for g in at_floor.values()),
        "table_offers": sum(g["n_offers"] for g in at_floor.values()),
        "groups_ge8": len(at_floor),
        "groups_total": len(groups),
        "groups_below_floor": len(groups) - len(at_floor),
        "regions": len({k[1] for k in at_floor}),
        # `table_records` sums n_hosts across groups, so a host that appears in
        # two groups is counted twice. v2.1 rendered that sum under the label
        # "PROVIDERS", which the caption itself defines as counting sites, and
        # overstated the count by 6.2%. Both numbers are published; the label
        # decides which one it means.
        "table_hosts_unique": len({r.get("host") for r in published
                                   if gs.group_key(r) in at_floor}),
        "table_group_entries": sum(g["n_hosts"] for g in at_floor.values()),
        # v2.1 rendered "1 currencies (USD, GBP, EUR)" by binding the caption
        # to `regions`. The currency list is its own fact and now has its own
        # keys.
        "currencies": sorted({r.get("currency") for r in published
                              if r.get("currency")}),
        "currencies_count": len({r.get("currency") for r in published
                                 if r.get("currency")}),
        "regions_all": sorted({k[1] for k in groups}),

        # distribution chart
        "dist_n": dist_n,
        "dist_median_band": band,

        # publication rate, per role, on hosts whose captured pages name the role
        "publish_rate_overall_pct": publish_rate.get("overall_pct"),
        "publish_rate_hosts_read": publish_rate.get("hosts_read"),
        "publish_rate_by_role": {
            role: v["publish_pct"] for role, v in
            sorted(publish_rate.get("by_role", {}).items(),
                   key=lambda kv: -kv[1]["publish_pct"])
        },

        "date_first_capture": dates[0],
        "date_last_capture": dates[1],
    }


def build_delta(groups: dict, v2_rates: dict) -> list[dict]:
    keys = sorted(set(groups) | set(v2_rates))
    out = []
    for key in keys:
        role, region, model = key
        g = groups.get(key)
        v2 = v2_rates.get(key)
        v21_med = g["native"]["median"] if g and g["native"] else None
        v2_med = v2["median"] if v2 else None
        delta = round(v21_med - v2_med, 2) if (v21_med is not None and v2_med) else ""
        pct = (round(100 * (v21_med - v2_med) / v2_med, 1)
               if (v21_med is not None and v2_med) else "")
        if g is None:
            note = "group emptied by the evidence and scope rules"
        elif not g["meets_floor"]:
            note = f"below the n>={gs.REPORTING_FLOOR} reporting floor; counted, not published"
        elif v2 is None:
            note = "new group in v2.1"
        else:
            note = ""
        # The reporting floor has to hold in every file of the release, not
        # just in the one the page renders. v2.1 shipped this table with
        # v21_median_native and v21_median_hourly_usd filled in for all 31
        # sub-floor groups, including nine that are a single provider, while
        # the page said those groups "carry no figure anywhere, here or in the
        # prose". A number in a column called median, computed from one host,
        # is exactly what the floor exists to prevent.
        shown = bool(g and g["meets_floor"])
        out.append({
            "role": role, "region": region, "model": model,
            "v2_n": v2["n"] if v2 else "",
            "v21_n_hosts": g["n_hosts"] if g else 0,
            "n_delta": (g["n_hosts"] if g else 0) - (v2["n"] if v2 else 0),
            "v2_median": v2_med if v2_med is not None else "",
            "v21_median_native": (v21_med if (shown and v21_med is not None) else ""),
            "median_delta": delta if shown else "",
            "median_delta_pct": pct if shown else "",
            "v21_median_hourly_usd": (g["hourly_usd"]["median"]
                                      if (shown and g and g["hourly_usd"]) else ""),
            "v21_published": "yes" if shown else "no",
            "note": note,
        })
    return out


# --------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------

def _host_medians(rows: list[dict]) -> list[float]:
    import statistics
    per_host: dict[str, list[float]] = {}
    for r in rows:
        v = gs.hourly_usd(r)
        if v is not None:
            per_host.setdefault(r.get("host", ""), []).append(v)
    return sorted(statistics.median(sorted(v)) for v in per_host.values())


def cross_check_axes(published: list[dict]) -> dict:
    """Do the three routes to an hourly figure agree with each other?

    They should not agree exactly - a retainer buys volume and ought to price
    below spot - but they have to sit in the same neighbourhood. This is the
    only external check available on the hours divisor, and it is the reason
    the divisor is 32.5 and not the 12 that the raw, unit-mixed field
    suggested: at 12 hours the retainer route claims $417/h, twice what the
    market charges by the hour, which cannot be right.
    """
    import statistics
    out = {}
    for unit, label in (("per_hour", "stated_hourly"),
                        ("per_day", "from_day_rate"),
                        ("per_month", "from_retainer")):
        v = _host_medians([r for r in published if r.get("unit") == unit])
        out[label] = {
            "n_hosts": len(v),
            "median_usd_per_hour": round(statistics.median(v), 2) if v else None,
        } if v else None
    return out


def hours_sensitivity(published: list[dict], lock: dict) -> dict:
    """What the published headline would say under other hours assumptions.

    v2.1 answered a different question from the one the reader is asking. It
    measured offer-level medians over the default-divisor rows only, so at 32.5
    hours it printed $153.85 while the headline beside it said $169.23, and the
    two could not be read against each other at all. This recomputes the
    headline itself - every published host, every unit, retainers that publish
    their own hours left alone - and the 32.5-hour column therefore reproduces
    the headline exactly. 25h and 40h are in because they are the assumptions a
    sceptical reader reaches for.
    """
    import statistics
    from decimal import Decimal as D
    out = {}
    for hours in ("12", "20", "25", "32.5", "40", "52"):
        divisor = float(D(hours))
        per_host: dict[str, list[float]] = {}
        for r in published:
            hourly = gs.hourly_usd(r)
            if hourly is None:
                continue
            if (r.get("unit") == "per_month"
                    and (r.get("hours_source") or "").startswith("default")):
                try:
                    used = float(r.get("hours_per_month_used") or 0)
                except ValueError:
                    used = 0.0
                if used > 0:
                    hourly = hourly * used / divisor
            per_host.setdefault(r.get("host", ""), []).append(hourly)
        v = sorted(statistics.median(sorted(x)) for x in per_host.values())
        out[f"{hours}h"] = round(statistics.median(v), 2) if v else None
    repriced = sum(1 for r in published
                   if r.get("unit") == "per_month"
                   and (r.get("hours_source") or "").startswith("default"))
    return {
        "basis": ("the published hourly headline, recomputed at each divisor. "
                  "Only the retainers with no published hours of their own move."),
        "hosts": len({r.get("host") for r in published}),
        "records_repriced": repriced,
        "median_usd_per_hour_at": out,
        "note": ("12h was the median of the raw hours_included column before "
                 "the audit, when hours per week and days per month were being "
                 "read as hours per month. 52h is the median of every host "
                 "whose text states a commitment once the v2.1.1 evidence scan "
                 "is counted, and is the number the divisor would move to if "
                 "the wider pool were adopted."),
    }


QUARANTINE_FIELDS = [
    "host", "offer_seq", "role", "currency", "unit",
    "price_low", "price_high", "rate_hourly_usd",
    "hours_per_month_used", "hours_source", "reason", "evidence_quote",
]


def build_quarantine(rows: list[dict]) -> list[dict]:
    """Rows the evidence rules accept and a plausibility band rejects.

    Published as a file rather than dropped quietly: a reader who counts the
    records and finds fewer than the funnel promised is owed the list.
    """
    out = []
    for r in rows:
        if not is_priced(r):
            continue
        if r.get("scope_verdict") not in ("include", "", None):
            continue
        if (r.get("dup_keep") or "keep") != "keep":
            continue
        v = verify_row(r)
        if gate_pass(v) or not v.quarantines:
            continue
        blocking = [x for x in v.reasons
                    if x not in CONFIDENCE_REASONS and x not in v.quarantines]
        if blocking:
            continue          # excluded on the evidence, not on plausibility
        out.append({
            "host": r.get("host", ""),
            "offer_seq": r.get("offer_seq", ""),
            "role": r.get("role", ""),
            "currency": r.get("currency", ""),
            "unit": r.get("unit", ""),
            "price_low": r.get("price_low", ""),
            "price_high": r.get("price_high", ""),
            "rate_hourly_usd": r.get("rate_hourly_usd", ""),
            "hours_per_month_used": r.get("hours_per_month_used", ""),
            "hours_source": r.get("hours_source", ""),
            "reason": ";".join(v.quarantines),
            "evidence_quote": repair_mojibake(" || ".join(evidence_quotes(r)))[:300],
        })
    out.sort(key=lambda d: (d["reason"], d["host"], str(d["offer_seq"])))
    return out


def numeric_changes(groups: dict, base_rates: dict, base_metrics: dict,
                    portal: dict, baseline_version: str) -> dict:
    """Every published median that moved, with its size, and the headline moves.

    v2.1's changelog listed six method changes and not one result. A reader who
    had quoted "$7,000 for a fractional CPO" two days earlier could not learn
    from it that the figure was now $8,000, by how much, or why. A dataset
    published for citation owes that reader a restatement notice.
    """
    moved, held, withdrawn = [], [], []

    # A group that fell below the floor did not move; it is gone. Every delta
    # table measures "what changed" and therefore cannot see it. COO/US/Monthly
    # went from n=8 at $3,938 to n=7 and out of the release, and the first
    # version of this block listed six of the previous edition's seven
    # published groups without saying where the seventh went. A reader who
    # quoted the withdrawn figure two days earlier has to be able to find it
    # here, which means listing it by name, with the figure that was published.
    for key, base in sorted(base_rates.items()):
        if not base or not base.get("median"):
            continue
        g = groups.get(key)
        if g and g["meets_floor"] and g["native"]:
            continue
        withdrawn.append({
            "group": "/".join(key),
            "n_hosts_before": base["n"],
            "n_hosts_now": g["n_hosts"] if g else 0,
            "median_before": base["median"],
            "median_now": None,
            "reason": (
                f"fell below the n>={gs.REPORTING_FLOOR} reporting floor and is "
                f"not published in this edition. The group is still counted and "
                f"named in the groups file; it carries no figure."
            ),
        })

    for key, g in sorted(groups.items()):
        if not g["meets_floor"] or not g["native"]:
            continue
        base = base_rates.get(key)
        if not base or not base.get("median"):
            continue
        now, before = g["native"]["median"], base["median"]
        entry = {
            "group": "/".join(key),
            "n_hosts_before": base["n"], "n_hosts_now": g["n_hosts"],
            "median_before": before, "median_now": now,
            "change_pct": round(100.0 * (now - before) / before, 1),
        }
        (moved if abs(entry["change_pct"]) >= 0.05 else held).append(entry)

    bp = base_metrics.get("portal", base_metrics)
    headline = {}
    for key, label in (("us_monthly_median", "US monthly median"),
                       ("hourly_usd_median", "hourly median, USD"),
                       ("published", "providers published"),
                       ("tracked", "hosts tracked")):
        before, now = bp.get(key), portal.get(key)
        if before in (None, 0) or now is None:
            continue
        headline[key] = {
            "label": label, "before": before, "now": now,
            "change_pct": round(100.0 * (now - before) / before, 1),
        }
    return {
        "previous_version": baseline_version,
        "published_group_medians_moved": moved,
        "published_group_medians_unchanged": held,
        "published_group_withdrawn": withdrawn,
        "groups_published_in_previous_edition": len(base_rates),
        "groups_accounted_for": len(moved) + len(held) + len(withdrawn),
        "headline": headline,
        "continuity_note": (
            "measured only on the groups that clear the reporting floor in "
            "both editions. A group of one or two hosts that did not move has "
            "not demonstrated continuity of a market; it has demonstrated that "
            "one provider did not edit a page."
        ),
    }


def confidence_flagged_groups(groups: dict) -> list[dict]:
    """Published groups that rest on no high-confidence record at all.

    Sivan's ruling of 2026-09-03 turned strict_pass and dual_agreement from a
    veto into a confidence tier. A tier nobody can see is a veto given up for
    nothing, so the release has to name the groups the reader should treat with
    the most caution, and the table has to mark them. `(none)/US/Hourly` is
    published on 0 high, 1 medium and 7 low records: it is the clearest case
    the rule exists for.
    """
    out = []
    for key, g in sorted(groups.items()):
        if not g["meets_floor"] or not g["native"]:
            continue
        c = g["confidence"]
        high = int(c.get("high", 0))
        if high:
            continue
        out.append({
            "group": "/".join(key),
            "n_hosts": g["n_hosts"],
            "high": high,
            "medium": int(c.get("medium", 0)),
            "low": int(c.get("low", 0)),
            "note": ("no record in this group had two independent extractions "
                     "agree and the strict parse pass. The figures are "
                     "published and counted; the table marks the group."),
        })
    return out


PUBLISHER_HOST = "saasfractionalcpo.com"


def self_inclusion(published: list[dict]) -> str:
    """Where the publisher sits in its own index, said with the number.

    v2.1 said "one host out of 175" and left out where. It was at the 89th
    percentile, on two records that were both wrong: 22.5 hours where the page
    says 25, and the measured default where the page says three to four days a
    week. Both are corrected in v2.1.1, and the sentence now carries the
    percentile so a reader does not have to compute it to check us.
    """
    import statistics
    per_host: dict[str, list[float]] = {}
    for r in published:
        v = gs.hourly_usd(r)
        if v is not None:
            per_host.setdefault(r.get("host", ""), []).append(v)
    values = sorted(statistics.median(sorted(v)) for v in per_host.values())
    ours = per_host.get(PUBLISHER_HOST)
    if not values or not ours:
        return (f"{PUBLISHER_HOST}, the publisher of this index, is not in the "
                "published set of this edition.")
    mine = statistics.median(sorted(ours))
    pct = round(100.0 * sum(1 for v in values if v < mine) / len(values))
    suffix = "th" if 10 <= pct % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(pct % 10, "th")
    offers = "; ".join(
        f"${float(r.get('price_low') or r.get('price_high')):,.0f}/month at "
        f"{r.get('hours_per_month_used')} hours"
        for r in sorted(published, key=lambda x: str(x.get("offer_seq")))
        if r.get("host") == PUBLISHER_HOST and r.get("unit") == "per_month"
    )
    return (
        f"{PUBLISHER_HOST}, the publisher of this index, is one of the sampled "
        f"providers ({offers}). It is one host out of {len(values)}, it is not "
        f"excluded, and its median of ${mine:,.2f} an hour sits at the "
        f"{pct}{suffix} percentile of the index."
    )


def hours_evidence_flags(all_rows: list[dict], published: list[dict]) -> dict:
    """How much of the hourly divisor is read off the page, and how much assumed."""
    import hours_evidence as he
    monthly = [r for r in published if r.get("unit") == "per_month"]
    src = Counter((r.get("hours_source") or "") for r in monthly)
    from_evidence = sum(v for k, v in src.items() if k in gs.HOURS_FROM_EVIDENCE)
    pool = gs.evidence_divisor_pool(published)
    import statistics
    return {
        "monthly_records": len(monthly),
        "hours_read_from_the_page": from_evidence,
        "hours_from_the_measured_default": len(monthly) - from_evidence,
        "by_source": dict(src.most_common()),
        "recall_note": (
            "v2.1 read hours only out of the collector's hours_included field "
            "and only where a manual audit had accepted the reading. v2.1.1 "
            "also reads a time commitment out of the offer's own price and "
            "cadence quotes, which recovered "
            f"{src.get('evidence_offer', 0) + src.get('evidence_host_cadence', 0)} "
            "further records whose published hourly figure had contradicted "
            "the provider's own words."
        ),
        "divisor_used": str(rh.default_hours_per_month()),
        "divisor_estimated_on_hosts": len(rh.host_level_hours()),
        "all_hosts_stating_hours": len(pool),
        "median_of_all_hosts_stating_hours": (
            round(statistics.median(pool), 2) if pool else None),
        "open_question": (
            "the divisor in use is the median of the hosts the manual audit "
            "read. Across every host whose text states a commitment, including "
            "the ones the v2.1.1 scan recovered, the median is higher. Moving "
            "the divisor onto the wider pool restates the hourly headline and "
            "is a decision, not a repair, so this edition does not make it."
        ),
    }


def changes_vs_previous(groups: dict, published: list[dict], hl: dict) -> dict:
    """What moved, in numbers, so a reader who quoted us can find their figure.

    A CC BY dataset that shifts a group median by a fifth between editions and
    lists only the method changes has issued a restatement without a
    restatement notice. This block is that notice.
    """
    return {
        "previous_version": "v2.1",
        "why": ("method, not market. The snapshot is byte-identical to v2.1's; "
                "every difference below comes from three repairs: hours read "
                "out of the offer's own words instead of a default, a "
                "plausibility band enforced on the derived hourly axis as well "
                "as the captured one, and the publisher's own record corrected "
                "against its live page."),
        "note": ("figures for groups below the reporting floor are not listed "
                 "here for the same reason they are not listed anywhere else."),
    }


def capture_dates(all_rows) -> tuple[str, str]:
    seen = sorted({(r.get("capture_date") or "").strip()
                   for r in all_rows if (r.get("capture_date") or "").strip()})
    return (seen[0], seen[-1]) if seen else ("", "")


def build_metrics(all_rows, published, groups, lock, input_path, version,
                  v2_metrics, distribution) -> dict:
    priced = [r for r in all_rows if is_priced(r)]
    gate = [r for r in priced if gate_pass(verify_row(r))]
    in_scope = [r for r in gate if r.get("scope_verdict") in ("include", "", None)]
    strict_also = [r for r in published if clean_pass(verify_row(r))]

    hl = gs.headline(published)
    at_floor = {k: g for k, g in groups.items() if g["meets_floor"]}
    dist = rh.hours_distribution()

    hosts_all = {r.get("host") for r in all_rows}
    published_hosts = {r.get("host") for r in published}
    pub_rate = gs.publish_rate_by_role(all_rows, published)
    dates = capture_dates(all_rows)

    return {
        "version": version,
        "portal": build_portal_contract(all_rows, published, groups,
                                        distribution, hl, pub_rate, version,
                                        dates),
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "tools/generate_release.py",
        "snapshot": {
            "file": input_path.name,
            "md5": hashlib.md5(input_path.read_bytes()).hexdigest(),
            "rows": len(all_rows),
            "hosts": len(hosts_all),
        },
        "fx_lock": {
            "file": f"fx-lock-{lock['rate_date'].replace('-', '')}.json",
            "source": lock["source"],
            "rate_date": lock["rate_date"],
            "fetched_at_utc": lock["fetched_at_utc"],
            "usd_per_unit": lock["usd_per_unit"],
        },
        "funnel": {
            "rows_total": len(all_rows),
            "rows_priced": len(priced),
            "passes_evidence_and_plausibility": len(gate),
            "and_in_scope": len(in_scope),
            "and_deduplicated": len(published),
            "of_which_also_pass_strict_and_dual": len(strict_also),
        },
        "headline": hl,
        "cross_check_axes": cross_check_axes(published),
        "hours_sensitivity": hours_sensitivity(published, lock),
        "groups": {
            "total": len(groups),
            "published": len(at_floor),
            "below_reporting_floor": len(groups) - len(at_floor),
            "reporting_floor_n": gs.REPORTING_FLOOR,
            "published_keys": sorted("/".join(k) for k in at_floor),
        },
        "publish_rate": pub_rate,
        "methodology": {
            "publication_gate": (
                "evidence and plausibility. The price, its currency and its "
                "cadence are found word for word in a quote captured from the "
                "provider's own page, and the price sits inside a per-unit "
                "plausibility band. Where the provider states how many hours "
                "the retainer buys, the divisor behind the USD-per-hour column "
                "is quoted too; on the rest it is the measured default of 32.5 "
                "hours a month, and no published record contradicts its own "
                "words. The word-for-word guarantee is a guarantee about the "
                "captured price, not about the derived hourly figure."
            ),
            "confidence_columns": (
                "strict_pass and dual_agreement are reported as a confidence "
                "tier per record (high = both, medium = one, low = neither). "
                "They no longer remove a row from the index."
            ),
            "value_basis": "midpoint of a published range, labelled midpoint; "
                           "a single figure is labelled published",
            "normalisation": {
                "axis": "USD per hour",
                "per_hour": "as captured",
                "per_day": f"divided by {rh.HOURS_PER_DAY} hours",
                "per_month": (
                    "divided by the hours the provider publishes where it "
                    f"publishes them, otherwise by {rh.default_hours_per_month()} "
                    "hours per month"
                ),
                "hours_per_day_basis": (
                    "8. Corroborated on sackermanconsulting.com, which prices "
                    "4h as a half-day, 8h as a full day and 12h as a day and a half"
                ),
                "default_hours_per_month": str(rh.default_hours_per_month()),
                "default_hours_source": rh.DEFAULT_HOURS_SOURCE,
                "hours_readings_audited": dist["audited_rows"],
                "hours_readings_accepted": dist["accepted_rows"],
                "hours_readings_rejected": dist["rejected_rows"],
                "hours_distribution_per_offer": dist["per_offer"],
                "hours_distribution_per_host": dist["per_host"],
                "currency": (
                    "converted at the locked ECB reference rate of "
                    f"{lock['rate_date']}. Both the original currency and the "
                    "USD-per-hour figure are published."
                ),
            },
            "grouping": (
                "region is derived from the currency the provider quotes in, "
                "not from where the provider is. A country column derived from "
                "the ccTLD is published beside it and is empty for the ~90% of "
                "hosts on a .com."
            ),
            "dedup": "one host contributes one value per group, the median of "
                     "its own offers in that group",
            "reporting_floor": (
                f"a group is published only at n >= {gs.REPORTING_FLOOR} hosts. "
                "Smaller groups are counted and named but carry no figure."
            ),
            "interval": "percentile bootstrap over hosts, 10,000 iterations",
        },
        "quality_flags": {
            "self_inclusion": self_inclusion(published),
            "role_unspecified_groups_published": sorted(
                "/".join(k) for k in at_floor if k[0] == "(none)"),
            "confidence_mix": dict(Counter(confidence_tier(r) for r in published)),
            "groups_without_high_confidence": confidence_flagged_groups(groups),
            "hours_default_applies_to_rows": sum(
                1 for r in published
                if r.get("hours_source", "").startswith("default")),
            "hours_declared_rows": sum(
                1 for r in published if r.get("hours_source") == "declared"),
            "region_is_currency": (
                "regions US/UK/EU are currency buckets. A US provider quoting "
                "in euros lands in EU."
            ),
            "known_limitations": [
                "the hours default is measured on the "
                f"{len(rh.host_level_hours())} hosts whose published hours the "
                "manual audit accepted; providers that publish hours may not be "
                "typical of those that do not, and on this snapshot they are "
                "not: they are the more expensive tail",
                "a monthly retainer is not literally a block of hours, so the "
                "hourly equivalent is a comparison device, not a quotable rate",
                "the quartile spread of the hourly axis partly measures "
                "engagement size rather than price: across the offers that "
                "state both a price and their hours, hours rise almost in step "
                "with the retainer",
                "ccTLD resolves a country for roughly one host in ten",
            ],
            "hours_evidence": hours_evidence_flags(all_rows, published),
        },
        "changes_vs_previous": changes_vs_previous(groups, published, hl),
        "v2_baseline": {
            "generated": v2_metrics.get("generated"),
            "us_monthly_median": v2_metrics.get("us_monthly_median"),
            "us_monthly_providers": v2_metrics.get("us_monthly_providers"),
            "published": v2_metrics.get("published"),
            "share_pct": v2_metrics.get("share_pct"),
        },
    }


# --------------------------------------------------------------------------

def _write(path: Path, fields: list[str], records: list[dict]) -> None:
    """Released CSVs carry a UTF-8 BOM.

    records-v2.1.csv holds 112 pound and euro signs. Excel on Windows opens a
    BOM-less UTF-8 CSV as cp1252 and renders every one of them as mojibake, so
    the first thing a journalist saw when checking a quote was a broken file.
    Every CSV reader that matters accepts the BOM; Excel is the only one that
    needs it.
    """
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n",
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(records)


def run(input_path: Path, fx_lock_path: Path, outdir: Path, version: str,
        repo_data: Path, baseline: Path | None = None,
        baseline_version: str = "v2.1") -> dict:
    lock = load_lock(fx_lock_path)
    rows = list(csv.DictReader(input_path.open(newline="", encoding="utf-8")))
    published = gs.publishable_rows(rows)
    groups = gs.aggregate(published)
    gs.add_confidence(groups, published)
    v2_rates, v2_metrics = load_v2(repo_data)

    outdir.mkdir(parents=True, exist_ok=True)
    portal = outdir / f"portal-rates-{version}.csv"
    metrics_p = outdir / f"portal-metrics-{version}.json"
    records_p = outdir / f"records-{version}.csv"
    delta_p = outdir / f"delta-vs-v2-{version}.csv"
    hours_p = outdir / f"hours-audit-{version}.csv"
    dist_p = outdir / f"portal-distribution-{version}.csv"

    distribution = build_distribution(published)

    quarantine_p = outdir / f"quarantine-{version}.csv"
    hours_ev_p = outdir / f"hours-evidence-{version}.csv"

    _write(portal, PORTAL_FIELDS, build_portal(groups))
    _write(records_p, RECORD_FIELDS, build_records(published))
    _write(delta_p, DELTA_FIELDS, build_delta(groups, v2_rates))
    _write(dist_p, DISTRIBUTION_FIELDS, distribution)
    _write(hours_p, list(rh.AUDIT[0].as_dict().keys()),
           [r.as_dict() for r in rh.AUDIT])
    quarantined = build_quarantine(rows)
    _write(quarantine_p, QUARANTINE_FIELDS, quarantined)
    _write(hours_ev_p, he.AUDIT_FIELDS, he.audit(rows))

    outputs = {
        "portal_rates": str(portal), "portal_metrics": str(metrics_p),
        "records": str(records_p), "delta": str(delta_p),
        "hours_audit": str(hours_p), "distribution": str(dist_p),
        "quarantine": str(quarantine_p), "hours_evidence": str(hours_ev_p),
    }

    metrics = build_metrics(rows, published, groups, lock, input_path, version,
                            v2_metrics, distribution)
    metrics["quarantine"] = {
        "records": len(quarantined),
        "reasons": dict(Counter(q["reason"] for q in quarantined).most_common()),
        "file": quarantine_p.name,
        "note": ("rows that clear the evidence rules and then fall outside a "
                 "plausibility band. Named and counted here rather than "
                 "dropped in silence."),
    }

    if baseline is not None:
        base_rates, base_metrics = load_v2(baseline, baseline_version)
        base_delta_p = outdir / f"delta-vs-{baseline_version}-{version}.csv"
        _write(base_delta_p, DELTA_FIELDS, build_delta(groups, base_rates))
        outputs["delta_vs_baseline"] = str(base_delta_p)
        metrics["changes_vs_previous"].update(
            numeric_changes(groups, base_rates, base_metrics,
                            metrics["portal"], baseline_version))

    metrics_p.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")

    return {
        "outputs": outputs,
        "portal": metrics["portal"],
        "funnel": metrics["funnel"],
        "headline": metrics["headline"],
        "groups": metrics["groups"],
        "quarantine": metrics["quarantine"],
        "changes_vs_previous": metrics["changes_vs_previous"],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--fx-lock", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--version", default="v2.1")
    ap.add_argument("--repo-data", type=Path,
                    default=Path(__file__).resolve().parent.parent / "data")
    ap.add_argument("--baseline", type=Path,
                    help="directory holding the previous release, for a "
                         "like-for-like delta and a restatement notice")
    ap.add_argument("--baseline-version", default="v2.1")
    args = ap.parse_args(argv)
    json.dump(run(args.input, args.fx_lock, args.outdir, args.version,
                  args.repo_data, args.baseline, args.baseline_version),
              sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
