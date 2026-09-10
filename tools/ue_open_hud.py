"""Open BP_FightHUD. See ue_open_pieces.py for why this is a script."""
import unreal

a = unreal.load_asset("/Game/Blueprints/BP_FightHUD.BP_FightHUD")
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([a])
unreal.log("RM_OPEN | BP_FightHUD")
