"""Create the Tier 0 greybox actors: tile, marker, dog, rex, kid.

    "D:/Software/UE_5.5/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" ^
      "D:/Side Projects/AI Game Dev Course/RexMachinaUE/RexMachina.uproject" ^
      -run=pythonscript -script=".../tools/ue_make_actors.py" -unattended -nopause

Runs headless -- no editor window and no window focus required.

Everything is built from Engine/BasicShapes, so Tier 0 needs no downloaded
asset at all. This is the spec's own advice taken literally: "A grey box with
two capsules that cuts you off and tells you why is worth more than a dressed
arena that chases."

BP_Marker is not decoration. It is the tile Rex moved to, and without it on
screen the prediction is invisible and the One Wow does not read -- the fight
just looks like a chase.

Sizes are in centimetres and derive from TileSize = 200 on BP_FightManager. The
engine Cube is 100cm, so a scale of 2.0 gives one 200cm tile.
"""
import unreal

BEL = unreal.BlueprintEditorLibrary
L = unreal.log
E = unreal.log_error

PKG = "/Game/Blueprints"
SHAPES = "/Engine/BasicShapes/%s.%s"

MATS = "/Game/Materials/%s.%s"

#  asset name, mesh, scale, z offset (cm), material instance, note
ACTORS = [
    ("BP_Tile",   "Cube",     (2.0, 2.0, 0.10),   0.0,  "MI_Tile",   "one 200cm floor tile"),
    ("BP_Marker", "Cube",     (1.80, 1.80, 0.04), 12.0, "MI_Marker", "the tile Rex moved to"),
    ("BP_Dog",    "Cylinder", (0.60, 0.60, 0.55), 55.0, "MI_Dog",    "the player"),
    ("BP_Rex",    "Cylinder", (0.70, 0.70, 0.80), 80.0, "MI_Rex",    "the robot"),
    ("BP_Kid",    "Cone",     (0.60, 0.60, 1.00), 100.0, "MI_Kid",   "the goal"),
]


def make_actor(name, mesh_name, scale, z, mat_name, note):
    path = "%s/%s" % (PKG, name)
    bp = unreal.load_asset(path + "." + name)
    if bp is None:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Actor)
        bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, PKG, unreal.Blueprint, factory)
    if bp is None:
        E("  %-10s could not create" % name)
        return None

    mesh = unreal.load_asset(SHAPES % (mesh_name, mesh_name))
    if mesh is None:
        E("  %-10s missing mesh %s" % (name, mesh_name))
        return None

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    if not handles:
        E("  %-10s no subobject handles" % name)
        return None

    # reuse the mesh component if this is a re-run, else add one
    comp = None
    for h in handles[1:]:
        data = sds.k2_find_subobject_data_from_handle(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
        if isinstance(obj, unreal.StaticMeshComponent):
            comp = obj
            break

    if comp is None:
        params = unreal.AddNewSubobjectParams()
        params.set_editor_property("parent_handle", handles[0])
        params.set_editor_property("new_class", unreal.StaticMeshComponent)
        params.set_editor_property("blueprint_context", bp)
        new_handle, fail = sds.add_new_subobject(params)
        if fail and str(fail):
            E("  %-10s add_new_subobject: %s" % (name, fail))
        sds.rename_subobject(new_handle, "Mesh")
        data = sds.k2_find_subobject_data_from_handle(new_handle)
        comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)

    if comp is None:
        E("  %-10s could not reach the component template" % name)
        return None

    comp.set_editor_property("static_mesh", mesh)
    mi = unreal.load_asset(MATS % (mat_name, mat_name))
    if mi is not None:
        # override_materials is the property that persists on a Blueprint
        # component template; set_material on the template does not stick.
        comp.set_editor_property("override_materials", [mi])
    else:
        L("  %-10s material %s missing -- run ue_make_materials.py first"
          % (name, mat_name))
    comp.set_editor_property("relative_scale3d", unreal.Vector(*scale))
    comp.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, z))
    # Tiles and markers are scenery; nothing should bump into them. Collision is
    # a method on PrimitiveComponent, not an editor property, and it is not
    # worth failing the build over on a greybox -- so it is attempted, not
    # required.
    try:
        comp.set_collision_profile_name("NoCollision")
    except Exception as exc:
        L("  %-10s collision left at default (%s)" % (name, str(exc)[:60]))

    BEL.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(path)
    L("  %-10s %-9s %-11s scale %-18s z=%-6.1f %s"
      % (name, mesh_name, mat_name, str(scale), z, note))
    return bp


def verify():
    """A create is not proof. Read each component back off the Blueprint.

    Do NOT check with get_components_by_class on the class default object:
    components added to a Blueprint live in its construction script, not on the
    CDO, so that call returns nothing even when the component is present and
    correct. The subobject data is the truth here -- the same view used to add
    them.
    """
    L("  ---- verify ----")
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    bad = 0
    for name, mesh_name, scale, z, mat_name, _ in ACTORS:
        bp = unreal.load_asset("%s/%s.%s" % (PKG, name, name))
        if bp is None:
            E("    %-10s MISSING" % name)
            bad += 1
            continue
        comp = None
        for h in sds.k2_gather_subobject_data_for_blueprint(bp):
            data = sds.k2_find_subobject_data_from_handle(h)
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
            if isinstance(obj, unreal.StaticMeshComponent):
                comp = obj
                break
        if comp is None:
            E("    %-10s has no StaticMeshComponent" % name)
            bad += 1
            continue
        got = comp.get_editor_property("static_mesh")
        sc = comp.get_editor_property("relative_scale3d")
        ovr = comp.get_editor_property("override_materials")
        mat_ok = bool(ovr) and ovr[0] is not None and ovr[0].get_name() == mat_name
        ok = (got is not None and got.get_name() == mesh_name) and mat_ok
        L("    %-10s mesh=%-9s mat=%-11s scale=(%.2f, %.2f, %.2f)  %s"
          % (name, got.get_name() if got else "None",
             ovr[0].get_name() if ovr and ovr[0] else "None", sc.x, sc.y, sc.z,
             "OK" if ok else "MISMATCH"))
        if not ok:
            bad += 1
    L("  %s" % ("all %d actors correct" % len(ACTORS) if not bad
                else "%d problem(s)" % bad))


def main():
    L("---- Rex Machina Tier 0 actors ----")
    for a in ACTORS:
        make_actor(*a)
    verify()


main()
