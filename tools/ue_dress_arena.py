"""Dress L_Arena as the train yard: fence, cover, floods, and a skyline.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_dress_arena.py

Runs after ue_build_arena.py and adds nothing the fight depends on. The grid,
the four pieces, the camera and the manager are still that script's job, and
running it again wipes everything here -- which is the right way round, because
the greybox has to stay the thing that proves the fight reads.

**Why the train yard and not the yard.** DT_ArenaPhases has three phases and
the industrial kits only fit one of them: phase_train_yard asks for stationary
flatcars, a switch stand with its lamp lit, sodium floods on tall poles and
ballast underfoot. phase_yard asks for a porch, a garden hose and a chain-link
fence, and dressing it out of a factory kit would look like neither. The train
yard is also the phase the fight ends in, so it is the one worth building.

Cover and exit tiles are read out of the DataTable rather than typed here, so
moving a crate is a data edit. Everything else is placed relative to the grid.
"""
import re
import unreal

L = unreal.log
E = unreal.log_error

MAP = "/Game/Maps/L_Arena"
FAC = "/Game/Kits/Factory/%s.%s"
CITY = "/Game/Kits/City/%s.%s"
MAT = "/Game/Materials/%s.%s"

TILE = 200.0
GRID = 10
KID_TILE = (7, 4)
TAG = "RM_DRESS"

#  The grid occupies tile centres 0..1800, so its outer edge is -100..1900.
LO, HI = -100.0, (GRID - 1) * TILE + 100.0
MID = (GRID - 1) * TILE / 2.0


def mesh(path_fmt, name):
    m = unreal.load_asset(path_fmt % (name, name))
    if m is None:
        E("RM_YARD | missing mesh %s" % name)
    return m


def place(eas, m, x, y, z, scale, yaw=0.0, label="prop", mat=None, pitch=0.0):
    """One dressed StaticMeshActor, tagged so the next run can clear it."""
    if m is None:
        return None
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor,
                                   unreal.Vector(x, y, z),
                                   unreal.Rotator(0.0, pitch, yaw))
    if a is None:
        return None
    a.set_actor_label(label)
    a.tags = [TAG]
    comp = a.static_mesh_component
    comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    comp.set_static_mesh(m)
    if mat is not None:
        comp.set_material(0, mat)
    a.set_actor_scale3d(unreal.Vector(*scale) if isinstance(scale, tuple)
                        else unreal.Vector(scale, scale, scale))
    return a


def phase_tiles(row_index=2):
    """Cover and exit tiles for one DT_ArenaPhases row.

    The column comes back as UE's struct text, e.g. "((X=2,Y=4),(X=7,Y=3))",
    so the numbers are pulled out in pairs. Row 2 is phase_train_yard.
    """
    dt = unreal.load_asset("/Game/Data/DT_ArenaPhases.DT_ArenaPhases")
    if dt is None:
        E("RM_YARD | DT_ArenaPhases missing")
        return [], []
    out = {}
    for col in ("CoverTiles", "ExitTiles"):
        try:
            vals = unreal.DataTableFunctionLibrary.get_data_table_column_as_string(dt, col)
        except Exception as exc:
            E("RM_YARD | column %s unreadable: %s" % (col, str(exc)[:70]))
            out[col] = []
            continue
        raw = vals[row_index] if row_index < len(vals) else ""
        nums = [int(float(n)) for n in re.findall(r"-?\d+(?:\.\d+)?", raw)]
        out[col] = list(zip(nums[0::2], nums[1::2]))
        L("RM_YARD | %-11s row %d -> %s" % (col, row_index, out[col]))
    return out.get("CoverTiles", []), out.get("ExitTiles", [])


