# One take, no typing: the whole pipeline from agent output to the game loading it.
#
#   .\tools\demo_pipeline.ps1
#
# This is what the Assignment 10 video records. Every step is something the
# repo already does; the script only strings them together with pauses so the
# recording can be narrated. Ctrl+C at any pause stops it. Nothing here calls
# the API: the pipelines replay their recorded model turns, which is the point
# the audit makes about reproducibility.
param([int]$Pause = 4)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Step($n, $title, $why) {
  ""
  "=" * 78
  "  STEP $n   $title"
  "  $why"
  "=" * 78
  ""
  Start-Sleep -Seconds $Pause
}

Clear-Host
"REX MACHINA   pipeline run, prompt to engine"
"repo: $root"
Start-Sleep -Seconds $Pause

Step 1 "Retry Read: generate, evaluate, refine, circuit-break" `
  "Six lines the robot speaks after you lose. Every draft is checked against five GDD rules."
Push-Location "pipelines\a6-retry-read-ger"; python pipeline.py; Pop-Location
Start-Sleep -Seconds $Pause

Step 2 "Copy Desk: the style-guide agent" `
  "Journey narration scored out of ten against the house voice and rewritten from the reason."
Push-Location "pipelines\a7-copy-desk-style"; python pipeline.py; Pop-Location
Start-Sleep -Seconds $Pause

Step 3 "Engine integration: sync with checksums" `
  "Each table is copied into the build byte for byte. A checksum mismatch fails the run."
python tools\sync_datatables.py --pipelines "..\Deliverables"
Start-Sleep -Seconds $Pause

Step 4 "Headless tests" `
  "The game is played without a browser. Winnable from every journey outcome, veto holds, every line came from a table."
node tests\sim.js
Start-Sleep -Seconds $Pause

Step 5 "Adversarial QA agent" `
  "Re-attempts the six exploits the GDD closed, then fuzzes 300 fights."
node qa\adversary.js
Start-Sleep -Seconds $Pause

Step 6 "The game, loading those files" `
  "Static server, then the browser. The footer states the row count it loaded."
Start-Process "http://localhost:8000"
python -m http.server 8000
