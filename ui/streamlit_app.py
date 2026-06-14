from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from graph.pipeline import continue_after_approval, run_pipeline
from integrations.splunk_client import SplunkClient
from memory.chroma_store import IncidentMemory
from models.contracts import ApprovalDecision

load_dotenv(ROOT / ".env", override=True)

st.set_page_config(page_title="SentinelOps", page_icon="🛡️", layout="wide")

ACCENT = "#00A35C"

st.markdown(
    f"""
    <style>
      .stApp {{ background-color: #0f1117; color: #e8eaed; }}
      .badge-high {{ background: #b42318; color: white; padding: 4px 10px; border-radius: 999px; }}
      .badge-ok {{ background: {ACCENT}; color: white; padding: 4px 10px; border-radius: 999px; }}
      .panel {{ border: 1px solid #2a2f3a; border-radius: 12px; padding: 16px; background: #151922; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("SentinelOps")
st.caption("The autonomous self-healing SRE that closes the loop and compounds.")

if os.getenv("SPLUNK_USE_MOCK", "false").lower() == "true":
    st.info("Demo mode: using local sample data (Streamlit Cloud cannot reach localhost Splunk).")

if "agent_state" not in st.session_state:
    st.session_state.agent_state = None
if "awaiting_approval" not in st.session_state:
    st.session_state.awaiting_approval = False

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Live Incident Feed")
    if st.button("Run Watcher Scan", type="primary"):
        state = run_pipeline(approval=ApprovalDecision.PENDING)
        st.session_state.agent_state = state
        st.session_state.awaiting_approval = bool(state.proposed_fix)

    state = st.session_state.agent_state
    if state and state.incident_trigger:
        trigger = state.incident_trigger
        st.markdown(
            f"<span class='badge-high'>HIGH</span> **{trigger.metric_name}** "
            f"error_rate **{trigger.current_value}%** (threshold {trigger.threshold}%)",
            unsafe_allow_html=True,
        )
        st.write(f"Incident ID: `{trigger.incident_id}`")
        st.write(f"Affected services: {', '.join(trigger.affected_services)}")
    elif state:
        st.info("No active incident above threshold.")
    else:
        st.write("Run a watcher scan to detect incidents.")

with col2:
    st.subheader("Agent Reasoning Chain")
    if state:
        for event in state.events:
            st.write(f"- {event}")
        if state.diagnosis_report and state.diagnosis_report.cascade_warning:
            st.warning(state.diagnosis_report.cascade_warning)

st.divider()

left, center, right = st.columns(3)

with left:
    st.subheader("Approval Gate")
    if state and state.proposed_fix and st.session_state.awaiting_approval:
        fix = state.proposed_fix
        st.markdown(
            f"""
            **Recommended fix:** `{fix.recommended_fix}`  
            **Risk:** {fix.risk_level}  
            **ETA:** {fix.estimated_resolution_time}  
            **Rollback:** {fix.rollback_plan}
            """
        )
        approve_col, reject_col = st.columns(2)
        if approve_col.button("Approve", type="primary"):
            approved_state = continue_after_approval(state.model_copy(deep=True))
            st.session_state.agent_state = approved_state
            st.session_state.awaiting_approval = False
            st.success("Fix approved. Verifier completed.")
            st.rerun()
        if reject_col.button("Reject"):
            st.session_state.awaiting_approval = False
            st.error("Fix rejected. Incident escalated to human operator.")
    elif state and state.resolution_report:
        st.markdown(
            f"<span class='badge-ok'>{state.resolution_report.status.value}</span> "
            f"{state.resolution_report.message}",
            unsafe_allow_html=True,
        )
    else:
        st.write("No pending approval.")

with center:
    st.subheader("Memory")
    memory = IncidentMemory(persist_dir=os.getenv("CHROMA_PERSIST_DIR", ".chroma"))
    recent = memory.recent_resolved(limit=5)
    if recent:
        for item in recent:
            st.write(
                f"- `{item.get('metric_name')}` → {item.get('recommended_fix')} "
                f"({item.get('status')})"
            )
    else:
        st.write("No resolved incidents stored yet.")

with right:
    st.subheader("System Status")
    client = SplunkClient()
    st.write(f"Splunk backend: **{client.status}**")
    with open(ROOT / "policy.yaml", "r", encoding="utf-8") as handle:
        policy = yaml.safe_load(handle)
    st.write("Policy rules active:")
    st.code(yaml.dump({"auto_remediate": policy["auto_remediate"], "always_escalate": policy["always_escalate"]}))
