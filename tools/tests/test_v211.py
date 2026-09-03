#!/usr/bin/env python3
"""v2.1.1 - the repairs the adversarial statistical review of 2026-09-03 required.

Every test here is named after the case in PROF-STAT-QA-V21 that it locks down.
Where the review's own arithmetic and this pipeline's disagree, the test says
which and why: the review read a page's text by eye and got two of the twenty-nine
records wrong in the other direction, and both of those readings are frozen here
too, so the disagreement is a decision on the record and not a drift.
"""

from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import generate_release as gr  # noqa: E402
import group_stats as gs  # noqa: E402
import hours_evidence as he  # noqa: E402
import normalize_rates as nr  # noqa: E402
import retainer_hours as rh  # noqa: E402
import verify_evidence as V  # noqa: E402

csv.field_size_limit(2 ** 31 - 1)


def offer(**kw):
    """A priced monthly row, with whatever evidence the test needs."""
    base = {
        "host": "example.com", "offer_seq": "0", "provider": "Example",
        "role": "CTO", "currency": "USD", "unit": "per_month",
        "price_low": "8000", "price_high": "",
        "hours_included": "", "cadence_published": "none-published",
        "context_verdict": "owned", "dual_agreement": "agree",
        "strict_pass": "true", "scope_verdict": "include", "dup_keep": "keep",
        "evidence_json": json.dumps({"price_low": "$8,000 per month"}),
    }
    base.update(kw)
    return base


def ctx_for(rows):
    return he.index_by_host(rows)[rows[0]["host"]]


# --------------------------------------------------------------------------
# C1 - the divisor now has to come out of the evidence
# --------------------------------------------------------------------------

@pytest.mark.parametrize("text,basis,hours", [
    # the four conventions a retainer page actually uses
    ("Momentum £4,799 /month 1 Day/Week", "days_per_week", Decimal("34.6666666667")),
    ("Breakthrough £9,599 /month 2 Days/Week", "days_per_week", Decimal("69.3333333333")),
    ("Remote retainers from £2,499 /month (2 days/month)", "days_per_month", Decimal(16)),
    ("10-20 hrs/week", "hours_per_week", Decimal("65")),
    ("4 to 8 hours per month", "hours_per_month", Decimal(6)),
    # ranges take their midpoint, the same rule prices already follow
    ("A typical engagement of 1 to 4 days per week", "days_per_week",
     Decimal("86.6666666667")),
    ("Offer two Fractional CPO Intensive $15,000 /mo 3 to 4 days a week",
     "days_per_week", Decimal("121.3333333333")),
    # an open-ended figure is read at its floor: fewer hours, higher rate,
    # the conservative direction for a rate index
    ("3+ days/week", "days_per_week", Decimal(104)),
    # non-English pages are read too; the index reports in EUR and GBP
    ("2 Tage pro Woche", "days_per_week", Decimal("69.3333333333")),
    ("10 heures par semaine", "hours_per_week", Decimal("43.3333333333")),
])
def test_a_time_commitment_is_read_and_converted(text, basis, hours):
    readings = he.scan_text(text)
    assert len(readings) == 1, readings
    assert readings[0].basis == basis
    assert abs(readings[0].hours_per_month - hours) < Decimal("0.001")


@pytest.mark.parametrize("text", [
    "14-day free trial",
    "engagements are month-to-month with 30 days notice",
    "Most engagements require a minimum 3-month initial commitment",
    "A typical engagement works out at £3,600 to £19,200 per month",
    "$200 per hour",
    "Two to three week deep-dive",
    # deliberately not read: converting needs a days-per-month assumption the
    # page does not give. The manual audit made the same call on talpaperin.com
    "about 4-5 hours a day",
])
def test_what_is_not_a_time_commitment(text):
    assert he.scan_text(text) == []


def test_a_string_copied_onto_every_offer_describes_the_host_not_the_offer():
    """talpaperin.com carries one cadence on six offers, including the $22,000 one."""
    rows = [
        offer(offer_seq=str(i), price_low=p,
              cadence_published="About 3 hours a week Advisor $2,000 /mo",
              host="talpaperin.example")
        for i, p in enumerate(["2000", "6000", "22000"])
    ]
    ctx = ctx_for(rows)
    assert he.read_offer_hours(rows[2], ctx).status == he.NO_READING


