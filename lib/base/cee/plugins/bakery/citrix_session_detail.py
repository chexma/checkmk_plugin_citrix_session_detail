#!/usr/bin/env python3
"""Bakery plugin for Citrix Session Detail.

Deploys the PowerShell agent plugin and a configuration file
with MaxRecordCount to Windows hosts.
"""

from pathlib import Path
from typing import Any

from .bakery_api.v1 import (
    OS,
    FileGenerator,
    Plugin,
    PluginConfig,
    register,
)


def get_citrix_session_detail_files(conf: dict[str, Any]) -> FileGenerator:
    """Generate plugin files for Windows agent."""
    yield Plugin(
        base_os=OS.WINDOWS,
        source=Path("citrix_session_detail.ps1"),
        target=Path("citrix_session_detail.ps1"),
    )

    max_record_count = conf.get("max_record_count", 500)
    yield PluginConfig(
        base_os=OS.WINDOWS,
        lines=[f"max_record_count = {max_record_count}"],
        target=Path("citrix_session_detail.cfg"),
        include_header=True,
    )


register.bakery_plugin(
    name="citrix_session_detail",
    files_function=get_citrix_session_detail_files,
)
