# Package the Act 3 showcase for Windows.
#
#   powershell -ExecutionPolicy Bypass -File tools\ue_package.ps1
#
# Blueprint-only, so this cooks against the launcher engine's precompiled
# binaries and never touches a compiler. The engine is not in Program Files on
# this machine; the path below comes from the Epic launcher manifest.
param(
  [string]$Engine  = "D:\Software\UE_5.5",
  [string]$Project = "D:\Side Projects\AI Game Dev Course\RexMachinaUE\RexMachina.uproject",
  [string]$Out     = "D:\Side Projects\AI Game Dev Course\RexMachinaUE\Packaged",
  [string]$Config  = "Shipping"
)
$ErrorActionPreference = "Stop"
$uat = Join-Path $Engine "Engine\Build\BatchFiles\RunUAT.bat"
foreach ($p in @($uat, $Project)) { if (-not (Test-Path $p)) { throw "missing: $p" } }

$log = Join-Path (Split-Path $Out -Parent) "package.log"
Remove-Item $log -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $Out | Out-Null

"packaging $Config to $Out"
"log: $log"
$started = Get-Date

& $uat BuildCookRun `
  -project="$Project" `
  -noP4 -utf8output -nodebuginfo `
  -platform=Win64 -clientconfig="$Config" `
  -cook -build -stage -pak -iostore -compressed -prereqs `
  -archive -archivedirectory="$Out" `
  -nocompileeditor -installed `
  2>&1 | Tee-Object -FilePath $log

$code = $LASTEXITCODE
"exit code: $code   elapsed: {0:n1} min" -f ((Get-Date) - $started).TotalMinutes
if ($code -ne 0) { "FAILED - last errors:"; Select-String -Path $log -Pattern "Error:|error C|Exception" | Select-Object -Last 15 | ForEach-Object { "  " + $_.Line } }
exit $code
