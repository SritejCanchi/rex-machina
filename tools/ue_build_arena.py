"""Build L_Arena: the 10x10 greybox grid with the dog, the robot and the kid.

    "D:/Software/UE_5.5/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" ^
      "D:/Side Projects/AI Game Dev Course/RexMachinaUE/RexMachina.uproject" ^
      -run=pythonscript -script=".../tools/ue_build_arena.py" -unattended -nopause

Headless -- no editor window, no window focus. Re-runnable: it makes the level
from scratch each time, so it is a build step rather than something hand-placed
that has to be maintained.

Every number here comes from docs/UNREAL-BLUEPRINT-SPEC.md and matches the
constants already on BP_FightManager, so the level and the logic cannot drift:

    TileSize  200      DogSpawn (0,0)     RexSpawn (5,5)     KidTile (7,4)

The grid is 10x10 because GridSpan is "10x10" in all three DT_ArenaPhases rows.

Manhattan((0,0),(7,4)) is 11, which is why Approach divides by 11: the dog
starts exactly 11 tiles from the kid and Approach reads 0 at spawn, 1 on
arrival.
"""
import unreal

L = unreal.log
E = unreal.log_error

MAP = "/Game/Maps/L_Arena"
BP = "/Game/Blueprints/%s.%s"

TILE = 200.0
GRID_W, GRID_H = 10, 10
DOG_SPAWN = (0, 0)
REX_SPAWN = (5, 5)
KID_TILE = (7, 4)


def world_of(tile_x, tile_y, z=0.0):
    """TileToWorld, in Python: (X * TileSize, Y * TileSize, z)."""
    return unreal.Vector(tile_x * TILE, tile_y * TILE, z)


def load_class(name):
    bp = unreal.load_asset(BP % (name, name))
    if bp is None:
        E("  missing Blueprint %s -- run tools/ue_make_actors.py first" % name)
        return None
    return bp.generated_class()


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    classes = {}
    for n in ("BP_Tile", "BP_Marker", "BP_Dog", "BP_Rex", "BP_Kid"):
        c = load_class(n)
        if c is None:
            return
        classes[n] = c

    L("---- building %s ----" % MAP)
    les.new_level(MAP)

    # ---- light, or the greybox is a black screen ----------------------------
    sun = eas.spawn_actor_from_class(unreal.DirectionalLight,
                                     unreal.Vector(0, 0, 1000),
                                     unreal.Rotator(0, -55, 35))
    sky = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 1000))
    L("  light: DirectionalLight + SkyLight")

    # ---- the floor ----------------------------------------------------------
    # Checkered, because a flat expanse of one colour gives the eye nothing to
    # count tiles against -- and this fight is entirely about counting tiles.
    dark = unreal.load_asset("/Game/Materials/MI_Tile.MI_Tile")
    light = unreal.load_asset("/Game/Materials/MI_TileAlt.MI_TileAlt")
    tiles = 0
    for x in range(GRID_W):
        for y in range(GRID_H):
            a = eas.spawn_actor_from_class(classes["BP_Tile"], world_of(x, y))
            if not a:
                continue
            a.set_actor_label("Tile_%d_%d" % (x, y))
            m = light if (x + y) % 2 else dark
            comp = a.get_component_by_class(unreal.StaticMeshComponent)
            if comp is not None and m is not None:
                comp.set_material(0, m)
            tiles += 1
    L("  tiles: %d, checkered" % tiles)

    # ---- the three that matter ---------------------------------------------
    for name, tile, label in (("BP_Dog", DOG_SPAWN, "Dog"),
                              ("BP_Rex", REX_SPAWN, "Rex"),
                              ("BP_Kid", KID_TILE, "Kid"),
                              ("BP_Marker", REX_SPAWN, "PredictionMarker")):
        a = eas.spawn_actor_from_class(classes[name], world_of(tile[0], tile[1]))
        if a:
            a.set_actor_label(label)
            L("  %-16s at tile %s -> %s" % (label, tile, world_of(*tile)))

    # ---- a camera that frames the whole grid --------------------------------
    centre_x = (GRID_W - 1) * TILE / 2.0
    centre_y = (GRID_H - 1) * TILE / 2.0
    cam = eas.spawn_actor_from_class(
        unreal.CameraActor,
        unreal.Vector(centre_x, centre_y - 2400.0, 2000.0),
        unreal.Rotator(0.0, -38.0, 90.0))
    if cam:
        cam.set_actor_label("ArenaCamera")
        try:
            cam.set_editor_property("auto_activate_for_player",
                                    unreal.AutoReceiveInput.PLAYER0)
        except Exception as exc:
            L("  camera auto-activate not set (%s)" % str(exc)[:60])
        L("  camera at (%.0f, %.0f, 2000) looking down 38 degrees" %
          (centre_x, centre_y - 2400.0))

    # ---- the fight manager itself ------------------------------------------
    # It has no visible component -- it is where the round loop lives. Its
    # BeginPlay copies DogSpawn/RexSpawn into DogTile/RexTile and calls
    # SyncActors, so the three actors above snap onto the tiles the logic
    # believes they are on. Without this actor in the level nothing runs the
    # fight at all, and the arena is just scenery.
    fm = unreal.load_asset("/Game/Blueprints/BP_FightManager.BP_FightManager")
    if fm is not None:
        a = eas.spawn_actor_from_class(fm.generated_class(),
                                       unreal.Vector(0, 0, 400))
        if a:
            a.set_actor_label("FightManager")
            L("  FightManager placed -- BeginPlay seeds the fight and syncs actors")
    else:
        E("  BP_FightManager missing -- run tools/ue_build_fightmanager.py first")

    # ---- the self-test rides along so PIE always runs the assertions --------
    st = unreal.load_asset("/Game/Blueprints/BP_SelfTest.BP_SelfTest")
    if st is not None:
        a = eas.spawn_actor_from_class(st.generated_class(),
                                       unreal.Vector(0, 0, 600))
        if a:
            a.set_actor_label("SelfTest")
            L("  SelfTest actor placed -- assertions print on every Play")

    les.save_current_level()
    L("  saved %s" % MAP)

    # ---- verify by counting what is actually in the level -------------------
    all_actors = eas.get_all_level_actors()
    counts = {}
    for a in all_actors:
        counts[a.get_class().get_name()] = counts.get(a.get_class().get_name(), 0) + 1
    L("  ---- verify ----")
    for k in sorted(counts):
        L("    %-28s %d" % (k, counts[k]))
    expect_tiles = GRID_W * GRID_H
    got_tiles = counts.get("BP_Tile_C", 0)
    L("  %s" % ("grid is %dx%d as specified" % (GRID_W, GRID_H)
                if got_tiles == expect_tiles
                else "TILE COUNT WRONG: %d, wanted %d" % (got_tiles, expect_tiles)))


main()
