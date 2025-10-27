# Run the Flask app using Waitress (production-friendly for Windows)
# Usage: .\run.ps1 [port]
param(
    [int]$port = 5000
)
$python = Join-Path -Path $PSScriptRoot -ChildPath 'venv\Scripts\python.exe'
if (-Not (Test-Path $python)) {
    Write-Error "Python venv not found. Create it with: python -m venv venv"
    exit 1
}
# Install waitress if missing
& $python -m pip install --quiet waitress
# Start waitress
& $python -m waitress --listen=0.0.0.0:$port app:app
