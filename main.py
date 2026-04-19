from __future__ import annotations

import argparse
import asyncio
import logging

from app.config import Settings, load_settings
from app.service import AlertPipelineService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Async Suricata alerting microservice")
    parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="Path to YAML configuration file",
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def run(settings: Settings) -> None:
    service = AlertPipelineService(settings)
    await service.start()


def main() -> None:
    args = parse_args()
    settings = load_settings(args.config)
    configure_logging(settings.log_level)

    try:
        asyncio.run(run(settings))
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Shutdown requested by user")


if __name__ == "__main__":
    main()