def test_an_offers_own_quote_is_read():
    """saasfractionalcpo.com offer two: the case with an absolute ground truth."""
    rows = [
        offer(offer_seq="0", price_low="8000", host="saasfractionalcpo.example",
              evidence_json=json.dumps({
                  "price_low": "$8,000 /mo",
                  "cadence_published": "25 hours a month",
                  "offering_type": "Offer one Fractional CPO Partner $8,000 /mo "
                                   "25 hours a month. 3 month minimum.",
              })),
        offer(offer_seq="1", price_low="15000", host="saasfractionalcpo.example",
              evidence_json=json.dumps({
                  "price_low": "$15,000 /mo",
                  "cadence_published": "25 hours a month",
                  "offering_type": "Offer two Fractional CPO Intensive $15,000 /mo "
                                   "3 to 4 days a week. 3 month minimum.",
              })),
    ]
    ctx = ctx_for(rows)
    out = he.read_offer_hours(rows[1], ctx)
    assert out.status == he.FOUND
    assert out.reading.quote == "3 to 4 days a week"
    assert abs(out.hours - Decimal("121.3333333333")) < Decimal("0.001")
    # and offer one's own allowance did not leak onto offer two
    assert "25 hours" not in out.reading.quote


def test_a_host_wide_cadence_is_used_only_when_there_is_one_retainer_to_attach_it_to():
    """fractionalcoo.net yes, contineofy.com no."""
    one_product = [
        offer(host="one.example", offer_seq=str(i),
              price_low="15000", price_high="40000",
              evidence_json=json.dumps({
                  "price_low": "$15K-$40K/month",
                  "cadence_published": "2-3 days per week"}))
        for i in (0, 5)
    ]
    ctx = ctx_for(one_product)
    out = he.read_offer_hours(one_product[0], ctx)
    assert out.status == he.FOUND_HOST_CADENCE
    assert abs(out.hours - Decimal("86.6666666667")) < Decimal("0.001")

    tiers = [
        offer(host="tiers.example", offer_seq=str(i), price_low=p,
              evidence_json=json.dumps({
                  "price_low": f"${p}/mo",
                  "hours_included": h,
                  "cadence_published": "20 hours per month"}))
        for i, (p, h) in enumerate([("3500", "20 hours per month"),
                                    ("6000", "40 hours per month"),
                                    ("12000", "")])
    ]
    ctx = ctx_for(tiers)
    # tier one's allowance must not price tier three
    assert he.read_offer_hours(tiers[2], ctx).status == he.NO_READING


def test_the_manual_audit_outranks_the_scan():
    """marketingeyedallas.com's "3 Hours Per Month" belongs to a bundled intern."""
    r = offer(host="marketingeyedallas.com", offer_seq="0",
              evidence_json=json.dumps({
                  "price_low": "$8,000 per month",
                  "hours_included": "Free 3 Hours Per Month Intern Graphic "
                                    "Design & Web"}))
    out = he.read_offer_hours(r, ctx_for([r]))
    assert out.status == he.AUDIT_REJECTED
    assert he.scan_text("Free 3 Hours Per Month Intern") != []   # it does match


def test_two_commitments_in_one_offer_fall_back_and_say_so():
    r = offer(host="ambiguous.example",
              evidence_json=json.dumps({
                  "price_low": "$500/mo",
                  "offering_type": "1 day/week",
                  "cadence_published": "3 days a week"}))
    out = he.read_offer_hours(r, ctx_for([r]))
    assert out.status == he.AMBIGUOUS
    assert "more than one commitment" in out.note


def test_our_own_record_matches_the_live_page():
    """The one row in the index with an absolute ground truth.

    saasfractionalcpo.com/ says "$8,000 /mo 25 hours a month". v2.1 published
    22.5 hours, an 11% error on the row we control completely.
    """
    hours, _ = rh.declared_hours("saasfractionalcpo.com", "0")
    assert hours == Decimal(25)


# --------------------------------------------------------------------------
# rule 7 - the gate that keeps the divisor honest
# --------------------------------------------------------------------------

