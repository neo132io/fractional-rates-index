#!/usr/bin/env python3
"""The residuals PROF-STAT-QA-V211-ROUND2 left open on the file side.

Two items, both named in that report as non-blocking: N6, the one released CSV
that shipped without a byte-order mark, and N7, the prior-edition median that
the delta table still printed for groups that never cleared a reporting floor
in any edition. Neither changes a published figure. Both are locked here so a
later release cannot reopen them.

The tests run against the generator, not against the shipped v2.1.1 bytes. The
v2.1.1 artifacts stay as they were released; these fixes take effect with the
next release, which is what the project's own corrections policy requires.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

import generate_release as gr  # noqa: E402
import group_stats as gs  # noqa: E402

FIXTURE = Path(__file__).with_name("fixtures") / "priced-fixture.csv"


def group(n_hosts, median, hourly, meets_floor=None):
    if meets_floor is None:
        meets_floor = n_hosts >= gs.REPORTING_FLOOR
    return {
        "n_hosts": n_hosts, "n_offers": n_hosts, "meets_floor": meets_floor,
        "native": {"n": n_hosts, "median": median, "p25": median, "p75": median},
        "hourly_usd": {"n": n_hosts, "median": hourly, "p25": hourly,
                       "p75": hourly},
        "confidence": {},
    }


def prior(n, median):
    return {"median": median, "p25": median, "p75": median, "n": n,
            "publish": ""}


# --------------------------------------------------------------------------
# N6 - every released CSV opens in Excel, the groups file included
# --------------------------------------------------------------------------

def test_the_groups_file_is_written_with_a_byte_order_mark(tmp_path):
    """groups-v2.1.1.csv was the one file of nine that shipped without it.

    It carried no non-ASCII character, so nothing broke. It names every
    currency bucket in the index, though, and the first sub-floor group to
    reach the file with a pound or a euro sign in it would have opened as
    mojibake while the other eight files opened cleanly.
    """
    out = tmp_path / "groups.csv"
    gs.run(FIXTURE, out)
    assert out.read_bytes()[:3] == b"\xef\xbb\xbf"


def test_the_groups_file_still_reads_back_as_utf8(tmp_path):
    out = tmp_path / "groups.csv"
    gs.run(FIXTURE, out)
    with out.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    assert rows
    assert list(rows[0].keys())[0] == "role"


# --------------------------------------------------------------------------
# N7 - the floor applies to the comparison column too
# --------------------------------------------------------------------------

def test_a_prior_median_off_one_provider_is_not_reprinted():
    """The two figures v2.1 withdrew came straight back in the delta file.

    CPO/EU/Hourly at 83 euros was a phantom that appeared in no quote, and
    CPO/EU/Day at 1,363 euros was a range whose top was the year 2026. Both
    were single-provider v2.0 groups, both were withdrawn from the page, and
    both were still printed under a column called v2_median.
    """
    groups = {("CPO", "EU", "Hourly"): group(1, None, None, meets_floor=False)}
    v2 = {("CPO", "EU", "Hourly"): prior(1, 83.0)}
    row = gr.build_delta(groups, v2)[0]
    assert row["v2_median"] == ""
    assert row["v2_n"] == 1
    assert "prior median withheld" in row["note"]


def test_a_prior_median_that_cleared_the_floor_survives():
    """A reader who cited $5,000 for a fractional COO has to be able to find it.

    COO/US/Monthly held twelve providers in v2.0. That figure had standing when
    it was published, so the withdrawal is only meaningful if the number it
    withdraws is still visible beside it.
    """
    groups = {("COO", "US", "Monthly"): group(7, None, None, meets_floor=False)}
    v2 = {("COO", "US", "Monthly"): prior(12, 5000.0)}
    row = gr.build_delta(groups, v2)[0]
    assert row["v2_median"] == 5000.0
    assert row["v21_median_native"] == ""
    assert row["v21_published"] == "no"
    assert "prior median withheld" not in row["note"]


def test_a_delta_is_only_computed_between_two_standing_figures():
    """A percentage move against a hidden number is not a measurement."""
    groups = {("CTO", "UK", "Day"): group(9, 1200.0, 150.0)}
    v2 = {("CTO", "UK", "Day"): prior(5, 1000.0)}
    row = gr.build_delta(groups, v2)[0]
    assert row["v21_median_native"] == 1200.0
    assert row["v2_median"] == ""
    assert row["median_delta"] == ""
    assert row["median_delta_pct"] == ""


def test_a_delta_between_two_published_groups_is_unchanged():
    groups = {("CMO", "US", "Monthly"): group(26, 8250.0, 182.0)}
    v2 = {("CMO", "US", "Monthly"): prior(29, 7000.0)}
    row = gr.build_delta(groups, v2)[0]
    assert row["v2_median"] == 7000.0
    assert row["v21_median_native"] == 8250.0
    assert row["median_delta"] == 1250.0
    assert row["median_delta_pct"] == 17.9
    assert row["note"] == ""
