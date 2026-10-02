# Unity 6.6 port, built with Unity AI

Project: Unity 6.6 (6000.6.2f1), Universal 2D, Unity AI on a trial plan. The Unity
project itself lives outside this repo; this folder holds everything that matters
for review.

| Path | What it is | Written by |
|---|---|---|
| `Scripts/NemesisReadTable.cs`, `Scripts/Editor/NemesisReadImporter.cs` | Loads `data/DT_NemesisReads.json` into a ScriptableObject. Menu: **Rex Machina > Import Nemesis Reads** | by hand |
| `Plans/rex-boss-turn-port.md` | The plan Unity AI wrote in Plan mode | Unity AI, Plan mode |
| `Scripts/NemesisTurnLogic.cs`, `Scripts/RexBossAgent.cs`, `Scripts/Editor/RexBossTurnVerification.cs` | The C# boss turn, its scene component and its 8-check harness | Unity AI, Agent mode |
| `parity/` | Replays the same move sequences through `game.js` and the C# port and diffs them turn by turn | by hand, run over Unity MCP |
| `AIAssistantSkills/rex-machina-reads/SKILL.md` | Project skill: every line Rex says must be true of the running game, verified by simulation | by hand |

## Parity check

```bash
node unity/parity/js_trace.js > unity/parity/js_trace.json
```

Run `parity/ParityReplay.cs` inside the Unity Editor (Unity MCP `RunCommand`, or any
editor script runner) to write `cs_trace.json`, then:

```bash
python unity/parity/compare.py
```

As delivered by Agent mode the port matched 17 of 48 turns: it counted moves the game
refuses (into the fence, onto Rex's tile) as turns. After one bug report it matches 48 of 48.
