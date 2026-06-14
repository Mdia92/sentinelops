from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from integrations.splunk_client import SplunkClient, load_policy
from models.contracts import AgentState, IncidentTrigger, Severity


def run_watcher(state: AgentState) -> AgentState:
    client = SplunkClient()
    policy = load_policy()
    threshold = float(policy["watcher"]["error_rate_threshold"])
    rows = client.run_search()

    trigger: IncidentTrigger | None = None
    best_match: tuple[str, float] | None = None
    for row in rows:
        metric_name = row.get("metric_name")
        value = row.get("current_value", row.get("error_rate"))
        if metric_name is None or value is None:
            continue
        current_value = float(value)
        if current_value > threshold and (best_match is None or current_value > best_match[1]):
            best_match = (metric_name, current_value)

    if best_match:
        metric_name, current_value = best_match
        affected = sorted({metric_name})
        related = [
            r.get("metric_name")
            for r in rows
            if r.get("metric_name") != metric_name and float(r.get("error_rate", 0)) > 3.5
        ]
        affected.extend([name for name in related if name])
        trigger = IncidentTrigger(
            incident_id=str(uuid4())[:8],
            timestamp=datetime.now(timezone.utc).isoformat(),
            metric_name=metric_name,
            current_value=current_value,
            threshold=threshold,
            affected_services=sorted(set(affected)),
            severity=Severity.HIGH if current_value < 8 else Severity.CRITICAL,
        )

    state.incident_trigger = trigger
    state.mcp_status = client.status
    if trigger:
        state.add_event(
            f"Watcher detected {trigger.metric_name} at {trigger.current_value}% (> {threshold}%)"
        )
    else:
        state.add_event("Watcher scan complete — no threshold breach")
    return state
