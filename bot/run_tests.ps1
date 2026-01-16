# run_tests.ps1
# Runs pytest for the project in the current folder.

Write-Host "Running pytest..." -ForegroundColor Cyan

# Move to the folder containing this script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Find Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python is not installed or not on PATH."
    exit 1
}

# Check whether pytest is installed (PowerShell-friendly)
$pytestCheck = python -c "import importlib.util; import sys; sys.exit(0 if importlib.util.find_spec('pytest') else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "pytest not found. Installing pytest..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { Write-Error "Failed to upgrade pip."; exit 1 }

    python -m pip install pytest
    if ($LASTEXITCODE -ne 0) { Write-Error "Failed to install pytest."; exit 1 }
}

# Run tests
python -m pytest -q
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "All tests passed." -ForegroundColor Green
} else {
    Write-Host "Tests failed." -ForegroundColor Red
}

exit $exitCode