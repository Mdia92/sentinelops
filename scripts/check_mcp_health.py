"""Verify Splunk MCP bridge and official Splunk MCP endpoints."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import requests
import urllib3
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / "vendor" / "splunk-mcp" / ".env")
urllib3.disable_warnings()


def check_bridge_http(base_url: str) -> dict:
    result = {"endpoint": base_url, "ok": False, "detail": ""}
    try:
        response = requests.get(f"{base_url.rstrip('/')}/openapi.json", timeout=8)
        result["ok"] = response.status_code == 200
        result["detail"] = f"openapi.json status={response.status_code}"
    except Exception as exc:
        result["detail"] = str(exc)
    return result


async def check_bridge_ping(base_url: str) -> dict:
    result = {"endpoint": f"{base_url}/sse", "ok": False, "detail": ""}
    try:
        from mcp.client.session import ClientSession
        from mcp.client.sse import sse_client

        async with sse_client(url=f"{base_url.rstrip('/')}/sse") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                ping = await session.call_tool("ping", {})
                text = ping.content[0].text if ping.content else "{}"
                payload = json.loads(text) if text.startswith("{") else {"raw": text}
                result["ok"] = payload.get("status") == "ok"
                result["detail"] = json.dumps(payload)
    except Exception as exc:
        result["detail"] = str(exc)
    return result


def check_official_mcp(url: str, token: str) -> dict:
    result = {"endpoint": url, "ok": False, "detail": ""}
    if not token or token.startswith("PASTE_"):
        result["detail"] = "SPLUNK_TOKEN not configured in .env"
        return result
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"client": "sentinelops", "version": "0.1"},
    }
    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
            verify=False,
        )
        result["ok"] = response.status_code == 200
        result["detail"] = response.text[:500]
    except Exception as exc:
        result["detail"] = str(exc)
    return result


def check_splunk_rest(host: str, port: int, token: str) -> dict:
    result = {"endpoint": f"https://{host}:{port}/services/search/jobs/export", "ok": False, "detail": ""}
    if not token or token.startswith("PASTE_"):
        result["detail"] = "SPLUNK_TOKEN not configured in .env"
        return result
    query = 'search index=* | head 1'
    try:
        response = requests.post(
            result["endpoint"],
            headers={"Authorization": f"Bearer {token}"},
            data={"search": query, "output_mode": "json"},
            timeout=20,
            verify=False,
        )
        result["ok"] = response.status_code == 200
        result["detail"] = f"status={response.status_code}, bytes={len(response.text)}"
    except Exception as exc:
        result["detail"] = str(exc)
    return result


async def main() -> int:
    bridge_url = os.getenv("SPLUNK_MCP_BRIDGE_URL", "http://localhost:8765")
    official_url = os.getenv("SPLUNK_OFFICIAL_MCP_URL", "https://localhost:8089/services/mcp")
    token = os.getenv("SPLUNK_TOKEN", "")

    checks = [
        ("bridge_http", check_bridge_http(bridge_url)),
        ("splunk_rest", check_splunk_rest(os.getenv("SPLUNK_HOST", "localhost"), int(os.getenv("SPLUNK_PORT", "8089")), token)),
        ("official_mcp", check_official_mcp(official_url, token)),
    ]

    try:
        checks.append(("bridge_ping", await check_bridge_ping(bridge_url)))
    except ImportError:
        checks.append(("bridge_ping", {"ok": False, "detail": "mcp client libs unavailable"}))

    print(json.dumps({name: payload for name, payload in checks}, indent=2))
    return 0 if any(item[1].get("ok") for item in checks) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
