# Crop a region of the last grab (coords are in ue.png pixel space) and upscale.
param([int]$X, [int]$Y, [int]$W, [int]$H, [double]$Zoom = 2.0,
      [string]$In  = "$PSScriptRoot\ue.png",
      [string]$Out = "$PSScriptRoot\crop.png")
Add-Type -AssemblyName System.Drawing
$src = [System.Drawing.Image]::FromFile($In)
$rect = New-Object System.Drawing.Rectangle($X, $Y, $W, $H)
$cut = ($src -as [System.Drawing.Bitmap]).Clone($rect, $src.PixelFormat)
$nw = [int]($W * $Zoom); $nh = [int]($H * $Zoom)
$big = New-Object System.Drawing.Bitmap($nw, $nh)
$g = [System.Drawing.Graphics]::FromImage($big)
$g.InterpolationMode = "HighQualityBicubic"
$g.DrawImage($cut, 0, 0, $nw, $nh)
$g.Dispose()
$big.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$big.Dispose(); $cut.Dispose(); $src.Dispose()
"cropped ${W}x${H} at ($X,$Y) -> ${nw}x${nh}"
