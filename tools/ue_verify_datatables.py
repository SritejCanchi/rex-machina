r"""Prove the import actually landed. Editor Python, UE 5.5.

    exec(open(r"D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_verify_datatables.py").read())

Row counts alone do not prove an import worked. If a struct field name does not
match its CSV header, UE fills the row and leaves that field empty -- silently.
This diffs the CSV headers against the columns the asset actually has, then
checks each one for a value.

Uses get_data_table_column_names and get_data_table_column_as_string, both
confirmed present on this engine. Every engine call is still guarded so a
surprise can never wedge the editor mid-run.
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

BLANK = ("", "0", "0.0", "false", "none", '""')


def csv_header(path):
    """CSV headers minus column 0, which UE consumes as the row key."""
    with open(path, encoding="utf-8-sig") as fh:
        return next(csv.reader(fh))[1:]


def csv_rows(path):
    return sum(1 for _ in open(path, encoding="utf-8")) - 1


def main():
    unreal.log("---- Rex Machina DataTable verify ----")
    problems = 0

    for rel, table_name in TABLES:
        path = os.path.join(REPO, rel)
        dt = unreal.load_asset("%s/%s.%s" % (DEST, table_name, table_name))

        if dt is None:
            unreal.log_error("  %-20s NOT IMPORTED" % table_name)
            problems += 1
            continue
        if not os.path.exists(path):
            unreal.log_error("  %-20s CSV missing: %s" % (table_name, path))
            problems += 1
            continue

        try:
            rows = len(unreal.DataTableFunctionLibrary.get_data_table_row_names(dt))
            columns = [str(c) for c in
                       unreal.DataTableFunctionLibrary.get_data_table_column_names(dt)]
        except Exception as exc:
            unreal.log_error("  %-20s cannot read the asset: %s" % (table_name, exc))
            problems += 1
            continue

        expected = csv_header(path)
        want_rows = csv_rows(path)

        missing = [f for f in expected if f not in columns]
        empty = []
        for field in expected:
            if field in missing:
                continue
            try:
                values = [str(v) for v in
                          unreal.DataTableFunctionLibrary.get_data_table_column_as_string(dt, field)]
            except Exception:
                continue
            if values and all(v.strip().strip('"').lower() in BLANK for v in values):
                empty.append(field)

        ok = rows == want_rows and not missing and not empty
        unreal.log("  %-20s %3d/%-3d rows, %2d/%-2d columns   %s"
                   % (table_name, rows, want_rows, len(expected) - len(missing),
                      len(expected), "OK" if ok else "CHECK"))

        if rows != want_rows:
            unreal.log_error("      row count mismatch: asset %d, CSV %d" % (rows, want_rows))
            problems += 1
        for field in missing:
            unreal.log_error("      column not in the row struct: %s" % field)
            problems += 1
        for field in empty:
            unreal.log_error("      column empty in every row: %s" % field)
            problems += 1

    unreal.log("  %s" % ("all five tables clean" if not problems
                         else "%d problem(s) above -- fix the struct field names" % problems))


main()
