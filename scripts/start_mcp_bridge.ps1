$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Vendor = Join-Path $Root "vendor\splunk-mcp"

if (-not (Test-Path (Join-Path $Root ".env"))) {
  Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
}

$envFile = Join-Path $Vendor ".env"
if (-not (Test-Path $envFile)) {
  Copy-Item (Join-Path $Root ".env.example") $envFile
}

Get-Content (Join-Path $Root ".env") | ForEach-Object {
  if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
    $name = $matches[1].Trim()
    $value = $matches[2].Trim()
    Set-Item -Path "env:$name" -Value $value
  }
}

Set-Location $Vendor
pip install -e . -q
$port = if ($env:FASTMCP_PORT) { $env:FASTMCP_PORT } else { "8765" }
Write-Output "Starting Splunk MCP bridge on http://localhost:$port (Splunk Web UI stays on :8000)"
python splunk_mcp.py sse
