# Getting the Unreal build playable

Worked backwards from a single acceptance test. UE 5.5, Blueprint only.
The browser build at sritej.itch.io/rex-machina stays the submitted playable
link; this is the downloadable showcase.

## 1. The acceptance test

Everything below exists to make this sentence true:

> A person downloads a zip, runs `RexMachina.exe`, and sees a 10x10 yard with a
> dog, a robot dog and a kid. They press a direction. That advances one round.
> The robot moves to the tile it predicted they were about to step on -- and
> when that prediction would take it further away, it cuts inside instead. It
> says a line naming something it measured off their movement. Fifteen rounds or
> fifteen stamina later they reach the kid or they don't, and are told which.

If a task does not serve that sentence, it is Tier 2 or it is cut.

## 2. Backwards from the test

Read right to left. Each arrow is "requires".

    outcome shown      <- CheckEnd <- Approach <- Manhattan
    round advances     <- OnPlayerMove <- InBounds, RexAct, SpeakRead, CheckEnd
    the veto           <- RexAct <- Predict, StepToward <- Manhattan, InBounds
    the robot speaks   <- SpeakRead <- FiringCategories <- DirFreq, Band
                                    <- DT_NemesisReads lookup
    a world to see     <- BP_Tile grid, BP_Dog, BP_Rex, BP_Kid <- TileToWorld
    state to read      <- WBP_FightHUD <- BP_FightManager variables
    a way to act       <- BP_FightPlayerController <- input mappings

Two leaves are already done and verified: the **variables** (24, constants read
back off the compiled CDO) and the **data** (42 rows, 56/56 columns).
Everything else is open.

## 3. The unlock: generate graphs as text -- CONFIRMED WORKING

UE serialises selected Blueprint nodes to the clipboard as text and rebuilds
them on paste, wires included. This was tested end to end on `Manhattan`:
`tools/bp_gen.py` emitted 8 nodes and every internal wire, the paste
materialised the whole graph, and it compiled in 312 ms. `Manhattan` is now
built, wired, compiled and saved -- and it was generated, not hand-placed.

So the graphs are diffable and reproducible: the generator lives in the repo
next to the pipelines, and regenerating the fight is a command.

**What the experiment established, all verified in the editor:**

- Both directions work. Reading gives an exact template; writing rebuilds it.
- **Wires resolve only inside the pasted set.** `LinkedTo` pointing at a node
  that already exists in the graph is silently dropped. So a generated body
  cannot stitch itself onto the pre-existing entry node.
- **The function entry node cannot be deleted; the result node can.** So the
  result can be generated, but the entry's parameters must be connected by
  hand.
- Net cost per function: **two or three manual wires**, not thirty.
- Under large world coordinates a Blueprint float is a double and serialises as
  `PinType.PinCategory="real"` with `PinType.PinSubCategory="double"`. Emit
  `"float"` and the pin silently mismatches.
- `MemberParent` quoting is exact:
  `MemberParent="/Script/CoreUObject.Class'/Script/Engine.KismetMathLibrary'"`
- Every KismetMathLibrary member name resolved first try: `BreakVector2D`,
  `Subtract_DoubleDouble`, `Abs`, `Add_DoubleDouble`, `FTrunc`.

**One hazard.** Dropping a wire *near* a result pin rather than *on* it makes
UE silently add a new output parameter to the function signature. It compiles
clean and looks right. Check the Details panel after wiring a return, and undo
if an unexpected pin appears.

## 4. The verification problem, and the answer

A Blueprint graph cannot be read back and checked -- there is no K2Node API.
"It compiled" is the only structural signal, and a Blueprint compiles happily
with a wire on the wrong pin. Every other layer of this build was proved by
read-back, so this is the one place the safety net is missing.

The answer is to verify **behaviour instead of structure**. Build `BP_SelfTest`,
an actor that runs assertions on BeginPlay in a test map and prints PASS/FAIL.
Port these straight from `tests/sim.js`, which already defines them:

- `Manhattan((0,0),(7,4)) == 11`
- `Approach` is 0 at spawn and 1 at the kid, and never accumulates
- `Band(100) == clinical`, `Band(45) == confident`, `Band(10) == strained`
- `StepToward` never returns an out-of-bounds tile
- **the veto invariant**: after `RexAct`, distance to the dog is never greater
  than before it -- asserted every round, over a few hundred randomised runs
- every line spoken came from `DT_NemesisReads`

The last two are the same assertions `tests/sim.js` makes against the browser
build, so a passing self-test means both builds obey one rule set.

## 5. Simplifications the data allows

Checked against the CSVs, not assumed:

- **`GridSpan` is `10x10` in all three phases.** `InBounds` needs no string
  parsing at runtime -- use two integer constants. Saves a parsing routine and
  about 15 nodes. Keep the column; the pipeline still authors it.
- **`ExitTiles` and `CoverTiles` are 2-3 pairs per phase.** Parse once on
  BeginPlay into arrays of Vector2D, or hardcode for Tier 0. No JSON library.
- **Four of the seven firing categories are cheap.** `sealing_direction`
  (DirFreq), `stall_detected` (count "wait" in the last 4), `charge_strain`
  (one compare), `gait_read` (a bool). Those four already reach 12 of the 24
  generated lines. `periodicity_called` is the most expensive function in the
  spec and gates one category -- but it closes GDD exploit 5, so it is Tier 1,
  not cut.
