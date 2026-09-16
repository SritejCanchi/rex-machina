# Grab an Unreal window with PrintWindow(PW_RENDERFULLCONTENT).
# The screenshot tool's desktop-composite path cannot see these windows; this
# asks the window to render itself into a bitmap instead.
#
#   .\grab.ps1                     -> the main editor
#   .\grab.ps1 -Title BP_Fight     -> the Blueprint editor
#   .\grab.ps1 -Process UnrealGame-Win64-Shipping -Title RexMachina -Scale 1
#                                  -> the packaged game
#
# The packaged game is a different process from the editor, and for a
# Blueprint-only project it is not even named after the project: the launcher
# at the archive root is a shim, and the window belongs to the engine's
# prebuilt UnrealGame binary.
#
# Prints the mapping needed to turn PNG pixels into computer-use coordinates.
param(
  [string]$Title = "Unreal Editor",
  [string]$Process = "UnrealEditor",
  [string]$Out = "$PSScriptRoot\ue.png",
  [int]$Scale = 2
)

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices;
[StructLayout(LayoutKind.Sequential)] public struct RC { public int L,T,R,B; }
public class PW2 {
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RC r);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr p);
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern int GetWindowThreadProcessId(IntPtr h, out int pid);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
}
"@

$proc = Get-Process -Name $Process -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $proc) {
  "no process named '$Process'. Unreal-ish processes running:"
  Get-Process | Where-Object { $_.ProcessName -match "Unreal|RexMachina" } |
    ForEach-Object { "  {0}  (pid {1})  '{2}'" -f $_.ProcessName, $_.Id, $_.MainWindowTitle }
  exit 1
}
$ue = $proc.Id
$script:hits = @()
$cb = [PW2+EnumProc]{ param($h,$p)
  $q=0; [void][PW2]::GetWindowThreadProcessId($h,[ref]$q)
  if ($q -eq $ue) {
    $sb = New-Object System.Text.StringBuilder 512
    [void][PW2]::GetWindowText($h,$sb,512)
    if ($sb.Length -gt 0) { $script:hits += [pscustomobject]@{H=$h;T=$sb.ToString()} }
  }
  return $true }
[void][PW2]::EnumWindows($cb, [IntPtr]::Zero)

$win = $script:hits | Where-Object { $_.T -like "*$Title*" } | Select-Object -First 1
if (-not $win) {
  "no window matching '$Title'. windows:"
  $script:hits | ForEach-Object { "  " + $_.T }
  exit 1
}

$r = New-Object RC
[void][PW2]::GetWindowRect($win.H, [ref]$r)
$w = $r.R - $r.L; $ht = $r.B - $r.T
$bmp = New-Object System.Drawing.Bitmap($w, $ht)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
$ok = [PW2]::PrintWindow($win.H, $hdc, 2)
$g.ReleaseHdc($hdc); $g.Dispose()

$nw = [int]($w / $Scale); $nh = [int]($ht / $Scale)
$small = New-Object System.Drawing.Bitmap($nw, $nh)
$g2 = [System.Drawing.Graphics]::FromImage($small)
$g2.InterpolationMode = "HighQualityBicubic"
$g2.DrawImage($bmp, 0, 0, $nw, $nh)
$g2.Dispose()
$small.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose(); $small.Dispose()

# computer-use frame is 1568 wide for a 3440-wide monitor
$k = 3440.0 / 1568.0
"window   : $($win.T)"
"ok       : $ok   rect ${w}x${ht} at ($($r.L),$($r.T))   png ${nw}x${nh}"
"tool_x = (png_x * $Scale + $($r.L)) / $k"
"tool_y = (png_y * $Scale + $($r.T)) / $k"
