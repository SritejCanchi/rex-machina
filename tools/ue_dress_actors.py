"""Put the Kenney indicator meshes on the marker, and make the shared palette.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_dress_actors.py

Runs after ue_make_actors.py, which builds the same five Blueprints out of
engine primitives. That greybox stage stays in the repo on purpose: it is the
version that needs no downloaded asset, and it is what proves the fight reads
without art. This script is the dressing pass on top of it, and it only ever
edits the component template -- the graphs, the variables and the round loop
are untouched.

Kenney's factory kit is authored on a 100cm grid. TileSize here is 200, so the
kit scale is almost always 2.0 and the two indicator decals land exactly on a
tile with no fudging.

The three characters used to be dressed here too, out of the same kits. They
are not any more: neither kit has an animal or a person in it, so the dog and
the kid were the same round mascot at two sizes and Rex was a crane, and the
whole board read as placeholder. ue_build_characters.py builds those three out
of primitives instead. This script now owns the marker and the palette.
"""
import unreal

BEL = unreal.BlueprintEditorLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
L = unreal.log
E = unreal.log_error

PKG = "/Game/Blueprints"
MATS = "/Game/Materials"
KIT = "/Game/Kits/Factory"
SHAPES = "/Engine/BasicShapes/%s.%s"

#  Extra instances this pass needs. ue_make_materials.py owns the parent and
#  the first six; these are additions, created here so the dressing pass is
#  one script rather than two that have to run in order.
EXTRA_MI = [
    ("MI_RexHot", (0.30, 0.02, 0.02), (3.20, 0.10, 0.05), "Rex's head lamp"),
    ("MI_KidPad", (0.50, 0.36, 0.10), (0.90, 0.55, 0.12), "the tile the kid is on"),
    ("MI_Fence",  (0.17, 0.16, 0.14), (0.00, 0.00, 0.00), "the arena edge"),
    ("MI_Ballast", (0.05, 0.05, 0.045), (0.00, 0.00, 0.00), "the ground the yard sits on"),
]

#  asset, kit mesh, scale, z, yaw, material override (None keeps the kit palette)
DRESS = [
    # The kit's indicator decals are exactly 100 units square, so at scale 2
    # the cross lands on one 200-unit tile with nothing to fudge.
    ("BP_Marker", "indicator-special-cross", (2.0, 2.0, 2.0), 7.0, 0.0, "MI_Marker"),
]


def make_extra_materials():
    parent = unreal.load_asset("%s/M_Greybox.M_Greybox" % MATS)
    if parent is None:
        E("RM_DRESS | M_Greybox missing -- run ue_make_materials.py first")
        return
    for name, base, emis, note in EXTRA_MI:
        path = "%s/%s" % (MATS, name)
        mi = unreal.load_asset(path + "." + name)
        if mi is None:
            mi = AT.create_asset(name, MATS, unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
        if mi is None:
            E("RM_DRESS | %-11s could not create" % name)
            continue
        MEL.set_material_instance_parent(mi, parent)
        MEL.set_material_instance_vector_parameter_value(
            mi, "BaseColor", unreal.LinearColor(base[0], base[1], base[2], 1.0))
        MEL.set_material_instance_vector_parameter_value(
            mi, "Emissive", unreal.LinearColor(emis[0], emis[1], emis[2], 1.0))
        unreal.EditorAssetLibrary.save_asset(path)
        L("RM_DRESS | %-11s %s" % (name, note))


def components(bp):
    """Every component template on the Blueprint, by name.

    Components added to a Blueprint live in its construction data, not on the
    class default object, so get_components_by_class on the CDO returns
    nothing even when they are all present. The subobject view is the truth.
    """
    out = {}
    for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
        data = SDS.k2_find_subobject_data_from_handle(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
        if obj is not None:
            out[obj.get_name()] = (h, obj)
    return out


def body_mesh(bp):
    """The body, never one of the accents.

    Component names come back suffixed -- "Mesh" reads as
    "Mesh_GEN_VARIABLE" -- and once Rex has an Eye there are two
    StaticMeshComponents, so "the first one found" is a coin flip that
    silently puts crane-magnet's mesh onto the lamp sphere.
    """
    for cname, (h, obj) in components(bp).items():
        if isinstance(obj, unreal.StaticMeshComponent) and cname.startswith("Mesh"):
            return obj
    return None


def add_component(bp, parent_handle, cls, name):
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", parent_handle)
    params.set_editor_property("new_class", cls)
    params.set_editor_property("blueprint_context", bp)
    handle, fail = SDS.add_new_subobject(params)
    if fail and str(fail):
        E("RM_DRESS | add %s: %s" % (name, fail))
        return None
    SDS.rename_subobject(handle, name)
    data = SDS.k2_find_subobject_data_from_handle(handle)
    return unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)


def dress(name, mesh_name, scale, z, yaw, mat_name):
    bp = unreal.load_asset("%s/%s.%s" % (PKG, name, name))
    if bp is None:
        E("RM_DRESS | %-10s missing -- run ue_make_actors.py first" % name)
        return
    mesh = unreal.load_asset("%s/%s.%s" % (KIT, mesh_name, mesh_name))
    if mesh is None:
        E("RM_DRESS | %-10s missing mesh %s" % (name, mesh_name))
        return

    comp = body_mesh(bp)
    if comp is None:
        E("RM_DRESS | %-10s has no StaticMeshComponent named Mesh" % name)
        return

    comp.set_editor_property("static_mesh", mesh)
    # The motion graph eases this component's world location every Tick, and a
    # Static component refuses to move at all -- silently, in a shipping build.
    comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    comp.set_editor_property("relative_scale3d", unreal.Vector(*scale))
    comp.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, z))
    comp.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, yaw))
    if mat_name:
        mi = unreal.load_asset("%s/%s.%s" % (MATS, mat_name, mat_name))
        # override_materials is what persists on a component template;
        # set_material on the template silently does not stick.
        comp.set_editor_property("override_materials", [mi] if mi else [])
    else:
        comp.set_editor_property("override_materials", [])

    BEL.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset("%s/%s" % (PKG, name))
    L("RM_DRESS | %-10s %-24s scale %-16s z=%-5.1f mat=%s"
      % (name, mesh_name, str(scale), z, mat_name or "(kit palette)"))


def verify():
    L("RM_DRESS | ---- verify ----")
    bad = 0
    for name, mesh_name, scale, z, yaw, mat_name in DRESS:
        bp = unreal.load_asset("%s/%s.%s" % (PKG, name, name))
        if bp is None:
            E("RM_DRESS |   %-10s MISSING" % name)
            bad += 1
            continue
        got = body_mesh(bp)
        m = got.get_editor_property("static_mesh") if got else None
        ok = m is not None and m.get_name() == mesh_name
        L("RM_DRESS |   %-10s mesh=%-24s %s"
          % (name, m.get_name() if m else "None", "OK" if ok else "MISMATCH"))
        bad += 0 if ok else 1
    L("RM_DRESS | %s" % ("all dressed" if not bad else "%d problem(s)" % bad))


def main():
    L("RM_DRESS | ---- dressing pass ----")
    make_extra_materials()
    for d in DRESS:
        dress(*d)
    verify()


main()
