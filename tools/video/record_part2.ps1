# Open the game in demo mode in its own Chrome window, record that window
# for a fixed time, then close the window. Demo mode titles the page, so
# the window is found even with other Rex Machina tabs open.
param([int]$Seconds = 60, [string]$Title = "Rex Machina demo")
$scratch = Join-Path $PSScriptRoot "out"; New-Item -ItemType Directory -Force $scratch | Out-Null
. "$PSScriptRoot\winlib.ps1"
Add-Type @"
using System; using System.Runtime.InteropServices;
public class PM { [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l); }
"@
$ff = python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
Remove-Item "$scratch\part2.ts" -ErrorAction SilentlyContinue
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chrome)) { $chrome = "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe" }
Start-Process $chrome -ArgumentList "--new-window","--window-size=1180,1240","--window-position=40,40","http://localhost:8000/index.html#demo"
$h = Wait-Window $Title 15
if ($h -eq [IntPtr]::Zero) { "browser window '$Title' not found"; exit 1 }
$region = Place-Window $h 40 40 1180 1240
"region {0},{1} {2}x{3}" -f $region.x, $region.y, $region.w, $region.h
$t0 = Get-Date
$rec = Start-Grab $ff $region 20 $Seconds "$scratch\part2.ts"
@{ t0 = $t0.ToString("HH:mm:ss.fff"); pid = $rec.Id } + $region | ConvertTo-Json | Set-Content "$scratch\times2.json"
"recording for $Seconds s from $($t0.ToString('HH:mm:ss.fff'))"
$rec.WaitForExit()
[void][PM]::PostMessage($h, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
Get-Item "$scratch\part2.ts" | Select-Object Length
