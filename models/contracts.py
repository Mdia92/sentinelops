from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalDecision(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    ESCALATE = "ESCALATE"
    PENDING = "PENDING"


class IncidentTrigger(BaseModel):
    incident_id: str
    timestamp: str
    metric_name: str
    current_value: float
    threshold: float
    affected_services: list[str] = Field(default_factory=list)
    severity: Severity = Severity.HIGH


class DiagnosisReport(BaseModel):
    incident_id: str
    root_cause_hypothesis: str
    blast_radius: float
    confidence_score: float
    evidence_list: list[str] = Field(default_factory=list)
    similar_incidents: list[str] = Field(default_factory=list)
    cascade_warning: str | None = None


class RemediationOption(BaseModel):
    action: str
    risk_level: str
    estimated_resolution_time: str
    rollback_plan: str


class ProposedFix(BaseModel):
    incident_id: str
    recommended_fix: str
    risk_level: str
    estimated_resolution_time: str
    rollback_plan: str
    options: list[RemediationOption] = Field(default_factory=list)
    approval_required: bool = True


class ResolutionReport(BaseModel):
    incident_id: str
    status: ResolutionStatus
    metric_name: str
    current_value: float
    threshold: float
    message: str
    retry_count: int = 0


class AgentState(BaseModel):
    incident_trigger: IncidentTrigger | None = None
    diagnosis_report: DiagnosisReport | None = None
    proposed_fix: ProposedFix | None = None
    resolution_report: ResolutionReport | None = None
    approval_decision: ApprovalDecision = ApprovalDecision.PENDING
    selected_action: str | None = None
    retry_count: int = 0
    events: list[str] = Field(default_factory=list)
    mcp_status: str = "unknown"

    def add_event(self, message: str) -> None:
        self.events.append(message)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
