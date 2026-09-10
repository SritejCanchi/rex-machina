"""Create BP_FightHUD and BP_FightGameMode, and point the map at them.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_make_hud.py

The graph goes in separately, from generated/fighthud.txt. This only builds the
two assets and the wiring between them, which is all editor-property work and
none of it belongs in a Blueprint graph:

    L_Arena's World Settings -> GameModeOverride -> BP_FightGameMode
    BP_FightGameMode         -> HUDClass         -> BP_FightHUD

Without the GameMode override the level uses GameModeBase, whose HUDClass is
the empty default AHUD, and a perfectly correct HUD graph draws nothing at all
because the class is never instantiated.
"""
import unreal

BEL = unreal.BlueprintEditorLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
L = unreal.log
E = unreal.log_error

PKG = "/Game/Blueprints"
MAP = "/Game/Maps/L_Arena"


def make(name, parent_class):
    path = "%s/%s" % (PKG, name)
    bp = unreal.load_asset(path + "." + name)
    if bp is None:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", parent_class)
        bp = AT.create_asset(name, PKG, unreal.Blueprint, factory)
    if bp is None:
        E("RM_HUD | could not create %s" % name)
        return None
    BEL.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(path)
    # parent_class here is the Python wrapper type, not a UClass, so it has
    # __name__ and not get_name().
    L("RM_HUD | %-18s parent %s" % (name, parent_class.__name__))
    return bp


def main():
    hud = make("BP_FightHUD", unreal.HUD)
    gm = make("BP_FightGameMode", unreal.GameModeBase)
    if hud is None or gm is None:
        return

    # HUDClass lives on the class default object, so it can only be set after a
    # compile has produced one.
    cdo = unreal.get_default_object(gm.generated_class())
    cdo.set_editor_property("hud_class", hud.generated_class())
    BEL.compile_blueprint(gm)
    unreal.EditorAssetLibrary.save_asset("%s/BP_FightGameMode" % PKG)
    got = unreal.get_default_object(gm.generated_class()).get_editor_property("hud_class")
    L("RM_HUD | BP_FightGameMode HUDClass = %s"
      % (got.get_name() if got else "None"))

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    if world is None or MAP.split("/")[-1] not in world.get_path_name():
        E("RM_HUD | not on %s -- GameMode override NOT set" % MAP)
        return
    ws = world.get_world_settings()
    ws.set_editor_property("default_game_mode", gm.generated_class())
    les.save_current_level()
    back = world.get_world_settings().get_editor_property("default_game_mode")
    L("RM_HUD | %s GameModeOverride = %s"
      % (MAP, back.get_name() if back else "None"))


main()
