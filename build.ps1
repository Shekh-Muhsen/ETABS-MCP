<#
.SYNOPSIS
    Build etabs-mcp.exe and pack into etabs-mcp.mcpb.

.PARAMETER SkipPyInstaller
    Skip PyInstaller and use the existing dist/etabs-mcp.exe.

.PARAMETER Install
    After packing, hot-swap the exe into the Claude Desktop extension folder.

.EXAMPLE
    .\build.ps1
    .\build.ps1 -SkipPyInstaller
    .\build.ps1 -Install
    .\build.ps1 -SkipPyInstaller -Install
#>
param(
    [switch]$SkipPyInstaller,
    [switch]$Install
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

function Step { param($msg) Write-Host "`n==> $msg" -ForegroundColor Cyan }
function OK   { param($msg) Write-Host "    OK: $msg" -ForegroundColor Green }
function Warn { param($msg) Write-Host "    WARN: $msg" -ForegroundColor Yellow }
function Fail { param($msg) Write-Host "    FAIL: $msg" -ForegroundColor Red; exit 1 }

# ---- 1. PyInstaller ----------------------------------------------------------
if (-not $SkipPyInstaller) {
    Step "PyInstaller -- compiling src + skills into dist/etabs-mcp.exe"

    $py = $null
    foreach ($cmd in @("py", "python", "python3")) {
        try { $py = (Get-Command $cmd -ErrorAction Stop).Source; break } catch {}
    }
    if (-not $py) { Fail "Python not found. Install Python and retry." }
    OK "Python: $py"

    Push-Location $Root
    try {
        # Native exes write INFO to stderr; temporarily allow non-terminating errors
        $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        & $py -m PyInstaller mcpb/etabs-mcp.spec --noconfirm
        $ec = $LASTEXITCODE
        $ErrorActionPreference = $prev
        if ($ec -ne 0) { Fail "PyInstaller failed (exit $ec)." }
    } finally { Pop-Location }

    $exe = Join-Path $Root "dist\etabs-mcp.exe"
    if (-not (Test-Path $exe)) { Fail "dist/etabs-mcp.exe not found after build." }
    $mb = [math]::Round((Get-Item $exe).Length / 1MB, 1)
    OK "dist/etabs-mcp.exe  ($mb MB)"
} else {
    Step "PyInstaller skipped -- using existing dist/etabs-mcp.exe"
    $exe = Join-Path $Root "dist\etabs-mcp.exe"
    if (-not (Test-Path $exe)) { Fail "dist/etabs-mcp.exe not found. Run without -SkipPyInstaller first." }
    OK "Using $exe"
}

# ---- 1b. Sync version from version.py → manifest.json -----------------------
Step "Syncing version from src/etabs_mcp/version.py -> mcpb/manifest.json"

$versionPy = Join-Path $Root "src\etabs_mcp\version.py"
$manifestPath = Join-Path $Root "mcpb\manifest.json"

$serverVersion = $null
foreach ($line in Get-Content $versionPy) {
    if ($line -match 'SERVER_VERSION\s*=\s*"([^"]+)"') {
        $serverVersion = $Matches[1]
        break
    }
}
if (-not $serverVersion) { Fail "Could not read SERVER_VERSION from version.py." }

$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
$manifest.version = $serverVersion
$json = $manifest | ConvertTo-Json -Depth 10
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($manifestPath, $json, $utf8NoBom)
OK "version = $serverVersion"

# ---- 2. Stage ----------------------------------------------------------------
Step "Staging -- assembling mcpb-staging/"

$staging = Join-Path $Root "mcpb-staging"
New-Item -ItemType Directory -Path $staging -Force | Out-Null

Copy-Item $exe "$staging\etabs-mcp.exe" -Force
OK "etabs-mcp.exe"

Copy-Item (Join-Path $Root "mcpb\manifest.json") "$staging\manifest.json" -Force
OK "manifest.json"

$assets = Join-Path $Root "assets"
if (Test-Path $assets) {
    Copy-Item $assets "$staging\assets" -Recurse -Force
    OK "assets/"
}

# ---- 3. mcpb pack ------------------------------------------------------------
Step "Packing -- mcpb-staging/ => etabs-mcp.mcpb"

$out = Join-Path $Root "etabs-mcp.mcpb"

Push-Location $Root
try {
    $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    npx --yes "@anthropic-ai/mcpb" pack mcpb-staging $out
    $ec = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($ec -ne 0) { Fail "mcpb pack failed (exit $ec)." }
} finally { Pop-Location }

if (-not (Test-Path $out)) { Fail "etabs-mcp.mcpb not found after pack." }
$mb = [math]::Round((Get-Item $out).Length / 1MB, 1)
OK "etabs-mcp.mcpb  ($mb MB)"

# ---- 4. Install (optional) ---------------------------------------------------
if ($Install) {
    Step "Installing into Claude Desktop extensions"

    $extDir = "$env:APPDATA\Claude\Claude Extensions\local.mcpb.etabs-mcp-contributors.etabs-mcp"
    if (-not (Test-Path $extDir)) {
        Warn "Extension dir not found: $extDir"
        Warn "Install etabs-mcp.mcpb via Claude Desktop first, then re-run with -Install."
    } else {
        $destExe = Join-Path $extDir "etabs-mcp.exe"
        try {
            Copy-Item $exe $destExe -Force
            OK "Hot-swapped $destExe"
            Warn "Restart Claude Desktop to activate the new build."
        } catch {
            Warn "exe locked (Claude Desktop is running)."
            Warn "Close Claude Desktop first, or copy manually:"
            Write-Host "    copy `"$exe`" `"$destExe`"" -ForegroundColor Gray
        }
    }
}

# ---- Done --------------------------------------------------------------------
Step "Done"
Write-Host ""
Write-Host "  Outputs:" -ForegroundColor White
Write-Host "    dist\etabs-mcp.exe  -- standalone executable" -ForegroundColor Gray
Write-Host "    etabs-mcp.mcpb      -- Claude Desktop extension (install via drag-drop or Extensions menu)" -ForegroundColor Gray
Write-Host ""
Write-Host "  Usage:" -ForegroundColor White
Write-Host "    Full build:               .\build.ps1" -ForegroundColor Gray
Write-Host "    Pack only (fast):         .\build.ps1 -SkipPyInstaller" -ForegroundColor Gray
Write-Host "    Build + hot-swap:         .\build.ps1 -Install" -ForegroundColor Gray
Write-Host "    Pack + hot-swap (fast):   .\build.ps1 -SkipPyInstaller -Install" -ForegroundColor Gray
Write-Host ""
