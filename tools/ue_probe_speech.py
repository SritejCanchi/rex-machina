"""Report everything SpeakRead needs that cannot be read off disk.

Run from the editor's Python console (bottom bar, set to Python):

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_probe_speech.py

then read the RM_PROBE lines out of RexMachinaUE/Saved/Logs/RexMachina.log.

Two things are only knowable from inside the editor. A user-defined struct's
properties are stored with a GUID suffix -- `Line` is really something like
`Line_5_9AF3...` -- so a BreakStruct node's pin names cannot be guessed, the
same trap that made get_data_table_column_names useless for the import
verifier. And whether Python can reach a Blueprint's graphs at all decides
whether the remaining functions can be built without the graph editor.
"""
import unreal

L = unreal.log


def line(tag, msg):
    L("RM_PROBE %s | %s" % (tag, msg))


def struct_properties():
    """The internal, GUID-suffixed property names on F_NemesisRead."""
    path = "/Game/Data/F_NemesisRead.F_NemesisRead"
    s = unreal.load_asset(path)
    if s is None:
        line("STRUCT", "MISSING %s" % path)
        return
    line("STRUCT", "loaded %s (%s)" % (path, type(s).__name__))
    try:
        for d in unreal.StructIterator(s) if hasattr(unreal, "StructIterator") else []:
            line("STRUCT", "iter %s" % d)
    except Exception:
        pass
    # The reliable route: make a default instance and ask it for field names.
    try:
        inst = unreal.StructBase  # placeholder; real read is below
    except Exception:
        pass
    try:
        names = [str(n) for n in unreal.EditorAssetLibrary.get_metadata_tag_values(s)]
        line("STRUCT", "metadata tags: %s" % names[:12])
    except Exception as exc:
        line("STRUCT", "metadata unavailable: %s" % str(exc)[:80])


def datatable():
    dt = unreal.load_asset("/Game/Data/DT_NemesisReads.DT_NemesisReads")
    if dt is None:
        line("TABLE", "MISSING DT_NemesisReads")
        return
    rows = unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)
    line("TABLE", "rows=%d first=%s last=%s" % (len(rows), rows[0], rows[-1]))
    # The export is the only view that uses the authored column names.
    csv = unreal.DataTableFunctionLibrary.export_data_table_to_csv_string(dt)
    head = csv.splitlines()[0] if csv else "(empty)"
    line("TABLE", "header: %s" % head)
    if csv:
        first = csv.splitlines()[1]
        line("TABLE", "row0: %s" % first[:150])


def graph_access():
    """Can Python see a Blueprint's graphs? Decides if the editor is needed."""
    bp = unreal.load_asset("/Game/Blueprints/BP_FightManager.BP_FightManager")
    if bp is None:
        line("GRAPH", "MISSING BP_FightManager")
        return
    for prop in ("function_graphs", "ubergraph_pages", "new_variables",
                 "macro_graphs", "delegate_signature_graphs"):
        try:
            v = bp.get_editor_property(prop)
            line("GRAPH", "%s -> %s (len %s)" % (prop, type(v).__name__,
                                                 len(v) if hasattr(v, "__len__") else "?"))
        except Exception as exc:
            line("GRAPH", "%s -> NOT READABLE (%s)" % (prop, str(exc)[:70]))
    hits = [n for n in dir(unreal.BlueprintEditorLibrary)
            if any(k in n.lower() for k in ("graph", "node", "pin"))]
    line("GRAPH", "BlueprintEditorLibrary graph/node/pin members: %s" % hits)
    kis = [n for n in dir(unreal) if "K2Node" in n or "EdGraph" in n]
    line("GRAPH", "unreal module EdGraph/K2Node types: %s" % kis[:20])


def main():
    line("BEGIN", "----")
    datatable()
    struct_properties()
    graph_access()
    line("END", "----")


main()
