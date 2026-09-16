# Run one editor Python script headlessly against the project.
#
#   powershell -ExecutionPolicy Bypass -File tools\ue_run_python.ps1 -Script tools\ue_import_sounds.py
#
# Driving the editor by hand is slow and, on this machine, half blind: its
# windows do not screenshot. A commandlet run prints to stdout instead, so the
# script's own log lines are the feedback.
param(
  [Parameter(Mandatory=$true)][string]$Script,
  [string]$Engine  = "D:\Software\UE_5.5",
  [string]$Project = "D:\Side Projects\AI Game Dev Course\RexMachinaUE\RexMachina.uproject"
)
$ErrorActionPreference = "Stop"
$cmd = Join-Path $Engine "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
if (-not (Test-Path $cmd))    { throw "no editor at $cmd" }
if (-not (Test-Path $Script)) { throw "no script at $Script" }
$Script = (Resolve-Path $Script).Path

# The editor's -script= argument does not survive a path with spaces: it takes
# everything up to the first one and reports the truncation as a missing file.
# This repo lives under "D:\Side Projects\AI Game Dev Course", so every script
# hits it. Stage a copy somewhere without spaces and run that.
$stage = Join-Path $env:TEMP "rm_ue_py"
New-Item -ItemType Directory -Force -Path $stage | Out-Null
$staged = Join-Path $stage (Split-Path $Script -Leaf)
Copy-Item $Script $staged -Force

# unreal.log() does not reach stdout from a commandlet; it only reaches the
# editor log. Read that afterwards, or the script appears to run silently.
$editorLog = Join-Path (Split-Path $Project -Parent) "Saved\Logs\RexMachina.log"
$before = if (Test-Path $editorLog) { (Get-Item $editorLog).Length } else { 0 }

"running $Script"
"  staged as $staged"
& $cmd "$Project" -run=pythonscript -script="$staged" -unattended -nopause -nosplash -stdout -UTF8Output 2>&1 |
  Where-Object { $_ -match "Traceback|LogPython: Error|Python script executed" } |
  ForEach-Object { "  " + ($_ -replace '^\[[^\]]*\]\[[^\]]*\]', '') }
$code = $LASTEXITCODE

if (Test-Path $editorLog) {
  "--- script output ---"
  Get-Content $editorLog |
    Where-Object { $_ -match "RM_[A-Z]+ \|" } |
    ForEach-Object { "  " + ($_ -split "RM_[A-Z]+ \| ")[-1] } |
    Select-Object -Last 60
}

# A handled ensure makes the editor exit non-zero even when the script did its
# job -- importing audio trips one for a decoder the commandlet does not load.
# Report it rather than pretending it passed.
"exit code: $code$(if ($code -ne 0) { '  (editor logged errors; check the lines above before trusting it)' })"
exit $code
