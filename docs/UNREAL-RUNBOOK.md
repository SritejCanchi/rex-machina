# Unreal runbook

**Status: steps 1-3 done, step 4 scaffolded.** The five structs are built, all
42 rows are imported across the five DataTables, and verify reports 56/56
columns populated with 0 errors. `BP_FightManager` exists with all 24 variables,
all 14 constants set to their spec values and verified by read-back, and all 15
function graphs stubbed -- built by `tools/ue_build_fightmanager.py`, checked by
`tools/ue_verify_fightmanager.py`.

`Manhattan` also has its full signature: A and B as Vector 2D, Distance as
Integer, marked pure. The Blueprint compiles clean and is saved.

What is left is the node graphs. Read this before starting them.

**The graphs cannot be verified from outside.** UE exposes no K2Node API to
Python, which means not only that nodes and wires must be placed by hand, but
that nothing can read a finished graph back and check it. Every other layer of
this build was proved by read-back -- the DataTables against their source CSVs,
the Blueprint variables against the compiled class default object. A graph is
the one thing where "it compiled" is the only signal, and a Blueprint compiles
happily with a wire on the wrong pin.

So wire in small pieces and test each one, rather than building the whole fight
and compiling once. Build order, each a dependency of the next:

    Manhattan  ->  InBounds  ->  StepToward  ->  Predict  ->  RexAct
    Band  ->  DirFreq  ->  Periodicity  ->  FiringCategories  ->  SpeakRead

`RexAct` and `SpeakRead` are the One Wow. The remaining five functions --
TileToWorld, Approach, CheckGate, CheckEnd, OnPlayerMove -- can stay stubs
without stopping a demo of the veto.

Two practical notes from building the scaffold in the editor. Drag off an
existing pin and search from there: UE creates the node already connected,
which removes the separate wire-drag and its failure mode. And a function's
signature lives in the Details panel with the entry node selected, not in the
graph.


Order of operations for the Act 3 showcase build. UE 5.5, Blueprint only, no C++.
The browser build at https://sritej.itch.io/rex-machina stays the submitted
playable link; this is a downloadable showcase, not a replacement.

## 0. Engine version, and the project already exists

**This machine does not have UE 5.0.** `C:\Program Files\Epic Games\UE_5.0` is
the MetaHuman 5.0 plugin -- its own Epic manifest says `AppName: MetaHuman_5.0`
-- 602 MB, no `Binaries/Win64`, no editor anywhere in it. The engine actually
installed is **UE 5.5.4** at `D:\Software\UE_5.5`, complete, Python plugin
present.

Everything here targets 5.5. Nothing was lost by the switch: Blueprint-only
compiles no C++, so the MSVC 14.44 toolset that could not build a 5.0 project
was never on the path anyway.

`D:\Side Projects\AI Game Dev Course\RexMachinaUE\RexMachina.uproject`

Scaffolded, deliberately outside this repo so UE's `Intermediate/`, `Saved/` and
`DerivedDataCache/` never land in it. `PythonScriptPlugin` and
`EditorScriptingUtilities` are enabled in the `.uproject`, so **no plugin
click-path and no restart**. Double-click it and UE opens on an empty level; no
startup map is pinned, which is intentional.

If it refuses to open, delete the folder and make a new Blank / Blueprint / no
starter content project in 5.5 instead, then enable the Python Editor Script
Plugin by hand. Nothing downstream depends on the scaffold. The project has been
opened once already and loads clean.

## 1. The five row structs  (the only slow part)

`docs/UNREAL-STRUCT-CHECKLIST.md`, field by field, in build-priority order.
56 fields total. This cannot be scripted, and that was **verified against this
engine**, not assumed: `unreal.StructureFactory` and `unreal.UserDefinedStruct`
both exist, but `UserDefinedStruct` exposes only generic UObject methods and
`StructureEditorUtils` is absent from the Python bindings entirely. There is no
add-variable API. It is hand typing, about 30-40 minutes.

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

Or headless, with no editor open:

    "D:\Software\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" ^
      "D:\Side Projects\AI Game Dev Course\RexMachinaUE\RexMachina.uproject" ^
      -run=pythonscript -script=".../tools/ue_import_datatables.py" -unattended -nopause

Output lands in `RexMachinaUE/Saved/Logs/`, not on stdout. Expect
`24 + 3 + 6 + 6 + 3 = 42 rows`. Run it today, before the structs exist, and it
fails cleanly five times with `missing row struct ... make it first` -- that is
the script working, and it has been tested that far.

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
