$ErrorActionPreference = "Stop"

Write-Host "Local Media Toolkit bootstrap for Windows"

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "FFmpeg not found. Installing Gyan.FFmpeg with winget..."
        winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
        Write-Host "FFmpeg installed. You may need to reopen PowerShell so PATH is refreshed."
    } else {
        throw "Neither FFmpeg nor winget was found. Install FFmpeg using https://ffmpeg.org/download.html"
    }
} else {
    Write-Host "FFmpeg already available."
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.10+ is required. Install Python, then rerun this script."
}

python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Write-Host "Done. Run: .\.venv\Scripts\Activate.ps1; localmedia doctor"
