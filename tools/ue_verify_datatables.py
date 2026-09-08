r"""Prove the import actually landed. Editor Python, UE 5.5.

    exec(open(r"D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_verify_datatables.py").read())

Row counts alone do not prove an import worked. If a struct field name does not
match its CSV header, UE fills the row and leaves that field empty -- silently.
This diffs the CSV headers against the columns the asset actually has, then
checks each one for a value.

Verifies against export_data_table_to_csv_string, which is what the asset
actually holds. Do NOT use get_data_table_column_names here: on a
UserDefinedStruct it returns internal GUID-suffixed names like
"ReadID_2_B854...", which never match a CSV header. The export names are the
clean ones. Every engine call is guarded so a surprise cannot wedge the editor.
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
            dumped = list(csv.reader(
                unreal.DataTableFunctionLibrary
                      .export_data_table_to_csv_string(dt).splitlines()))
        except Exception as exc:
            unreal.log_error("  %-20s cannot export: %s" % (table_name, exc))
            problems += 1
            continue

        got_header, got_rows = dumped[0][1:], dumped[1:]   # col 0 is the row key
        expected = csv_header(path)
        want_rows = csv_rows(path)

        missing = [f for f in expected if f not in got_header]
        empty = []
        for field in expected:
            if field in missing:
                continue
            i = got_header.index(field) + 1
            values = [r[i] for r in got_rows if len(r) > i]
            if values and all(v.strip().strip('"').lower() in BLANK for v in values):
                empty.append(field)

        ok = len(got_rows) == want_rows and not missing and not empty
        unreal.log("  %-20s %3d/%-3d rows, %2d/%-2d columns   %s"
                   % (table_name, len(got_rows), want_rows,
                      len(expected) - len(missing), len(expected),
                      "OK" if ok else "CHECK"))

        if len(got_rows) != want_rows:
            unreal.log_error("      row count mismatch: asset %d, CSV %d"
                             % (len(got_rows), want_rows))
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
