param(
    [string]$HostAddress = "192.168.111.134"
)

$ErrorActionPreference = "Stop"
$ports = 6053, 6054, 6055, 6056
$failed = $false

foreach ($port in $ports) {
    $result = Test-NetConnection -ComputerName $HostAddress -Port $port -WarningAction SilentlyContinue
    [pscustomobject]@{
        Host = $HostAddress
        Port = $port
        Reachable = $result.TcpTestSucceeded
    }
    if (-not $result.TcpTestSucceeded) {
        $failed = $true
    }
}

if ($failed) {
    throw "One or more ESPHome ports are unreachable. Check VMware/LAN routing and the VM firewall."
}
