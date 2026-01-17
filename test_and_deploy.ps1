# test_and_deploy.ps1
# Runs pytest; if tests pass, deploys checking_on_the_boys.py via scp.

$ErrorActionPreference = "Stop"

Write-Host "Running tests..." -ForegroundColor Cyan

# Move to the folder containing this script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# --- Config ---
# Deploy all Python files under the `bot` folder.
$SourceDir = ".\bot"
$KeyPath = ".\Prod Key Pair.pem"
$RemoteUserHost = "ec2-user@ec2-18-191-173-105.us-east-2.compute.amazonaws.com"
$RemotePath = "BigBot2/"
# --------------

# Basic checks
if (-not (Test-Path $SourceDir)) {
    Write-Error "Cannot find source directory: $SourceDir"
    exit 1
}

# Collect files to deploy
$FilesToDeploy = Get-ChildItem -Path $SourceDir -Filter *.py -File | Select-Object -ExpandProperty Name
if (-not $FilesToDeploy -or $FilesToDeploy.Count -eq 0) {
    Write-Error "No .py files found in $SourceDir to deploy."
    exit 1
}

if (-not (Test-Path $KeyPath)) {
    Write-Error "Cannot find SSH key file at: $KeyPath"
    exit 1
}

# Ensure python exists
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not on PATH."
    exit 1
}

# Ensure pytest exists (install if missing)
python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('pytest') else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "pytest not found. Installing pytest..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { Write-Error "Failed to upgrade pip."; exit 1 }
    python -m pip install pytest
    if ($LASTEXITCODE -ne 0) { Write-Error "Failed to install pytest."; exit 1 }
}

# Run tests
python -m pytest -q
$testExit = $LASTEXITCODE

if ($testExit -ne 0) {
    Write-Host "Tests failed. Not deploying." -ForegroundColor Red
    exit $testExit
}

Write-Host "Tests passed. Deploying $FileToDeploy..." -ForegroundColor Green

# Use scp (requires OpenSSH client available on Windows)
if (-not (Get-Command scp -ErrorAction SilentlyContinue)) {
    Write-Error "scp not found. Install OpenSSH Client (Windows Optional Features) or use PuTTY pscp."
    exit 1
}

# Deploy files from $SourceDir
$overallExit = 0
foreach ($file in $FilesToDeploy) {
    $localPath = Join-Path $SourceDir $file
    Write-Host "Deploying $localPath -> $RemoteUserHost:$RemotePath$file" -ForegroundColor Cyan
    scp -i $KeyPath $localPath "$RemoteUserHost`:$RemotePath$file"
    $scpExit = $LASTEXITCODE
    if ($scpExit -ne 0) {
        Write-Host "Deploy failed for $file (scp exit code $scpExit)." -ForegroundColor Red
        $overallExit = $scpExit
        break
    }
}

if ($overallExit -ne 0) {
    exit $overallExit
}

Write-Host "All files deployed successfully." -ForegroundColor Green
exit 0