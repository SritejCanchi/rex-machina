# Repeated runs: the same question, ten times

Question (Unity AI Assistant, Ask mode, Unity Lite tier, a fresh conversation each run):

> Using Assets/RexMachina/Data/DT_NemesisReads.json and Assets/RexMachina/gdd_rex_machina.md:
> Rex is the boss agent. If the player moves right six turns in a row, which ReadCategory and
> ChargeBand rows could fire, and what line would Rex say? Answer as a short table with ReadID,
> TriggerCondition and Line.

Five runs with the project skill `AIAssistantSkills/rex-machina-reads` set to Allow, five with it
set to Deny. Credits are read from each answer. Each answer was scored by hand against the C# port
run over Unity MCP (silent on turns 1 to 3, "Movement repeated on cycle." on turn 4, the
exit-fixation line on turn 5, turn 6 refused at the fence).

| Field | Meaning |
|---|---|
| `rows_ok` | cites real rows from the table, no invented IDs |
| `runtime_ok` | says what Rex actually says, turn by turn, with nothing wrong |
| `simulated` | executed editor code to check, visible as a tool call |
| `exit_flag` | flags that the exit-fixation line claims two approaches when the trigger needs one |

| | Runs | Credits | runtime_ok | simulated | exit_flag |
|---|---|---|---|---|---|
| With skill | 5 | 9 to 19, mean 12.8 | 5 | 3 | 3 |
| Without skill | 5 | 7 to 11, mean 9.2 | 0 | 0 | 0 |

Five runs a side is a small sample. Read it as a direction, not a rate.
