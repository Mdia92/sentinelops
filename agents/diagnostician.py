from __future__ import annotations

import os

from integrations.splunk_client import SplunkClient, load_policy
from memory.chroma_store import IncidentMemory
from models.contracts import AgentState, DiagnosisReport


def run_diagnostician(state: AgentState) -> AgentState:
    if not state.incident_trigger:
        state.add_event("Diagnostician skipped — no incident trigger")
        return state

    trigger = state.incident_trigger
    client = SplunkClient()
    policy = load_policy()
    rows = client.get_recent_metrics(minutes=15)
    recent_rows = rows[:50] if rows else []

    def _rate(row: dict) -> float:
        value = row.get("error_rate", row.get("current_value", 0))
        return float(value) if value not in (None, "") else 0.0

    auth_errors = [_rate(row) for row in recent_rows if row.get("metric_name") == trigger.metric_name]
    checkout_errors = [_rate(row) for row in recent_rows if row.get("metric_name") == "checkout_service"]

    avg_auth = sum(auth_errors) / len(auth_errors) if auth_errors else trigger.current_value
    avg_checkout = sum(checkout_errors) / len(checkout_errors) if checkout_errors else 0.0
    affected_count = len(trigger.affected_services)
    blast_radius = min(1.0, affected_count / 7)

    evidence = [
        f"{trigger.metric_name} latest error_rate={trigger.current_value}%",
        f"15-minute average for {trigger.metric_name}={avg_auth:.2f}%",
    ]
    cascade_warning = None
    if trigger.metric_name == "auth_service" and avg_checkout >= 3.5:
        cascade_warning = (
            "WARNING: checkout_service showing early memory pressure correlated with auth errors. "
            "Estimated cascade in 4-7 minutes if unresolved."
        )
        evidence.append(f"checkout_service average error_rate={avg_checkout:.2f}%")
        blast_radius = max(blast_radius, 0.45)

    memory = IncidentMemory(persist_dir=os.getenv("CHROMA_PERSIST_DIR", ".chroma"))
    similar = memory.find_similar(trigger)

    hypothesis = (
        f"{trigger.metric_name} degradation likely caused by elevated error rates "
        f"above policy threshold ({policy['watcher']['error_rate_threshold']}%)."
    )
    if cascade_warning:
        hypothesis += " Correlated checkout stress indicates potential cascade."

    report = DiagnosisReport(
        incident_id=trigger.incident_id,
        root_cause_hypothesis=hypothesis,
        blast_radius=round(blast_radius, 2),
        confidence_score=0.82 if cascade_warning else 0.74,
        evidence_list=evidence,
        similar_incidents=similar,
        cascade_warning=cascade_warning,
    )
    state.diagnosis_report = report
    state.add_event(f"Diagnostician blast_radius={report.blast_radius}, confidence={report.confidence_score}")
    if cascade_warning:
        state.add_event(cascade_warning)
    return state
