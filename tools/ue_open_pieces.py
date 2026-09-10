"""Open the four piece Blueprints so the motion graph can be pasted into each.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_open_pieces.py

Opening them from Python rather than the Content Browser matters for one dull
reason: typing a path into the editor's Python console goes through the
clipboard, so anything already there is gone. Open first, copy second.
"""
import unreal

PATHS = ["/Game/Blueprints/BP_Dog.BP_Dog",
         "/Game/Blueprints/BP_Rex.BP_Rex",
         "/Game/Blueprints/BP_Kid.BP_Kid",
         "/Game/Blueprints/BP_Marker.BP_Marker"]

assets = [unreal.load_asset(p) for p in PATHS]
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets(
    [a for a in assets if a is not None])
unreal.log("RM_OPEN | opened %d piece Blueprints" % len([a for a in assets if a]))
