"""Build L_SelfTest: the assertions, and nothing else.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_build_selftest_map.py

BP_SelfTest used to ride along in L_Arena so the thirty-four assertions ran on
every Play. That was fine while the arena was a greybox and stopped being fine
the moment it was worth looking at: the self-test drives OnPlayerMove, which
calls SyncActors, which moves the dog, Rex and the marker -- the level actors,
not copies. So the fight opened with every piece parked wherever the last
assertion left it, and the marker sat on the dog.

The assertions are worth keeping, so they get their own map instead of being
deleted. Play L_SelfTest to run them; play L_Arena to play the game.
"""
import unreal

L = unreal.log
E = unreal.log_error

MAP = "/Game/Maps/L_SelfTest"


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        les.load_level(MAP)
    else:
        les.new_level(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    where = world.get_path_name() if world else "(no world)"
    if MAP.split("/")[-1] not in where:
        E("RM_ST | editor is on %s, not %s -- refusing to build" % (where, MAP))
        return

    cleared = 0
    for a in eas.get_all_level_actors():
        if a.get_class().get_name().startswith("BP_"):
            eas.destroy_actor(a)
            cleared += 1
    if cleared:
        L("RM_ST | cleared %d actors from the previous build" % cleared)

    st = unreal.load_asset("/Game/Blueprints/BP_SelfTest.BP_SelfTest")
    if st is None:
        E("RM_ST | BP_SelfTest missing")
        return
    a = eas.spawn_actor_from_class(st.generated_class(), unreal.Vector(0, 0, 0))
    if a:
        a.set_actor_label("SelfTest")

    # The assertions print to the Output Log, so the map needs nothing to look
    # at. It does need a light, because a map with none opens black and reads
    # as a broken build rather than as a test harness.
    eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500),
                               unreal.Rotator(0, -50, 30))
    eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 500))

    saved = les.save_current_level()
    if saved is False:
        E("RM_ST | save_current_level returned False -- %s NOT written" % MAP)
    else:
        L("RM_ST | saved %s -- Play it to run the assertions" % MAP)


main()
