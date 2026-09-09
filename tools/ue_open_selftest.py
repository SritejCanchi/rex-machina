"""Open BP_SelfTest's editor window, so the self-test graph can be pasted.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_open_selftest.py

Typing into the editor's Python console goes through the clipboard, so the
asset has to be opened before the graph text is put there, not after.
"""
import unreal

PATH = "/Game/Blueprints/BP_SelfTest.BP_SelfTest"
asset = unreal.load_asset(PATH)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([asset])
unreal.log("RM_OPEN | opened %s" % PATH)