def fix_exposure(eas):
    """Pin the exposure, then light the yard to that.

    Auto exposure defeats the whole point of a dark yard with hot pools in it:
    the darker the scene gets, the harder the histogram pushes it back up, so
    every attempt at dusk came out as a white board with black shadows. Locking
    min and max brightness to the same value turns the eye adaptation off and
    makes the light intensities below mean what they say.
    """
    ppv = eas.spawn_actor_from_class(unreal.PostProcessVolume,
                                     unreal.Vector(MID, MID, 500.0))
    if ppv is None:
        E("RM_YARD | could not spawn the post process volume")
        return
    ppv.set_actor_label("YardLook")
    ppv.tags = [TAG]
    ppv.set_editor_property("unbound", True)
    st = ppv.get_editor_property("settings")
    for flag, name, value in (
            # These two are EV100, not a multiplier: 1.0 is a dim room and
            # pinning both there is what made a floodlit yard read as white.
            # 9 is roughly "outdoors under lights".
            ("override_auto_exposure_min_brightness", "auto_exposure_min_brightness", 10.4),
            ("override_auto_exposure_max_brightness", "auto_exposure_max_brightness", 10.4),
            ("override_bloom_intensity", "bloom_intensity", 0.55),
            ("override_vignette_intensity", "vignette_intensity", 0.45),
            ("override_film_slope", "film_slope", 0.85),
            ("override_film_toe", "film_toe", 0.6)):
        try:
            st.set_editor_property(flag, True)
            st.set_editor_property(name, value)
        except Exception as exc:
            L("RM_YARD | post process %s not set (%s)" % (name, str(exc)[:50]))
    ppv.set_editor_property("settings", st)
    L("RM_YARD | exposure pinned, bloom and vignette on")


