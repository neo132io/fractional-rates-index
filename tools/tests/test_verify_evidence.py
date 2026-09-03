#!/usr/bin/env python3
"""Tests for the deterministic evidence verifier.

The named cases are the failures the statistical audit found in v2.0
(STAT-QA-RATES-INDEX-20260903). Every one of them must be caught, and at least
one honest row must survive. Fixture rows are real records cut from
core-staging.csv md5 7a45392c27bfe11b1d80fae1a4b33872, the snapshot the audit
itself used.

    pytest tools/tests -q
"""

from __future__ import annotations

import csv
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import verify_evidence as V  # noqa: E402

FIXTURE = Path(__file__).with_name("fixtures") / "priced-fixture.csv"

REGION = {"USD": "US", "GBP": "UK", "EUR": "EU"}
MODEL = {"per_month": "Monthly", "per_day": "Day", "per_hour": "Hourly"}

csv.field_size_limit(2 ** 31 - 1)


# --------------------------------------------------------------------------
# fixture plumbing
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rows() -> list[dict]:
    with FIXTURE.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def pick(rows, host, price_low, price_high="", currency=None, unit=None):
    for r in rows:
        if r["host"] != host or r["price_low"] != price_low:
            continue
        if r["price_high"] != price_high:
            continue
        if currency and r["currency"] != currency:
            continue
        if unit and r["unit"] != unit:
            continue
        return r
    raise AssertionError(f"fixture row not found: {host} {price_low}-{price_high}")


def group_of(row):
    return (row["role"], REGION.get(row["currency"], ""), MODEL.get(row["unit"], ""))


# --------------------------------------------------------------------------
# the named failures from the audit
# --------------------------------------------------------------------------

def test_f3_phantom_eur_83_is_rejected(rows):
    """F3: CPO/EU/Hourly EUR 83.

    The extractor wrote its own answer, "EUR 83", into the evidence slot. The
    page itself says "EUR 100-320 per hour" - a different number in a different
    string. Grounding is co-located, so the bare restatement cannot certify an
    hourly rate and the row must not publish.
    """
    row = pick(rows, "fractional-csuite.com", "83", "", "EUR", "per_hour")
    v = V.verify_row(row)
    assert v.status == V.REJECT
    assert set(v.reasons) & set(V.GROUNDING_REASONS), v.reasons
    assert v.details["bare_money_quote"] == "price_low"
    # and the pooled-evidence reading, which is what let it through in v2.0,
    # is recorded rather than acted on
    assert v.details.get("grounded_only_when_pooled") == "price_low"


def test_f2_year_2026_read_as_a_euro_price_is_rejected(rows):
    """F2: CPO/EU/Day EUR 700-2026, midpoint EUR 1,363.

    "day rates in Europe in 2026 range from EUR 700 to EUR 1,900" - 2026 is the
    year, harvested as the top of the range.
    """
    row = pick(rows, "fractional-csuite.com", "700", "2026", "EUR", "per_day")
    v = V.verify_row(row)
    assert v.status == V.REJECT
    assert "year_read_as_price" in v.reasons
    assert v.details["year_fields"] == "price_high"


def test_year_guard_leaves_a_real_price_that_looks_like_a_year(rows):
    """A price of 2,025 is a price when the page writes it as money."""
    assert V.year_verdict(Decimal(2026), "in 2026 range from EUR 700") == "year"
    assert V.year_verdict(Decimal(2025), "$2,025 per month") == "price"
    assert V.year_verdict(Decimal(2025), "EUR 2025/mo") == "price"
    assert V.year_verdict(Decimal(1900), "EUR 1,900 a day") == "not_a_year"


