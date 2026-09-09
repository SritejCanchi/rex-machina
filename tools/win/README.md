# Driving the editor when you cannot see it

Three PowerShell helpers. They exist because the ordinary desktop-capture path
returns a black frame for Unreal's windows on this machine, and because the
main editor and the Blueprint editor are both maximised to the same rectangle,
so a click lands on whichever happens to be on top.

    ./grab.ps1                    # the main editor  -> ue.png
    ./grab.ps1 -Title BP_Fight    # the Blueprint editor
    ./crop.ps1 -X 700 -Y 110 -W 200 -H 70 -Zoom 6   # ue.png -> crop.png
    ./focus.ps1 -Title "Unreal Editor" -Show 3      # front it, keep it maximised

`grab.ps1` asks the window to draw itself into a bitmap
(`PrintWindow` with `PW_RENDERFULLCONTENT`) rather than reading the screen, so
it works whatever is covering the window. It prints the arithmetic that turns a
pixel in the PNG into a screen coordinate; read a pin's position off a `crop.ps1`
blow-up, convert, then click.

A Blueprint pin is three or four pixels wide at zoom-to-fit. Zoom the graph in
before dragging a wire, or the drag grabs the node body and moves the node.

`focus.ps1`'s `-Show` is a raw `ShowWindow` command: 3 maximises, 5 shows
without changing the size, 6 minimises. Do not pass 9 (`SW_RESTORE`) to a
maximised window -- it un-maximises it, every coordinate you measured moves,
and the next click lands on the desktop.

## Testing input in Play In Editor

Two things swallow keystrokes and neither reports anything:

- **The wrong window is in front.** PIE runs inside the main editor's viewport,
  so keys go nowhere while the Blueprint editor is on top. Minimise it
  (`focus.ps1 -Title BP_ -Show 6`), front the editor, then click the viewport
  once.
- **The game has captured the mouse.** Once it has, clicks on the editor
  toolbar do not reach it, so Stop does nothing. `Shift+F1` releases the
  capture; then Stop works.

The check that tells you input is arriving: press a direction that walks into
the fence. `The fence is there. Nothing on that side.` in the Output Log means
the whole chain from key to round is live.
