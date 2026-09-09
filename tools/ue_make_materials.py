"""Create M_Greybox and the material instances that make the board readable.

    "D:/Software/UE_5.5/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" ^
      "D:/Side Projects/AI Game Dev Course/RexMachinaUE/RexMachina.uproject" ^
      -run=pythonscript -script=".../tools/ue_make_materials.py" -unattended -nopause

Headless. Re-runnable.

Tier 0 is a greybox, but it still has to be legible: with every actor on the
default grey material the dog, the robot and the kid are indistinguishable and
the fight cannot be read at all. Colour here is not decoration, it is the
minimum needed to see what is happening.

One parent material with two parameters, then one instance per thing. Instances
are cheap and the colours can be retuned later without touching a graph.

The marker is emissive on purpose. It marks the tile Rex moved to -- the single
most important thing on screen, and the whole point of the One Wow -- so it
should read as a machine readout rather than as scenery.
"""
import unreal

MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
L = unreal.log
E = unreal.log_error

PKG = "/Game/Materials"
PARENT = "M_Greybox"

#  instance name, base colour RGB, emissive RGB, what it is
INSTANCES = [
    ("MI_Tile",    (0.16, 0.15, 0.13), (0.0, 0.0, 0.0),   "floor, dark"),
    ("MI_TileAlt", (0.22, 0.21, 0.18), (0.0, 0.0, 0.0),   "floor, light - checker"),
    ("MI_Dog",     (0.62, 0.34, 0.16), (0.0, 0.0, 0.0),   "the dog, warm"),
    ("MI_Rex",     (0.26, 0.30, 0.36), (0.02, 0.05, 0.07), "the robot, cold"),
    ("MI_Kid",     (0.88, 0.78, 0.42), (0.10, 0.08, 0.03), "the kid, lit"),
    ("MI_Marker",  (0.05, 0.35, 0.45), (0.00, 0.55, 0.80), "the predicted tile"),
]


def make_parent():
    path = "%s/%s" % (PKG, PARENT)
    mat = unreal.load_asset(path + "." + PARENT)
    is_new = mat is None
    if is_new:
        mat = AT.create_asset(PARENT, PKG, unreal.Material, unreal.MaterialFactoryNew())
    if mat is None:
        E("could not create %s" % path)
        return None

    # Build the graph only on first creation. Material.expressions is a
    # protected property and cannot be read from Python, so "has it been built"
    # is inferred from whether the asset already existed -- which is also what
    # keeps a re-run from stacking duplicate nodes.
    if is_new:
        base = MEL.create_material_expression(
            mat, unreal.MaterialExpressionVectorParameter, -400, 0)
        base.set_editor_property("parameter_name", "BaseColor")
        base.set_editor_property("default_value", unreal.LinearColor(0.5, 0.5, 0.5, 1.0))
        MEL.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)

        emis = MEL.create_material_expression(
            mat, unreal.MaterialExpressionVectorParameter, -400, 250)
        emis.set_editor_property("parameter_name", "Emissive")
        emis.set_editor_property("default_value", unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
        MEL.connect_material_property(emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

        rough = MEL.create_material_expression(
            mat, unreal.MaterialExpressionScalarParameter, -400, 500)
        rough.set_editor_property("parameter_name", "Roughness")
        rough.set_editor_property("default_value", 0.85)
        MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

        MEL.recompile_material(mat)
        L("  %s built: BaseColor, Emissive, Roughness" % PARENT)
    else:
        L("  %s already has a graph, left alone" % PARENT)

    unreal.EditorAssetLibrary.save_asset(path)
    return mat


def make_instance(name, base, emis, note, parent):
    path = "%s/%s" % (PKG, name)
    mi = unreal.load_asset(path + "." + name)
    if mi is None:
        mi = AT.create_asset(name, PKG, unreal.MaterialInstanceConstant,
                             unreal.MaterialInstanceConstantFactoryNew())
    if mi is None:
        E("  %-11s could not create" % name)
        return
    MEL.set_material_instance_parent(mi, parent)
    MEL.set_material_instance_vector_parameter_value(
        mi, "BaseColor", unreal.LinearColor(base[0], base[1], base[2], 1.0))
    MEL.set_material_instance_vector_parameter_value(
        mi, "Emissive", unreal.LinearColor(emis[0], emis[1], emis[2], 1.0))
    unreal.EditorAssetLibrary.save_asset(path)
    L("  %-11s base=%-22s %s" % (name, str(base), note))


def verify(parent):
    """Read each instance back and confirm its parent and its colour."""
    L("  ---- verify ----")
    bad = 0
    for name, base, emis, _ in INSTANCES:
        mi = unreal.load_asset("%s/%s.%s" % (PKG, name, name))
        if mi is None:
            E("    %-11s MISSING" % name)
            bad += 1
            continue
        p = mi.get_editor_property("parent")
        got = MEL.get_material_instance_vector_parameter_value(mi, "BaseColor")
        ok = (p is not None and p.get_name() == PARENT
              and abs(got.r - base[0]) < 1e-3 and abs(got.g - base[1]) < 1e-3)
        L("    %-11s parent=%-11s base=(%.2f, %.2f, %.2f)  %s"
          % (name, p.get_name() if p else "None", got.r, got.g, got.b,
             "OK" if ok else "MISMATCH"))
        if not ok:
            bad += 1
    L("  %s" % ("all %d instances correct" % len(INSTANCES) if not bad
                else "%d problem(s)" % bad))


def main():
    L("---- Rex Machina materials ----")
    unreal.EditorAssetLibrary.make_directory(PKG)
    parent = make_parent()
    if parent is None:
        return
    for name, base, emis, note in INSTANCES:
        make_instance(name, base, emis, note, parent)
    verify(parent)


main()
