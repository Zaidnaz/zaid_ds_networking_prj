param(
    [string]$ConfigPath = "config/settings.yaml"
)

if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Error "Python virtual environment not found at .venv. Create it first with: python -m venv .venv"
    exit 1
}

. .\.venv\Scripts\Activate.ps1
python main.py --config $ConfigPath
