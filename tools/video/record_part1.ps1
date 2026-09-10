# Record the pipeline console until the server in step 6 has been up for
# ten seconds, then finish ffmpeg cleanly and close the console.
$scratch = Join-Path $PSScriptRoot "out"; New-Item -ItemType Directory -Force $scratch | Out-Null
. "$PSScriptRoot\winlib.ps1"
$ff = python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
$log = "$scratch\demo.log"; Remove-Item $log, "$scratch\part1.ts" -ErrorAction SilentlyContinue
$con = Start-Process powershell.exe -ArgumentList "-NoProfile","-NoExit","-ExecutionPolicy","Bypass","-File","$PSScriptRoot\demo_window.ps1","-Log","$log","-Pause","9" -PassThru
$h = Wait-Window "REX MACHINA pipeline" 20
if ($h -eq [IntPtr]::Zero) { "console window not found"; taskkill /T /F /PID $con.Id | Out-Null; exit 1 }
$region = Place-Window $h 40 40 1180 840
"region {0},{1} {2}x{3}" -f $region.x, $region.y, $region.w, $region.h
$t0 = Get-Date
$rec = Start-Grab $ff $region 15 260 "$scratch\part1.ts"
$step6 = $null
while ($true) {
  Start-Sleep -Milliseconds 400
  $el = ((Get-Date) - $t0).TotalSeconds
  if (-not $step6 -and (Test-Path $log)) {
    if (Select-String -Path $log -Pattern "STEP 6 " -Quiet -ErrorAction SilentlyContinue) { $step6 = $el }
  }
  if ($step6 -and $el -gt $step6 + 11) { break }
  if ($el -gt 250) { break }
}
$end = ((Get-Date) - $t0).TotalSeconds
Stop-Grab $rec
taskkill /T /F /PID $con.Id | Out-Null
@{ t0 = $t0.ToString("HH:mm:ss.fff"); end = $end; step6 = $step6 } + $region | ConvertTo-Json | Set-Content "$scratch\times1.json"
"recorded {0:n1}s, step 6 at {1:n1}" -f $end, $step6
Get-Item "$scratch\part1.ts" | Select-Object Length
