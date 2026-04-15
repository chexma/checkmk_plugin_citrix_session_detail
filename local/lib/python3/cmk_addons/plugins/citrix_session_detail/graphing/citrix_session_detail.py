#!/usr/bin/env python3
"""Graphing definitions for Citrix Session Detail plugin."""

from cmk.graphing.v1 import Title
from cmk.graphing.v1.graphs import Graph, MinimalRange
from cmk.graphing.v1.metrics import Color, DecimalNotation, Metric, TimeNotation, Unit
from cmk.graphing.v1.perfometers import Closed, FocusRange, Open, Perfometer, Stacked

metric_citrix_sessions_active = Metric(
    name="citrix_sessions_active",
    title=Title("Active sessions"),
    unit=Unit(DecimalNotation("")),
    color=Color.GREEN,
)

metric_citrix_sessions_disconnected = Metric(
    name="citrix_sessions_disconnected",
    title=Title("Disconnected sessions"),
    unit=Unit(DecimalNotation("")),
    color=Color.ORANGE,
)

metric_citrix_sessions_total = Metric(
    name="citrix_sessions_total",
    title=Title("Total sessions"),
    unit=Unit(DecimalNotation("")),
    color=Color.BLUE,
)

metric_citrix_session_max_disconnected_age = Metric(
    name="citrix_session_max_disconnected_age",
    title=Title("Oldest disconnected session age"),
    unit=Unit(TimeNotation()),
    color=Color.YELLOW,
)

graph_citrix_sessions = Graph(
    name="citrix_sessions",
    title=Title("Citrix Sessions"),
    compound_lines=[
        "citrix_sessions_active",
        "citrix_sessions_disconnected",
    ],
    simple_lines=[
        "citrix_sessions_total",
    ],
    minimal_range=MinimalRange(0, 10),
)

perfometer_citrix_sessions = Stacked(
    name="citrix_sessions",
    lower=Perfometer(
        name="citrix_sessions_active_perf",
        focus_range=FocusRange(Closed(0), Open(30)),
        segments=["citrix_sessions_active"],
    ),
    upper=Perfometer(
        name="citrix_sessions_disconnected_perf",
        focus_range=FocusRange(Closed(0), Open(10)),
        segments=["citrix_sessions_disconnected"],
    ),
)
