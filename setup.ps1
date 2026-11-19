# DesiQuip one-time setup for a Windows machine (built for the RTX 4070 laptop).
# Run from the repo root in PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
# Safe to run again: it skips anything already installed.

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "    OK  $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "    !!  $msg" -ForegroundColor Yellow }
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
}
function Has($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Winget-Install($id, $name) {
    Write-Host "    installing $name ..."
    winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements | Out-Null
    Refresh-Path
}

Step "Checking disk space"
$drive = (Get-Item $Root).PSDrive
$freeGB = [math]::Round($drive.Free / 1GB)
if ($freeGB -lt 50) { Warn "Only $freeGB GB free on $($drive.Name): (spec asks for 100 GB). Renders and models need room." }
else { Ok "$freeGB GB free on $($drive.Name):" }
$cFree = [math]::Round((Get-PSDrive C).Free / 1GB)
if ($cFree -lt 10) { Warn "Only $cFree GB free on C: - npm/pip caches and the Chrome render engine live there." }

Step "Checking path length (Windows 260-character limit)"
# Deepest dependency file is ~145 chars below the repo root (.venv\Lib\site-packages\...).
$longPaths = (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -ErrorAction SilentlyContinue).LongPathsEnabled -eq 1
if (-not $longPaths -and ($Root.Length + 150) -gt 259) {
    throw ("Repo path is too long ($($Root.Length) chars) for Windows' 260-char limit. Either clone to a short " +
           "folder such as C:\dev\DesiQuip, or enable long paths (admin PowerShell): " +
           "Set-ItemProperty HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem LongPathsEnabled 1")
}
Ok "Repo path is $($Root.Length) chars$(if ($longPaths) { ' (long paths enabled)' })"

Step "System tools (Python 3.13, Node.js 22 LTS, FFmpeg, Git)"
if (-not (Has winget)) { throw "winget not found. Install 'App Installer' from the Microsoft Store, then re-run." }
$py = Get-Command py -ErrorAction SilentlyContinue
$pyOk = $false
if ($py) { & py -3.13 --version 2>$null | Out-Null; $pyOk = ($LASTEXITCODE -eq 0) }
if (-not $pyOk) { Winget-Install "Python.Python.3.13" "Python 3.13" } else { Ok "Python 3.13" }

$nodeOk = $false
if (Has node) { $major = [int]((node --version).TrimStart("v").Split(".")[0]); $nodeOk = ($major -ge 20 -and $major % 2 -eq 0) }
if (-not $nodeOk) { Winget-Install "OpenJS.NodeJS.LTS" "Node.js LTS" } else { Ok "Node.js $(node --version)" }

if (-not (Has ffmpeg)) { Winget-Install "Gyan.FFmpeg" "FFmpeg" } else { Ok "FFmpeg" }
if (-not (Has git))    { Winget-Install "Git.Git" "Git" } else { Ok "Git" }
Refresh-Path

Step "NVIDIA GPU"
$gpu = $false
if (Has nvidia-smi) {
    $name = (nvidia-smi --query-gpu=name,memory.total --format=csv,noheader) -join ", "
    Ok "$name"; $gpu = $true
} else { Warn "No NVIDIA driver found - Whisper and encoding will run on the CPU (slower). Install the latest NVIDIA driver." }

Step "Python environment (.venv)"
if (-not (Test-Path ".venv\Scripts\python.exe")) { & py -3.13 -m venv .venv }
$vpy = Join-Path $Root ".venv\Scripts\python.exe"
& $vpy -m pip install --quiet --upgrade pip
& $vpy -m pip install --quiet -r requirements.txt
if ($gpu) {
    # CUDA 12 runtime libraries for faster-whisper (CTranslate2) - no full CUDA toolkit needed.
    & $vpy -m pip install --quiet "nvidia-cublas-cu12" "nvidia-cudnn-cu12==9.*"
}
Ok "Python packages installed"

Step "Remotion (video template)"
Push-Location remotion
npm ci --no-audit --no-fund
node node_modules/@remotion/cli/remotion-cli.js browser ensure
Pop-Location
Ok "Remotion ready"

Step "Secrets"
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env"; Ok ".env created from .env.example (fill in keys when you reach that week)" }
else { Ok ".env already exists (left unchanged)" }
New-Item -ItemType Directory -Force secrets, jobs, logs | Out-Null
if (-not (Test-Path "secrets\client_secret.json")) { Warn "secrets\client_secret.json missing - needed only for YouTube upload (see the API keys guide)." }

Step "Self-test"
& $vpy -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Unit tests failed - see output above." }
Ok "All unit tests pass"

Write-Host "`nSetup complete. Make the demo Short (about 1-4 min on the GPU laptop):" -ForegroundColor Green
Write-Host "    Copy-Item -Recurse examples\demo-001 jobs\"
Write-Host "    .\.venv\Scripts\python -m desiquip make demo-001"
Write-Host "    -> jobs\demo-001\final.mp4"
