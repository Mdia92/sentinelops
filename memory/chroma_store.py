from __future__ import annotations

import json
from typing import Any

import chromadb

from models.contracts import (
    AgentState,
    DiagnosisReport,
    IncidentTrigger,
    ProposedFix,
    ResolutionReport,
)


class IncidentMemory:
    def __init__(self, persist_dir: str = ".chroma") -> None:
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="sentinelops_incidents",
            metadata={"hnsw:space": "cosine"},
        )

    def _incident_text(self, trigger: IncidentTrigger, diagnosis: DiagnosisReport | None) -> str:
        parts = [
            trigger.metric_name,
            str(trigger.current_value),
            diagnosis.root_cause_hypothesis if diagnosis else "",
        ]
        return " | ".join(parts)

    def store_resolution(
        self,
        trigger: IncidentTrigger,
        diagnosis: DiagnosisReport,
        proposed: ProposedFix,
        resolution: ResolutionReport,
    ) -> None:
        doc_id = f"{trigger.incident_id}:{resolution.status.value}"
        self.collection.upsert(
            ids=[doc_id],
            documents=[self._incident_text(trigger, diagnosis)],
            metadatas=[
                {
                    "incident_id": trigger.incident_id,
                    "metric_name": trigger.metric_name,
                    "status": resolution.status.value,
                    "recommended_fix": proposed.recommended_fix,
                }
            ],
        )

    def find_similar(self, trigger: IncidentTrigger, limit: int = 3) -> list[str]:
        if self.collection.count() == 0:
            return []
        query = f"{trigger.metric_name} {trigger.current_value}"
        results = self.collection.query(query_texts=[query], n_results=limit)
        matches: list[str] = []
        metadatas = results.get("metadatas") or [[]]
        for item in metadatas[0]:
            matches.append(
                f"{item.get('metric_name')} -> {item.get('recommended_fix')} ({item.get('status')})"
            )
        return matches

    def recent_resolved(self, limit: int = 5) -> list[dict[str, Any]]:
        if self.collection.count() == 0:
            return []
        data = self.collection.get(limit=limit)
        rows: list[dict[str, Any]] = []
        for idx, doc_id in enumerate(data.get("ids", [])):
            metadata = data["metadatas"][idx]
            rows.append(
                {
                    "id": doc_id,
                    "metric_name": metadata.get("metric_name"),
                    "recommended_fix": metadata.get("recommended_fix"),
                    "status": metadata.get("status"),
                }
            )
        return rows

    def dump_state(self) -> str:
        return json.dumps(self.recent_resolved(), indent=2)
