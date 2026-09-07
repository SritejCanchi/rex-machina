"""Import every pipeline CSV into UE as a DataTable. Editor Python, UE 5.0.

Run it from inside the editor:
    Window > Developer Tools > Output Log, switch the dropdown to Python, then
    exec(open(r"D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_import_datatables.py").read())

Or headless, which is what you want for the pipeline video:
    "C:\\Program Files\\Epic Games\\UE_5.0\\Engine\\Binaries\\Win64\\UnrealEditor-Cmd.exe" ^
      "D:\\path\\RexMachina\\RexMachina.uproject" ^
      -run=pythonscript -script="D:/.../tools/ue_import_datatables.py"

Requires the Python Editor Script Plugin, which ships with 5.0. Enable it once
under Edit > Plugins > Scripting.

The five row structs must exist first. docs/UNREAL-SETUP.md lists their exact
fields. This script does the part worth automating: it re-imports all five
tables from the pipeline output in one run, so regenerating content is a
command rather than a click path.
"""
import os
import unreal

# Where the pipeline writes. Adjust only if you move the repo.
REPO = r"D:\Side Projects\AI Game Dev Course\rex-machina"
DEST = "/Game/Data"          # content browser folder for the DataTables

TABLES = [
    # csv relative to REPO,                                    struct asset,          table asset
    (r"pipelines\a4-canon-index-rag\out\DT_NemesisReads.csv",   "F_NemesisRead",   "DT_NemesisReads"),
    (r"pipelines\a4-canon-index-rag\out\DT_ArenaPhases.csv",    "F_ArenaPhase",    "DT_ArenaPhases"),
    (r"pipelines\a4-canon-index-rag\out\DT_JourneyHazards.csv", "F_JourneyHazard", "DT_JourneyHazards"),
    (r"pipelines\a6-retry-read-ger\out\DT_RetryReads.csv",      "F_RetryRead",     "DT_RetryReads"),
    (r"pipelines\a7-copy-desk-style\out\DT_JourneyBeats.csv",   "F_JourneyBeat",   "DT_JourneyBeats"),
]


def struct_asset(name):
    path = "%s/%s.%s" % (DEST, name, name)
    s = unreal.load_asset(path)
    if s is None:
        unreal.log_error("missing row struct %s. Make it first, see docs/UNREAL-SETUP.md" % path)
    return s


def build_task(csv_path, struct, table_name):
    settings = unreal.CSVImportSettings()
    settings.set_editor_property("import_row_struct", struct)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", csv_path)
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", table_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("factory", unreal.CSVImportFactory())
    task.set_editor_property("options", settings)
    return task


def main():
    unreal.EditorAssetLibrary.make_directory(DEST)
    tasks, wanted = [], []
    for rel, struct_name, table_name in TABLES:
        csv_path = os.path.join(REPO, rel)
        if not os.path.exists(csv_path):
            unreal.log_error("missing CSV: %s" % csv_path)
            continue
        s = struct_asset(struct_name)
        if s is None:
            continue
        tasks.append(build_task(csv_path, s, table_name))
        wanted.append(table_name)

    if tasks:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    unreal.log("---- Rex Machina DataTable import ----")
    total = 0
    for name in wanted:
        dt = unreal.load_asset("%s/%s.%s" % (DEST, name, name))
        if dt is None:
            unreal.log_error("  %-20s FAILED" % name)
            continue
        rows = unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)
        total += len(rows)
        unreal.log("  %-20s %3d rows" % (name, len(rows)))
    unreal.log("  %d rows imported from pipeline output. No file was hand edited." % total)


main()
