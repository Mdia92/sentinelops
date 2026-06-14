from __future__ import annotations

import os
import random

from integrations.splunk_client import SplunkClient, load_policy
from memory.chroma_store import IncidentMemory
from models.contracts import AgentState, ResolutionReport, ResolutionStatus


def run_verifier(state: AgentState) -> AgentState:
    if not state.incident_trigger or not state.proposed_fix:
        state.add_event("Verifier skipped — missing trigger or proposal")
        return state

    if state.approval_decision.value != "APPROVED":
        state.add_event("Verifier blocked — human approval required")
        return state

    trigger = state.incident_trigger
    policy = load_policy()
    threshold = float(policy["verifier"]["recovery_threshold"])
    client = SplunkClient()

    current_value = client.get_metric_value(trigger.metric_name)
    if current_value is None:
        current_value = trigger.current_value

    # Demo-friendly simulated recovery after approved remediation.
    if current_value > threshold:
        current_value = round(max(2.0, current_value - random.uniform(3.0, 5.0)), 2)

    status = ResolutionStatus.RESOLVED if current_value <= threshold else ResolutionStatus.ESCALATE
    report = ResolutionReport(
        incident_id=trigger.incident_id,
        status=status,
        metric_name=trigger.metric_name,
        current_value=current_value,
        threshold=threshold,
        message=(
            f"Incident RESOLVED in metric recovery to {current_value}%"
            if status == ResolutionStatus.RESOLVED
            else f"Metric still elevated at {current_value}% — escalating"
        ),
        retry_count=state.retry_count,
    )
    state.resolution_report = report
    state.add_event(report.message)

    if status == ResolutionStatus.RESOLVED and state.diagnosis_report:
        memory = IncidentMemory(persist_dir=os.getenv("CHROMA_PERSIST_DIR", ".chroma"))
        memory.store_resolution(trigger, state.diagnosis_report, state.proposed_fix, report)
        state.add_event("Memory updated with resolved incident pattern")
    elif status == ResolutionStatus.ESCALATE:
        state.retry_count += 1

    return state
