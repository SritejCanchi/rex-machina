"""Can a Blueprint read one DataTable column as a plain string array?

If GetDataTableColumnAsString works with the authored column name, SpeakRead
needs no GetDataTableRow node, no BreakStruct, and no struct pin at all: the
line is Array_Get(lines, index) where index is arithmetic. That removes the
only two node classes still uncaptured, and with them the last reason the
speech work needs the graph editor for anything but pasting.

Run from the editor's Python console; read RM_COL lines out of the log.
"""
import unreal

L = unreal.log


def line(tag, msg):
    L("RM_COL %s | %s" % (tag, msg))


def main():
    dt = unreal.load_asset("/Game/Data/DT_NemesisReads.DT_NemesisReads")
    if dt is None:
        line("FAIL", "DT_NemesisReads missing")
        return

    # The GUID-suffixed internal names, in case the authored one is rejected.
    try:
        cols = unreal.DataTableFunctionLibrary.get_data_table_column_names(dt)
        line("INTERNAL", "%s" % [str(c) for c in cols])
    except Exception as exc:
        line("INTERNAL", "unavailable: %s" % str(exc)[:90])

    for name in ("Line", "ReadCategory", "ChargeBand"):
        try:
            vals = unreal.DataTableFunctionLibrary.get_data_table_column_as_string(dt, name)
            line("AUTHORED", "%-13s -> %d values, [0]=%r" %
                 (name, len(vals), (vals[0][:60] if vals else None)))
        except Exception as exc:
            line("AUTHORED", "%-13s -> FAILED %s" % (name, str(exc)[:90]))

    # Confirm ordering matches the CSV, since the whole index scheme rests on it.
    try:
        lines = unreal.DataTableFunctionLibrary.get_data_table_column_as_string(dt, "Line")
        cats = unreal.DataTableFunctionLibrary.get_data_table_column_as_string(dt, "ReadCategory")
        bands = unreal.DataTableFunctionLibrary.get_data_table_column_as_string(dt, "ChargeBand")
        for i in (0, 4, 6, 12, 20):
            if i < len(lines):
                line("ORDER", "%2d %-18s %-10s %s" % (i, cats[i], bands[i], lines[i][:52]))
    except Exception as exc:
        line("ORDER", "unavailable: %s" % str(exc)[:90])


main()
