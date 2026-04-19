# Enhanced Network Intrusion Detection System (NIDS) with Asynchronous Alarming

A custom Network Intrusion Detection System workflow that combines Suricata packet inspection with a Python asynchronous alerting microservice.

The design bridges passive monitoring and active incident response by continuously parsing Suricata alerts from `eve.json`, triaging severity, and triggering immediate notifications for high/critical events.

## Quick Start

1. Create and activate virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy and edit settings:

```powershell
Copy-Item config\settings.example.yaml config\settings.yaml
```

4. Start Suricata:

```powershell
suricata -i 1 -S rules\custom.rules -l .\suricata-logs
```

5. Start alerter service:

```powershell
python main.py --config config/settings.yaml
```

6. Start dashboard and open browser:

```powershell
python dashboard_server.py --host 127.0.0.1 --port 8080 --alerts-file data/alerts.log.jsonl
```

Open `http://127.0.0.1:8080`

For exact input and output contracts, see `INPUT_OUTPUT_INSTRUCTIONS.md`.

## High-Level Summary

This project uses:

- **Packet Capture & Inspection:** Npcap (Windows packet capture driver)
- **Detection Engine:** Suricata
- **Alerter Backend:** Python (asyncio-based)
- **Data Format:** JSON (`eve.json`)
- **Environment:** Windows PowerShell

Suricata performs high-speed inspection and writes structured events. The Python backend tails those events in near real time and routes alerts based on severity:

- **Low/Medium:** Persisted locally for forensic review
- **High/Critical:** Immediate outbound notifications (webhook and optional SMS via webhook gateway)

## Architecture

1. Suricata monitors traffic on a selected interface using custom rule files.
2. Suricata writes alert events to `eve.json`.
3. Python service tails `eve.json` asynchronously.
4. Service normalizes alert metadata (source IP, signature, timestamp, severity).
5. Service dispatches notifications based on severity thresholds.

## Project Structure

```text
zaid_ds_network_prj/
  app/
    __init__.py
    config.py
    models.py
    notifier.py
    parser.py
    service.py
    utils.py
  config/
    settings.example.yaml
  data/
    alerts.log.jsonl
    sample_eve.json
  rules/
    custom.rules
  scripts/
    run_dashboard.ps1
    run_alerter.ps1
  frontend/
    index.html
    styles.css
    app.js
  dashboard_server.py
  main.py
  requirements.txt
  README.md
```

## Key Features

- **Real-time asynchronous log tailing** for Suricata `eve.json`
- **Severity-based triage pipeline**
- **Webhook notifications** for high/critical alerts
- **Optional multi-endpoint fanout**
- **Structured local JSONL archive** for low/medium and all-severity audit trails
- **Rule-driven intrusion detection** using Suricata custom signatures

## Prerequisites

- Windows 10/11
- Npcap installed
- Suricata installed and in PATH
- Python 3.10+

## Setup

### 1. Create virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure settings

```powershell
Copy-Item config\settings.example.yaml config\settings.yaml
```

Edit `config/settings.yaml`:

- Set `eve_file_path` to your Suricata `eve.json`
- Add webhook URL(s)
- Tune severity threshold and polling interval

## Running Suricata

Use your active interface and custom rule file. Example:

```powershell
suricata -i 1 -S rules\custom.rules -l .\suricata-logs
```

This produces `suricata-logs\eve.json` (path may vary by Suricata config).

## Running the Alerter

```powershell
python main.py --config config/settings.yaml
```

Or with helper script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_alerter.ps1
```

## Running the Frontend Dashboard

Start the dashboard server:

```powershell
python dashboard_server.py --host 127.0.0.1 --port 8080 --alerts-file data/alerts.log.jsonl
```

Or with helper script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_dashboard.ps1
```

Open:

- `http://127.0.0.1:8080`

Available endpoints:

- `/api/health`
- `/api/summary`
- `/api/alerts?limit=200`

The UI polls the backend and displays:

- Total and per-severity counts
- Recent alerts table (time, severity, src/dst, signature, protocol)

## Alert Routing Logic

Suricata alert severity values are interpreted as:

- `1`: Critical
- `2`: High
- `3`: Medium
- `>=4`: Low

Routing behavior:

- If severity label is `high` or `critical`, outbound webhook notifications are sent.
- All alerts are persisted as JSONL to `data/alerts.log.jsonl`.

## Example Event Flow

1. Suricata rule matches malicious pattern.
2. New alert entry appears in `eve.json`.
3. Python service parses and classifies event.
4. If high/critical, payload posted to configured webhook(s).
5. Event archived locally for audit and dashboard ingestion.

## Custom Rules

See `rules/custom.rules` for starter signatures such as:

- ICMP sweep detection
- Basic TCP SYN scan indication
- Suspicious payload marker

Adjust SIDs, thresholds, and content matches for your environment.

## Data Outputs

- `data/alerts.log.jsonl`: normalized alert archive
- Console logs: operational status and notification outcomes

## Security Notes

- Store secret webhook tokens in environment variables or a secure vault.
- Restrict outbound access to approved notification endpoints.
- Validate webhook TLS certificates in production (enabled by default).

## Roadmap

- Add retry queues and dead-letter handling
- Add metrics endpoint for SOC dashboards
- Add SIEM connectors (Splunk/Elastic/Sentinel)
- Add unit and integration tests around parser and notifier

## License

For educational and demonstration use. Add your preferred open-source license before distribution.
