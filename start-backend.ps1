Set-Location $PSScriptRoot\backend
$env:PYTHONPATH = "."
if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -q
if (-not (Test-Path .env)) { Copy-Item ..\.env.example .env }
python scripts\seed.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
