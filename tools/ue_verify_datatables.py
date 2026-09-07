"""Prove the import actually landed. Editor Python, UE 5.0.

    exec(open(r"D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_verify_datatables.py").read())

Row counts alone do not prove an import worked. If a struct field name does not
match its CSV header, UE imports the row and leaves that field empty -- silently.
This checks every column the CSV declares and reports the ones that did not make
it, which is exactly what a misspelt field looks like.

Every engine call is guarded. If an API is missing on this build the script says
so and falls back to the next check rather than throwing, so it can never wedge
the editor mid-run. A FALLBACK line means that check could not run, not that the
table is bad.
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

BLANK = ("", "0", "0.0", "false", "none", "\"\"")


def csv_fields(abs_path):
    """CSV headers minus column 0, which UE consumes as the row key."""
    with open(abs_path, encoding="utf-8-sig") as fh:
        return next(csv.reader(fh))[1:]


def column_values(dt, field):
    """Values of one column, or None if this build cannot report columns."""
    fn = getattr(unreal.DataTableFunctionLibrary, "get_data_table_column_as_string", None)
    if fn is None:
        return None
    try:
        return list(fn(dt, field))
    except Exception:
        return []          # the call exists and rejected the name: field absent


def main():
    unreal.log("---- Rex Machina DataTable verify ----")
    problems = 0
    columns_checkable = True

    for rel, table_name in TABLES:
        abs_path = os.path.join(REPO, rel)
        dt = unreal.load_asset("%s/%s.%s" % (DEST, table_name, table_name))

        if dt is None:
            unreal.log_error("  %-20s NOT IMPORTED" % table_name)
            problems += 1
            continue
        if not os.path.exists(abs_path):
            unreal.log_error("  %-20s CSV missing: %s" % (table_name, abs_path))
            problems += 1
            continue

        try:
            rows = len(unreal.DataTableFunctionLibrary.get_data_table_row_names(dt))
        except Exception as exc:
            unreal.log_error("  %-20s cannot read row names: %s" % (table_name, exc))
            problems += 1
            continue

        expected = csv_fields(abs_path)
        expected_rows = sum(1 for _ in open(abs_path, encoding="utf-8")) - 1

        missing, empty, unchecked = [], [], False
        for field in expected:
            values = column_values(dt, field)
            if values is None:
                unchecked = True
                columns_checkable = False
                break
            if not values:
                missing.append(field)
            elif all(v.strip().strip('"').lower() in BLANK for v in values):
                empty.append(field)

        row_ok = rows == expected_rows
        ok = row_ok and not (missing or empty)
        note = "FALLBACK (row count only)" if unchecked else ("OK" if ok else "CHECK")
        unreal.log("  %-20s %3d/%-3d rows, %2d fields declared   %s"
                   % (table_name, rows, expected_rows, len(expected), note))

        if not row_ok:
            unreal.log_error("      row count mismatch: asset has %d, CSV has %d"
                             % (rows, expected_rows))
            problems += 1
        for field in missing:
            unreal.log_error("      column not in the row struct: %s" % field)
            problems += 1
        for field in empty:
            unreal.log_error("      column empty in every row: %s" % field)
            problems += 1

    if not columns_checkable:
        unreal.log("  note: this build has no get_data_table_column_as_string, so")
        unreal.log("        only row counts were checked. Spot-check one row of")
        unreal.log("        DT_NemesisReads by hand: Line and ChargeBand must be filled.")
    unreal.log("  %s" % ("all five tables clean" if not problems
                         else "%d problem(s) above -- fix the struct field names" % problems))


main()
