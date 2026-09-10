# Recording the pipeline video without a hand on the mouse

    .	oolsideoecord_part1.ps1     # the console: demo_pipeline.ps1, grabbed until step 6 is up
    .	oolsideoecord_part2.ps1     # the browser: index.html#demo in its own window, 58 s
    python toolsideo\captions.py     # captions from the shot list, timed to the console log
    .	oolsideo\compose.ps1          # trim, fit to 1080p, burn captions, join

Everything lands in `tools/video/out/`. The final file is
`rex-machina-pipeline-run.mp4`, about three minutes. ffmpeg comes from the
`imageio-ffmpeg` package; part 2 needs a static server on port 8000 and a
Chrome install.

Two things that cost an evening. Windows Terminal and Chrome both draw with
DirectX here, so a GDI grab of the window comes back black; the scripts grab
the desktop region the window occupies instead, after placing the window and
bringing it to the front. And ffmpeg has to be stopped with a `q` on stdin,
not killed, or the last minute of the file never leaves its buffer.
