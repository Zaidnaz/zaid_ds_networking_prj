from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class WebhookNotifier:
    def __init__(self, webhook_urls: list[str], timeout_seconds: float) -> None:
        self.webhook_urls = webhook_urls
        self.timeout_seconds = timeout_seconds

    async def notify(self, payload: dict[str, Any]) -> None:
        if not self.webhook_urls:
            logger.debug("No webhook URLs configured; skipping notify")
            return

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            tasks = [self._post(client, url, payload) for url in self.webhook_urls]
            await asyncio.gather(*tasks)

    async def _post(self, client: httpx.AsyncClient, url: str, payload: dict[str, Any]) -> None:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info("Webhook notification sent to %s (status=%s)", url, response.status_code)
        except Exception as exc:
            logger.error("Failed webhook notification to %s: %s", url, exc)
