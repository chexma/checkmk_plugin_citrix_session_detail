#!/usr/bin/env python3
"""Tests for Citrix Session Detail check plugin."""

from cmk.agent_based.v2 import Metric, Result, State

from cmk_addons.plugins.citrix_session_detail.agent_based.citrix_session_detail import (
    check_citrix_session_count,
    discover_citrix_session_count,
    parse_citrix_session_detail,
)

# Raw agent output as whitespace-split string_table (default separator)
FLAT_STRING_TABLE = [
    ["mydomain.local\\UserA", "Active", "mydomain.local\\server-citrix1", "24.03.2026", "07:38:17"],
    [
        "mydomain.local\\UserB",
        "Disconnected",
        "mydomain.local\\server-citrix1",
        "10.03.2026",
        "14:56:30",
    ],
    [
        "mydomain.local\\UserC",
        "Active",
        "mydomain.local\\server-citrix2",
        "24.03.2026",
        "14:53:10",
    ],
    [
        "mydomain.local\\UserD",
        "Active",
        "mydomain.local\\server-citrix2",
        "24.03.2026",
        "15:45:42",
    ],
    [
        "mydomain.local\\UserE",
        "Active",
        "mydomain.local\\server-citrix2",
        "24.03.2026",
        "15:55:12",
    ],
    [
        "mydomain.local\\UserF",
        "Active",
        "mydomain.local\\server-citrix3",
        "24.03.2026",
        "15:28:07",
    ],
    [
        "mydomain.local\\UserG",
        "Disconnected",
        "mydomain.local\\server-citrix3",
        "24.03.2026",
        "15:56:14",
    ],
    ["mydomain.local\\UserH", "Active", "mydomain.local\\server-citrix3"],
    [
        "mydomain.local\\UserI",
        "Active",
        "mydomain.local\\server-citrix3",
        "24.03.2026",
        "09:48:26",
    ],
    ["mydomain.local\\UserJ", "Active", "mydomain.local\\server-citrix3"],
]

DEFAULT_PARAMS = {
    "active_levels": ("fixed", (20, 30)),
    "disconnected_levels": ("fixed", (5, 10)),
    "disconnected_age_levels": ("fixed", (86400.0, 259200.0)),
}


class TestParse:
    def test_parse_flat_format(self):
        result = parse_citrix_session_detail(FLAT_STRING_TABLE)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 10

    def test_parse_username_extraction(self):
        result = parse_citrix_session_detail(FLAT_STRING_TABLE)
        usernames = [s["username"] for s in result]
        assert "UserA" in usernames
        assert "UserB" in usernames
        assert "UserJ" in usernames

    def test_parse_states(self):
        result = parse_citrix_session_detail(FLAT_STRING_TABLE)
        states = {s["username"]: s["state"] for s in result}
        assert states["UserA"] == "Active"
        assert states["UserB"] == "Disconnected"

    def test_parse_idle_since(self):
        result = parse_citrix_session_detail(FLAT_STRING_TABLE)
        sessions = {s["username"]: s for s in result}
        assert sessions["UserA"]["idle_since"] is not None
        assert sessions["UserB"]["idle_since"] is not None

    def test_parse_missing_idle_since(self):
        result = parse_citrix_session_detail(FLAT_STRING_TABLE)
        sessions = {s["username"]: s for s in result}
        assert sessions["UserH"]["idle_since"] is None
        assert sessions["UserJ"]["idle_since"] is None

    def test_parse_empty(self):
        assert parse_citrix_session_detail([]) is None

    def test_parse_short_lines(self):
        assert parse_citrix_session_detail([["only_one_field"]]) is None


class TestDiscovery:
    def test_discover_service(self):
        section = parse_citrix_session_detail(FLAT_STRING_TABLE)
        services = list(discover_citrix_session_count(section))
        assert len(services) == 1
        assert services[0].item is None

    def test_discover_empty(self):
        services = list(discover_citrix_session_count(None))
        assert services == []


class TestCheck:
    def test_check_session_counts(self):
        section = parse_citrix_session_detail(FLAT_STRING_TABLE)
        results = list(check_citrix_session_count(DEFAULT_PARAMS, section))
        assert any(isinstance(r, Result) for r in results)
        assert any(isinstance(r, Metric) and r.name == "citrix_sessions_total" for r in results)

    def test_check_total_metric(self):
        section = parse_citrix_session_detail(FLAT_STRING_TABLE)
        results = list(check_citrix_session_count(DEFAULT_PARAMS, section))
        total = [r for r in results if isinstance(r, Metric) and r.name == "citrix_sessions_total"]
        assert total[0].value == 10

    def test_check_ok_state(self):
        # Use a small section with only active sessions → all OK
        active_only = [
            ["mydomain.local\\UserC", "Active", "mydomain.local\\srv", "24.03.2026", "14:53:10"],
            ["mydomain.local\\UserD", "Active", "mydomain.local\\srv", "24.03.2026", "15:45:42"],
        ]
        section = parse_citrix_session_detail(active_only)
        results = list(check_citrix_session_count(DEFAULT_PARAMS, section))
        states = [r.state for r in results if isinstance(r, Result)]
        assert all(s == State.OK for s in states)

    def test_check_empty_section(self):
        results = list(check_citrix_session_count(DEFAULT_PARAMS, None))
        assert results == []

    def test_check_disconnected_details(self):
        section = parse_citrix_session_detail(FLAT_STRING_TABLE)
        results = list(check_citrix_session_count(DEFAULT_PARAMS, section))
        notices = [r.details for r in results if isinstance(r, Result) and r.details]
        details_text = " ".join(notices)
        assert "UserB" in details_text

    def test_check_with_low_thresholds(self):
        params = {
            "active_levels": ("fixed", (1, 2)),
            "disconnected_levels": ("fixed", (1, 2)),
            "disconnected_age_levels": ("fixed", (3600.0, 7200.0)),
        }
        section = parse_citrix_session_detail(FLAT_STRING_TABLE)
        results = list(check_citrix_session_count(params, section))
        # 8 active (> crit 2) - should have CRIT
        states = [r.state for r in results if isinstance(r, Result)]
        assert State.CRIT in states