def test_a_row_that_ignores_its_own_stated_hours_is_quarantined():
    r = offer(hours_evidence_hours="86.67", hours_per_month_used="32.5",
              rate_hourly_usd="246.15")
    v = V.verify_row(r)
    assert "hours_contradict_evidence" in v.quarantines
    assert V.gate_pass(v) is False


def test_the_hours_gate_is_silent_before_normalisation():
    assert V.verify_row(offer()).quarantines == []


def test_the_hours_gate_passes_when_the_divisor_is_the_stated_one():
    r = offer(hours_evidence_hours="86.67", hours_per_month_used="86.67",
              rate_hourly_usd="186.88")
    assert V.gate_pass(V.verify_row(r)) is True


# --------------------------------------------------------------------------
# M5 - the plausibility band on the derived axis
# --------------------------------------------------------------------------

@pytest.mark.parametrize("hourly,reason", [
    ("15.38", "implausible_hourly_derived_below_floor"),
    ("1538.46", "implausible_hourly_derived_above_ceiling"),
])
def test_a_derived_rate_outside_the_band_is_quarantined(hourly, reason):
    """v2.1 filtered "$20 an hour" as implausible and published $15.38 derived."""
    v = V.verify_row(offer(rate_hourly_usd=hourly))
    assert reason in v.quarantines
    assert V.gate_pass(v) is False


def test_a_derived_rate_inside_the_band_publishes():
    assert V.gate_pass(V.verify_row(offer(rate_hourly_usd="246.15"))) is True


def test_the_band_is_the_same_one_rule_5_uses():
    assert V.PLAUSIBILITY["per_hour"] == (Decimal(25), Decimal(1000))


# --------------------------------------------------------------------------
# H3 - the verdict label says what was checked
# --------------------------------------------------------------------------

def test_the_two_confidence_checks_do_not_produce_a_reject():
    v = V.verify_row(offer(strict_pass="false", dual_agreement="disagree"))
    assert v.status == "PASS"
    assert "not_own_price" not in v.reasons
    assert set(v.reasons) == {"strict_pass_false", "dual_not_agree"}


def test_a_record_carries_the_recomputed_verdict_not_the_snapshots():
    r = offer(strict_pass="false",
              verify_verdict="REJECT", verify_reasons="not_own_price",
              rate_hourly_usd="246.15", value_published="8000")
    rec = gr.build_records([r])[0]
    assert rec["evidence_verdict"] == "PASS"
    assert rec["evidence_reasons"] == ""
    assert rec["confidence_reasons"] == "strict_pass_false"
    assert "verify_verdict" not in rec


# --------------------------------------------------------------------------
# H1 - the interval that carries the divisor's uncertainty
# --------------------------------------------------------------------------

def test_the_joint_interval_is_wider_than_the_sampling_one():
    rows = [
        offer(host=f"h{i}.example", price_low=str(p),
              rate_hourly_usd=f"{p / 32.5:.2f}",
              hours_per_month_used="32.5", hours_source="default")
        for i, p in enumerate(range(3000, 13000, 500))
    ]
    pool = gs.divisor_pool()
    sampling = gs.bootstrap_ci(sorted(float(r["rate_hourly_usd"]) for r in rows))
    joint = gs.joint_bootstrap_ci(rows, pool)
    assert joint is not None
    assert joint["ci95_high"] - joint["ci95_low"] > sampling[1] - sampling[0]
    assert joint["divisor_point"] == float(rh.default_hours_per_month())


def test_the_divisor_pool_is_the_sample_the_default_is_estimated_from():
    pool = gs.divisor_pool()
    import statistics
    assert len(pool) == len(rh.host_level_hours())
    assert statistics.median(pool) == float(rh.default_hours_per_month())


def test_a_row_with_its_own_hours_is_not_repriced_by_the_bootstrap():
    """Only the retainers that publish nothing move when the divisor moves."""
    rows = [
        offer(host="a.example", rate_hourly_usd="200", unit="per_hour"),
        offer(host="b.example", rate_hourly_usd="100",
              hours_per_month_used="50", hours_source="evidence_offer"),
    ]
    joint = gs.joint_bootstrap_ci(rows, gs.divisor_pool())
    assert joint["hosts_on_the_default_divisor"] == 0


