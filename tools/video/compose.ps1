# Two recordings into one 1080p file: trim, fit on a navy canvas, burn the
# captions, join. The browser part loses its tab strip and address bar.
param([double]$Trim1 = 3.5, [int]$ChromeTop = 88)
$v = Join-Path $PSScriptRoot "out"
$ff = python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
Set-Location $v
$fit = "scale=w=1920:h=1080:force_original_aspect_ratio=decrease:flags=lanczos,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0a1428,setsar=1,fps=30,format=yuv420p"
& $ff -y -hide_banner -loglevel error -i part1.ts -ss $Trim1 -vf "$fit,ass=p1.ass" -c:v libx264 -preset medium -crf 19 p1.mp4
& $ff -y -hide_banner -loglevel error -i part2.ts -vf "crop=iw:ih-${ChromeTop}:0:${ChromeTop},$fit,ass=p2.ass" -c:v libx264 -preset medium -crf 19 p2.mp4
"file 'p1.mp4'`nfile 'p2.mp4'" | Set-Content list.txt -Encoding ascii
& $ff -y -hide_banner -loglevel error -f concat -safe 0 -i list.txt -c copy -movflags +faststart "rex-machina-pipeline-run.mp4"
Get-Item p1.mp4, p2.mp4, rex-machina-pipeline-run.mp4 | Select-Object Name, Length
& $ff -hide_banner -i rex-machina-pipeline-run.mp4 2>&1 | Select-String "Duration" | ForEach-Object { $_.Line.Trim() }