def test_f27_prose_in_typed_evidence_slots(rows):
    """F27: evidence_json carries prose where a typed value belongs.

    The row below has the same sentence stuffed into price_high, currency and
    unit. The verifier does not trust the slot names - it reads the strings. On
    this snapshot the prose happens to contain the number, the symbol and the
    cadence, so the row is honest and passes; the defect is schema hygiene, not
    a wrong number. The synthetic twin underneath is the same shape with prose
    that does NOT support the typed value, and that one must be rejected.
    """
    prose_rows = [
        r for r in rows
        if '"currency": "$' in (r["evidence_json"] or "")
        and '"unit": "$' in (r["evidence_json"] or "")
    ]
    assert prose_rows, "fixture lost its F27-shaped row"

    forged = dict(prose_rows[0])
    forged["price_low"] = "4200"
    forged["price_high"] = ""
    forged["evidence_json"] = (
        '{"price_low": "Pricing is bespoke and set after a scoping call.",'
        ' "price_high": "Pricing is bespoke and set after a scoping call.",'
        ' "currency": "Pricing is bespoke and set after a scoping call.",'
        ' "unit": "Pricing is bespoke and set after a scoping call."}'
    )
    v = V.verify_row(forged)
    assert v.status == V.REJECT
    assert "value_not_in_evidence" in v.reasons
    assert "currency_not_in_evidence" in v.reasons
    assert "unit_not_in_evidence" in v.reasons


def test_a_clean_row_passes(rows):
    """USD 9,000 to 21,000 a month, quoted verbatim, provider's own price."""
    row = pick(rows, "512financial.com", "9000", "21000", "USD", "per_month")
    v = V.verify_row(row)
    assert v.status == V.PASS, v.reasons
    assert v.reasons == []
    assert v.details["representative_value"] == "15000"


def test_the_publishers_own_row_passes(rows):
    """saasfractionalcpo.com is inside its own sample (F21) and is held to the
    same rule as everyone else."""
    row = pick(rows, "saasfractionalcpo.com", "8000", "", "USD", "per_month")
    assert V.verify_row(row).status == V.PASS


def test_saas_subscription_is_quarantined_not_published(rows):
    """F15: USD 39 a month is a software plan, not an executive retainer."""
    row = pick(rows, "gigx.com", "39", "", "USD", "per_month")
    v = V.verify_row(row)
    assert v.status == V.QUARANTINE
    assert "implausible_below_floor" in v.reasons


def test_currency_must_be_in_the_quote(rows):
    """The same offer, captured twice.

    paqanyway.com yields two rows for one EUR 3,350 monthly price. One quote
    reads "EUR 3,350 per month" and publishes; the other reads "3,350 per
    month", where the currency was inferred rather than read, and must not.
    """
    quoted = [r for r in rows if r["host"] == "paqanyway.com"
              and '"price_low": "EUR 3,350 per month"' in r["evidence_json"]]
    inferred = [r for r in rows if r["host"] == "paqanyway.com"
                and '"price_low": "3,350 per month"' in r["evidence_json"]]
    assert len(quoted) == 1 and len(inferred) == 1

    assert V.verify_row(quoted[0]).status == V.PASS
    v = V.verify_row(inferred[0])
    assert v.status == V.REJECT
    assert "currency_not_in_evidence" in v.reasons


def test_unit_must_be_in_the_quote(rows):
    """"$127.50" alone cannot establish an hourly rate."""
    row = pick(rows, "kledigital.com", "127.5", "", "USD", "per_hour")
    v = V.verify_row(row)
    assert v.status == V.REJECT
    assert "unit_not_in_evidence" in v.reasons


def test_own_price_gate(rows):
    """Rule 6: publish only own + agree + strict."""
    base = pick(rows, "512financial.com", "9000", "21000", "USD", "per_month")
    assert V.own_price_gate(base) == []
    for field_, bad, expected in [
        ("context_verdict", "market", "context_not_own"),
        ("dual_agreement", "disagree:2offers", "dual_not_agree"),
        ("strict_pass", "false", "strict_pass_false"),
    ]:
        broken = dict(base)
        broken[field_] = bad
        v = V.verify_row(broken)
        assert v.status == V.REJECT
        assert "not_own_price" in v.reasons
        assert expected in v.details["own_price_gate_failed"]


# --------------------------------------------------------------------------
# unit-level rules
# --------------------------------------------------------------------------

@pytest.mark.parametrize("value,text,found", [
    (Decimal(8000), "we charge $8,000 per month", True),
    (Decimal(8000), "we charge $8000 per month", True),
    (Decimal(8000), "we charge $8k per month", True),
    (Decimal(8000), "we charge $8K per month", True),
    (Decimal(8000), "we charge EUR 8.000 per month", True),
    (Decimal(8000), "we charge $8 000 per month", True),
    (Decimal(8500), "we charge $8.5k per month", True),
    (Decimal(8000), "we charge $18,000 per month", False),   # substring guard
    (Decimal(8000), "we charge $80,000 per month", False),
    (Decimal(83), "EUR 100-320 per hour", False),            # the phantom
    (Decimal("127.5"), "$127.50", True),
    (Decimal(1_000_000), "$1M seed", True),
])
def test_format_variants(value, text, found):
    assert bool(V.find_value(value, text)) is found


