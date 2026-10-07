# Citrix Session Detail Monitoring for Checkmk

Checkmk 2.4 plugin that monitors Citrix XenApp/XenDesktop sessions per Citrix
server.

A PowerShell agent plugin on the Citrix **Delivery Controller** collects all
sessions via `Get-BrokerSession` and distributes them via **piggyback** to the
individual Citrix servers.

## Features

- Number of active and disconnected sessions per server
- Age of the oldest disconnected session, with configurable thresholds
- List of all disconnected sessions (user, idle time) in the service details

## Services Created

| Service | Host | Description |
|---------|------|-------------|
| Citrix Sessions | each Citrix server (piggyback) | Session counts and oldest disconnected session age |

## Rulesets

| Ruleset | Type | Parameters |
|---------|------|------------|
| Citrix Session Count | Service monitoring rule | Upper levels for active / disconnected sessions and oldest disconnected session age (defaults 20/30, 5/10, 1d/3d) |
| Citrix Session Detail | Agent bakery rule | Maximum number of sessions queried (`MaxRecordCount`, default 500) |

## Requirements

- Checkmk 2.4.0p1 or later
- Windows Checkmk agent on a Citrix Delivery Controller with the Citrix
  PowerShell snap-ins (`Get-BrokerSession`)

## Download

See the [Releases page](https://github.com/chexma/checkmk_plugin_citrix_session_detail/releases/latest).

## License

GPLv2