# --------------------------------------------------------------------------
# M7 - the reporting floor holds in every file of the release
# --------------------------------------------------------------------------

def test_the_delta_file_carries_no_figure_for_a_group_below_the_floor():
    groups = {
        ("CPO", "UK", "Monthly"): {
            "n_hosts": 1, "n_offers": 1, "meets_floor": False,
            "native": {"n": 1, "median": 12000.0, "p25": 12000.0, "p75": 12000.0},
            "hourly_usd": {"n": 1, "median": 498.36, "p25": 498.36, "p75": 498.36},
            "confidence": {},
        },
    }
    row = gr.build_delta(groups, {})[0]
    assert row["v21_median_native"] == ""
    assert row["v21_median_hourly_usd"] == ""
    assert row["v21_published"] == "no"
    assert "below the n>=8 reporting floor" in row["note"]


# --------------------------------------------------------------------------
# M6, M11, L1 - the display facts the page got wrong
# --------------------------------------------------------------------------

def test_the_contract_separates_group_entries_from_unique_providers():
    """"120 PROVIDERS" was a sum of per-group counts; seven hosts sat in two groups."""
    metrics = _release_metrics()
    portal = metrics["portal"]
    assert portal["table_hosts_unique"] <= portal["table_group_entries"]
    assert portal["table_group_entries"] == portal["table_records"]


def test_the_contract_carries_the_currency_list_as_its_own_fact():
    """"1 currencies (USD, GBP, EUR)" came from binding the caption to `regions`."""
    metrics = _release_metrics()
    portal = metrics["portal"]
    assert portal["currencies_count"] == len(portal["currencies"]) == 3
    assert portal["currencies_count"] != portal["regions"]


def test_the_quartile_is_published_unrounded_as_well():
    metrics = _release_metrics()
    portal = metrics["portal"]
    assert portal["us_monthly_p25_exact"] >= portal["us_monthly_p25"]


# --------------------------------------------------------------------------
# the release itself
# --------------------------------------------------------------------------

RELEASE = Path("D:/index-v2/staging/release-v2.1.1")


def _release_rows(name):
    if not (RELEASE / name).exists():
        pytest.skip("the v2.1.1 release has not been generated")
    with (RELEASE / name).open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _release_metrics():
    path = RELEASE / "portal-metrics-v2.1.1.json"
    if not path.exists():
        pytest.skip("the v2.1.1 release has not been generated")
    return json.loads(path.read_text(encoding="utf-8"))


def test_no_published_record_contradicts_its_own_stated_hours():
    """The whole point of C1, checked on the shipped file."""
    bad = [r for r in _release_rows("records-v2.1.1.csv")
           if r["hours_evidence_quote"]
           and r["hours_source"].startswith("default")]
    assert bad == []


def test_the_named_cases_from_the_review_are_fixed():
    records = {(r["host"], r["price_low"], r["unit"]): r
               for r in _release_rows("records-v2.1.1.csv")}

    # PROF-STAT-QA-V21 C1: £12,000 midpoint on "1 to 4 days per week"
    cto = records[("ctoondemand.co.uk", "8000", "per_month")]
    assert cto["hours_per_month_used"] == "86.67"
    assert cto["hours_evidence_quote"] == "1 to 4 days per week"
    assert abs(float(cto["rate_hourly_usd"]) - 186.88) < 0.02

    # PROF-STAT-QA-V21 C3: our own $15,000 offer, "3 to 4 days a week"
    ours = records[("saasfractionalcpo.com", "15000", "per_month")]
    assert ours["hours_per_month_used"] == "121.33"
    assert abs(float(ours["rate_hourly_usd"]) - 123.63) < 0.02

    # and our $8,000 offer at the 25 hours the live page states
    ours8 = records[("saasfractionalcpo.com", "8000", "per_month")]
    assert ours8["hours_per_month_used"] == "25"
    assert abs(float(ours8["rate_hourly_usd"]) - 320.00) < 0.02


