# Your tasks — step by step

Everything below requires **your** account, browser, or physical actions. Work top to bottom. Estimated total: **3–4 hours** (excluding video rehearsal).

**Repo (done):** https://github.com/Mdia92/sentinelops  
**Deadline:** June 15, 2026 at **9:00 AM PDT**

---

## Phase 0 — Security (2 minutes)

- [ ] **Delete** `C:\Users\diamo\Documents\token.txt` — token is already in `.env` locally; the text file is a leak risk.
- [ ] Confirm `.env` is **never** committed (already in `.gitignore`).

---

## Phase 1 — GitHub polish (5 minutes)

- [ ] Open https://github.com/Mdia92/sentinelops
- [ ] Confirm repo is **Public**
- [ ] Click **⚙ Settings → General → License** (or edit the About box on the main page)
- [ ] Set license to **MIT** (must match the `LICENSE` file in the repo)
- [ ] Optional: add description: *The autonomous self-healing SRE that closes the loop and compounds.*
- [ ] Optional: add topics: `splunk`, `langgraph`, `streamlit`, `hackathon`, `observability`

---

## Phase 2 — Official Splunk MCP app (30–45 minutes)

Judges expect **Splunk MCP Server** by name. Your REST + local bridge work; this app is the sponsor-aligned spine.

1. [ ] Open Splunk Web: http://localhost:8000  
2. [ ] **Apps → Find more apps** (or Splunkbase)
3. [ ] Search **Splunk MCP Server** → [Splunkbase app 7931](https://splunkbase.splunk.com/app/7931)
4. [ ] Install the app → restart Splunk if prompted
5. [ ] **Settings → Roles →** your role (e.g. `admin` or custom) → **Capabilities**
   - Enable **`mcp_tool_execute`**
6. [ ] Verify official endpoint (PowerShell):

```powershell
cd C:\Users\diamo\Projects\sentinelops
python scripts/check_mcp_health.py
```

- [ ] **`splunk_rest.ok`** and **`bridge_ping.ok`** should be **true**
- [ ] **`official_mcp.ok`** needs a **separate MCP encrypted token** (see below)

### If `official_mcp` says "Invalid token audience"

The MCP app is installed, but your REST/hackathon token is not valid for MCP. In Splunk Web → **Splunk MCP Server app** → create an **encrypted MCP token** → add to `.env` as `SPLUNK_MCP_TOKEN`. Re-run health check until `official_mcp.ok: true`. Until then, REST + bridge work for your demo.

Optional but valuable:

- [ ] Install **Splunk AI Assistant for SPL** from Splunkbase (enables `generate_spl` MCP tools)

---

## Phase 3 — Local demo environment (10 minutes)

Before recording or presenting locally:

1. [ ] Splunk is running (`http://localhost:8000` loads)
2. [ ] Start MCP bridge (separate terminal — **keep it open**):

```powershell
cd C:\Users\diamo\Projects\sentinelops
.\scripts\start_mcp_bridge.ps1
```

3. [ ] Health check:

```powershell
python scripts\check_mcp_health.py
```

Expect: `bridge_http.ok`, `bridge_ping.ok`, `splunk_rest.ok` all **true**.

4. [ ] Run dashboard:

```powershell
streamlit run ui/streamlit_app.py
```

5. [ ] Click **Run Watcher Scan** → see `auth_service` spike → cascade warning → **Approve** → RESOLVED

---

## Phase 4 — Streamlit Cloud hosted URL (20–30 minutes)

Judges need a URL that opens in a browser **without** installing anything. Cloud **cannot** reach your `localhost` Splunk — deploy in **demo mode**.

1. [ ] Go to https://share.streamlit.io/ (sign in with GitHub)
2. [ ] **New app**
   - Repository: `Mdia92/sentinelops`
   - Branch: `master`
   - Main file path: **`ui/streamlit_app.py`**
3. [ ] **Advanced settings → Secrets** — paste (adjust token if you want cloud to try REST; mock is safer for judges):

```toml
SPLUNK_USE_MOCK = "true"
SPLUNK_HOST = "localhost"
SPLUNK_PORT = "8089"
SPLUNK_TOKEN = ""
CHROMA_PERSIST_DIR = ".chroma"
```

4. [ ] Deploy → wait for green **Running**
5. [ ] Open the `*.streamlit.app` URL in an **incognito** window — confirm UI loads and **Run Watcher Scan** works
6. [ ] Save that URL for Devpost

**Demo strategy:** Your **YouTube video** proves real Splunk + MCP locally. The **hosted URL** proves the product UI for judges who won't install Splunk.

---

## Phase 5 — Record 3-minute YouTube video (60–90 minutes)

Rules: **Public** (not unlisted), **under 3:00**.

### Before recording

- [ ] Splunk Web + SentinelOps Streamlit + MCP bridge all running
- [ ] Close unrelated tabs/notifications
- [ ] Use OBS, Xbox Game Bar, or similar

### Script (from hackathon brief)

| Time | Show | Say (approx.) |
|------|------|----------------|
| 0:00–0:20 | Splunk search or dashboard, error climbing | *"It's 2 AM. Error rate crossed 8%. Your SRE is asleep… unless you have SentinelOps."* |
| 0:20–0:50 | Streamlit — click **Run Watcher Scan** | Watcher fires, Diagnostician reasoning appears |
| 0:50–1:20 | **Pause** on cascade warning line | *"I never programmed cascade detection. It found this by correlating two metric streams."* |
| 1:20–1:50 | Approval card → click **Approve** → Verifier | Error rate drops, RESOLVED |
| 1:50–2:20 | Run scan **again** | Memory panel — faster second resolution |
| 2:20–3:00 | MCP status, `policy.yaml`, memory panel | *"SentinelOps never sleeps, never forgets, gets better every time."* |

### Upload

- [ ] YouTube → **Public**
- [ ] Title e.g. *SentinelOps — Splunk Agentic Ops Hackathon 2026*
- [ ] Copy video URL for Devpost

---

## Phase 6 — Devpost final submission (20 minutes)

1. [ ] https://splunk.devpost.com → your draft
2. [ ] Fill **all** required fields:

| Field | Value |
|-------|--------|
| Project name | SentinelOps |
| Tagline | The autonomous self-healing SRE that closes the loop and compounds |
| Track | **Observability** |
| GitHub | https://github.com/Mdia92/sentinelops |
| Hosted URL | Your Streamlit Cloud URL |
| Video | Your public YouTube URL |
| Built with | Splunk MCP Server, Splunk Hosted Models, Foundation AI Security Model, LangGraph, ChromaDB, FastAPI, Streamlit, Claude API |

3. [ ] Description (~300 words): problem → closed loop → human gate → cascade finding → memory moat
4. [ ] **Submit** before **June 15, 9:00 AM PDT**

---

## Phase 7 — Optional enhancements

- [ ] **Anthropic API key** in local `.env` → smarter Proposer (`ANTHROPIC_API_KEY=...`)
- [ ] Join Slack **#splunk-ai-hackathon** for judge Q&A
- [ ] Re-upload fresh `sample_incidents.log` before video if you want **latest** error_rate > 5% in Splunk (regenerate: `python scripts/generate_sample_data.py`)

---

## When you return — tell me

1. Which phases you completed (checklist numbers)
2. Streamlit Cloud URL (if deployed)
3. Whether **official_mcp.ok** is true after Splunkbase install
4. Any errors (screenshot or paste)

I’ll then: wire official MCP if installed, tune Devpost copy, and fix any blockers before submit.
