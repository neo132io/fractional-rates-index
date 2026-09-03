#!/usr/bin/env python3
"""Group aggregates for the Fractional Rates Index.

Reproduces the v2.0 derivation rules that the release agent confirmed against
the live page (RELEASE-V21-CHECKPOINT sec 6b):

    region  = currency        USD -> US, GBP -> UK, EUR -> EU
    model   = unit            per_month -> Monthly, per_day -> Day, per_hour -> Hourly
    value   = midpoint of the published range, else the single endpoint
    dedup   = median of one host's offers inside (host, role, region, model)
    n       = hosts in the group, not offers

and adds what stage 4 requires:

  * every group reported twice, in its own currency and in USD per hour, off
    the columns normalize_rates.py writes
  * n >= 8 enforced. Groups below the floor are counted and named but carry no
    published figure, so a reader never sees a "median" that is one provider
  * n_hosts and n_offers as separate columns, because 16 offers from 5 hosts
    is not a sample of 16
  * a bootstrap 95% interval on the headline
  * no publish rate per group. That number was never defined at group level;
    the honest version is per role, over the hosts we actually read, and it
    lives in its own table

The publication gate is evidence plus plausibility (Sivan, 2026-09-03).
`strict_pass` and `dual_agreement` no longer veto a row: they become the
confidence tier reported beside it.

    python tools/group_stats.py --input <normalized.csv> --out groups.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_evidence import (  # noqa: E402
    clean_pass, confidence_tier, gate_pass, is_priced, representative_value,
    verify_row,
)

csv.field_size_limit(2 ** 31 - 1)

REGION = {"USD": "US", "GBP": "UK", "EUR": "EU"}
MODEL = {"per_month": "Monthly", "per_day": "Day", "per_hour": "Hourly"}
CURRENCY_OF_REGION = {"US": "USD", "UK": "GBP", "EU": "EUR"}

REPORTING_FLOOR = 8
BOOTSTRAP_ITERATIONS = 10_000
BOOTSTRAP_SEED = 20260903          # fixed, so the interval is reproducible


def group_key(row: dict) -> tuple[str, str, str]:
    role = (row.get("role") or "").strip() or "(none)"
    return role, REGION.get(row.get("currency", ""), "?"), MODEL.get(row.get("unit", ""), "?")


def hourly_usd(row: dict) -> float | None:
    raw = (row.get("rate_hourly_usd") or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


# --------------------------------------------------------------------------
# quantiles - numpy's linear interpolation, the rule v2.0 used
# --------------------------------------------------------------------------

def _quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def _summary(values: list[float]) -> dict:
    v = sorted(values)
    return {
        "n": len(v),
        "median": round(statistics.median(v), 2),
        "p25": round(_quantile(v, 0.25), 2),
        "p75": round(_quantile(v, 0.75), 2),
    }


HOURS_FROM_EVIDENCE = ("declared", "evidence_offer", "evidence_host_cadence")


def divisor_pool() -> list[float]:
    """The sample the default divisor is the median of.

    This is deliberately the manual audit's 21 hosts and not the wider set of
    hosts whose hours the v2.1.1 evidence scan recovered. The interval below
    answers "how well is 32.5 pinned down by the readings it was estimated
    from", which is a variance question. Whether 32.5 is the right centre at
    all once the recovered readings are counted is a bias question with a
    different answer - see `evidence_divisor_pool` - and it is not something a
    confidence interval can express.
    """
    from retainer_hours import host_level_hours
    return [float(h) for h in host_level_hours()]


def evidence_divisor_pool(rows: list[dict]) -> list[float]:
    """One hours figure per host whose captured text states a commitment.

    The audit's 21 hosts plus everything the evidence scan recovered. Reported
    as a diagnostic, not used: moving the divisor onto this pool restates the
    headline, and that is a decision, not a repair.
    """
    per_host: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        if r.get("unit") != "per_month":
            continue
        if (r.get("hours_source") or "") not in HOURS_FROM_EVIDENCE:
            continue
        try:
            h = float(r.get("hours_per_month_used") or 0)
        except ValueError:
            continue
        if h > 0:
            per_host[r.get("host", "")].append(h)
    return sorted(statistics.median(sorted(v)) for v in per_host.values())


def joint_bootstrap_ci(rows: list[dict], pool: list[float],
                       iterations: int = BOOTSTRAP_ITERATIONS,
                       seed: int = BOOTSTRAP_SEED) -> dict | None:
    """A 95% interval that carries the divisor's uncertainty as well as the sample's.

    The published v2.1 interval resampled hosts and held the 32.5-hour divisor
    fixed, which measures the smaller of the two unknowns: 83% of the hosts in
    the headline get their value from `retainer / divisor`, and the divisor is
    a median of a couple of dozen readings. Resampling only the hosts produced
    $153.85-$200.00 and invited the reader to conclude the true figure is in
    there with 95% confidence. It is not: the divisor alone moves the headline
    further than that interval is wide.

    Each iteration draws a fresh divisor - the median of a bootstrap resample
    of the hosts that publish their hours - reprices every retainer that has no
    published hours of its own, and then resamples the hosts.
    """
    if len(pool) < 2:
        return None
    fixed: dict[str, list[float]] = defaultdict(list)
    variable: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        host = r.get("host", "")
        hourly = hourly_usd(r)
        if hourly is None:
            continue
        if r.get("unit") == "per_month" and (r.get("hours_source") or "").startswith("default"):
            try:
                hours = float(r.get("hours_per_month_used") or 0)
            except ValueError:
                hours = 0.0
            if hours > 0:
                variable[host].append(hourly * hours)   # back to USD per month
                continue
        fixed[host].append(hourly)

    hosts = sorted(set(fixed) | set(variable))
    if len(hosts) < 2:
        return None

    rng = random.Random(seed)
    n_pool, n_hosts = len(pool), len(hosts)
    medians, divisors = [], []
    for _ in range(iterations):
        divisor = statistics.median([pool[rng.randrange(n_pool)] for _ in range(n_pool)])
        divisors.append(divisor)
        per_host = [
            statistics.median(sorted(
                fixed.get(h, []) + [u / divisor for u in variable.get(h, [])]))
            for h in hosts
        ]
        medians.append(statistics.median(
            [per_host[rng.randrange(n_hosts)] for _ in range(n_hosts)]))
    medians.sort()
    divisors.sort()
    lo = medians[int(0.025 * (iterations - 1))]
    hi = medians[int(0.975 * (iterations - 1))]
    return {
        "ci95_low": round(lo, 2),
        "ci95_high": round(hi, 2),
        "divisor_pool_hosts": n_pool,
        "divisor_point": round(statistics.median(pool), 2),
        "divisor_ci95_low": round(divisors[int(0.025 * (iterations - 1))], 2),
        "divisor_ci95_high": round(divisors[int(0.975 * (iterations - 1))], 2),
        "hosts_on_the_default_divisor": len(variable),
        "method": (
            "joint percentile bootstrap: each of "
            f"{iterations} iterations draws a divisor from the "
            f"{n_pool} hosts that publish their hours, reprices every retainer "
            "that publishes none, and then resamples the hosts. "
            f"Seed {seed}."
        ),
    }


def bootstrap_ci(values: list[float], iterations: int = BOOTSTRAP_ITERATIONS,
                 seed: int = BOOTSTRAP_SEED) -> tuple[float, float] | None:
    """Percentile bootstrap 95% interval for the median.

    Resamples the host-level values, not the offers: the offers inside one host
    are the same provider's price ladder and resampling them would pretend to a
    precision the sample does not have.
    """
    if len(values) < 2:
        return None
    rng = random.Random(seed)
    n = len(values)
    medians = []
    for _ in range(iterations):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        medians.append(statistics.median(sample))
    medians.sort()
    lo = medians[int(0.025 * (iterations - 1))]
    hi = medians[int(0.975 * (iterations - 1))]
    return round(lo, 2), round(hi, 2)


# --------------------------------------------------------------------------
# host-level collapse, then group aggregates in both axes
# --------------------------------------------------------------------------

def host_values(rows: list[dict]) -> dict[tuple, dict[str, dict[str, list[float]]]]:
    """group -> host -> {'native': [...], 'hourly': [...]} for every offer."""
    out: dict[tuple, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(lambda: {"native": [], "hourly": []}))
    for r in rows:
        native = representative_value(r)
        if native is None:
            continue
        bucket = out[group_key(r)][r.get("host", "")]
        bucket["native"].append(float(native))
        h = hourly_usd(r)
        if h is not None:
            bucket["hourly"].append(h)
    return out


def aggregate(rows: list[dict], floor: int = REPORTING_FLOOR) -> dict[tuple, dict]:
    groups = {}
    for key, hosts in host_values(rows).items():
        native = sorted(statistics.median(sorted(h["native"]))
                        for h in hosts.values() if h["native"])
        hourly = sorted(statistics.median(sorted(h["hourly"]))
                        for h in hosts.values() if h["hourly"])
        n_hosts = len(native)
        n_offers = sum(len(h["native"]) for h in hosts.values())
        tiers = Counter()
        entry = {
            "n_hosts": n_hosts,
            "n_offers": n_offers,
            "meets_floor": n_hosts >= floor,
            "native": _summary(native) if native else None,
            "hourly_usd": _summary(hourly) if hourly else None,
            "confidence": tiers,
        }
        groups[key] = entry
    return groups


def add_confidence(groups: dict, rows: list[dict]) -> None:
    for r in rows:
        key = group_key(r)
        if key in groups:
            groups[key]["confidence"][confidence_tier(r)] += 1


# --------------------------------------------------------------------------
# publish rate, per role, over the hosts actually read
# --------------------------------------------------------------------------

ROLES = ("CPO", "CTO", "CMO", "CFO", "COO", "CRO")

_ROLE_URL = {r: __import__("re").compile(r"(?<![a-z])" + r.lower() + r"(?![a-z])")
             for r in ROLES}


def _pages_read_int(row: dict) -> int:
    try:
        return int(float(row.get("pages_read") or 0))
    except (TypeError, ValueError):
        return 0


def publish_rate_by_role(rows: list[dict], published_rows: list[dict]) -> dict:
    """Hosts that yielded a publishable rate for a role, over hosts read for it.

    The denominator is not "every host in the seed list" - most of those were
    never fetched, and dividing by them measures the crawler, not the market.
    It is the hosts whose captured pages actually mention the role, taken from
    the coverage manifest the collector wrote at capture time.
    """
    read_hosts: set[str] = set()
    role_denominator: dict[str, set[str]] = {r: set() for r in ROLES}

    for r in rows:
        host = r.get("host", "")
        if r.get("outcome") == "error" or _pages_read_int(r) <= 0:
            continue
        read_hosts.add(host)
        try:
            manifest = json.loads(r.get("coverage_manifest") or "{}")
        except (ValueError, TypeError):
            manifest = {}
        urls = " ".join(
            [manifest.get("seed") or ""] + list(manifest.get("pages_read") or [])
        ).lower()
        for role in ROLES:
            if _ROLE_URL[role].search(urls):
                role_denominator[role].add(host)

    numerator: dict[str, set[str]] = {r: set() for r in ROLES}
    for r in published_rows:
        role = r.get("role", "")
        if role in numerator:
            numerator[role].add(r.get("host", ""))

    out = {
        "hosts_read": len(read_hosts),
        "definition": (
            "hosts with a publishable rate for the role, over hosts whose "
            "captured pages mention that role"
        ),
        "by_role": {},
    }
    for role in ROLES:
        den = len(role_denominator[role])
        num = len(numerator[role] & read_hosts)
        out["by_role"][role] = {
            "hosts_read_for_role": den,
            "hosts_published": num,
            "publish_pct": round(100 * num / den, 1) if den else None,
        }
    overall_num = len({r.get("host", "") for r in published_rows} & read_hosts)
    out["overall_pct"] = round(100 * overall_num / len(read_hosts), 1) if read_hosts else None
    out["hosts_published_any"] = overall_num
    return out


# --------------------------------------------------------------------------
# selection
# --------------------------------------------------------------------------

def publishable_rows(rows: list[dict]) -> list[dict]:
    """Evidence + plausibility, in scope, and the kept copy of a duplicate."""
    out = []
    for r in rows:
        if not is_priced(r):
            continue
        if r.get("scope_verdict") not in ("include", "", None):
            continue
        if (r.get("dup_keep") or "keep") != "keep":
            continue
        if not gate_pass(verify_row(r)):
            continue
        out.append(r)
    return out


def strict_rows(rows: list[dict]) -> list[dict]:
    return [r for r in publishable_rows(rows) if clean_pass(verify_row(r))]


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

OUT_FIELDS = [
    "role", "region", "model", "currency",
    "n_hosts", "n_offers", "meets_floor",
    "median_native", "p25_native", "p75_native",
    "median_hourly_usd", "p25_hourly_usd", "p75_hourly_usd",
    "confidence_high", "confidence_medium", "confidence_low",
]


def _record(key, g) -> dict:
    role, region, model = key
    native = g["native"] or {}
    hourly = g["hourly_usd"] or {}
    show = g["meets_floor"]
    return {
        "role": role, "region": region, "model": model,
        "currency": CURRENCY_OF_REGION.get(region, ""),
        "n_hosts": g["n_hosts"], "n_offers": g["n_offers"],
        "meets_floor": "yes" if show else "no",
        "median_native": native.get("median", "") if show else "",
        "p25_native": native.get("p25", "") if show else "",
        "p75_native": native.get("p75", "") if show else "",
        "median_hourly_usd": hourly.get("median", "") if show else "",
        "p25_hourly_usd": hourly.get("p25", "") if show else "",
        "p75_hourly_usd": hourly.get("p75", "") if show else "",
        "confidence_high": g["confidence"].get("high", 0),
        "confidence_medium": g["confidence"].get("medium", 0),
        "confidence_low": g["confidence"].get("low", 0),
    }


def headline(rows: list[dict]) -> dict:
    """Two headlines: the unified hourly axis, and US monthly for continuity."""
    def host_medians(subset, field):
        per_host: dict[str, list[float]] = defaultdict(list)
        for r in subset:
            v = hourly_usd(r) if field == "hourly" else representative_value(r)
            if v is None:
                continue
            per_host[r.get("host", "")].append(float(v))
        return sorted(statistics.median(sorted(v)) for v in per_host.values())

    all_hourly = host_medians(rows, "hourly")
    us_monthly = host_medians(
        [r for r in rows if r.get("currency") == "USD" and r.get("unit") == "per_month"],
        "native")

    out = {}
    for name, values, unit in (
        ("hourly_usd_all", all_hourly, "USD/hour"),
        ("us_monthly_native", us_monthly, "USD/month"),
    ):
        if not values:
            out[name] = None
            continue
        s = _summary(values)
        ci = bootstrap_ci(values)
        out[name] = {
            "unit": unit,
            "n_hosts": s["n"],
            "median": s["median"],
            "p25": s["p25"],
            "p75": s["p75"],
            "ci95_low": ci[0] if ci else None,
            "ci95_high": ci[1] if ci else None,
            "ci_method": f"percentile bootstrap over hosts, "
                         f"{BOOTSTRAP_ITERATIONS} iterations, seed {BOOTSTRAP_SEED}",
        }

    # The hourly headline carries a second interval, the one that also prices
    # in how little is known about the divisor. The sampling-only interval is
    # kept beside it, and labelled, because they answer different questions and
    # v2.1 published only the narrow one.
    joint = joint_bootstrap_ci(rows, divisor_pool())
    if out.get("hourly_usd_all") and joint:
        out["hourly_usd_all"]["ci95_sampling_only_low"] = out["hourly_usd_all"]["ci95_low"]
        out["hourly_usd_all"]["ci95_sampling_only_high"] = out["hourly_usd_all"]["ci95_high"]
        out["hourly_usd_all"]["ci95_low"] = joint["ci95_low"]
        out["hourly_usd_all"]["ci95_high"] = joint["ci95_high"]
        out["hourly_usd_all"]["ci_method"] = joint["method"]
        out["hourly_usd_all"]["divisor"] = {
            k: joint[k] for k in (
                "divisor_pool_hosts", "divisor_point",
                "divisor_ci95_low", "divisor_ci95_high",
                "hosts_on_the_default_divisor")
        }
    return out


def run(input_path: Path, out_path: Path | None,
        floor: int = REPORTING_FLOOR) -> dict:
    rows = list(csv.DictReader(input_path.open(newline="", encoding="utf-8")))
    priced = [r for r in rows if is_priced(r)]
    published = publishable_rows(rows)
    strict = strict_rows(rows)

    groups = aggregate(published, floor)
    add_confidence(groups, published)

    records = [_record(k, groups[k]) for k in sorted(groups)]
    if out_path:
        with out_path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=OUT_FIELDS, lineterminator="\n")
            w.writeheader()
            w.writerows(records)

    at_floor = [k for k, g in groups.items() if g["meets_floor"]]
    return {
        "rows_total": len(rows),
        "rows_priced": len(priced),
        "rows_published": len(published),
        "rows_strict_also": len(strict),
        "groups_total": len(groups),
        "groups_at_or_above_floor": len(at_floor),
        "groups_below_floor": len(groups) - len(at_floor),
        "floor": floor,
        "groups_shown": sorted("/".join(k) for k in at_floor),
        "headline": headline(published),
        "publish_rate": publish_rate_by_role(rows, published),
        "confidence_mix": dict(Counter(confidence_tier(r) for r in published)),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--floor", type=int, default=REPORTING_FLOOR)
    args = ap.parse_args(argv)
    json.dump(run(args.input, args.out, args.floor), sys.stdout,
              ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
