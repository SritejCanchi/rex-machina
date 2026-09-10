"""Import the Kenney meshes the arena needs, and report their real size.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_import_kits.py

Only the meshes on the list below. The two kits hold about two hundred
between them and importing all of them would put a hundred megabytes of
unreferenced assets in a repo whose entire Content folder is currently two.

Kenney FBX are authored at roughly one unit per metre, not Unreal's
centimetre, so every one of them arrives tiny. Rather than guess a scale,
this prints each mesh's bounding box after import; ue_build_arena.py sizes
things from those numbers.

Re-runnable: replace_existing is on, so a second run overwrites rather than
making Mesh_1.
"""
import os
import unreal

L = unreal.log
E = unreal.log_error

RAW = "D:/Side Projects/AI Game Dev Course/RexMachinaUE/RawAssets/unzipped"
FACTORY = RAW + "/kenney_factory-kit_3.0/Models/FBX format"
CITY = RAW + "/kenney_city-kit-industrial_2.0/Models/FBX format"

#  Every mesh has a job. Nothing is imported "in case".
WANTED = [
    # the pieces
    (FACTORY, "oopi", "/Game/Kits/Factory"),            # the dog, and the kid
    (FACTORY, "crane-magnet", "/Game/Kits/Factory"),    # Rex
    (FACTORY, "indicator-special-cross", "/Game/Kits/Factory"),   # Rex's guess
    (FACTORY, "indicator-special-area", "/Game/Kits/Factory"),    # the kid's tile
    # the arena edge -- "the fence is there" has to be visible to mean anything
    (FACTORY, "structure-wall", "/Game/Kits/Factory"),
    (FACTORY, "warning-traffic", "/Game/Kits/Factory"),
    (FACTORY, "warning-orange", "/Game/Kits/Factory"),
    # cover
    (FACTORY, "box-large", "/Game/Kits/Factory"),
    (FACTORY, "box-wide", "/Game/Kits/Factory"),
    (FACTORY, "box-small", "/Game/Kits/Factory"),
    # dressing, outside the grid
    (FACTORY, "hopper-round", "/Game/Kits/Factory"),
    (FACTORY, "pipe-large", "/Game/Kits/Factory"),
    (FACTORY, "pipe-large-long", "/Game/Kits/Factory"),
    (FACTORY, "machine", "/Game/Kits/Factory"),
    (FACTORY, "conveyor-long", "/Game/Kits/Factory"),
    (FACTORY, "catwalk-straight", "/Game/Kits/Factory"),
    (FACTORY, "cog-a", "/Game/Kits/Factory"),
    (FACTORY, "screen-wide", "/Game/Kits/Factory"),
    (FACTORY, "structure-short", "/Game/Kits/Factory"),
    (FACTORY, "structure-medium", "/Game/Kits/Factory"),
    # skyline. Rex runs on sunlight, so the solar farm is not decoration.
    (CITY, "solar-panel-landscape-group", "/Game/Kits/City"),
    (CITY, "shipping-container-a", "/Game/Kits/City"),
    (CITY, "shipping-container-b", "/Game/Kits/City"),
    (CITY, "chimney-large", "/Game/Kits/City"),
    (CITY, "detail-tank-large", "/Game/Kits/City"),
    (CITY, "water-tower", "/Game/Kits/City"),
    (CITY, "building-e", "/Game/Kits/City"),
    (CITY, "building-k", "/Game/Kits/City"),
    (CITY, "building-r", "/Game/Kits/City"),
]


def options():
    o = unreal.FbxImportUI()
    o.set_editor_property("import_mesh", True)
    o.set_editor_property("import_as_skeletal", False)
    o.set_editor_property("import_materials", True)
    o.set_editor_property("import_textures", True)
    o.set_editor_property("mesh_type_to_import",
                          unreal.FBXImportType.FBXIT_STATIC_MESH)
    d = o.static_mesh_import_data
    d.set_editor_property("combine_meshes", True)
    d.set_editor_property("generate_lightmap_u_vs", True)
    d.set_editor_property("auto_generate_collision", True)
    # Kenney authors Z-up already; letting UE "convert scene" as well flips
    # every piece onto its side.
    d.set_editor_property("convert_scene", True)
    d.set_editor_property("force_front_x_axis", False)
    return o


def main():
    tasks, missing = [], []
    for folder, name, dest in WANTED:
        path = os.path.join(folder, name + ".fbx")
        if not os.path.exists(path):
            missing.append(path)
            continue
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", path)
        t.set_editor_property("destination_path", dest)
        t.set_editor_property("automated", True)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("save", True)
        t.set_editor_property("options", options())
        tasks.append(t)

    for m in missing:
        E("RM_KIT | missing %s" % m)
    if not tasks:
        E("RM_KIT | nothing to import -- is RawAssets/unzipped there?")
        return

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    # A task that reports success can still have produced nothing, so measure.
    for folder, name, dest in WANTED:
        asset_name = name.replace("-", "_")
        for candidate in (name, asset_name, "SM_" + name):
            path = "%s/%s.%s" % (dest, candidate, candidate)
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                mesh = unreal.load_asset(path)
                bmin, bmax = mesh.get_bounding_box().min, mesh.get_bounding_box().max
                L("RM_KIT | %-30s %-24s size %7.1f %7.1f %7.1f" % (
                    candidate, dest.split("/")[-1],
                    bmax.x - bmin.x, bmax.y - bmin.y, bmax.z - bmin.z))
                break
        else:
            E("RM_KIT | %s did not land in %s" % (name, dest))


main()
