# Bring one of the editor's windows to the front by title.
# Both the main editor and the Blueprint editor are maximised to the same
# rect, so a click lands on whichever is on top -- and the screenshot path
# cannot see either. This picks.
param([string]$Title = "Unreal Editor", [int]$Show = 5)
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices;
public class FG {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr p);
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern int GetWindowThreadProcessId(IntPtr h, out int pid);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
}
"@
$ue = (Get-Process -Name UnrealEditor -ErrorAction Stop).Id
$script:hits = @()
$cb = [FG+EnumProc]{ param($h,$p)
  $q=0; [void][FG]::GetWindowThreadProcessId($h,[ref]$q)
  if ($q -eq $ue) {
    $sb = New-Object System.Text.StringBuilder 512
    [void][FG]::GetWindowText($h,$sb,512)
    if ($sb.Length -gt 0) { $script:hits += [pscustomobject]@{H=$h;T=$sb.ToString()} }
  }
  return $true }
[void][FG]::EnumWindows($cb, [IntPtr]::Zero)
$win = $script:hits | Where-Object { $_.T -like "*$Title*" } | Select-Object -First 1
if (-not $win) { "no window matching '$Title'"; exit 1 }
[void][FG]::ShowWindow($win.H, $Show)  # 5 SW_SHOW, 3 SW_MAXIMIZE; 9 (RESTORE) un-maximises
[void][FG]::SetForegroundWindow($win.H)
"fronted: $($win.T)"