def test_where_this_pipeline_and_the_review_disagree_it_is_on_purpose():
    """Two of the review's twenty-nine readings are rejected, with reasons.

    golosnichenko.com  the review took "3-5 days per week", which the page
                       attaches to an Executive CTO tier priced "Custom". The
                       $4,400 retainer's own cadence line says ~6 hours a week.
    contineofy.com     the review took "20 hours per month", which is tier
                       one's allowance on a five-tier page; the $12,000 tier
                       publishes no hours of its own.
    """
    records = {(r["host"], r["price_low"]): r
               for r in _release_rows("records-v2.1.1.csv")}
    gol = records[("golosnichenko.com", "4400")]
    assert gol["hours_per_month_used"] == "26"
    assert gol["hours_evidence_quote"] == "6 hours per week"

    con = records[("contineofy.com", "12000")]
    assert con["hours_source"] == "default"
    assert con["hours_evidence_quote"] == ""


def test_the_quarantine_file_names_every_row_the_band_removed():
    metrics = _release_metrics()
    rows = _release_rows("quarantine-v2.1.1.csv")
    assert len(rows) == metrics["quarantine"]["records"]
    assert all("implausible" in r["reason"] for r in rows)
    published = {(r["host"], r["price_low"], r["unit"])
                 for r in _release_rows("records-v2.1.1.csv")}
    assert not any((r["host"], r["price_low"], r["unit"]) in published
                   for r in rows)


def test_no_published_record_sits_outside_the_hourly_band():
    for r in _release_rows("records-v2.1.1.csv"):
        assert 25.0 <= float(r["rate_hourly_usd"]) <= 1000.0, r["host"]


def test_no_record_carries_a_reject_label_for_a_check_it_passed():
    for r in _release_rows("records-v2.1.1.csv"):
        assert r["evidence_verdict"] == "PASS", (r["host"], r["evidence_reasons"])
        assert r["evidence_reasons"] == ""


def test_the_release_files_open_correctly_in_excel():
    """112 pound and euro signs; a BOM-less UTF-8 CSV renders them as mojibake."""
    for name in ("records-v2.1.1.csv", "portal-rates-v2.1.1.csv",
                 "delta-vs-v2.1-v2.1.1.csv", "quarantine-v2.1.1.csv"):
        assert (RELEASE / name).read_bytes()[:3] == b"\xef\xbb\xbf", name


def test_the_metrics_carry_a_restatement_notice_with_numbers_in_it():
    metrics = _release_metrics()
    changes = metrics["changes_vs_previous"]
    assert changes["previous_version"] == "v2.1"
    assert changes["headline"]["hourly_usd_median"]["before"] == 169.23
    for entry in changes["published_group_medians_moved"]:
        assert entry["median_before"] != entry["median_now"]
        assert entry["change_pct"] != 0


def test_the_headline_publishes_both_intervals_and_labels_them():
    metrics = _release_metrics()
    h = metrics["headline"]["hourly_usd_all"]
    assert h["ci95_low"] < h["ci95_sampling_only_low"]
    assert h["ci95_high"] > h["ci95_sampling_only_high"]
    assert h["divisor"]["divisor_point"] == 32.5


def test_the_publisher_says_where_it_sits_in_its_own_index():
    metrics = _release_metrics()
    text = metrics["quality_flags"]["self_inclusion"]
    assert "percentile" in text
    assert "25 hours" in text and "121.33 hours" in text


# --------------------------------------------------------------------------
# PROF-STAT-QA-V211-ROUND2, the closed list of publication blockers
# --------------------------------------------------------------------------


def test_a_group_that_fell_below_the_floor_is_named_in_the_restatement():
    """N1. COO/US/Monthly went from n=8 at $3,938 to n=7 and out of the index.

    A delta table measures what moved, so it cannot see a group that is simply
    gone. Without this block the notice listed six of the previous edition's
    seven published groups and said nothing about the seventh.
    """
    changes = _release_metrics()["changes_vs_previous"]
    withdrawn = changes["published_group_withdrawn"]
    assert withdrawn, "no withdrawal block in the restatement notice"
    coo = [w for w in withdrawn if w["group"] == "COO/US/Monthly"]
    assert coo, [w["group"] for w in withdrawn]
    assert coo[0]["n_hosts_before"] == 8 and coo[0]["n_hosts_now"] == 7
    assert coo[0]["median_before"] == 3938.0
    assert coo[0]["median_now"] is None
    assert "reporting floor" in coo[0]["reason"]


