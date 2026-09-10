# Shared: find a top-level window by title fragment, place it, and read the
# desktop region it occupies. Windows Terminal and Chrome both draw with
# DirectX here, so a GDI window grab is black; the desktop region is not.
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices;
public struct RECT { public int L, T, R, B; }
public class WL {
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int hh, bool r);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr h, int a, out RECT r, int s);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr p);
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
}
"@
[void][WL]::SetProcessDPIAware()
function Find-WindowByTitle([string]$Fragment) {
  $script:found = [IntPtr]::Zero
  $cb = [WL+EnumProc]{ param($h, $p)
    if (-not [WL]::IsWindowVisible($h)) { return $true }
    $sb = New-Object System.Text.StringBuilder 512; [void][WL]::GetWindowText($h, $sb, 512)
    if ($sb.ToString() -like "*$Fragment*") { $script:found = $h; return $false }
    return $true }
  [void][WL]::EnumWindows($cb, [IntPtr]::Zero)
  return $script:found
}
function Wait-Window([string]$Fragment, [int]$Seconds = 20) {
  $n = 0
  while ($n -lt $Seconds * 5) { $h = Find-WindowByTitle $Fragment; if ($h -ne [IntPtr]::Zero) { return $h }; Start-Sleep -Milliseconds 200; $n++ }
  return [IntPtr]::Zero
}
function Place-Window([IntPtr]$h, [int]$x, [int]$y, [int]$w, [int]$hh) {
  [void][WL]::ShowWindow($h, 9); [void][WL]::MoveWindow($h, $x, $y, $w, $hh, $true); [void][WL]::SetForegroundWindow($h)
  Start-Sleep -Milliseconds 500
  $r = New-Object RECT
  if ([WL]::DwmGetWindowAttribute($h, 9, [ref]$r, 16) -ne 0) { [void][WL]::GetWindowRect($h, [ref]$r) }
  return @{ x = $r.L; y = $r.T; w = [Math]::Floor(($r.R - $r.L) / 2) * 2; h = [Math]::Floor(($r.B - $r.T) / 2) * 2 }
}
function Start-Grab([string]$ff, $region, [int]$fps, [int]$maxSec, [string]$out) {
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $ff
  $psi.Arguments = "-y -nostats -loglevel warning -f gdigrab -framerate $fps -draw_mouse 0 -offset_x $($region.x) -offset_y $($region.y) -video_size $($region.w)x$($region.h) -i desktop -t $maxSec -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -f mpegts `"$out`""
  $psi.UseShellExecute = $false; $psi.RedirectStandardInput = $true; $psi.CreateNoWindow = $true
  return [System.Diagnostics.Process]::Start($psi)
}
function Stop-Grab($rec) { $rec.StandardInput.Write("q"); $rec.StandardInput.Flush(); if (-not $rec.WaitForExit(20000)) { $rec.Kill() } }
