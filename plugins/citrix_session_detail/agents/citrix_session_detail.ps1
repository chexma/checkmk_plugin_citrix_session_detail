# CheckMK Agent Plugin: Citrix Session Detail
# Collects Citrix session data and outputs piggyback sections per server.
#
# Requires: Citrix PowerShell Snap-in (Citrix.Broker.Admin)
# Place in: C:\ProgramData\checkmk\agent\plugins\

# Read MaxRecordCount from config file (deployed by Agent Bakery)
$maxRecordCount = 500
$configDir = $env:MK_CONFDIR
if (-not $configDir) {
    $configDir = "C:\ProgramData\checkmk\agent\config"
}

$configFile = Join-Path $configDir "citrix_session_detail.cfg"

if (Test-Path $configFile) {
    Get-Content $configFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -match '^max_record_count\s*=\s*(\d+)$') {
            $maxRecordCount = [int]$Matches[1]
        }
    }
}

# Load Citrix Snap-in
try {
    Add-PSSnapin Citrix.Broker.Admin.V2 -ErrorAction Stop
} catch {
    exit 0
}

# Get sessions
try {
    $sessions = Get-BrokerSession -Username:* -SortBy:MachineName -MaxRecordCount:$maxRecordCount -ErrorAction Stop
} catch {
    exit 0
}

if (-not $sessions) {
    exit 0
}

# Get broker machines
$brokermachines = Get-BrokerMachine | Select-Object -ExpandProperty MachineName

# Build hashtable: MachineName -> Sessions[]
$grouped = @{}
$sessions | Group-Object MachineName | ForEach-Object {
    $grouped[$.Name] = $.Group
}

# Output piggyback data per machine
foreach ($machineName in $brokermachines) {

    # Extract short hostname from "DOMAIN\hostname"
    $shortName = ($machineName -split '\\')[-1]

    Write-Host "<<<<$shortName>>>>"
    Write-Host "<<<citrix_session_detail>>>"

    if ($grouped.ContainsKey($machineName)) {
        foreach ($s in $grouped[$machineName]) {

            $idle = ""
            if ($s.IdleSince) {
                $idle = $s.IdleSince.ToString("dd.MM.yyyy HH:mm:ss")
            }

            Write-Host "$($s.UserName) $($s.SessionState) $($s.MachineName) $idle"
        }
    }

    Write-Host "<<<<>>>>"
}