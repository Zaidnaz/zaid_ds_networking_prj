from __future__ import annotations

import json
from typing import Any

from app.config import SEVERITY_LABELS_DEFAULT
from app.models import NormalizedAlert, utc_now_iso


def normalize_alert_event(raw_event: dict[str, Any]) -> NormalizedAlert | None:
    if raw_event.get("event_type") != "alert":
        return None

    alert = raw_event.get("alert", {})
    severity = int(alert.get("severity", 4))
    severity_label = SEVERITY_LABELS_DEFAULT.get(severity, "low")

    return NormalizedAlert(
        timestamp=str(raw_event.get("timestamp", utc_now_iso())),
        src_ip=str(raw_event.get("src_ip", "unknown")),
        dest_ip=str(raw_event.get("dest_ip", "unknown")),
        signature=str(alert.get("signature", "unknown-signature")),
        severity=severity,
        severity_label=severity_label,
        category=str(alert.get("category", "uncategorized")),
        proto=str(raw_event.get("proto", "unknown")),
        event_type="alert",
        raw=raw_event,
    )


def parse_json_line(line: str) -> dict[str, Any] | None:
    stripped = line.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None
