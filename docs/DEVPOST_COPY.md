# Devpost submission copy (paste and trim to ~300 words)

## SentinelOps

On-call engineers lose sleep to alert storms that describe problems but never fix them. SentinelOps is an autonomous self-healing SRE that closes the full operational loop: detect, diagnose, propose, human-approve, act, verify, and remember.

**How it works:** A four-agent LangGraph pipeline connects to Splunk through the MCP Server and REST API. The Watcher Agent runs deterministic SPL to detect threshold breaches. The Diagnostician correlates logs and metrics, estimates blast radius, and queries ChromaDB vector memory for similar past incidents. The Proposer ranks remediation options behind a mandatory human approval gate defined in policy-as-code (`policy.yaml`). The Verifier re-queries Splunk to confirm recovery before closing the incident—no fix is trusted until metrics prove it worked.

**Why it wins:** During testing, SentinelOps surfaced a checkout-service cascade risk correlated with auth errors—a pattern we never explicitly coded (Law 26). On repeat incidents, memory pre-loads prior resolutions, cutting response time dramatically. Splunk is the spine: without MCP and live index data, the system is blind.

**Built with:** Splunk MCP Server, Splunk Hosted Models, Foundation AI Security Model, LangGraph, ChromaDB, FastAPI, Streamlit, Claude API.

**Track:** Observability

**Links:**
- GitHub: https://github.com/Mdia92/sentinelops
- Hosted: (your Streamlit URL)
- Video: (your YouTube URL)
