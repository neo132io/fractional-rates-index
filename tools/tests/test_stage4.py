#!/usr/bin/env python3
"""Tests for stage 4: FX locking, hourly normalisation, group statistics.

Everything here is offline. The FX tests build their own lock dict rather than
calling frankfurter, and the one test that does touch the network path asserts
that an unreachable API stops the release instead of inventing a rate.
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import fx_rates  # noqa: E402
import group_stats as gs  # noqa: E402
import retainer_hours as rh  # noqa: E402
import normalize_rates as nr  # noqa: E402
from verify_evidence import confidence_tier, gate_pass, verify_row  # noqa: E402


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def lock():
    return {
        "fx_lock_version": 1,
        "source": "test",
        "rate_date": "2026-09-03",
        "fetched_at_utc": "2026-09-03T12:00:00Z",
        "usd_per_unit": {"USD": "1", "GBP": "1.35", "EUR": "1.1615"},
    }


def row(**kw) -> dict:
    base = {
        "host": "example.com", "offer_seq": "0", "provider": "Example",
        "role": "CPO", "currency": "USD", "unit": "per_month",
        "price_low": "8000", "price_high": "", "hours_included": "",
        "evidence_json": json.dumps({"price_low": "$8,000 per month"}),
        "strict_pass": "true", "dual_agreement": "agree",
        "context_verdict": "own", "scope_verdict": "include", "dup_keep": "keep",
        "outcome": "extracted", "pages_read": "3", "coverage_manifest": "{}",
    }
    base.update(kw)
    return base


# --------------------------------------------------------------------------
# FX
# --------------------------------------------------------------------------

def test_usd_per_unit_derives_cross_rates_from_the_eur_payload():
    payload = {"base": "EUR", "date": "2026-09-03",
               "rates": {"USD": 1.1615, "GBP": 0.86055, "SEK": 11.1245}}
    table = fx_rates.usd_per_unit(payload, ["USD", "EUR", "GBP", "SEK"])
    assert table["USD"] == "1"
    assert Decimal(table["EUR"]) == Decimal("1.1615")
    # GBP: 1.1615 / 0.86055 = 1.3497...
    assert Decimal(table["GBP"]).quantize(Decimal("0.0001")) == Decimal("1.3497")
    assert Decimal(table["SEK"]) < Decimal("0.2")


def test_a_currency_the_ecb_does_not_publish_stops_the_release():
    payload = {"base": "EUR", "date": "2026-09-03", "rates": {"USD": 1.1615}}
    with pytest.raises(fx_rates.FxUnavailable) as exc:
        fx_rates.usd_per_unit(payload, ["USD", "XYZ"])
    assert "XYZ" in str(exc.value)


def test_an_unreachable_api_raises_rather_than_returning_a_guess():
    with pytest.raises(fx_rates.FxUnavailable):
        fx_rates.fetch_ecb_rates("https://127.0.0.1:9/latest", timeout=1)


def test_lock_filename_is_dated_by_the_ecb_rate_date(lock):
    assert fx_rates.lock_filename(lock) == "fx-lock-20260903.json"


def test_lock_round_trips_through_disk(tmp_path, lock):
    path = fx_rates.write_lock(lock, tmp_path)
    again = fx_rates.load_lock(path)
    assert fx_rates.rate_of(again, "GBP") == Decimal("1.35")


def test_a_currency_missing_from_the_lock_is_an_error_not_a_default(lock):
    with pytest.raises(fx_rates.FxUnavailable):
        fx_rates.rate_of(lock, "AUD")


def test_loading_a_non_lock_file_is_refused(tmp_path):
    p = tmp_path / "not-a-lock.json"
    p.write_text('{"hello": 1}', encoding="utf-8")
    with pytest.raises(fx_rates.FxUnavailable):
        fx_rates.load_lock(p)


# --------------------------------------------------------------------------
# retainer hours - the audit
# --------------------------------------------------------------------------

def test_the_audit_covers_fifty_one_readings_and_rejects_ten():
    d = rh.hours_distribution()
    assert d["audited_rows"] == 51
    assert d["rejected_rows"] == 10
    assert d["accepted_rows"] == 41


def test_the_three_lucrum_rows_are_rejected_as_an_sla_column():
    for seq in ("1", "2", "3"):
        hours, why = rh.declared_hours("lucrumconsulting.com", seq)
        assert hours is None
        assert "SLA" in why


def test_hours_per_week_convert_at_fifty_two_over_twelve():
    hours, why = rh.declared_hours("erikalpurcell.com", "0")
    assert hours == Decimal(10) * (Decimal(52) / Decimal(12))
    assert "hours_per_week" in why


def test_days_per_month_convert_at_eight_hours_a_day():
    hours, _ = rh.declared_hours("prodevel.co.uk", "1")
    assert hours == Decimal(32)


def test_a_stated_range_collapses_to_its_midpoint():
    hours, why = rh.declared_hours("solunapartners.com", "0")   # 10-15 hours/month
    assert hours == Decimal("12.5")
    assert "midpoint" in why


def test_an_open_ended_reading_is_read_at_its_floor():
    hours, why = rh.declared_hours("trailmarktech.com", "2")    # "20+ hrs/month"
    assert hours == Decimal(20)
    assert "floor" in why


def test_an_unaudited_row_has_no_reading_and_no_rejection_note():
    hours, why = rh.declared_hours("nowhere.example", "0")
    assert hours is None and why == ""


def test_the_default_is_the_measured_host_level_median():
    assert rh.default_hours_per_month() == Decimal("32.5")
    assert rh.default_hours_per_month() == Decimal(
        str(rh.hours_distribution()["per_host"]["median"]))


# --------------------------------------------------------------------------
# normalisation
# --------------------------------------------------------------------------

def test_an_hourly_rate_passes_through_untouched(lock):
    out = nr.normalize_row(
        row(unit="per_hour", price_low="250",
            evidence_json=json.dumps({"price_low": "$250 per hour"})),
        lock, Decimal("32.5"))
    assert out["rate_hourly_usd"] == "250.00"
    assert "per_hour as captured" in out["normalization_basis"]


def test_a_day_rate_divides_by_eight(lock):
    out = nr.normalize_row(
        row(unit="per_day", price_low="1600",
            evidence_json=json.dumps({"price_low": "$1,600 per day"})),
        lock, Decimal("32.5"))
    assert out["rate_hourly_usd"] == "200.00"
    assert "/ 8h" in out["normalization_basis"]


def test_a_retainer_uses_the_providers_own_hours_when_it_has_them(lock):
    out = nr.normalize_row(
        row(host="contineofy.com", offer_seq="1", price_low="6000"),
        lock, Decimal("32.5"))
    assert out["hours_per_month_used"] == "40"          # "40 hours per month"
    assert out["hours_source"] == "declared"
    assert out["rate_hourly_usd"] == "150.00"


def test_a_retainer_without_hours_uses_the_measured_default(lock):
    out = nr.normalize_row(row(price_low="6500"), lock, Decimal("32.5"))
    assert out["hours_per_month_used"] == "32.5"
    assert out["hours_source"] == "default"
    assert out["rate_hourly_usd"] == "200.00"


def test_a_rejected_hours_reading_falls_back_and_says_so(lock):
    out = nr.normalize_row(
        row(host="digitalapplied.com", offer_seq="0", currency="EUR",
            price_low="2000"),
        lock, Decimal("32.5"))
    assert out["hours_source"] == "default_after_rejected_reading"
    assert "units" in out["normalization_basis"]


def test_the_declared_and_default_paths_give_different_answers(lock):
    same_price = "6500"
    declared = nr.normalize_row(
        row(host="contineofy.com", offer_seq="1", price_low=same_price),
        lock, Decimal("32.5"))
    default = nr.normalize_row(row(price_low=same_price), lock, Decimal("32.5"))
    assert declared["rate_hourly_usd"] != default["rate_hourly_usd"]
    assert Decimal(declared["rate_hourly_usd"]) == Decimal("162.50")   # / 40h
    assert Decimal(default["rate_hourly_usd"]) == Decimal("200.00")    # / 32.5h


def test_currency_is_converted_at_the_locked_rate(lock):
    out = nr.normalize_row(
        row(currency="GBP", unit="per_hour", price_low="100",
            evidence_json=json.dumps({"price_low": "£100 per hour"})),
        lock, Decimal("32.5"))
    assert out["rate_hourly_usd"] == "135.00"
    assert out["fx_usd_per_unit"] == "1.35"
    assert "@2026-09-03" in out["normalization_basis"]


def test_a_range_normalises_from_its_midpoint(lock):
    out = nr.normalize_row(
        row(unit="per_hour", price_low="200", price_high="300",
            evidence_json=json.dumps({"price_low": "$200 to $300 per hour"})),
        lock, Decimal("32.5"))
    assert out["rate_hourly_usd"] == "250.00"
    assert out["normalization_basis"].startswith("midpoint(200,300)=250")


def test_the_basis_string_carries_the_whole_chain(lock):
    out = nr.normalize_row(row(currency="EUR", price_low="3000"),
                           lock, Decimal("32.5"))
    basis = out["normalization_basis"]
    for fragment in ("published(3000) EUR", "per_month / 32.5h",
                     "FX EUR 1.1615", "@2026-09-03", "USD/h"):
        assert fragment in basis


def test_an_unpriced_row_normalises_to_nothing(lock):
    out = nr.normalize_row(row(price_low="", price_high=""), lock, Decimal("32.5"))
    assert out["rate_hourly_usd"] == ""


def test_a_currency_the_index_does_not_report_in_is_left_alone(lock):
    # AUD is in the capture but outside the reported population, so the row is
    # not normalised at all. The guard that matters if that population ever
    # widens is fx_rates.rate_of, covered above.
    assert nr.normalize_row(row(currency="AUD"), lock,
                            Decimal("32.5"))["rate_hourly_usd"] == ""


def test_widening_the_reported_currencies_without_the_lock_raises(monkeypatch, lock):
    monkeypatch.setattr(nr, "is_priced", lambda r: True)
    with pytest.raises(fx_rates.FxUnavailable):
        nr.normalize_row(row(currency="AUD"), lock, Decimal("32.5"))


# --------------------------------------------------------------------------
# the publication gate
# --------------------------------------------------------------------------

def test_the_gate_ignores_the_two_confidence_checks():
    # v2.1.1: they are reported one by one and no longer sit under a
    # `not_own_price` label that says a check failed which never ran.
    r = row(strict_pass="false", dual_agreement="disagree")
    v = verify_row(r)
    assert v.status == "PASS"
    assert sorted(v.reasons) == ["dual_not_agree", "strict_pass_false"]
    assert "not_own_price" not in v.reasons
    assert gate_pass(v) is True


def test_a_price_that_is_not_the_providers_own_is_still_rejected():
    # The third sub-check is not a confidence signal. A market commentary is
    # not this provider's price, whatever the extraction flags say.
    v = verify_row(row(context_verdict="market_commentary"))
    assert v.status == "REJECT" and "context_not_own" in v.reasons
    assert gate_pass(v) is False


def test_the_gate_still_fails_a_row_that_is_out_of_band():
    # $100/month is below the 500 floor; it also has a confidence flag down,
    # and verdict precedence used to hide the quarantine. The gate must see it.
    r = row(price_low="100", strict_pass="false",
            evidence_json=json.dumps({"price_low": "$100 per month"}))
    v = verify_row(r)
    assert "strict_pass_false" in v.reasons
    assert v.quarantines == ["implausible_below_floor"]
    assert gate_pass(v) is False


def test_the_gate_fails_a_row_whose_value_is_not_in_the_quote():
    r = row(evidence_json=json.dumps({"price_low": "call us for pricing"}))
    assert gate_pass(verify_row(r)) is False


def test_confidence_tiers_read_the_two_pipeline_flags():
    assert confidence_tier(row()) == "high"
    assert confidence_tier(row(strict_pass="false")) == "medium"
    assert confidence_tier(row(dual_agreement="disagree")) == "medium"
    assert confidence_tier(row(strict_pass="false",
                               dual_agreement="disagree")) == "low"


# --------------------------------------------------------------------------
# group statistics
# --------------------------------------------------------------------------

def _group_rows(n_hosts: int, **kw) -> list[dict]:
    rows = []
    for i in range(n_hosts):
        rows.append(row(host=f"h{i}.example", price_low=str(1000 * (i + 1)),
                        rate_hourly_usd=str(10 * (i + 1)), **kw))
    return rows


def test_a_group_below_the_floor_is_counted_but_not_published():
    rows = _group_rows(7)
    groups = gs.aggregate(rows)
    key = ("CPO", "US", "Monthly")
    assert groups[key]["n_hosts"] == 7
    assert groups[key]["meets_floor"] is False
    record = gs._record(key, dict(groups[key], confidence={}))
    assert record["median_native"] == ""
    assert record["median_hourly_usd"] == ""
    assert record["n_hosts"] == 7


def test_a_group_at_the_floor_is_published():
    groups = gs.aggregate(_group_rows(8))
    key = ("CPO", "US", "Monthly")
    assert groups[key]["meets_floor"] is True
    record = gs._record(key, dict(groups[key], confidence={}))
    assert record["median_native"] == 4500.0
    assert record["median_hourly_usd"] == 45.0


def test_n_hosts_and_n_offers_are_counted_separately():
    rows = _group_rows(3)
    rows.append(row(host="h0.example", offer_seq="1", price_low="9999",
                    rate_hourly_usd="99"))
    groups = gs.aggregate(rows)
    g = groups[("CPO", "US", "Monthly")]
    assert g["n_hosts"] == 3
    assert g["n_offers"] == 4


def test_one_host_contributes_one_value_however_many_offers_it_lists():
    noisy = [row(host="loud.example", offer_seq=str(i), price_low="100000",
                 rate_hourly_usd="1000") for i in range(20)]
    quiet = _group_rows(8)
    groups = gs.aggregate(quiet + noisy)
    g = groups[("CPO", "US", "Monthly")]
    assert g["n_hosts"] == 9
    assert g["n_offers"] == 28
    assert g["native"]["median"] == 5000.0     # the 20 loud offers move it once


def test_the_group_table_carries_no_publish_percentage():
    assert not any("publish" in f for f in gs.OUT_FIELDS)


def test_publish_rate_is_reported_per_role_over_hosts_read():
    manifest = json.dumps({"seed": "https://a.example/fractional-cpo",
                           "pages_read": ["https://a.example/fractional-cpo"]})
    read_and_published = row(host="a.example", coverage_manifest=manifest)
    read_not_published = row(host="b.example", coverage_manifest=manifest)
    never_fetched = row(host="c.example", outcome="error", pages_read="0",
                        coverage_manifest=manifest)
    out = gs.publish_rate_by_role(
        [read_and_published, read_not_published, never_fetched],
        [read_and_published])
    assert out["hosts_read"] == 2
    assert out["by_role"]["CPO"] == {"hosts_read_for_role": 2,
                                     "hosts_published": 1, "publish_pct": 50.0}
    assert out["by_role"]["CTO"]["hosts_read_for_role"] == 0
    assert out["by_role"]["CTO"]["publish_pct"] is None


def test_the_bootstrap_interval_brackets_the_median_and_is_reproducible():
    values = [float(v) for v in range(100, 1100, 100)]
    lo, hi = gs.bootstrap_ci(values)
    assert lo <= 550.0 <= hi
    assert (lo, hi) == gs.bootstrap_ci(values)


def test_the_bootstrap_declines_to_report_an_interval_on_one_value():
    assert gs.bootstrap_ci([42.0]) is None


def test_the_headline_reports_both_axes_with_intervals():
    hl = gs.headline(_group_rows(10))
    assert hl["hourly_usd_all"]["unit"] == "USD/hour"
    assert hl["us_monthly_native"]["unit"] == "USD/month"
    assert hl["hourly_usd_all"]["ci95_low"] <= hl["hourly_usd_all"]["median"]
    assert hl["hourly_usd_all"]["median"] <= hl["hourly_usd_all"]["ci95_high"]


def test_publishable_rows_drop_the_out_of_scope_and_the_duplicate_copy():
    keep = row(host="k.example")
    out_of_scope = row(host="s.example", scope_verdict="exclude")
    dropped_twin = row(host="d.example", dup_keep="drop")
    assert gs.publishable_rows([keep, out_of_scope, dropped_twin]) == [keep]


# --------------------------------------------------------------------------
# release assembly
# --------------------------------------------------------------------------

import generate_release as gr  # noqa: E402


def test_a_double_encoded_currency_symbol_is_repaired():
    assert gr.repair_mojibake("Â£1,500 /month") == "£1,500 /month"
    assert gr.repair_mojibake("â‚¬2,000 / month") == "€2,000 / month"


def test_a_clean_quote_is_untouched():
    for s in ("£1,500 /month", "$8,000 per month", ""):
        assert gr.repair_mojibake(s) == s


def test_a_repair_that_would_change_a_digit_is_refused():
    weird = "Â£1,500"
    assert gr.repair_mojibake(weird).count("1") == weird.count("1")


def test_an_unrepairable_string_is_left_exactly_as_captured():
    s = "Ã¿\udcff broken"
    assert gr.repair_mojibake(s) == s