def test_every_group_published_last_edition_is_accounted_for():
    """N1, the general rule. Moved plus held plus withdrawn has to be all of them."""
    changes = _release_metrics()["changes_vs_previous"]
    counted = (len(changes["published_group_medians_moved"])
               + len(changes["published_group_medians_unchanged"])
               + len(changes["published_group_withdrawn"]))
    assert counted == changes["groups_accounted_for"]
    assert counted == changes["groups_published_in_previous_edition"]


def test_a_group_with_no_corroborated_record_is_flagged_for_the_table():
    """H2. The confidence tier was bought with a veto; it has to be visible."""
    flagged = _release_metrics()["quality_flags"]["groups_without_high_confidence"]
    names = {g["group"] for g in flagged}
    assert "(none)/US/Hourly" in names, names
    for g in flagged:
        assert g["high"] == 0
        assert g["medium"] + g["low"] == g["n_hosts"] or g["n_hosts"] > 0


def test_the_group_table_carries_the_flag_column_the_theme_reads():
    """H2, on the artifact the template actually loads."""
    rows = _release_rows("portal-rates-v2.1.1.csv")
    assert "confidence_flag" in rows[0]
    for r in rows:
        expected = "no_high_confidence_record" if int(r["confidence_high"]) == 0 else ""
        assert r["confidence_flag"] == expected, r["role"]


def test_the_verifiability_claim_is_said_on_its_coverage_not_on_its_rule():
    """N2. Rule 7 stops a record contradicting itself. It does not quote 32.5.

    Four published monthly records in five divide by the measured default, so a
    blanket "every number is found word for word in a quote" is false of the
    USD-per-hour column.
    """
    gate = _release_metrics()["methodology"]["publication_gate"]
    assert "Every published number is found word for word" not in gate
    assert "measured default of 32.5" in gate
    assert "not about the derived hourly figure" in gate

    rows = _release_rows("records-v2.1.1.csv")
    monthly = [r for r in rows if r["unit"] == "per_month"]
    on_default = [r for r in monthly if r["hours_source"].startswith("default")]
    assert len(on_default) / len(monthly) > 0.75


def test_the_acceptance_gate_reads_a_record_file_that_carries_a_bom():
    """N3, and the regression that hid inside it.

    v2.1.1 gave the record files a BOM for Excel. Read as plain utf-8 the first
    column becomes "\ufeffhost", every snapshot lookup misses, and the gate
    quietly falls back to checking the crawl seed instead of the evidence page.
    That scored the release at 73.5 percent on pages it was never meant to read.
    """
    import acceptance_gate as ag

    path = RELEASE / "records-v2.1.1.csv"
    if not path.exists():
        pytest.skip("the v2.1.1 release has not been generated")
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert "host" in rows[0]
    assert len(ag.hours_evidence_rows(rows)) == 20


@pytest.mark.parametrize("quote,text,expected", [
    ("1-2 days/week", "commit to 1 \u2013 2 days/week", True),
    ("1-2 days/week", "1-2 days/week", True),
    ("10-20 hrs/week", "roughly 10-20 hrs/week", True),
    ("6 hours per week", "just 6  hours per week", True),
    ("1 Day/Week", "the 1 day/week tier", True),
    ("3+ days/week", "we want 3+ days/week", True),
    ("1-2 days/week", "1 to 2 days/week", False),
    ("2 days/month", "2 days per month", False),
])
def test_the_hours_quote_matcher_allows_only_whitespace_and_dash_variation(
        quote, text, expected):
    """N3. Word for word means word for word; the page may re-hyphenate."""
    import acceptance_gate as ag
    assert bool(ag.quote_pattern(quote).search(text)) is expected


def test_the_acceptance_gate_ran_on_this_release_and_passed():
    """N3. M4 stood open because no gate report existed for this edition."""
    path = RELEASE / "acceptance-gate-v2.1.1.json"
    if not path.exists():
        pytest.skip("the v2.1.1 acceptance gate has not been run")
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["verdict"] == "PASS"
    assert report["accuracy_on_reachable"] >= report["threshold"]
    hours = report["hours_evidence_gate"]
    assert hours["records"] == 20, "the hours citations are checked in full"
    assert hours["reachable"] == hours["records"]
    assert hours["passed"] == hours["records"]
