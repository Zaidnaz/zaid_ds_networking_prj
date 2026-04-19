param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8080,
    [string]$AlertsFile = "data/alerts.log.jsonl"
)

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Error "Python virtual environment not found at .venv. Create it first with: python -m venv .venv"
    exit 1
}

.\.venv\Scripts\python dashboard_server.py --host $Host --port $Port --alerts-file $AlertsFile
