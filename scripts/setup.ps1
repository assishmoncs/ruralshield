$ErrorActionPreference = "Stop"

$Python = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
& $Python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt pytest ruff

Write-Host ""
Write-Host "RuralShield local environment is ready."
Write-Host "Activate it later with: .\.venv\Scripts\Activate.ps1"
Write-Host "Run checks with: pytest -q; ruff check backend/lambda ml tests"
