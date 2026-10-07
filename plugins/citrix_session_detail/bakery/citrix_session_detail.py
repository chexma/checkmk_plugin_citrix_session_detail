#!/usr/bin/env python3
"""Bakery plugin for Citrix Session Detail (Bakery API v2_unstable, Checkmk 2.5).

Deploys the PowerShell agent plugin and a configuration file
with MaxRecordCount to Windows hosts.
"""

from pathlib import Path

from cmk.bakery.v2_unstable import OS, BakeryPlugin, FileGenerator, Plugin, PluginConfig
from pydantic import BaseModel


class Config(BaseModel):
    max_record_count: int = 500


def get_citrix_session_detail_files(conf: Config) -> FileGenerator:
    """Generate plugin files for Windows agent."""
    yield Plugin(
        base_os=OS.WINDOWS,
        source=Path("citrix_session_detail.ps1"),
    )

    yield PluginConfig(
        base_os=OS.WINDOWS,
        lines=[f"max_record_count = {conf.max_record_count}"],
        target=Path("citrix_session_detail.cfg"),
        include_header=True,
    )


bakery_plugin_citrix_session_detail = BakeryPlugin(
    name="citrix_session_detail",
    parameter_parser=Config.model_validate,
    default_parameters=None,
    files_function=get_citrix_session_detail_files,
)
