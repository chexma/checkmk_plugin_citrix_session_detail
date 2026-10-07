# CHANGELOG

All notable changes to this project will be documented in this file.

## 1.5.0 - 2026-10-07

- Requires Checkmk 2.5 (2.5.0p1 to 2.5.0p99); use 1.1.1 on Checkmk 2.4
- Bakery plugin migrated to the Bakery API v2 (`cmk.bakery.v2_unstable`) and
  moved with the PowerShell agent plugin into the plugin family
  (`citrix_session_detail/bakery/`, `citrix_session_detail/agents/`)
- MKP now contains the bakery plugin and the agent plugin
- Agent plugin: fix missing `#` on the first comment line (PowerShell error on every run)

## 1.1.1 - 2026-05-06

- Handle empty sessions so the service does not go stale
- Piggyback-only model: one `Citrix Sessions` service per Citrix server (no items)
