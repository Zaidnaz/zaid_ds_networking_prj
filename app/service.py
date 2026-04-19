from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from app.config import Settings
from app.models import NormalizedAlert
from app.notifier import WebhookNotifier
from app.parser import normalize_alert_event, parse_json_line
from app.utils import ensure_parent_dir

logger = logging.getLogger(__name__)


class AlertPipelineService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.eve_path = Path(settings.eve_file_path)
        self.archive_path = Path(settings.archive_output_path)
        self.notifier = WebhookNotifier(settings.webhook_urls, settings.request_timeout_seconds)

    async def start(self) -> None:
        ensure_parent_dir(self.archive_path)
        logger.info("Starting alert pipeline. Watching: %s", self.eve_path)

        while not self.eve_path.exists():
            logger.warning("Waiting for eve.json file to appear at: %s", self.eve_path)
            await asyncio.sleep(self.settings.poll_interval_seconds)

        await self._tail_loop()

    async def _tail_loop(self) -> None:
        offset = self.eve_path.stat().st_size

        while True:
            try:
                file_size = self.eve_path.stat().st_size
                if file_size < offset:
                    # Handle truncation/rotation by resetting offset.
                    offset = 0

                if file_size == offset:
                    await asyncio.sleep(self.settings.poll_interval_seconds)
                    continue

                with self.eve_path.open("r", encoding="utf-8") as eve_handle:
                    eve_handle.seek(offset)
                    new_lines = eve_handle.readlines()
                    offset = eve_handle.tell()
            except FileNotFoundError:
                logger.warning("eve.json disappeared, waiting for file to return: %s", self.eve_path)
                await asyncio.sleep(self.settings.poll_interval_seconds)
                continue

            for line in new_lines:
                event = parse_json_line(line)
                if not event:
                    continue

                alert = normalize_alert_event(event)
                if not alert:
                    continue

                await self._handle_alert(alert)

    async def _handle_alert(self, alert: NormalizedAlert) -> None:
        payload = alert.to_dict()
        self._archive_alert(payload)

        if alert.severity_label in self.settings.high_or_critical_labels:
            logger.warning(
                "High-priority alert detected src=%s signature=%s severity=%s",
                alert.src_ip,
                alert.signature,
                alert.severity_label,
            )
            await self.notifier.notify(
                {
                    "timestamp": alert.timestamp,
                    "src_ip": alert.src_ip,
                    "dest_ip": alert.dest_ip,
                    "signature": alert.signature,
                    "severity": alert.severity_label,
                    "category": alert.category,
                }
            )
        else:
            logger.info(
                "Alert captured for review src=%s signature=%s severity=%s",
                alert.src_ip,
                alert.signature,
                alert.severity_label,
            )

    def _archive_alert(self, payload: dict[str, object]) -> None:
        with self.archive_path.open("a", encoding="utf-8") as out:
            out.write(json.dumps(payload, ensure_ascii=True) + "\n")
