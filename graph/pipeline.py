from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from agents.diagnostician import run_diagnostician
from agents.proposer import run_proposer
from agents.verifier import run_verifier
from agents.watcher import run_watcher
from integrations.splunk_client import load_policy
from models.contracts import AgentState, ApprovalDecision


def _route_after_watcher(state: AgentState) -> Literal["diagnostician", "end"]:
    return "diagnostician" if state.incident_trigger else "end"


def _route_after_proposer(state: AgentState) -> Literal["human_gate", "end"]:
    return "human_gate" if state.proposed_fix else "end"


def _route_after_gate(state: AgentState) -> Literal["verifier", "end"]:
    if state.approval_decision == ApprovalDecision.APPROVED:
        return "verifier"
    return "end"


def _route_after_verifier(state: AgentState) -> Literal["proposer", "end"]:
    policy = load_policy()
    if (
        state.resolution_report
        and state.resolution_report.status.value == "ESCALATE"
        and state.retry_count < int(policy["max_retries"])
    ):
        return "proposer"
    return "end"


def human_gate(state: AgentState) -> AgentState:
    if state.approval_decision == ApprovalDecision.PENDING:
        state.add_event("Human gate active — waiting for approval decision")
    return state


def build_graph() -> Any:
    graph = StateGraph(AgentState)
    graph.add_node("watcher", run_watcher)
    graph.add_node("diagnostician", run_diagnostician)
    graph.add_node("proposer", run_proposer)
    graph.add_node("human_gate", human_gate)
    graph.add_node("verifier", run_verifier)

    graph.add_edge(START, "watcher")
    graph.add_conditional_edges("watcher", _route_after_watcher, {"diagnostician": "diagnostician", "end": END})
    graph.add_edge("diagnostician", "proposer")
    graph.add_conditional_edges("proposer", _route_after_proposer, {"human_gate": "human_gate", "end": END})
    graph.add_conditional_edges("human_gate", _route_after_gate, {"verifier": "verifier", "end": END})
    graph.add_conditional_edges("verifier", _route_after_verifier, {"proposer": "proposer", "end": END})
    return graph.compile()


def run_pipeline(approval: ApprovalDecision = ApprovalDecision.PENDING) -> AgentState:
    app = build_graph()
    state = AgentState(approval_decision=approval)
    result = app.invoke(state)
    if isinstance(result, dict):
        return AgentState.model_validate(result)
    return result


def continue_after_approval(state: AgentState) -> AgentState:
    state.approval_decision = ApprovalDecision.APPROVED
    state.add_event("Human operator approved remediation")
    return run_verifier(state)
