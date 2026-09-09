"""Print DT_NemesisReads' Line column exactly as SpeakRead sees it.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_dump_reads.py

SpeakRead indexes this column with `band * 8 + category`, which is only true if
the table's row order is the CSV's row order. This is the check for that.
"""
import unreal

DT = unreal.load_asset("/Game/Data/DT_NemesisReads.DT_NemesisReads")
col = unreal.DataTableFunctionLibrary.get_data_table_column_as_string(DT, "Line")
names = unreal.DataTableFunctionLibrary.get_data_table_row_names(DT)
for i, line in enumerate(col):
    unreal.log("RM_DT | %2d  %-46s  %s" % (i, str(names[i]), line))
