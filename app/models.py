from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class NormalizedAlert:
    timestamp: str
    src_ip: str
    dest_ip: str
    signature: str
    severity: int
    severity_label: str
    category: str
    proto: str
    event_type: str
    raw: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
