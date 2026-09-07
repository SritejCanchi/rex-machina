# Struct build checklist (generated from the CSV headers)

Ordered by what the Act 3 fight needs first. Build 1 and 2, run the import,
prove a row loads in a Blueprint, *then* do 3-5. Field order does not matter to
the importer (it matches by name) but typing in CSV order makes miscounts obvious.

The first CSV column is the row key and is NOT a struct field. Do not add it.

## 1. `F_NemesisRead`  ->  `DT_NemesisReads`  (24 rows)

the 24 things the robot says. Powers SpeakRead.

Key column `Name` — skip it. 8 fields:

| # | Field | Type |
|---|---|---|
| 1 | ReadID | String |
| 2 | ReadCategory | String |
| 3 | ChargeBand | String |
| 4 | Line | String |
| 5 | WordCount | Integer |
| 6 | ObservableCited | String |
| 7 | TriggerCondition | String |
| 8 | Provenance | String |

## 2. `F_ArenaPhase`  ->  `DT_ArenaPhases`  (3 rows)

the 3 arenas. Powers CheckGate, InBounds, cover_habit, exit_fixation.

Key column `Name` — skip it. 16 fields:

| # | Field | Type |
|---|---|---|
| 1 | PhaseID | String |
| 2 | PhaseIndex | Integer |
| 3 | ApproachLow | Float |
| 4 | ApproachHigh | Float |
| 5 | ArenaName | String |
| 6 | GridSpan | String |
| 7 | ExitTiles | String |
| 8 | CoverTiles | String |
| 9 | Light | String |
| 10 | SoundBed | String |
| 11 | Props | String |
| 12 | GateOpenMoment | String |
| 13 | PlayerSees | String |
| 14 | CallbackBeat | String |
| 15 | NemesisPressure | String |
| 16 | Provenance | String |

## 3. `F_RetryRead`  ->  `DT_RetryReads`  (6 rows)

what it says on respawn. Read after a loss.

Key column `RowName` — skip it. 8 fields:

| # | Field | Type |
|---|---|---|
| 1 | Gate | String |
| 2 | Phase | Integer |
| 3 | ChargeBand | String |
| 4 | Line | String |
| 5 | WordCount | Integer |
| 6 | Attempts | Integer |
| 7 | RulesFired | String |
| 8 | Provenance | String |

## 4. `F_JourneyHazard`  ->  `DT_JourneyHazards`  (6 rows)

Acts 1-2. Not read by the Act 3 fight; showcase only.

Key column `Name` — skip it. 14 fields:

| # | Field | Type |
|---|---|---|
| 1 | HazardID | String |
| 2 | Day | Integer |
| 3 | Act | Integer |
| 4 | Location | String |
| 5 | PursuerType | String |
| 6 | Telegraph | String |
| 7 | WindowTurns | Integer |
| 8 | TileSpan | String |
| 9 | EscapeCondition | String |
| 10 | FailCondition | String |
| 11 | CausesCondition | Boolean |
| 12 | Teaches | String |
| 13 | PlayerSees | String |
| 14 | Provenance | String |

## 5. `F_JourneyBeat`  ->  `DT_JourneyBeats`  (3 rows)

journey prose. Not read by the Act 3 fight; showcase only.

Key column `RowName` — skip it. 10 fields:

| # | Field | Type |
|---|---|---|
| 1 | Beat | String |
| 2 | ViolationClass | String |
| 3 | WordBudget | Integer |
| 4 | ToneTarget | String |
| 5 | Narration | String |
| 6 | WordCount | Integer |
| 7 | ScoreBefore | Float |
| 8 | ScoreAfter | Float |
| 9 | Repairs | Integer |
| 10 | Outcome | String |

## Totals

| Struct | Fields |
|---|---|
| F_NemesisRead | 8 |
| F_ArenaPhase | 16 |
| F_RetryRead | 8 |
| F_JourneyHazard | 14 |
| F_JourneyBeat | 10 |
| **all five** | **56** |
