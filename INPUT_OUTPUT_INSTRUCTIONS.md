# Input and Expected Output Instructions

This document defines the required inputs and expected outputs for the NIDS alerter pipeline and dashboard.

## Scope

Components covered:

- Alerter service (`main.py` + `app/` modules)
- Dashboard server (`dashboard_server.py`)
- Frontend dashboard (`frontend/`)

## 1. Alerter Service

Run command:

```powershell
python main.py --config config/settings.yaml
```

### 1.1 Required Inputs

1. Configuration file (`config/settings.yaml`)
2. Suricata event file (`eve.json`) containing JSON lines

### 1.2 Config Input Format

Example:

```yaml
eve_file_path: ./suricata-logs/eve.json
archive_output_path: ./data/alerts.log.jsonl
high_or_critical_labels:
  - high
  - critical
webhook_urls:
  - https://example.com/security-webhook
poll_interval_seconds: 0.5
request_timeout_seconds: 5.0
log_level: INFO
```

Field meaning:

- `eve_file_path`: path to Suricata `eve.json`
- `archive_output_path`: output file for normalized alerts
- `high_or_critical_labels`: labels that trigger active notifications
- `webhook_urls`: one or more outbound endpoints for high/critical alerts
- `poll_interval_seconds`: tail polling interval
- `request_timeout_seconds`: outbound webhook timeout
- `log_level`: logger level (`DEBUG|INFO|WARNING|ERROR`)

### 1.3 Event Input Format (from `eve.json`)

Each line must be valid JSON.

Minimum useful alert event structure:

```json
{
  "timestamp": "2026-04-19T10:10:01.000000+0000",
  "event_type": "alert",
  "src_ip": "192.168.1.22",
  "dest_ip": "192.168.1.1",
  "proto": "TCP",
  "alert": {
    "signature": "Custom NIDS suspicious payload marker",
    "category": "Potentially Bad Traffic",
    "severity": 2
  }
}
```

Notes:

- Non-`alert` events are ignored.
- Invalid JSON lines are skipped.

### 1.4 Expected Outputs

#### A) Console Output

Expected startup log:

```text
Starting alert pipeline. Watching: <path-to-eve.json>
```

Expected processing logs:

- High/Critical:

```text
High-priority alert detected src=<ip> signature=<sig> severity=<label>
```

- Low/Medium:

```text
Alert captured for review src=<ip> signature=<sig> severity=<label>
```

#### B) Archive Output File

Output file: `data/alerts.log.jsonl`

Each processed alert is written as one normalized JSON line.

Example output line:

```json
{
  "timestamp": "2026-04-19T10:10:01.000000+0000",
  "src_ip": "192.168.1.22",
  "dest_ip": "192.168.1.1",
  "signature": "Custom NIDS suspicious payload marker",
  "severity": 2,
  "severity_label": "high",
  "category": "Potentially Bad Traffic",
  "proto": "TCP",
  "event_type": "alert",
  "raw": {"...": "original event payload"}
}
```

#### C) Webhook Output (High/Critical only)

For severity labels in `high_or_critical_labels`, payload sent to each configured URL:

```json
{
  "timestamp": "2026-04-19T10:10:01.000000+0000",
  "src_ip": "192.168.1.22",
  "dest_ip": "192.168.1.1",
  "signature": "Custom NIDS suspicious payload marker",
  "severity": "high",
  "category": "Potentially Bad Traffic"
}
```

## 2. Dashboard Server

Run command:

```powershell
python dashboard_server.py --host 127.0.0.1 --port 8080 --alerts-file data/alerts.log.jsonl
```

### 2.1 Required Input

- Alerts archive JSONL file (`data/alerts.log.jsonl`)

### 2.2 Expected API Outputs

#### A) Health Endpoint

Request:

```http
GET /api/health
```

Expected response:

```json
{"status": "ok"}
```

#### B) Alerts Endpoint

Request:

```http
GET /api/alerts?limit=200
```

Expected response shape:

```json
{
  "alerts": [
    {
      "timestamp": "...",
      "src_ip": "...",
      "dest_ip": "...",
      "signature": "...",
      "severity": 2,
      "severity_label": "high",
      "category": "...",
      "proto": "TCP",
      "event_type": "alert",
      "raw": {}
    }
  ]
}
```

#### C) Summary Endpoint

Request:

```http
GET /api/summary
```

Expected response shape:

```json
{
  "total": 2,
  "counts": {
    "critical": 0,
    "high": 1,
    "medium": 1,
    "low": 0,
    "other": 0
  },
  "generated_at": "2026-04-19T09:34:19.237243+00:00"
}
```

## 3. Frontend Dashboard

URL:

```text
http://127.0.0.1:8080
```

### 3.1 Input to Frontend

Frontend reads from:

- `/api/alerts?limit=200`
- `/api/summary`

### 3.2 Expected UI Output

- Status indicator shows connected/disconnected state
- Severity cards show total and per-level counts
- Table lists recent alerts with:
  - Time
  - Severity
  - Source IP
  - Destination IP
  - Signature
  - Protocol

## 4. Severity Mapping Rules

The project maps Suricata numeric severities to labels:

- `1` -> `critical`
- `2` -> `high`
- `3` -> `medium`
- `4+` -> `low`

## 5. Quick Validation Checklist

1. Start alerter service.
2. Append sample lines from `data/sample_eve.json` to `suricata-logs/eve.json`.
3. Confirm new lines appear in `data/alerts.log.jsonl`.
4. Start dashboard server.
5. Call `/api/health` and `/api/summary`.
6. Open dashboard URL and verify rows/counters update.
