"""Put the Kenney meshes on the five actors, and give Rex a lit head.

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

The dog and the kid are the same creature at different sizes and colours. That
is the fiction: you are running to your person, not to a marker. Rex is the
magnet crane, which is the only thing in either kit that looms.
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
    ("BP_Marker", "indicator-special-cross", (2.0, 2.0, 2.0),   7.0,  0.0, "MI_Marker"),
    ("BP_Dog",    "oopi",                    (2.4, 2.4, 2.4),   5.0,  0.0, "MI_Dog"),
    ("BP_Kid",    "oopi",                    (1.5, 1.5, 1.5),   5.0, 180.0, "MI_Kid"),
    ("BP_Rex",    "crane-magnet",            (2.6, 2.6, 2.6),   5.0,  0.0, "MI_Rex"),
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


def named(have, prefix):
    """Look a component up by prefix -- see body_mesh for why not by name."""
    for cname, (h, obj) in have.items():
        if cname.startswith(prefix):
            return obj
    return None


def light_rex():
    """A red lamp in the magnet head, and a sphere so it reads when unlit.

    Rex is the only thing on the board that is dangerous and the only thing
    the player never controls, so it needs to be the only thing that emits.
    The point light is not for illumination -- it is so the tile Rex is
    standing on goes red before you look at it.
    """
    bp = unreal.load_asset("%s/BP_Rex.BP_Rex" % PKG)
    if bp is None:
        E("RM_DRESS | BP_Rex missing")
        return
    have = components(bp)
    root_handle = SDS.k2_gather_subobject_data_for_blueprint(bp)[0]

    eye = named(have, "Eye")
    if eye is None:
        eye = add_component(bp, root_handle, unreal.StaticMeshComponent, "Eye")
    if eye is not None:
        sphere = unreal.load_asset(SHAPES % ("Sphere", "Sphere"))
        eye.set_editor_property("static_mesh", sphere)
        eye.set_editor_property("relative_scale3d", unreal.Vector(0.28, 0.28, 0.28))
        eye.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 215.0))
        mi = unreal.load_asset("%s/MI_RexHot.MI_RexHot" % MATS)
        eye.set_editor_property("override_materials", [mi] if mi else [])
        try:
            eye.set_collision_profile_name("NoCollision")
        except Exception:
            pass

    lamp = named(have, "Lamp")
    if lamp is None:
        lamp = add_component(bp, root_handle, unreal.PointLightComponent, "Lamp")
    if lamp is not None:
        lamp.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 215.0))
        lamp.set_editor_property("intensity", 9000.0)
        lamp.set_editor_property("attenuation_radius", 420.0)
        # unreal.Color takes B, G, R, A positionally -- FColor's own field
        # order -- so the keywords are not optional. Passed positionally,
        # this red lamp came out blue and Rex glowed like the marker.
        lamp.set_editor_property("light_color",
                                 unreal.Color(r=255, g=44, b=26, a=255))
        lamp.set_editor_property("cast_shadows", False)

    BEL.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset("%s/BP_Rex" % PKG)
    L("RM_DRESS | BP_Rex    Eye + Lamp at z=215")


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
    rex = unreal.load_asset("%s/BP_Rex.BP_Rex" % PKG)
    names = sorted(components(rex).keys()) if rex else []
    L("RM_DRESS |   BP_Rex components: %s" % ", ".join(names))
    L("RM_DRESS | %s" % ("all dressed" if not bad else "%d problem(s)" % bad))


def main():
    L("RM_DRESS | ---- dressing pass ----")
    make_extra_materials()
    for d in DRESS:
        dress(*d)
    light_rex()
    verify()


main()
