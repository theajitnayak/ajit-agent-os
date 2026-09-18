param([string]$Python = "python")
$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    & $Python -c "import sys; assert sys.version_info >= (3,10), 'Python 3.10+ required'"
    if ($LASTEXITCODE -ne 0) { throw "Install Python 3.10 or newer, then rerun setup." }
    if (-not (Test-Path -LiteralPath '.venv')) {
        & $Python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Could not create virtual environment." }
    }
    & .\.venv\Scripts\python.exe -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Verification failed." }
    & .\.venv\Scripts\python.exe -m ajit_os examples/fictional-deals.json
    if ($LASTEXITCODE -ne 0) { throw "Demo failed." }
    Write-Host 'Ready. No packages, credentials or global settings were changed.'
} finally { Pop-Location }
