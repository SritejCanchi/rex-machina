# Unity 6.6 port (in progress)

Project: Unity 6.6 (6000.6.2f1), Universal 2D, Unity AI enabled. The Unity
project itself lives outside this repo; these are the scripts that read the
shared data contract.

- `Scripts/NemesisReadTable.cs`: the row type and a ScriptableObject that holds
  `data/DT_NemesisReads.json`.
- `Scripts/Editor/NemesisReadImporter.cs`: menu item **Rex Machina > Import
  Nemesis Reads**. Re-run after a pipeline run; no hand edits.

Setup: copy `data/*.json` to `Assets/RexMachina/Data/` and these scripts to
`Assets/RexMachina/Scripts/`, then run the menu item. 24 rows import.
