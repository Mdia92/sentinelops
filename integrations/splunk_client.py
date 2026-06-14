from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
import urllib3
import yaml
from dotenv import load_dotenv

urllib3.disable_warnings()

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy.yaml"
load_dotenv(ROOT / ".env", override=True)


def load_policy() -> dict[str, Any]:
    with POLICY_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


class SplunkClient:
    """Splunk access with official MCP -> REST -> local mock fallback chain."""

    def __init__(self) -> None:
        self.host = os.getenv("SPLUNK_HOST", "localhost")
        self.port = int(os.getenv("SPLUNK_PORT", "8089"))
        self.token = os.getenv("SPLUNK_TOKEN", "")
        self.official_mcp_url = os.getenv(
            "SPLUNK_OFFICIAL_MCP_URL", f"https://{self.host}:{self.port}/services/mcp"
        )
        self.bridge_url = os.getenv("SPLUNK_MCP_BRIDGE_URL", "http://localhost:8765")
        self.use_mock = os.getenv("SPLUNK_USE_MOCK", "false").lower() == "true"
        self.sample_log = Path(os.getenv("SAMPLE_LOG_PATH", "sample_incidents.log"))
        if not self.sample_log.is_absolute():
            self.sample_log = ROOT / self.sample_log
        self.policy = load_policy()
        self.last_backend = "unknown"

    @property
    def status(self) -> str:
        return f"{self.last_backend} active"

    def ping_bridge(self) -> dict[str, Any]:
        response = requests.get(f"{self.bridge_url.rstrip('/')}/openapi.json", timeout=5)
        response.raise_for_status()
        return {"status": "ok", "backend": "splunk-mcp-bridge", "url": self.bridge_url}

    def run_search(self, spl: str | None = None) -> list[dict[str, Any]]:
        if self.use_mock:
            return self._search_mock()

        query = spl or self.policy["watcher"]["spl_query"]
        if not query.strip().lower().startswith("search"):
            query = f"search {query.strip()}"

        if self.token and not self.token.startswith("PASTE_"):
            try:
                rows = self._search_rest(query)
                if rows:
                    self.last_backend = "Splunk REST"
                    return rows
            except Exception:
                pass

            try:
                rows = self._search_official_mcp(query)
                if rows:
                    self.last_backend = "Splunk Official MCP"
                    return rows
            except Exception:
                pass

        rows = self._search_mock()
        self.last_backend = "local mock"
        return rows

    def _search_official_mcp(self, query: str) -> list[dict[str, Any]]:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "run_splunk_query",
                "arguments": {"search_query": query, "max_results": 100},
            },
        }
        response = requests.post(
            self.official_mcp_url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
            verify=False,
        )
        response.raise_for_status()
        return self._parse_mcp_rows(response.json())

    def _parse_mcp_rows(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        content = payload.get("result", {}).get("content", [])
        if not content:
            return []
        text = content[0].get("text", "[]")
        parsed = json.loads(text) if isinstance(text, str) else text
        if isinstance(parsed, dict) and "results" in parsed:
            return parsed["results"]
        return parsed if isinstance(parsed, list) else [parsed]

    def _search_rest(self, query: str) -> list[dict[str, Any]]:
        search_url = f"https://{self.host}:{self.port}/services/search/jobs/export"
        response = requests.post(
            search_url,
            headers={"Authorization": f"Bearer {self.token}"},
            data={"search": query, "output_mode": "json"},
            timeout=30,
            verify=False,
        )
        response.raise_for_status()
        rows: list[dict[str, Any]] = []
        for line in response.text.splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if "result" in payload:
                rows.append(payload["result"])
        return rows

    def _search_mock(self) -> list[dict[str, Any]]:
        if not self.sample_log.exists():
            return []
        rows: list[dict[str, Any]] = []
        latest_by_metric: dict[str, dict[str, Any]] = {}
        with self.sample_log.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                metric = row.get("metric_name")
                if metric:
                    latest_by_metric[metric] = {
                        "metric_name": metric,
                        "current_value": row.get("error_rate"),
                        "error_rate": row.get("error_rate"),
                    }
        threshold = float(self.policy["watcher"]["error_rate_threshold"])
        return [
            row
            for row in latest_by_metric.values()
            if float(row.get("current_value", 0)) > threshold
        ] or list(latest_by_metric.values())

    def get_recent_metrics(self, minutes: int = 15) -> list[dict[str, Any]]:
        if self.use_mock and self.sample_log.exists():
            rows: list[dict[str, Any]] = []
            with self.sample_log.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        rows.append(json.loads(line))
            return rows[-minutes:] if len(rows) > minutes else rows

        query = "search index=* sourcetype=_json source=sample_incidents.log earliest=-24h | spath | head 100"
        return self.run_search(query)

    def get_metric_value(self, metric_name: str) -> float | None:
        if self.use_mock and self.sample_log.exists():
            rows = []
            with self.sample_log.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        rows.append(json.loads(line))
            matches = [row for row in rows if row.get("metric_name") == metric_name]
            if matches:
                return float(matches[-1].get("error_rate"))
            return None

        query = (
            f"search index=* sourcetype=_json earliest=-24h "
            f"| spath metric_name | search metric_name={metric_name} "
            f"| stats latest(error_rate) as current_value"
        )
        rows = self.run_search(query)
        if not rows:
            return None
        latest = rows[0]
        value = latest.get("current_value", latest.get("error_rate"))
        return float(value) if value is not None else None
