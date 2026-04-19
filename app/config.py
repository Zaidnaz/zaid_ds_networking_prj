from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class Settings:
    eve_file_path: str
    archive_output_path: str = "data/alerts.log.jsonl"
    high_or_critical_labels: set[str] = field(default_factory=lambda: {"high", "critical"})
    webhook_urls: list[str] = field(default_factory=list)
    poll_interval_seconds: float = 0.5
    request_timeout_seconds: float = 5.0
    log_level: str = "INFO"


SEVERITY_LABELS_DEFAULT = {
    1: "critical",
    2: "high",
    3: "medium",
    4: "low",
}


def _normalize_settings(raw: dict[str, Any]) -> Settings:
    if "eve_file_path" not in raw:
        raise ValueError("Missing required key: eve_file_path")

    labels = set(raw.get("high_or_critical_labels", ["high", "critical"]))
    webhook_urls = [url.strip() for url in raw.get("webhook_urls", []) if str(url).strip()]

    return Settings(
        eve_file_path=str(raw["eve_file_path"]),
        archive_output_path=str(raw.get("archive_output_path", "data/alerts.log.jsonl")),
        high_or_critical_labels={label.lower() for label in labels},
        webhook_urls=webhook_urls,
        poll_interval_seconds=float(raw.get("poll_interval_seconds", 0.5)),
        request_timeout_seconds=float(raw.get("request_timeout_seconds", 5.0)),
        log_level=str(raw.get("log_level", "INFO")),
    )


def load_settings(config_path: str) -> Settings:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    return _normalize_settings(raw)
