"""Build the dog, the robot dog and the kid out of engine primitives.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_build_characters.py

Replaces the dressing pass's single kit mesh per piece. The kits are an
industrial set and neither of them has an animal or a person in it, so the dog
and the kid were both the same round mascot at two sizes and Rex was a crane.
That reads as placeholder, which is what it was.

Nothing here is a downloaded asset either. Each piece is a small tree of
cubes, spheres and cylinders, which at this camera distance is a style rather
than a compromise: what has to survive is the silhouette, and three blocky
shapes that differ in body plan, proportion and colour survive it better than
three bought models that do not.

The three silhouettes are the whole point, from context/my-capstone.md:

    the dog        four legs, low and long, warm, a tail that reads at a glance
    the robot dog  the same body plan, taller and squarer, cold, one red visor
    the kid        two legs, small, a bright jacket -- not an animal at all

Rex shares the dog's plan on purpose. It is a robot *dog*, and the twist at the
end -- the switched-off machine opening one eye -- only lands if it has been
reading as a dog-shaped thing the whole fight.

Every part hangs off the component called `Mesh`, which keeps its own mesh
empty and acts as the pivot. That is not tidiness: the motion graph in each
piece's EventGraph eases `Mesh` toward the actor every Tick, so anything not
parented to it would teleport while the body slid.
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
SHAPES = "/Engine/BasicShapes/%s.%s"

#  name, base colour, emissive, what it is for
PALETTE = [
    ("MI_Dark",    (0.020, 0.020, 0.022), (0.0, 0.0, 0.0), "eyes, nose, hair, shoes"),
    ("MI_DogPale", (0.660, 0.470, 0.250), (0.0, 0.0, 0.0), "the dog's chest and snout"),
    ("MI_Skin",    (0.860, 0.680, 0.540), (0.0, 0.0, 0.0), "the kid"),
    ("MI_Cloth",   (0.820, 0.200, 0.140), (0.0, 0.0, 0.0), "the kid's jacket, so she reads"),
    ("MI_RexDark", (0.100, 0.110, 0.135), (0.0, 0.0, 0.0), "Rex's joints and feet"),
]

#  part name, shape, location, scale, pitch, material
#  Local Z is height above the tile, because Mesh sits on the tile surface.
DOG = [
    ("P_LegFL",  "Cube",     (30,  14, 20),  (0.15, 0.15, 0.40), 0, "MI_Dog"),
    ("P_LegFR",  "Cube",     (30, -14, 20),  (0.15, 0.15, 0.40), 0, "MI_Dog"),
    ("P_LegBL",  "Cube",     (-30, 14, 20),  (0.15, 0.15, 0.40), 0, "MI_Dog"),
    ("P_LegBR",  "Cube",     (-30, -14, 20), (0.15, 0.15, 0.40), 0, "MI_Dog"),
    ("P_PawFL",  "Cube",     (32,  14, 4),   (0.19, 0.17, 0.08), 0, "MI_Dark"),
    ("P_PawFR",  "Cube",     (32, -14, 4),   (0.19, 0.17, 0.08), 0, "MI_Dark"),
    ("P_PawBL",  "Cube",     (-28, 14, 4),   (0.19, 0.17, 0.08), 0, "MI_Dark"),
    ("P_PawBR",  "Cube",     (-28, -14, 4),  (0.19, 0.17, 0.08), 0, "MI_Dark"),
    ("P_Body",   "Cube",     (0,   0,  58),  (0.88, 0.42, 0.36), 0, "MI_Dog"),
    ("P_Chest",  "Cube",     (33,  0,  57),  (0.30, 0.46, 0.40), 0, "MI_DogPale"),
    ("P_Neck",   "Cube",     (49,  0,  73),  (0.24, 0.26, 0.28), 0, "MI_Dog"),
    ("P_Head",   "Cube",     (63,  0,  87),  (0.34, 0.32, 0.30), 0, "MI_Dog"),
    ("P_Snout",  "Cube",     (81,  0,  81),  (0.26, 0.20, 0.16), 0, "MI_DogPale"),
    ("P_Nose",   "Sphere",   (94,  0,  82),  (0.09, 0.09, 0.09), 0, "MI_Dark"),
    ("P_EarL",   "Cube",     (58,  13, 105), (0.09, 0.10, 0.22), -14, "MI_Dog"),
    ("P_EarR",   "Cube",     (58, -13, 105), (0.09, 0.10, 0.22), -14, "MI_Dog"),
    ("P_EyeL",   "Sphere",   (75,  10, 93),  (0.075, 0.075, 0.075), 0, "MI_Dark"),
    ("P_EyeR",   "Sphere",   (75, -10, 93),  (0.075, 0.075, 0.075), 0, "MI_Dark"),
    ("P_Tail",   "Cube",     (-53, 0,  72),  (0.30, 0.09, 0.09), 30, "MI_Dog"),
]

REX = [
    ("P_LegFL",  "Cube",     (34,  20, 29),  (0.16, 0.16, 0.58), 0, "MI_Rex"),
    ("P_LegFR",  "Cube",     (34, -20, 29),  (0.16, 0.16, 0.58), 0, "MI_Rex"),
    ("P_LegBL",  "Cube",     (-34, 20, 29),  (0.16, 0.16, 0.58), 0, "MI_Rex"),
    ("P_LegBR",  "Cube",     (-34, -20, 29), (0.16, 0.16, 0.58), 0, "MI_Rex"),
    ("P_FootFL", "Cube",     (36,  20, 5),   (0.23, 0.20, 0.10), 0, "MI_RexDark"),
    ("P_FootFR", "Cube",     (36, -20, 5),   (0.23, 0.20, 0.10), 0, "MI_RexDark"),
    ("P_FootBL", "Cube",     (-32, 20, 5),   (0.23, 0.20, 0.10), 0, "MI_RexDark"),
    ("P_FootBR", "Cube",     (-32, -20, 5),  (0.23, 0.20, 0.10), 0, "MI_RexDark"),
    ("P_Body",   "Cube",     (0,   0,  80),  (1.00, 0.50, 0.40), 0, "MI_Rex"),
    ("P_Hip",    "Cube",     (-42, 0,  82),  (0.34, 0.56, 0.46), 0, "MI_RexDark"),
    ("P_Shoulder", "Cube",   (38,  0,  82),  (0.34, 0.58, 0.48), 0, "MI_RexDark"),
    ("P_Spine",  "Cube",     (0,   0, 102),  (0.70, 0.16, 0.10), 0, "MI_RexDark"),
    ("P_Neck",   "Cube",     (58,  0,  96),  (0.20, 0.26, 0.24), 0, "MI_RexDark"),
    ("P_Head",   "Cube",     (74,  0, 110),  (0.40, 0.42, 0.32), 0, "MI_Rex"),
    ("P_Jaw",    "Cube",     (86,  0,  98),  (0.24, 0.30, 0.10), 0, "MI_RexDark"),
    # One visor, not two eyes. Two eyes would read as a face; one band reads as
    # a machine looking at you, and it is the thing that opens at the end.
    ("P_Visor",  "Cube",     (95,  0, 112),  (0.05, 0.34, 0.12), 0, "MI_RexHot"),
    ("P_AntL",   "Cylinder", (64,  14, 141), (0.04, 0.04, 0.30), 0, "MI_RexDark"),
    ("P_AntR",   "Cylinder", (64, -14, 141), (0.04, 0.04, 0.30), 0, "MI_RexDark"),
    ("P_Tail",   "Cube",     (-58, 0,  90),  (0.24, 0.10, 0.10), 18, "MI_RexDark"),
]

KID = [
    ("P_LegL",   "Cube",     (0,  11, 16),   (0.14, 0.15, 0.32), 0, "MI_Dark"),
    ("P_LegR",   "Cube",     (0, -11, 16),   (0.14, 0.15, 0.32), 0, "MI_Dark"),
    ("P_ShoeL",  "Cube",     (3,  11, 4),    (0.20, 0.17, 0.08), 0, "MI_Dark"),
    ("P_ShoeR",  "Cube",     (3, -11, 4),    (0.20, 0.17, 0.08), 0, "MI_Dark"),
    ("P_Torso",  "Cube",     (0,   0, 51),   (0.22, 0.34, 0.38), 0, "MI_Cloth"),
    ("P_ArmL",   "Cube",     (0,  22, 52),   (0.12, 0.11, 0.32), 0, "MI_Cloth"),
    ("P_ArmR",   "Cube",     (0, -22, 52),   (0.12, 0.11, 0.32), 0, "MI_Cloth"),
    ("P_HandL",  "Sphere",   (0,  22, 35),   (0.10, 0.10, 0.10), 0, "MI_Skin"),
    ("P_HandR",  "Sphere",   (0, -22, 35),   (0.10, 0.10, 0.10), 0, "MI_Skin"),
    ("P_Neck",   "Cube",     (0,   0, 73),   (0.10, 0.12, 0.07), 0, "MI_Skin"),
    ("P_Head",   "Sphere",   (0,   0, 89),   (0.30, 0.30, 0.30), 0, "MI_Skin"),
    ("P_Hair",   "Cube",     (-2,  0, 101),  (0.31, 0.31, 0.12), 0, "MI_Dark"),
    ("P_EyeL",   "Sphere",   (12,  6, 90),   (0.055, 0.055, 0.055), 0, "MI_Dark"),
    ("P_EyeR",   "Sphere",   (12, -6, 90),   (0.055, 0.055, 0.055), 0, "MI_Dark"),
]

#  asset, parts, scale on the Mesh pivot, yaw
#
#  Yaw matters more than any of the modelling. Everything is authored facing
#  +X, and the camera looks along +Y, so +X is screen-left and a piece built
#  that way shows the camera its flank at best and its back at worst -- Rex
#  spent a whole pass reading as a dark box because its visor was on the far
#  side. -90 turns a piece to face the camera; the odd numbers below are
#  three-quarter views, which show a silhouette and a face at the same time.
#
#  The parts are authored at roughly life size -- a 115cm dog, a 156cm robot,
#  a 106cm child -- and then scaled up together, because a tile is two metres
#  across and life size on a two-metre tile reads as a toy. Rex is scaled the
#  least and still ends up the tallest thing on the board, which is the point.
BUILDS = [("BP_Dog", DOG, 1.35, -68.0),
          ("BP_Rex", REX, 1.20, -112.0),
          ("BP_Kid", KID, 1.30, -90.0)]


def make_palette():
    parent = unreal.load_asset("%s/M_Greybox.M_Greybox" % MATS)
    if parent is None:
        E("RM_CHAR | M_Greybox missing -- run ue_make_materials.py first")
        return
    for name, base, emis, note in PALETTE:
        path = "%s/%s" % (MATS, name)
        mi = unreal.load_asset(path + "." + name)
        if mi is None:
            mi = AT.create_asset(name, MATS, unreal.MaterialInstanceConstant,
                                 unreal.MaterialInstanceConstantFactoryNew())
        if mi is None:
            E("RM_CHAR | %-11s could not create" % name)
            continue
        MEL.set_material_instance_parent(mi, parent)
        MEL.set_material_instance_vector_parameter_value(
            mi, "BaseColor", unreal.LinearColor(base[0], base[1], base[2], 1.0))
        MEL.set_material_instance_vector_parameter_value(
            mi, "Emissive", unreal.LinearColor(emis[0], emis[1], emis[2], 1.0))
        unreal.EditorAssetLibrary.save_asset(path)
        L("RM_CHAR | %-11s %s" % (name, note))


def handles(bp):
    """Every component handle on the Blueprint, keyed by its name.

    Names come back suffixed -- "Mesh" reads as "Mesh_GEN_VARIABLE" -- so the
    key here is the part before that suffix.
    """
    out = {}
    for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
        data = SDS.k2_find_subobject_data_from_handle(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
        if obj is not None:
            out[obj.get_name().split("_GEN_VARIABLE")[0]] = (h, obj)
    return out


def add(bp, parent_handle, cls, name):
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", parent_handle)
    params.set_editor_property("new_class", cls)
    params.set_editor_property("blueprint_context", bp)
    handle, fail = SDS.add_new_subobject(params)
    if fail and str(fail):
        E("RM_CHAR | add %s: %s" % (name, fail))
        return None, None
    SDS.rename_subobject(handle, name)
    data = SDS.k2_find_subobject_data_from_handle(handle)
    return handle, unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)


def drop(bp, root_handle, name):
    """Remove a component by name. Used once, to clear the kit-mesh era."""
    have = handles(bp)
    if name not in have:
        return False
    try:
        SDS.delete_subobject(root_handle, have[name][0], bp)
        L("RM_CHAR |   removed %s" % name)
        return True
    except Exception as exc:
        E("RM_CHAR |   could not remove %s: %s" % (name, str(exc)[:80]))
        return False


def build(asset, parts, mesh_scale, yaw):
    bp = unreal.load_asset("%s/%s.%s" % (PKG, asset, asset))
    if bp is None:
        E("RM_CHAR | %s missing" % asset)
        return
    root_handle = SDS.k2_gather_subobject_data_for_blueprint(bp)[0]
    have = handles(bp)
    if "Mesh" not in have:
        E("RM_CHAR | %s has no component called Mesh" % asset)
        return
    mesh_handle, mesh = have["Mesh"]

    # Mesh becomes the pivot and stops drawing. The motion graph moves this
    # component and this component only, so it has to stay, keep its name, and
    # keep its rest height of 5 above the tile.
    mesh.set_editor_property("static_mesh", None)
    mesh.set_editor_property("override_materials", [])
    mesh.set_editor_property("relative_scale3d",
                             unreal.Vector(mesh_scale, mesh_scale, mesh_scale))
    mesh.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 5.0))
    mesh.set_editor_property("relative_rotation",
                             unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
    mesh.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)

    # Rex's old head sphere and its lamp hung off the root, so they stayed put
    # while the eased body slid out from under them.
    for stale in ("Eye", "Lamp"):
        drop(bp, root_handle, stale)

    made = 0
    have = handles(bp)
    for name, shape, loc, scale, pitch, mat_name in parts:
        if name in have:
            comp = have[name][1]
        else:
            _, comp = add(bp, mesh_handle, unreal.StaticMeshComponent, name)
        if comp is None:
            continue
        comp.set_editor_property("static_mesh",
                                 unreal.load_asset(SHAPES % (shape, shape)))
        comp.set_editor_property("relative_location", unreal.Vector(*loc))
        comp.set_editor_property("relative_scale3d", unreal.Vector(*scale))
        # Rotator's positional order is roll, pitch, yaw. Every rotation here
        # is a pitch, and passing it first would roll the ears sideways.
        comp.set_editor_property("relative_rotation",
                                 unreal.Rotator(roll=0.0, pitch=pitch, yaw=0.0))
        comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        mi = unreal.load_asset("%s/%s.%s" % (MATS, mat_name, mat_name))
        comp.set_editor_property("override_materials", [mi] if mi else [])
        try:
            comp.set_collision_profile_name("NoCollision")
        except Exception:
            pass
        made += 1

    if asset == "BP_Rex":
        lamp = None
        if "Lamp" not in handles(bp):
            _, lamp = add(bp, mesh_handle, unreal.PointLightComponent, "Lamp")
        else:
            lamp = handles(bp)["Lamp"][1]
        if lamp is not None:
            lamp.set_editor_property("relative_location",
                                     unreal.Vector(102.0, 0.0, 112.0))
            lamp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
            lamp.set_editor_property("intensity", 7000.0)
            lamp.set_editor_property("attenuation_radius", 380.0)
            lamp.set_editor_property("light_color",
                                     unreal.Color(r=255, g=48, b=28, a=255))
            lamp.set_editor_property("cast_shadows", False)

    BEL.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset("%s/%s" % (PKG, asset))
    L("RM_CHAR | %-8s %2d parts under Mesh" % (asset, made))


def verify():
    L("RM_CHAR | ---- verify ----")
    for asset, parts, _, _yaw in BUILDS:
        bp = unreal.load_asset("%s/%s.%s" % (PKG, asset, asset))
        have = handles(bp) if bp else {}
        want = set(p[0] for p in parts)
        missing = sorted(want - set(have))
        mesh = have.get("Mesh", (None, None))[1]
        still = mesh.get_editor_property("static_mesh") if mesh else "no Mesh"
        L("RM_CHAR |   %-8s %d/%d parts, Mesh draws %s%s"
          % (asset, len(want) - len(missing), len(want),
             still if still else "nothing",
             "" if not missing else "  MISSING " + ", ".join(missing)))


def main():
    L("RM_CHAR | ---- characters ----")
    make_palette()
    for asset, parts, mesh_scale, yaw in BUILDS:
        build(asset, parts, mesh_scale, yaw)
    verify()


main()
