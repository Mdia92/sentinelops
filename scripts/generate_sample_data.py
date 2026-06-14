"""Generate sample_incidents.log for Splunk file upload."""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

SERVICES = [
    "auth_service",
    "checkout_service",
    "payment_service",
    "inventory_service",
    "notification_service",
    "search_service",
    "api_gateway",
]

AUTH_SPIKE_RATES = [6.2, 7.1, 8.3, 9.0, 6.8, 7.5]
CHECKOUT_STRESS_RATES = [3.8, 4.1, 4.4, 3.9, 4.2]


def build_entries(count: int = 50) -> list[dict]:
    now = datetime.now(timezone.utc)
    entries: list[dict] = []

    for index in range(count):
        timestamp = now - timedelta(minutes=count - index)
        metric_name = random.choice(SERVICES)

        if index in {38, 39, 40, 41, 42, 43}:
            metric_name = "auth_service"
            error_rate = AUTH_SPIKE_RATES[index - 38]
        elif index in {36, 37, 44, 45}:
            metric_name = "checkout_service"
            error_rate = CHECKOUT_STRESS_RATES[index - 36 if index < 40 else index - 44]
        else:
            error_rate = round(random.uniform(0.4, 4.8), 2)

        entries.append(
            {
                "timestamp": timestamp.isoformat(),
                "metric_name": metric_name,
                "error_rate": error_rate,
            }
        )

    return entries


def main() -> None:
    output = Path(__file__).resolve().parents[1] / "sample_incidents.log"
    entries = build_entries()
    with output.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + "\n")

    auth_spikes = [e for e in entries if e["metric_name"] == "auth_service" and e["error_rate"] > 5]
    print(f"Wrote {len(entries)} entries to {output}")
    print(f"auth_service entries above 5%: {len(auth_spikes)}")


if __name__ == "__main__":
    main()
