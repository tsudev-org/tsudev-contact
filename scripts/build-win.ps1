# build-win.ps1 - Gói bản phát hành Windows x64 cho tsudev-contact.
# LƯU Ý: file này PHẢI lưu ở UTF-8 CÓ BOM - Windows PowerShell 5.1 đọc .ps1 không BOM
# theo bảng mã ANSI, làm hỏng chữ tiếng Việt và gây lỗi cú pháp khi chạy.
# Chạy từ thư mục gốc repo:  powershell -ExecutionPolicy Bypass -File scripts\build-win.ps1
# Tên file xuất ra do src/app_info.py quyết định (.standards/docs/VERSIONING.md mục 2).
# Sản phẩm trong release/: <ten>.exe, <ten>.cdx.json (SBOM), SHA256SUMS.txt.

[CmdletBinding()]
param(
    # Bỏ qua bước cài đặt phụ thuộc (dùng khi môi trường đã sẵn sàng).
    [switch]$SkipDeps,
    # Bỏ qua bước chạy test (CI đã chạy test ở bước riêng).
    [switch]$SkipTests,
    # Giữ lại thư mục build/ trung gian để chẩn đoán lỗi PyInstaller.
    [switch]$KeepBuild,
    # Ký số bản .exe sau khi build (xem scripts\sign-win.ps1 để biết giới hạn).
    [switch]$Sign,
    # Tham số chứng thư chuyển thẳng cho sign-win.ps1: -PfxPath / -Thumbprint / -SelfSigned.
    [string]$PfxPath,
    [string]$Thumbprint,
    [switch]$SelfSigned,
    # Trình Python dùng để build (mặc định 'python' trong PATH hoặc venv đang bật).
    [string]$Python = 'python'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Invoke-Checked([string]$what) {
    if ($LASTEXITCODE -ne 0) { throw "$what thất bại (mã $LASTEXITCODE)." }
}

# --- 1. Kiểm tra Python ---
if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
    throw "Không tìm thấy '$Python'. Cài Python 3.11 rồi chạy lại."
}
Write-Step "Python: $(& $Python --version)"

# --- 2. Phụ thuộc: CHỈ cài từ file khóa có hash (SECURITY_BASELINE mục 5) ---
if (-not $SkipDeps) {
    Write-Step 'Cài phụ thuộc đã khóa (--require-hashes)'
    & $Python -m pip install --disable-pip-version-check --require-hashes --no-deps -r requirements.txt -r requirements-dev.txt
    Invoke-Checked 'Cài phụ thuộc'
}

# --- 3. Tên bản phát hành (nguồn duy nhất: src/app_info.py) ---
$releaseName = & $Python -c "from src.app_info import RELEASE_BASENAME; print(RELEASE_BASENAME)"
Invoke-Checked 'Đọc RELEASE_BASENAME'
$releaseName = $releaseName.Trim()
Write-Step "Bản phát hành: $releaseName.exe"

# --- 4. Kiểm thử ---
if (-not $SkipTests) {
    Write-Step 'Chạy test (lõi + giao diện)'
    & $Python -m pytest -q -p no:cacheprovider tests
    Invoke-Checked 'Kiểm thử'
}

# --- 5. Đóng gói ---
Write-Step 'PyInstaller'
& $Python -m PyInstaller --noconfirm --clean Contacts.spec
Invoke-Checked 'PyInstaller'

# --- 6. Chuyển sản phẩm sang release/ ---
$built = Join-Path $repoRoot "dist\$releaseName.exe"
if (-not (Test-Path $built)) { throw "Không thấy sản phẩm build tại $built" }
$releaseDir = Join-Path $repoRoot 'release'
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
Get-ChildItem $releaseDir -File | Remove-Item -Force
$final = Join-Path $releaseDir "$releaseName.exe"
Move-Item -Force $built $final
if (-not $KeepBuild) { Remove-Item -Recurse -Force (Join-Path $repoRoot 'build') -ErrorAction SilentlyContinue }

# --- 7. Ký số (tùy chọn) - phải ký TRƯỚC khi tính mã băm ---
if ($Sign -or $PfxPath -or $Thumbprint -or $SelfSigned) {
    Write-Step 'Ký số bản .exe'
    $signArgs = @{ Path = $final }
    if ($PfxPath)    { $signArgs['PfxPath'] = $PfxPath }
    if ($Thumbprint) { $signArgs['Thumbprint'] = $Thumbprint }
    if ($SelfSigned) { $signArgs['SelfSigned'] = $true }
    & (Join-Path $PSScriptRoot 'sign-win.ps1') @signArgs
}

# --- 8. SBOM CycloneDX của các thành phần đóng gói (SECURITY_BASELINE mục 5) ---
Write-Step 'Sinh SBOM (CycloneDX)'
$sbom = Join-Path $releaseDir "$releaseName.cdx.json"
& $Python -m cyclonedx_py requirements requirements.txt --output-format JSON --output-file $sbom
Invoke-Checked 'Sinh SBOM'

# --- 9. Mã băm để người tải tự đối chiếu ---
Write-Step 'Tính SHA256SUMS.txt'
$lines = Get-ChildItem $releaseDir -File | Where-Object { $_.Name -ne 'SHA256SUMS.txt' } | Sort-Object Name | ForEach-Object {
    "$((Get-FileHash -Algorithm SHA256 $_.FullName).Hash.ToLower())  $($_.Name)"
}
$lines | Set-Content -Path (Join-Path $releaseDir 'SHA256SUMS.txt') -Encoding ascii
$lines | ForEach-Object { Write-Host "  $_" }

$sizeMb = [math]::Round((Get-Item $final).Length / 1MB, 1)
Write-Step "XONG: $final ($sizeMb MB)"
