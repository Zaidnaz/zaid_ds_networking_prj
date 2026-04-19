from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


DEFAULT_ALERTS_PATH = Path("data/alerts.log.jsonl")
DEFAULT_STATIC_DIR = Path("frontend")


def load_recent_alerts(alerts_file: Path, limit: int = 100) -> list[dict]:
    if not alerts_file.exists():
        return []

    alerts: list[dict] = []
    with alerts_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                alerts.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return alerts[-limit:]


def summarize(alerts: list[dict]) -> dict:
    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "other": 0,
    }

    for alert in alerts:
        label = str(alert.get("severity_label", "other")).lower()
        if label in counts:
            counts[label] += 1
        else:
            counts["other"] += 1

    return {
        "total": len(alerts),
        "counts": counts,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


class DashboardHandler(SimpleHTTPRequestHandler):
    alerts_file: Path = DEFAULT_ALERTS_PATH

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json({"status": "ok"})
            return

        if parsed.path == "/api/alerts":
            params = parse_qs(parsed.query)
            try:
                limit = int(params.get("limit", ["100"])[0])
            except ValueError:
                limit = 100
            limit = max(1, min(limit, 1000))
            self._send_json({"alerts": load_recent_alerts(self.alerts_file, limit=limit)})
            return

        if parsed.path == "/api/summary":
            alerts = load_recent_alerts(self.alerts_file, limit=1000)
            self._send_json(summarize(alerts))
            return

        return super().do_GET()

    def log_message(self, format: str, *args) -> None:
        # Keep terminal output concise while polling.
        return

    def _send_json(self, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve NIDS frontend dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind")
    parser.add_argument(
        "--alerts-file",
        default=str(DEFAULT_ALERTS_PATH),
        help="Path to alerts JSONL file",
    )
    parser.add_argument(
        "--static-dir",
        default=str(DEFAULT_STATIC_DIR),
        help="Path to frontend static files",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()

    static_dir = Path(args.static_dir)
    if not static_dir.exists():
        raise FileNotFoundError(f"Static dir not found: {static_dir}")

    handler = DashboardHandler
    handler.alerts_file = Path(args.alerts_file)

    server = ThreadingHTTPServer((args.host, args.port), lambda *a, **k: handler(*a, directory=str(static_dir), **k))
    print(f"Dashboard running at http://{args.host}:{args.port}")
    print(f"Reading alerts from: {handler.alerts_file}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down dashboard server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
