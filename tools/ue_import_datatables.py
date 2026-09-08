r"""Import every pipeline CSV into UE as a DataTable. Editor Python, UE 5.5.

Run it from inside the editor:
    Window > Developer Tools > Output Log, switch the dropdown to Python, then
    exec(open(r"D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_import_datatables.py").read())

Or headless, which is what you want for the pipeline video:
    "D:\Software\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" ^
      "D:\Side Projects\AI Game Dev Course\RexMachinaUE\RexMachina.uproject" ^
      -run=pythonscript -script="D:/.../tools/ue_import_datatables.py" -unattended -nopause

Requires the Python Editor Script Plugin. RexMachina.uproject already enables it.

The five row structs must exist first. docs/UNREAL-SETUP.md lists their exact
fields. Creating them is the one step that cannot be scripted: UE exposes
UserDefinedStruct asset creation to Python but no API to add members to one --
verified against this engine, StructureEditorUtils is not in the Python bindings.

This does the part worth automating: it builds or reuses a DataTable per row
struct and fills it straight from the pipeline CSV, so regenerating content is a
command rather than a click path.
"""
import os
import unreal

REPO = r"D:\Side Projects\AI Game Dev Course\rex-machina"
DEST = "/Game/Data"

TABLES = [
    (r"pipelines\a4-canon-index-rag\out\DT_NemesisReads.csv",   "F_NemesisRead",   "DT_NemesisReads"),
    (r"pipelines\a4-canon-index-rag\out\DT_ArenaPhases.csv",    "F_ArenaPhase",    "DT_ArenaPhases"),
    (r"pipelines\a4-canon-index-rag\out\DT_JourneyHazards.csv", "F_JourneyHazard", "DT_JourneyHazards"),
    (r"pipelines\a6-retry-read-ger\out\DT_RetryReads.csv",      "F_RetryRead",     "DT_RetryReads"),
    (r"pipelines\a7-copy-desk-style\out\DT_JourneyBeats.csv",   "F_JourneyBeat",   "DT_JourneyBeats"),
]


def asset_path(name):
    return "%s/%s.%s" % (DEST, name, name)


def get_struct(name):
    s = unreal.load_asset(asset_path(name))
    if s is None:
        unreal.log_error("missing row struct %s -- make it first, see docs/UNREAL-SETUP.md"
                         % asset_path(name))
    return s


def get_or_make_table(table_name, struct):
    """Reuse the DataTable if it exists, else build one bound to this row struct."""
    dt = unreal.load_asset(asset_path(table_name))
    if dt is not None:
        return dt
    factory = unreal.DataTableFactory()
    factory.set_editor_property("struct", struct)
    return unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        table_name, DEST, unreal.DataTable, factory)


def main():
    unreal.EditorAssetLibrary.make_directory(DEST)
    unreal.log("---- Rex Machina DataTable import ----")
    total, failed = 0, 0

    for rel, struct_name, table_name in TABLES:
        csv_path = os.path.join(REPO, rel)
        if not os.path.exists(csv_path):
            unreal.log_error("  %-20s missing CSV: %s" % (table_name, csv_path))
            failed += 1
            continue

        struct = get_struct(struct_name)
        if struct is None:
            failed += 1
            continue

        try:
            dt = get_or_make_table(table_name, struct)
            if dt is None:
                raise RuntimeError("could not create the DataTable asset")
            # Fills from the CSV in place, matching struct fields to headers by
            # name and taking column 0 as the row key.
            unreal.DataTableFunctionLibrary.fill_data_table_from_csv_file(dt, csv_path)
            unreal.EditorAssetLibrary.save_asset(dt.get_path_name())
            rows = len(unreal.DataTableFunctionLibrary.get_data_table_row_names(dt))
            total += rows
            unreal.log("  %-20s %3d rows" % (table_name, rows))
        except Exception as exc:
            unreal.log_error("  %-20s FAILED: %s" % (table_name, exc))
            failed += 1

    unreal.log("  %d rows imported from pipeline output. No file was hand edited." % total)
    if failed:
        unreal.log_error("  %d table(s) failed -- see above" % failed)


main()
