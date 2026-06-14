from __future__ import annotations

import os

from integrations.splunk_client import load_policy
from models.contracts import AgentState, ProposedFix, RemediationOption


def _template_proposal(state: AgentState) -> ProposedFix:
    trigger = state.incident_trigger
    diagnosis = state.diagnosis_report
    assert trigger and diagnosis

    options = [
        RemediationOption(
            action="restart_pod",
            risk_level="LOW",
            estimated_resolution_time="2-4 minutes",
            rollback_plan="Redeploy previous pod revision from deployment history.",
        ),
        RemediationOption(
            action="clear_cache",
            risk_level="LOW",
            estimated_resolution_time="1-2 minutes",
            rollback_plan="Warm cache rebuilds automatically from origin.",
        ),
        RemediationOption(
            action="scale_up_to_2x",
            risk_level="MEDIUM",
            estimated_resolution_time="3-6 minutes",
            rollback_plan="Scale back to baseline replica count.",
        ),
    ]

    recommended = "restart_pod"
    if diagnosis.cascade_warning:
        recommended = "clear_cache"

    return ProposedFix(
        incident_id=trigger.incident_id,
        recommended_fix=recommended,
        risk_level="LOW" if recommended != "scale_up_to_2x" else "MEDIUM",
        estimated_resolution_time="2-4 minutes",
        rollback_plan=options[0].rollback_plan,
        options=options,
        approval_required=True,
    )


def _anthropic_proposal(state: AgentState) -> ProposedFix | None:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key.startswith("your_"):
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        trigger = state.incident_trigger
        diagnosis = state.diagnosis_report
        assert trigger and diagnosis

        prompt = (
            "You are SentinelOps Proposer. Return concise remediation guidance as plain text.\n"
            f"Incident: {trigger.model_dump_json()}\n"
            f"Diagnosis: {diagnosis.model_dump_json()}\n"
            "Recommend one fix from: restart_pod, clear_cache, scale_up_to_2x."
        )
        message = client.messages.create(
            model=os.getenv("PROPOSER_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text if message.content else "restart_pod"
        recommended = "restart_pod"
        for action in ["clear_cache", "scale_up_to_2x", "restart_pod"]:
            if action in text:
                recommended = action
                break
        proposal = _template_proposal(state)
        proposal.recommended_fix = recommended
        return proposal
    except Exception:
        return None


def run_proposer(state: AgentState) -> AgentState:
    if not state.diagnosis_report or not state.incident_trigger:
        state.add_event("Proposer skipped — missing diagnosis")
        return state

    policy = load_policy()
    diagnosis = state.diagnosis_report
    if diagnosis.blast_radius > float(policy["blast_radius_threshold"]):
        state.add_event("Proposer escalated — blast radius above policy threshold")
        state.approval_decision = state.approval_decision

    proposal = _anthropic_proposal(state) or _template_proposal(state)
    state.proposed_fix = proposal
    state.add_event(
        f"Proposer recommends {proposal.recommended_fix} (risk={proposal.risk_level}) — awaiting approval"
    )
    return state