def tune_lights(eas):
    """Take the greybox lighting down, and take every light off the bake.

    ue_build_arena.py puts in a bright sun and sky so a grey box is visible at
    all. Once the yard is dressed that reads as noon in an open field, and the
    floods have nothing to be brighter than. This is the same two lights, dimmed
    and warmed, plus Movable on everything -- a Static light without a lighting
    build prints LIGHTING NEEDS TO BE REBUILT across the running game.
    """
    for a in eas.get_all_level_actors():
        kind = a.get_class().get_name()
        if kind == "DirectionalLight":
            c = a.light_component
            c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
            c.set_editor_property("intensity", 0.9)
            # B, G, R, A positionally: see the note in ue_dress_actors.py.
            c.set_editor_property("light_color",
                                  unreal.Color(r=132, g=158, b=220, a=255))
            a.set_actor_rotation(unreal.Rotator(0.0, -42.0, 25.0), False)
        elif kind == "SkyLight":
            c = a.get_component_by_class(unreal.SkyLightComponent)
            if c:
                c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
                c.set_editor_property("intensity", 0.55)
                c.set_editor_property("light_color",
                                      unreal.Color(r=74, g=96, b=160, a=255))
        elif kind == "CameraActor":
            # Closer and a little lower than the greybox framing: the fence and
            # the flatcars now give the board an edge, so it can be filled.
            # Low enough to see the sides of things. At -43 the board was
            # legible and the pieces were plan views of themselves: a dog from
            # directly above is four dots and a rectangle.
            a.set_actor_location(unreal.Vector(MID, MID - 2750.0, 1980.0), False, False)
            a.set_actor_rotation(unreal.Rotator(0.0, -35.0, 90.0), False)
            comp = a.get_component_by_class(unreal.CameraComponent)
            if comp:
                comp.set_editor_property("field_of_view", 55.0)
    L("RM_YARD | sun dimmed to dusk, every light Movable, camera pulled in")


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        les.load_level(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    where = world.get_path_name() if world else "(no world)"
    if MAP.split("/")[-1] not in where:
        E("RM_YARD | editor is on %s, not %s -- refusing to dress" % (where, MAP))
        return
    L("RM_YARD | ---- dressing %s as the train yard ----" % MAP)

    # Clear only what this script owns. Everything else in the level belongs to
    # ue_build_arena.py and must survive.
    cleared = 0
    for a in eas.get_all_level_actors():
        tags = [str(t) for t in (a.tags or [])]
        if TAG in tags:
            eas.destroy_actor(a)
            cleared += 1
    for a in eas.get_all_level_actors():
        if a.get_class().get_name() in ("ExponentialHeightFog", "PostProcessVolume",
                                        "PointLight", "SpotLight"):
            eas.destroy_actor(a)
            cleared += 1
    if cleared:
        L("RM_YARD | cleared %d dressing actors" % cleared)

    # BP_SelfTest drives OnPlayerMove, which calls SyncActors, which moves the
    # level's own dog, Rex and marker. Left in L_Arena it means the fight opens
    # with every piece parked where the last assertion left it. The assertions
    # live in L_SelfTest now -- see ue_build_selftest_map.py.
    for a in eas.get_all_level_actors():
        if a.get_class().get_name().startswith("BP_SelfTest"):
            eas.destroy_actor(a)
            L("RM_YARD | removed the self-test actor -- it plays in L_SelfTest")

    fence_mi = unreal.load_asset(MAT % ("MI_Fence", "MI_Fence"))
    pad_mi = unreal.load_asset(MAT % ("MI_KidPad", "MI_KidPad"))
    ground_mi = unreal.load_asset(MAT % ("MI_Ballast", "MI_Ballast"))

    fix_exposure(eas)
    tune_lights(eas)

    # ---- ballast: the ground the yard sits on -------------------------------
    # Darker than the darkest tile on purpose. The board has to be the brightest
    # thing on screen or the eye has nothing to count against.
    cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
    place(eas, cube, MID, MID, -25.0, (140.0, 140.0, 0.4), 0.0, "Ballast", ground_mi)

    # ---- the fence ----------------------------------------------------------
    # This is the thing "The fence is there. Nothing on that side." refers to.
    # It was an invisible rule for the whole build; now it is a wall.
    # The near edge is kept low so it does not stand between the camera and the
    # board, which is the one thing the dressing must never do.
    # Four cubes, not forty-eight kit panels. structure-wall has a base plate
    # and an off-centre pivot, so a row of them came out crenellated and the
    # two axes did not line up with each other. A wall only has to read as a
    # hard edge the dog cannot cross, and the engine cube does that exactly.
    span = (GRID + 1) * TILE / 100.0            # cube is 100uu, so this is scale
    across, along = (span, 1.0), (1.0, span)
    for label, (x, y), (sx, sy), sz in (
            ("Fence_N", (MID, HI + 150), across, 1.3),
            ("Fence_W", (LO - 150, MID), along, 1.1),
            ("Fence_E", (HI + 150, MID), along, 1.1),
            # The near edge is a kerb, not a wall: anything taller stands
            # between the camera and the board, which the dressing must never do.
            ("Fence_S", (MID, LO - 150), across, 0.45)):
        place(eas, cube, x, y, sz * 50.0, (sx, sy, sz), 0.0, label, fence_mi)
    L("RM_YARD | fence: four walls, near edge kept to a kerb")

    # ---- cover, from the DataTable -----------------------------------------
    cover_tiles, exit_tiles = phase_tiles(2)
    crate = mesh(FAC, "box-large")
    crate2 = mesh(FAC, "box-wide")
    for i, (tx, ty) in enumerate(cover_tiles):
        m = crate if i % 2 == 0 else crate2
        place(eas, m, tx * TILE, ty * TILE, 5.0, (1.25, 1.25, 1.25),
              25.0 * i, "Cover_%d_%d" % (tx, ty))
    L("RM_YARD | cover: %d crates on the phase's own tiles" % len(cover_tiles))

    # ---- the kid stands on something lit ------------------------------------
    place(eas, mesh(FAC, "indicator-special-area"),
          KID_TILE[0] * TILE, KID_TILE[1] * TILE, 7.0, (2.0, 2.0, 2.0), 0.0,
          "KidPad", pad_mi)

    # ---- sodium floods on tall poles ---------------------------------------
    # The phase asks for "hard shadows that swing when nothing has touched the
    # pole". These do not swing; they do put four hot pools on the ballast so
    # the board is not evenly lit, which is what makes the tiles readable.
    post = mesh(FAC, "warning-traffic")
    for cx, cy in ((LO - 260, LO - 260), (LO - 260, HI + 260),
                   (HI + 260, LO - 260), (HI + 260, HI + 260)):
        pole = place(eas, post, cx, cy, 0.0, (3.0, 3.0, 6.0), 0.0, "FloodPost")
        if pole:
            # A pole standing in its own flood throws a black wedge right across
            # the board, and the board is the one thing that has to stay legible.
            pole.static_mesh_component.set_editor_property("cast_shadow", False)
        lamp = eas.spawn_actor_from_class(unreal.SpotLight,
                                          unreal.Vector(cx, cy, 1150.0),
                                          unreal.Rotator(0.0, -60.0, 0.0))
        if lamp:
            lamp.set_actor_label("Flood")
            lamp.tags = [TAG]
            c = lamp.light_component
            # Movable, because a baked light needs a lighting build and an
            # unbuilt one prints a red banner over the game.
            c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
            c.set_editor_property("intensity", 24000.0)
            c.set_editor_property("light_color",
                                  unreal.Color(r=255, g=176, b=94, a=255))
            c.set_editor_property("attenuation_radius", 3200.0)
            c.set_editor_property("outer_cone_angle", 42.0)
            c.set_editor_property("inner_cone_angle", 12.0)
            c.set_editor_property("cast_shadows", True)
            lamp.set_actor_rotation(
                unreal.Rotator(0.0, -62.0,
                               45.0 + (0.0 if cx < MID else 90.0)
                               + (0.0 if cy < MID else 180.0)), False)
    L("RM_YARD | floods: 4 poles with spot lights")

    # ---- the flatcars -------------------------------------------------------
    car_a, car_b = mesh(CITY, "shipping-container-a"), mesh(CITY, "shipping-container-b")
    for i in range(7):
        place(eas, car_a if i % 2 == 0 else car_b,
              -900.0 + i * 620.0, HI + 1500.0, 0.0, (4.5, 4.5, 4.5), 90.0,
              "Flatcar_%d" % i)
    L("RM_YARD | a line of stationary flatcars along the far side")

    # ---- yard machinery, in the margins ------------------------------------
    #  mesh, kit, x, y, z, scale, yaw
    PROPS = [
        ("machine", FAC, LO - 900, 300, 0.0, 3.0, 90.0),
        ("hopper-round", FAC, LO - 950, 1100, 0.0, 3.5, 0.0),
        ("pipe-large-long", FAC, LO - 700, 1700, 0.0, 2.5, 0.0),
        ("conveyor-long", FAC, HI + 800, 200, 0.0, 3.0, 0.0),
        ("catwalk-straight", FAC, HI + 900, 900, 0.0, 3.0, 0.0),
        ("cog-a", FAC, HI + 700, 1600, 200.0, 4.0, 0.0),
        ("screen-wide", FAC, LO - 400, -700, 0.0, 3.0, 45.0),
        ("structure-medium", FAC, HI + 500, -800, 0.0, 3.0, 0.0),
        ("solar-panel-landscape-group", CITY, HI + 1400, -600, 0.0, 5.0, 20.0),
        ("solar-panel-landscape-group", CITY, HI + 1400, 400, 0.0, 5.0, 20.0),
    ]
    for name, kit, x, y, z, s, yaw in PROPS:
        place(eas, mesh(kit, name), x, y, z, (s, s, s), yaw, "Prop_" + name)
    L("RM_YARD | %d machines in the margins" % len(PROPS))

    # ---- skyline ------------------------------------------------------------
    SKY = [
        ("chimney-large", 4200, 5200, 9.0),
        ("water-tower", -3800, 4600, 8.0),
        ("detail-tank-large", 5200, 2000, 7.0),
        ("building-r", -4600, 1200, 8.0),
        ("building-e", 2400, 6400, 9.0),
        ("building-k", -1800, 6000, 8.0),
        ("chimney-large", -5200, 3000, 7.0),
    ]
    for name, x, y, s in SKY:
        place(eas, mesh(CITY, name), x, y, 0.0, (s, s, s), 0.0, "Sky_" + name)
    L("RM_YARD | %d silhouettes on the horizon" % len(SKY))

    # ---- air ----------------------------------------------------------------
    fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog,
                                     unreal.Vector(MID, MID, -200.0))
    if fog:
        fog.set_actor_label("YardAir")
        fog.tags = [TAG]
        c = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
        if c:
            c.set_editor_property("fog_density", 0.035)
            c.set_editor_property("fog_height_falloff", 0.35)
            c.set_editor_property("fog_inscattering_luminance",
                                  unreal.LinearColor(0.12, 0.10, 0.09, 1.0))
        L("RM_YARD | height fog, so the skyline sits behind the yard")

    saved = les.save_current_level()
    if saved is False:
        E("RM_YARD | save_current_level returned False -- %s NOT written" % MAP)
    else:
        L("RM_YARD | saved %s" % MAP)

    counts = {}
    for a in eas.get_all_level_actors():
        k = a.get_class().get_name()
        counts[k] = counts.get(k, 0) + 1
    L("RM_YARD | ---- verify ----")
    for k in sorted(counts):
        L("RM_YARD |   %-28s %d" % (k, counts[k]))


main()
