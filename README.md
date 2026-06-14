# SentinelOps

The autonomous self-healing SRE that closes the loop and compounds.

**GitHub:** https://github.com/Mdia92/sentinelops  
**Your step-by-step checklist:** [docs/USER_CHECKLIST.md](docs/USER_CHECKLIST.md)

SentinelOps watches Splunk indexes, diagnoses incidents, proposes fixes behind a human approval gate, verifies recovery, and stores resolution patterns in vector memory.

## Architecture

```
Splunk Indexes
      |
      v
Splunk MCP Server  (primary spine)
      |
      v
+------------------+
|  Watcher Agent   |  SPL threshold scan
+--------+---------+
         |
         v
+----------------------+
| Diagnostician Agent  |  correlate logs + memory lookup
+----------+-----------+
           |
           v
+-------------------+
|  Proposer Agent   |  ranked remediation options
+---------+---------+
          |
          v
+-------------------+
|   Human Gate      |  Approve / Reject
+---------+---------+
          |
          v
+-------------------+
|  Verifier Agent   |  re-query metric -> RESOLVED / ESCALATE
+---------+---------+
          |
          v
+-------------------+
|  ChromaDB Memory  |  compound across sessions
+-------------------+
```

## Competitive Comparison

| Feature | SentinelOps | Traditional Alert System | Generic LLM Chatbot |
|---|---|---|---|
| Closed-loop verification | Yes | No | No |
| Compound memory | Yes (ChromaDB) | No | No |
| Policy-as-code human gate | Yes (`policy.yaml`) | Partial | No |
| Splunk-native data spine | Yes (MCP + REST) | Yes (alerts only) | Optional / decorative |
| Autonomous remediation | Yes, gated | No | Sometimes unsafe |
| Unprogrammed cascade finding | Yes (emergent correlation) | No | Unreliable |

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy environment template and fill secrets:

```bash
copy .env.example .env
```

3. Upload sample data to Splunk (or keep mock mode):

- File: `sample_incidents.log`
- Regenerate anytime: `python scripts/generate_sample_data.py`

4. Run dashboard:

```bash
streamlit run ui/streamlit_app.py
```

## Splunk MCP Setup (Important)

`https://github.com/splunk/splunk-mcp` **does not exist**. Use one of these:

1. **Official (recommended for judging):** Install [Splunk MCP Server on Splunkbase (app 7931)](https://splunkbase.splunk.com/app/7931). Endpoint: `https://localhost:8089/services/mcp`
2. **Local bridge (included):** [livehybrid/splunk-mcp](https://github.com/livehybrid/splunk-mcp) cloned to `vendor/splunk-mcp`, runs on **`http://localhost:8765`** (port 8000 is Splunk Web UI).

Start bridge:

```powershell
.\scripts\start_mcp_bridge.ps1
```

Health check:

```powershell
python scripts/check_mcp_health.py
```

## Splunk Upload (Manual)

In Splunk Web (`http://localhost:8000`):

1. Settings → Add Data → Upload
2. Select `sample_incidents.log`
3. Set sourcetype to `_json` or `sentinelops:incidents`
4. Verify with SPL:

```spl
search index=* sourcetype=_json source=sample_incidents.log earliest=-24h
| spath
| stats latest(error_rate) as current_value max(error_rate) as peak_value by metric_name
| eval current_value=if(current_value>5, current_value, peak_value)
| where current_value > 5
```

## Policy

`policy.yaml` defines:

- `auto_remediate`: allowed low-risk actions
- `always_escalate`: actions requiring human escalation
- `max_retries`: verifier retry limit
- `blast_radius_threshold`: auto-escalation threshold

## Built With

Splunk MCP Server, Splunk Hosted Models, Foundation AI Security Model, LangGraph, ChromaDB, FastAPI, Streamlit, Claude API

## License

MIT
