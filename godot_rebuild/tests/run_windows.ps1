# Usage: powershell -ExecutionPolicy Bypass -File .\tests\run_windows.ps1 -Godot "C:\Tools\Godot_v4.7.2-stable_win64_console.exe"
# ExecutionPolicy applies to this process only; no global policy is modified.
param([Parameter(Mandatory = $true)][string]$Godot)
$ErrorActionPreference = "Stop"
$Project = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path -LiteralPath $Godot -PathType Leaf)) {
    throw "Godot executable not found: $Godot"
}
$Godot = (Resolve-Path -LiteralPath $Godot).Path
$Version = & $Godot --version
if ($LASTEXITCODE -ne 0) { throw "Unable to launch Godot" }
Write-Host "Engine: $Version"
if ($Version -notmatch '^4\.7\.2\.') {
    throw "Use Godot 4.7.2 to match this project's target."
}
function Run-Engine([string[]]$EngineArgs) {
    $Log = & $Godot @EngineArgs 2>&1
    $Code = $LASTEXITCODE
    $Log | ForEach-Object { Write-Host $_ }
    if ($Code -ne 0 -or ($Log -match 'SCRIPT ERROR:|ERROR:|FAIL:')) {
        throw "Godot validation failed (exit $Code). Read the log above."
    }
    return $Log
}
$null = Run-Engine -EngineArgs @('--headless', '--path', $Project, '--editor', '--import')
$Results = Run-Engine -EngineArgs @('--headless', '--path', $Project, '--script', 'res://tests/run_all.gd')
if (-not ($Results -match 'PASS: .* checks; fixed ticks')) {
    throw "Runtime test runner did not report success."
}
Write-Host "Native Godot checks passed." -ForegroundColor Green
