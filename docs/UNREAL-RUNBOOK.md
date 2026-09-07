# Unreal runbook

Order of operations for the Act 3 showcase build. UE 5.0, Blueprint only, no C++.
The browser build at https://sritej.itch.io/rex-machina stays the submitted
playable link; this is a downloadable showcase, not a replacement.

## 0. The project already exists

`D:\Side Projects\AI Game Dev Course\RexMachinaUE\RexMachina.uproject`

Scaffolded, deliberately outside this repo so UE's `Intermediate/`, `Saved/` and
`DerivedDataCache/` never land in it. `PythonScriptPlugin` and
`EditorScriptingUtilities` are enabled in the `.uproject`, so **no plugin
click-path and no restart**. Double-click it and UE opens on an empty level; no
startup map is pinned, which is intentional.

If it refuses to open, delete the folder and make a new Blank / Blueprint / no
starter content project instead, then enable the Python Editor Script Plugin by
hand under Edit > Plugins. Nothing downstream depends on the scaffold.

## 1. The five row structs  (the only slow part)

`docs/UNREAL-STRUCT-CHECKLIST.md`, field by field, in build-priority order.
56 fields total. This cannot be scripted -- UE exposes struct asset creation to
Python but not member creation -- so it is hand typing, about 30-40 minutes.

Content Browser > Add > Blueprints > Structure. Each new struct opens with one
default Boolean member: rename and retype that as field 1 rather than leaving a
stray sixth field. Save each one.

**Get every name right the first time.** Renaming a field afterwards mints a new
GUID-backed property and orphans whatever was imported into the old one.

Do `F_NemesisRead` and `F_ArenaPhase` first, then stop and run step 2. Those two
are the only tables the fight reads. `DT_JourneyHazards` and `DT_JourneyBeats`
are Acts 1-2 and are never read by Act 3 logic; `DT_RetryReads` only fires after
a loss. If tomorrow goes sideways you want a working fight, not five half-built
structs.

## 2. Import

Window > Developer Tools > Output Log, dropdown to Python:

    exec(open(r"D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_import_datatables.py").read())

Expect `24 + 3 + 6 + 6 + 3 = 42 rows`.

If it fails, do not debug it on the clock: drag the five CSVs into the Content
Browser and pick the row struct in the dialog. Two minutes, guaranteed.

## 3. Verify

    exec(open(r"D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_verify_datatables.py").read())

Row counts do not prove an import worked. A struct field whose name does not
match its CSV header imports blank on every row, silently. This diffs the CSV
headers against what the asset actually stored.

A `FALLBACK (row count only)` line means the column check could not run on this
build, not that the table is bad. In that case open `DT_NemesisReads` and eyeball
one row: `Line` and `ChargeBand` must be filled.

## 4. The fight

`docs/UNREAL-BLUEPRINT-SPEC.md`, node by node. Build in the order that doc gives
at the end: the veto in `RexAct` first, then `SpeakRead`. Those two are the One
Wow. A grey box with two capsules that cuts you off and tells you why is worth
more than a dressed arena that chases.

## Known gaps

- `DT_RetryReads` covers 6 of the 9 gate x band combinations. Missing
  `yard/confident`, `fence_gap/strained`, `train_yard/clinical`. The spec does
  not say what to do on a miss -- fall back to silence, per the SpeakRead rule
  that silence beats a lie.
- Starting stamina is `17 - min(JourneyFails, 3)`. There is no journey in the
  Unreal build, so use 15 and expose it to test the 14-17 range.