@pytest.mark.parametrize("currency,text,found", [
    ("USD", "$5,000/mo", True),
    ("USD", "5,000 USD a month", True),
    ("GBP", "£1,500 a day", True),
    ("EUR", "€6,000/month", True),
    ("EUR", "3,350 per month", False),
    ("GBP", "$1,500 a day", False),
])
def test_currency_detection(currency, text, found):
    assert V.currency_in_text(currency, text) is found


@pytest.mark.parametrize("unit,text,found", [
    ("per_month", "$5,000 / month", True),
    ("per_month", "$5,000/mo", True),
    ("per_month", "monthly retainer of $5,000", True),
    ("per_month", "$5,000", False),
    ("per_hour", "$250 per hour", True),
    ("per_hour", "$250/hr", True),
    ("per_hour", "$250", False),
    ("per_day", "£1,000 day rate", True),
    ("per_day", "£1,000 daily", True),
    ("per_day", "£1,000", False),
])
def test_unit_detection(unit, text, found):
    assert V.unit_in_text(unit, text) is found


@pytest.mark.parametrize("value,unit,currency,verdict", [
    (Decimal(250), "per_hour", "USD", None),
    (Decimal(20), "per_hour", "USD", "implausible_below_floor"),
    (Decimal(2500), "per_hour", "USD", "implausible_above_ceiling"),
    (Decimal(1000), "per_day", "GBP", None),
    (Decimal(50), "per_day", "USD", "implausible_below_floor"),
    (Decimal(5000), "per_month", "USD", None),
    (Decimal(39), "per_month", "USD", "implausible_below_floor"),
    (Decimal(90000), "per_month", "USD", "implausible_above_ceiling"),
    # GBP 450/month is USD ~572 - above the floor only because of the coarse FX
    (Decimal(450), "per_month", "GBP", None),
])
def test_plausibility_bands(value, unit, currency, verdict):
    assert V.plausibility_check(value, unit, currency) == verdict


def test_bare_money_quote_detection():
    assert V.is_bare_money_quote("€83")
    assert V.is_bare_money_quote("$ 8,000")
    assert V.is_bare_money_quote("8000 USD")
    assert not V.is_bare_money_quote("$8,000 per month")
    assert not V.is_bare_money_quote("")


def test_population_definition(rows):
    """Every fixture row is in the priced population; the filter is the audit's."""
    assert all(V.is_priced(r) for r in rows)
    assert not V.is_priced({"price_low": "none-published", "price_high": "",
                            "currency": "USD", "unit": "per_month"})
    assert not V.is_priced({"price_low": "5000", "price_high": "",
                            "currency": "AUD", "unit": "per_month"})
    assert not V.is_priced({"price_low": "5000", "price_high": "",
                            "currency": "USD", "unit": "per_year"})


# --------------------------------------------------------------------------
# regression: the six groups reproduced digit for digit against the live page
# --------------------------------------------------------------------------

# RELEASE-V21-CHECKPOINT sec 6b confirmed these six groups reproduce exactly
# from the raw data. Freezing the verdict split makes any future change to the
# rules visible as a diff instead of a silent shift in what publishes.
GOLDEN = {
    ("CFO", "US", "Hourly"): {"PASS": 1, "REJECT": 10},
    ("CMO", "US", "Hourly"): {"PASS": 2, "REJECT": 6},
    ("COO", "US", "Hourly"): {"PASS": 6, "REJECT": 3},
    ("CPO", "US", "Hourly"): {"REJECT": 1},
    ("CTO", "UK", "Day"): {"PASS": 1, "REJECT": 5},
    ("CPO", "UK", "Day"): {"PASS": 2},
}


@pytest.mark.parametrize("group", sorted(GOLDEN))
def test_regression_on_reproduced_groups(rows, group):
    from collections import Counter
    counts = Counter(
        V.verify_row(r).status for r in rows if group_of(r) == group
    )
    assert dict(counts) == GOLDEN[group]


def test_regression_groups_are_all_present(rows):
    present = {group_of(r) for r in rows}
    assert set(GOLDEN) <= present
