# Unreal setup: the five row structs

UE 5.0, Blueprint only. Do this once. After it, `tools/ue_import_datatables.py`
re-imports every table in one run whenever a pipeline regenerates its output.

In the Content Browser: **Add > Blueprints > Structure**. Name it exactly as below.
Field names must match the CSV headers exactly or the import drops the column
silently. The `Name` column is the row key and is **not** a struct field.

## F_NemesisRead  (for DT_NemesisReads, 24 rows)

| Field | Type | Example |
|---|---|---|
| ReadID | String | nemesis_read_sealing_direction_clinical |
| ReadCategory | String | sealing_direction |
| ChargeBand | String | clinical |
| Line | String | Target favored left nine of twenty recorded mo |
| WordCount | Integer | 8 |
| ObservableCited | String | dir_freq_20 |
| TriggerCondition | String | one compass direction dominates dir_freq_20 |
| Provenance | String | generated |

## F_ArenaPhase  (for DT_ArenaPhases, 3 rows)

| Field | Type | Example |
|---|---|---|
| PhaseID | String | phase_yard |
| PhaseIndex | Integer | 1 |
| ApproachLow | Float | 0.0 |
| ApproachHigh | Float | 0.33 |
| ArenaName | String | yard |
| GridSpan | String | 10x10 |
| ExitTiles | String  (parse to tiles at runtime) | [[0, 4], [9, 7]] |
| CoverTiles | String  (parse to tiles at runtime) | [[3, 5], [6, 2]] |
| Light | String | Late afternoon, low sun across the grass; the  |
| SoundBed | String | Wind in a chain-link fence, a screen door knoc |
| Props | String | ["chain-link fence line", "porch steps", "coil |
| GateOpenMoment | String | The yard gate at the fence line unlatches and  |
| PlayerSees | String | Home ground turned into a ring. The robot dog  |
| CallbackBeat | String | the_street |
| NemesisPressure | String | Charge above 60 percent. It intercepts on the  |
| Provenance | String | generated |

## F_JourneyHazard  (for DT_JourneyHazards, 6 rows)

| Field | Type | Example |
|---|---|---|
| HazardID | String | shelter_gate |
| Day | Integer | 0 |
| Act | Integer | 1 |
| Location | String | shelter yard, the gate seam between kennel run |
| PursuerType | String | shelter handler with a catch pole, fixed loop  |
| Telegraph | String | catch pole swings left |
| WindowTurns | Integer | 4 |
| TileSpan | String | 5x3 |
| EscapeCondition | String | step through the gate seam on the turn after t |
| FailCondition | String | stand on the gate tile while the pole reaches  |
| CausesCondition | Boolean | False |
| Teaches | String | telegraph reading |
| PlayerSees | String | The yard gate stands open a dog's width, and a |
| Provenance | String | generated |

## F_RetryRead  (for DT_RetryReads, 6 rows)

| Field | Type | Example |
|---|---|---|
| RowName | String | retry_yard_clinical |
| Gate | String | yard |
| Phase | Integer | 1 |
| ChargeBand | String | clinical |
| Line | String | Yard loss noted. Rightward bias confirmed. Gai |
| WordCount | Integer | 9 |
| Attempts | Integer | 2 |
| RulesFired | String | R2_PRIOR_REF/R3_BUDGET |
| Provenance | String | model_refined |

## F_JourneyBeat  (for DT_JourneyBeats, 3 rows)

| Field | Type | Example |
|---|---|---|
| RowName | String | the_street |
| Beat | String | the_street |
| ViolationClass | String | Tone and voice |
| WordBudget | Integer | 30 |
| ToneTarget | String | bittersweet |
| Narration | String | You stand at the mouth of the cul-de-sac. The  |
| WordCount | Integer | 23 |
| ScoreBefore | Float | 1.0 |
| ScoreAfter | Float | 8.0 |
| Repairs | Integer | 3 |
| Outcome | String | stopped at the repair limit |

