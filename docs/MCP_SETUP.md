# Splunk MCP setup notes

## Why not github.com/splunk/splunk-mcp?

That repository returns **404**. Splunk's supported MCP path is the **Splunkbase app** (ID 7931), which exposes MCP inside Splunk on port **8089** at `/services/mcp`.

## What we installed instead

`vendor/splunk-mcp` is cloned from [livehybrid/splunk-mcp](https://github.com/livehybrid/splunk-mcp) — a standalone MCP bridge for development/demo.

| Service | URL | Port note |
|---|---|---|
| Splunk Web UI | http://localhost:8000 | Do not run MCP bridge here |
| Splunk Management API | https://localhost:8089 | Token auth |
| Official Splunk MCP | https://localhost:8089/services/mcp | Requires Splunkbase app 7931 |
| MCP bridge (this repo) | http://localhost:8765 | SSE + `/openapi.json` |

## Configure token

Edit both files with the same token:

- `.env`
- `vendor/splunk-mcp/.env`

```
SPLUNK_TOKEN=your_token_here
VERIFY_SSL=false
FASTMCP_PORT=8765
```

## Start + verify

```powershell
.\scripts\start_mcp_bridge.ps1
python scripts\check_mcp_health.py
```

Expected when token is set:

- `bridge_http.ok = true`
- `bridge_ping.ok = true`
- `splunk_rest.ok = true` (or `official_mcp.ok = true` if Splunkbase MCP app installed)

## Correct SPL for uploaded JSON logs

```spl
search index=* metric_name=* error_rate=*
| stats latest(error_rate) as current_value by metric_name
| where current_value > 5
```

If fields are not auto-extracted:

```spl
search index=*
| spath
| search metric_name=* error_rate=*
| stats latest(error_rate) as current_value by metric_name
| where current_value > 5
```
