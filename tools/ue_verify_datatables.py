"""Prove the import actually landed. Editor Python, UE 5.0.

    exec(open(r"D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_verify_datatables.py").read())

Row counts alone do not prove an import worked. If a struct field name does not
match its CSV header, UE imports the row and leaves that field empty -- silently.
This reads every imported row back and reports any field that is empty in every
row, which is exactly what a misspelt field looks like.
"""
import csv
import os
import unreal

REPO = r"D:\Side Projects\AI Game Dev Course\rex-machina"
DEST = "/Game/Data"

TABLES = [
    (r"pipelines\a4-canon-index-rag\out\DT_NemesisReads.csv",   "DT_NemesisReads"),
    (r"pipelines\a4-canon-index-rag\out\DT_ArenaPhases.csv",    "DT_ArenaPhases"),
    (r"pipelines\a4-canon-index-rag\out\DT_JourneyHazards.csv", "DT_JourneyHazards"),
    (r"pipelines\a6-retry-read-ger\out\DT_RetryReads.csv",      "DT_RetryReads"),
    (r"pipelines\a7-copy-desk-style\out\DT_JourneyBeats.csv",   "DT_JourneyBeats"),
]

BLANK = ("", "0", "0.0", "false", "none")


def main():
    unreal.log("---- Rex Machina DataTable verify ----")
    bad = 0
    for rel, table_name in TABLES:
        path = "%s/%s.%s" % (DEST, table_name, table_name)
        dt = unreal.load_asset(path)
        if dt is None:
            unreal.log_error("  %-20s NOT IMPORTED" % table_name)
            bad += 1
            continue

        with open(os.path.join(REPO, rel), encoding="utf-8-sig") as fh:
            expected = next(csv.reader(fh))[1:]          # drop the key column

        names = unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)
        # Round-trip through UE's own CSV exporter: it writes one column per
        # struct field, so it shows what actually made it into the asset.
        got = next(csv.reader(unreal.DataTableFunctionLibrary
                              .get_data_table_as_string(dt).splitlines()))[1:]
        got = [c.strip().strip('"') for c in got]

        missing = [f for f in expected if f not in got]
        extra = [f for f in got if f not in expected]

        rows = list(csv.DictReader(unreal.DataTableFunctionLibrary
                                   .get_data_table_as_string(dt).splitlines()))
        empty = [f for f in got
                 if rows and all((r.get(f) or "").strip().strip('"').lower() in BLANK
                                 for r in rows)]

        ok = not (missing or extra or empty)
        unreal.log("  %-20s %3d rows, %2d fields  %s"
                   % (table_name, len(names), len(got), "OK" if ok else "CHECK"))
        for label, fields in (("field in CSV but not in struct", missing),
                              ("field in struct but not in CSV", extra),
                              ("field empty in every row", empty)):
            for f in fields:
                unreal.log_error("      %s: %s" % (label, f))
                bad += 1

    unreal.log("  %s" % ("all five tables clean" if not bad
                         else "%d problem(s) above -- fix the struct field names" % bad))


main()
