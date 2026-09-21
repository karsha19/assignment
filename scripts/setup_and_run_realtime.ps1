param(
    [string]$ApiUrl = "http://127.0.0.1:8000",
    [string]$Username = "admin",
    [string]$Password = "Admin@12345",
    [switch]$InstallTesseract
)

Write-Host "Setting up virtual environment and running realtime test..."

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $root\..\

if (-not (Test-Path .venv)) {
    Write-Host "Creating virtual environment .venv..."
    python -m venv .venv
} else {
    Write-Host ".venv already exists"
}

Write-Host "Ensuring execution policy for this session..."
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force

Write-Host "Activating virtual environment..."
& .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip and installing requirements..."
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

Write-Host "Installing minimal runtime deps (requests, websockets) to be safe..."
pip install requests websockets

if ($InstallTesseract) {
    Write-Host "Tesseract install requested. Please install Tesseract manually on Windows from: https://github.com/UB-Mannheim/tesseract/wiki"
}

Write-Host "Running realtime test script against $ApiUrl"
python tools\test_realtime.py --api-url $ApiUrl --username $Username --password $Password

Pop-Location

Write-Host "Done. Paste any output here if you want help interpreting it." 
