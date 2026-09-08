# Act 3 in Blueprints: the logic, node by node

UE 5.5, Blueprint only. This is the fight from `game.js`, which is tested by
`tests/sim.js` and cleared by `qa/adversary.js`, written out so it can be built
without guessing. Where a number appears here it is the number the tests pass
against. Do not round them.

## Constants

Put these on `BP_FightManager` as public variables.

| Name | Type | Value | Source |
|---|---|---|---|
| MaxRounds | Integer | 15 | GDD §3 |
| StartCharge | Float | 100.0 | GDD §3 |
| PursuitCost | Float | 8.0 | A5, raised from the agent's 4.0 after playtesting |
| HoldCost | Float | 1.0 | A5 |
| SolarRecovery | Float | 2.0 | A5 |
| BandClinical | Float | 60.0 | GDD §3 register thresholds |
| BandConfident | Float | 30.0 | GDD §3 |
| MoveWindow | Integer | 4 | GDD §3, the machine forgets |
| FreqSpan | Integer | 20 | GDD §3, direction frequency |
| KidTile | Vector2D | (7, 4) | 11 tiles from spawn, fits a 15 round clock |
| DogSpawn | Vector2D | (0, 0) | |
| RexSpawn | Vector2D | (5, 5) | centre of a 10x10 |
| TileSize | Float | 200.0 | cm, your choice |

State: `DogTile`, `RexTile` (Vector2D), `Stamina` (Integer), `Round` (Integer),
`Charge` (Float), `Moves` (Array of String), `SpokenLines` (Array of String),
`LastCategory` (String), `PhaseIndex` (Integer), `Limping` (Boolean).

Starting stamina is `17 - min(JourneyFails, 3)`. With no journey in the Unreal
build, use 15 and expose it so you can test the range.

## Helper functions

**TileToWorld(Tile) -> Vector**
`(Tile.X * TileSize, Tile.Y * TileSize, 0)` plus the grid origin.

**Manhattan(A, B) -> Integer**
`abs(A.X - B.X) + abs(A.Y - B.Y)`.

**InBounds(Tile) -> Boolean**
Split `GridSpan` from the current phase row on "x" to get width and height.
True when `0 <= X < width` and `0 <= Y < height`.

**Approach() -> Float**
`1 - Manhattan(DogTile, KidTile) / 11`, clamped 0 to 1. Positional, never
accumulated. GDD §3 exploit 4 was the ratchet, and this formula is the fix.

**Band() -> String**
`Charge > 60` gives "clinical". `Charge >= 30` gives "confident". Otherwise
"strained".

**DirFreq() -> Map<String, Float>**
Take the last 20 entries of `Moves`, drop any "wait", count each of left,
right, up, down, divide each by the number kept. Empty gives all zeros.

**Periodicity() -> Float**
Take the last 20 entries of `Moves`. For each lag from 2 to 5, compare each
entry to the one `lag` earlier and count matches over comparisons. Return the
highest ratio. Fewer than 4 entries returns 0. This plus DirFreq is what closes
GDD §3 exploit 5, where a five-beat cycle hides inside a four-move window.

## The round

**OnPlayerMove(Direction)**

1. If Direction is not "wait", compute the target tile. If `InBounds` is false,
   print "The fence is there. Nothing on that side." and **return without
   consuming the round**. That message is not decoration: `qa/adversary.js`
   finding RM-003 was that a rejected move gave the player no feedback at all.
2. Set `DogTile` to the target. Append Direction to `Moves`. Increment `Round`.
3. Call `RexAct`.
4. Call `SpeakRead`.
5. `Stamina = max(0, Stamina - 1 - (Manhattan(RexTile, DogTile) <= 1 ? 1 : 0))`.
   The clamp is finding RM-002. Without it stamina reached -1 and the HUD
   showed it.
6. Call `CheckGate`, then `CheckEnd`.

**RexAct**

1. `Predicted = Predict()`.
2. `Before = Manhattan(RexTile, DogTile)`.
3. `Move = StepToward(RexTile, Predicted)`.
4. **If `Manhattan(Move, DogTile) > Before`, discard it and use
   `StepToward(RexTile, DogTile)`.** This is the engine-side veto from GDD
   §6.1, and it is the single most important node in the graph. Without it the
   player can lead the robot away and the fight becomes free. `tests/sim.js`
   asserts it every round of every run.
5. `Moved = Move != RexTile`. Set `RexTile = Move`.
6. `Charge = clamp(Charge - (Moved ? PursuitCost : HoldCost) + SolarRecovery, 0, 100)`.

**Predict() -> Vector2D**
Take the last 4 entries of `Moves`, drop "wait". Empty returns `DogTile`. Else
take the most frequent direction and return `DogTile` stepped once that way.

**StepToward(From, Target) -> Vector2D**
Best is `From`, best distance is `Manhattan(From, Target)`. For each of the
four directions, if the candidate is `InBounds` and strictly closer, take it.
Return best.

## Speaking

**FiringCategories() -> Array of String**, in this order, appending each that
is true:

1. `Periodicity() >= 0.6` gives "periodicity_called"
2. highest DirFreq value `>= 0.45` gives "sealing_direction"
3. two or more "wait" in the last 4 moves gives "stall_detected"
4. DogTile is in the phase's CoverTiles gives "cover_habit"
5. DogTile within 2 of any ExitTile gives "exit_fixation"
6. `Charge < 30` gives "charge_strain"
7. `Limping` gives "gait_read"

Return **all** that fire, not the first. Returning only the first is what made
a winning run surface 2 of the 24 generated lines instead of 7.

**SpeakRead**

For each category in `FiringCategories()`:

- Skip if it equals `LastCategory`. That is the GDD §4 suppression rule.
- Find the `DT_NemesisReads` row where `ReadCategory` matches and `ChargeBand`
  equals `Band()`. Skip if there is none.
- Skip if `SpokenLines` already contains that line.
- **Skip if the line names a compass direction that is not the dog's dominant
  direction.** Search the line for the whole words left, right, up, down. If it
  names any and the dominant direction is not among them, skip. This is finding
  RM-001. All three `sealing_direction` lines say "left" while the trigger
  fires for any dominant direction, so without this check the robot tells a
  right-running dog it favoured left.
- Otherwise set `LastCategory`, append the line to `SpokenLines`, show it, and
  stop.

If nothing survives, say nothing. Silence beats a lie.

## Phases and ending

**CheckGate**
Find the `DT_ArenaPhases` row where `Approach()` is at or above `ApproachLow`
and below `ApproachHigh`. Phase 3 is open-ended at the top. If
it differs from `PhaseIndex`, set it, then re-dress the arena: swap the
directional light and colour temperature per the row's `Light` string, swap the
ambient cue per `SoundBed`, and swap the prop set per `Props`. Announce
"The arena advances. " plus `ArenaName`.

**CheckEnd**
`Approach() >= 1` is a win, checked **before** stamina, so arriving on your last
legs counts. Otherwise `Stamina <= 0` or `Round >= MaxRounds` is a loss. On a
loss, record the current `PhaseID` with the "phase_" prefix stripped, and on the
retry open with the `DT_RetryReads` row matching that gate and the current band.

## What to build first

The veto in `RexAct`, then `SpeakRead`. Those two are the One Wow. A grey box
with two capsules that cuts you off and tells you why is worth more than a
dressed arena that chases.