- **`prior_attempt`** is an eighth category present in the data that
  `FiringCategories` never fires. It belongs to the retry screen, not the round
  loop.

## 6. Tiers

### Tier 0 -- grey box, One Wow, playable

The spec's own advice: *"A grey box with two capsules that cuts you off and
tells you why is worth more than a dressed arena that chases."*

- One arena. No phase changes.
- Grid of cube tiles, two material instances. Dog and Rex are capsules; the kid
  is a marker. Fixed angled camera.
- Functions: `Manhattan`, `InBounds`, `Approach`, `Band`, `DirFreq`,
  `StepToward`, `Predict`, `RexAct` (with the veto), `FiringCategories` (the
  four cheap categories), `SpeakRead` (including the direction guard),
  `CheckEnd`, `OnPlayerMove`, `TileToWorld`.
- `WBP_FightHUD`: round/15, stamina, charge, band, approach bar, the spoken
  line, and **a marker on the tile Rex moved to**. Without that marker the
  prediction is invisible and the One Wow does not land.
- Win and lose text. No audio, no props, no dressing.

### Tier 1 -- the full fight

- `Periodicity`, `cover_habit`, `exit_fixation` (needs the tile arrays).
- `CheckGate` and three-phase dressing: light colour and intensity, ambient bed,
  prop set, and the "The arena advances." announcement.
- `DT_RetryReads` on the loss screen, keyed on gate plus band.
- Limp state, and stamina exposed across 14-17.
- Audio: three ambient beds, servo whine, paw step, line stinger, win/lose.

### Tier 2 -- showcase

- Props per phase from the `Props` arrays.
- A pre-fight journey screen driven by `DT_JourneyHazards` that sets starting
  stamina -- three of the six hazards set the limp condition. This is how the
  fifth table earns its place in the build.
- `DT_JourneyBeats` as interstitial narration.
- Package for Windows and upload as a download beside the browser build.

## 7. Assets

Nothing here needs to be bought, and Tier 0 needs no external asset at all.

**Visual** -- all from `Engine/BasicShapes`:

| Thing | Built from |
|---|---|
| Tile | Cube, scaled to 2m x 2m x 0.1m, instanced 100x |
| Cover / exit tiles | same mesh, two material instances |
| Prediction marker | same mesh, thin, emissive |
| Dog | Capsule, warm material |
| Rex | Capsule, cold material, small emissive eye |
| Kid | Cylinder |
| Arena lighting | one DirectionalLight + SkyLight + one spot, three presets |

The three `Light` strings map onto those presets: low sun across grass; one
motion-timer lamp that keeps guessing wrong; sodium floods with hard shadows.

**Audio** -- seven cues, all findable CC0: three ambient beds (chain-link and a
screen door; a lamp on a timer; an idling engine and couplings taking up slack),
a servo whine on Rex's move, a paw step on the dog's, a stinger when a line
fires, and win/lose stings.

## 8. Narrative links

| Table | Rows | Where the player meets it | Tier |
|---|---|---|---|
| DT_NemesisReads | 24 | the line the robot says when a category fires | 0 |
| DT_ArenaPhases | 3 | light, sound and props swap; "The arena advances." | 1 |
| DT_RetryReads | 6 | the line on the retry screen after a loss | 1 |
| DT_JourneyHazards | 6 | pre-fight journey that sets starting stamina | 2 |
| DT_JourneyBeats | 3 | interstitial narration between phases | 2 |

**A gap worth deciding on.** `DT_ArenaPhases.CallbackBeat` holds `the_street`,
`limp_onset`, `train_leap`. `DT_JourneyBeats` holds `the_street`,
`boxcar_night`, `fed_by_stranger`. Only `the_street` joins. The phase-to-beat
callback therefore works for one arena in three. Either regenerate the A7 beats
against the three callback names, or drop the callback for the two with no beat
and say so in the GDD. Do not let it fail silently at runtime.

## 9. Packaging

Blueprint-only projects package against the engine's precompiled binaries -- no
Visual Studio, so the MSVC toolset that started all this stays irrelevant.
Platforms > Windows > Package Project, then ship the zip on itch as a download
beside the browser build.

## 10. Order of work

1. Prove the clipboard round-trip on `Manhattan`. Everything downstream depends
   on whether this works, so it is the first thing to learn.
2. `BP_SelfTest` with the Manhattan and Band assertions -- the harness exists
   before the code it checks.
3. Tier 0 functions, in dependency order, each landing with its assertion.
4. Grid, actors, camera, input.
5. `WBP_FightHUD`, including the prediction marker.
6. Play it. Fix what is not fun before adding anything.
7. Tier 1, then Tier 2 only if the clock allows.

## 11. Risks

- **The paste format may not round-trip.** Fallback is hand-wiring Tier 0 and
  cutting Tier 1. Learn this on day one, not on day three.
- **Graphs stay structurally unverifiable.** `BP_SelfTest` is the mitigation and
  it is not optional.
- **Three arenas are three times the dressing for no extra One Wow.** If
  anything slips, cut arenas before cutting the veto or the reads.
