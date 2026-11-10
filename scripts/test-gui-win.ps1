# test-gui-win.ps1 - Chạy toàn bộ test (lõi + giao diện PySide6) trên Windows trong venv riêng.
# LƯU Ý: file này PHẢI lưu ở UTF-8 CÓ BOM (xem đầu scripts/build-win.ps1).
# Chạy từ thư mục gốc repo:  powershell -ExecutionPolicy Bypass -File scripts\test-gui-win.ps1
# Mặc định giao diện chạy offscreen; thêm -Visible để thấy cửa sổ thật trong lúc test.

[CmdletBinding()]
param(
    [switch]$Visible,
    # Thư mục venv (mặc định trong %TEMP%, không đụng Python hệ thống).
    [string]$Venv = (Join-Path $env:TEMP 'tsudev-contact-venv')
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

if (-not (Test-Path (Join-Path $Venv 'Scripts\python.exe'))) {
    Write-Step "Tạo venv tại $Venv"
    & py -3.11 -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw 'Không tạo được venv (cần Python 3.11: py -3.11).' }
}
$python = Join-Path $Venv 'Scripts\python.exe'
Write-Step 'Cài phụ thuộc đã khóa (--require-hashes)'
& $python -m pip install --disable-pip-version-check -q --require-hashes --no-deps -r requirements.txt -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'Cài phụ thuộc thất bại.' }

if (-not $Visible) { $env:QT_QPA_PLATFORM = 'offscreen' }
Write-Step 'Chạy pytest'
& $python -m pytest -q -p no:cacheprovider tests
if ($LASTEXITCODE -ne 0) { throw 'Kiểm thử thất bại.' }
Write-Step 'XONG: toàn bộ test đạt.'
