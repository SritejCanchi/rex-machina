# The console the video records. Title first, so the grabber can find it;
# a fixed size; then the repo's own demo script with slower pauses so the
# captions have time to be read. Every output line is also appended to a
# log with a wall-clock stamp, so the captions can be timed to the screen.
param([string]$Log, [int]$Pause = 9)
$host.UI.RawUI.WindowTitle = "REX MACHINA pipeline"
try { mode con cols=112 lines=38 } catch {}
Clear-Host
Start-Sleep -Seconds 5
Set-Location (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
& ".\tools\demo_pipeline.ps1" -Pause $Pause *>&1 | ForEach-Object {
  $_
  Add-Content -Path $Log -Value ("{0} {1}" -f (Get-Date).ToString("HH:mm:ss.fff"), $_)
}
