#!/usr/bin/env python3
"""Agent-based check plugin for Citrix Session Detail monitoring.

Parses session data and creates one service per piggyback host showing
session counts and oldest disconnected session age.

Supports two data formats:
1. Flat (whitespace-separated, all servers in one section):
   DOMAIN\\User  State  DOMAIN\\Server  dd.MM.yyyy HH:mm:ss
2. Piggyback (tab-separated, per server):
   User  State  yyyy-MM-dd HH:mm:ss
"""

import time
from datetime import datetime

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    Metric,
    Result,
    Service,
    State,
    check_levels,
    render,
)


def _parse_datetime(date_str):
    """Try to parse datetime string in supported formats.

    Timestamps from Citrix are local time, so we parse without timezone
    and use local time for comparison.
    """
    for fmt in ("%d.%m.%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.timestamp()
        except ValueError:
            continue
    return None


def parse_citrix_session_detail(string_table):
    """Parse citrix_session_detail section.

    Returns a flat list of sessions (server field is ignored since piggyback
    assigns each host its own data).
    """
    sessions = []
    for line in string_table:
        if len(line) < 2:
            continue

        username = line[0].rsplit("\\", 1)[-1]
        state = line[1]
        idle_since = None

        # Check if field[2] is a server name (contains backslash) → skip it
        idx = 2
        if len(line) > 2 and "\\" in line[2]:
            idx = 3

        # Parse datetime from remaining fields
        if idx < len(line):
            date_str = " ".join(line[idx:])
            idle_since = _parse_datetime(date_str)

        sessions.append(
            {
                "username": username,
                "state": state,
                "idle_since": idle_since,
            }
        )

    return sessions if sessions else None


def discover_citrix_session_count(section):
    """Discover a single service (one per piggyback host)."""
    if section:
        yield Service()


def check_citrix_session_count(params, section):
    """Check session counts and oldest disconnected session age."""
    if not section:
        return

    sessions = section

    active = [s for s in sessions if s["state"] == "Active"]
    disconnected = [s for s in sessions if s["state"] == "Disconnected"]
    total = len(sessions)
    now = time.time()

    # Session counts
    yield from check_levels(
        len(active),
        levels_upper=params.get("active_levels"),
        metric_name="citrix_sessions_active",
        label="Active",
        render_func=lambda v: str(int(v)),
    )

    yield from check_levels(
        len(disconnected),
        levels_upper=params.get("disconnected_levels"),
        metric_name="citrix_sessions_disconnected",
        label="Disconnected",
        render_func=lambda v: str(int(v)),
    )

    yield Metric("citrix_sessions_total", total)
    yield Result(state=State.OK, notice=f"Total: {total}")

    # Oldest disconnected session age
    if disconnected:
        ages = []
        for s in disconnected:
            if s["idle_since"] is not None:
                age = max(0, now - s["idle_since"])
                ages.append((age, s))

        if ages:
            ages.sort(key=lambda x: x[0], reverse=True)
            oldest_age, _oldest_session = ages[0]

            yield from check_levels(
                oldest_age,
                levels_upper=params.get("disconnected_age_levels"),
                metric_name="citrix_session_max_disconnected_age",
                label="Oldest disconnected",
                render_func=render.timespan,
            )

            # Details: list all disconnected sessions
            details_lines = ["Disconnected sessions:"]
            for age, s in ages:
                since_str = datetime.fromtimestamp(s["idle_since"]).strftime("%d.%m.%Y %H:%M")
                details_lines.append(
                    f"  {s['username']} - {render.timespan(age)} (since {since_str})"
                )
            yield Result(state=State.OK, notice="\n".join(details_lines))

        else:
            yield Result(
                state=State.OK,
                notice="Disconnected sessions present but no idle time reported",
            )


agent_section_citrix_session_detail = AgentSection(
    name="citrix_session_detail",
    parse_function=parse_citrix_session_detail,
)

check_plugin_citrix_session_count = CheckPlugin(
    name="citrix_session_count",
    sections=["citrix_session_detail"],
    service_name="Citrix Sessions",
    discovery_function=discover_citrix_session_count,
    check_function=check_citrix_session_count,
    check_default_parameters={
        "active_levels": ("fixed", (20, 30)),
        "disconnected_levels": ("fixed", (5, 10)),
        "disconnected_age_levels": ("fixed", (86400.0, 259200.0)),
    },
    check_ruleset_name="citrix_session_count",
)
