# MY CAPSTONE — Source of Truth

**Working title:** *REX MACHINA*
**Logline:** A shelter dog journeys home to the family that gave it away — and must outwit
the robot dog they replaced it with.
**Engine / stack:** **Unreal Engine 5** (C++ / Blueprints) + Claude API (Haiku 4.5).
Later: CrewAI, RAG, GOAP/Utility. Class prototypes use Phaser; the capstone is **UE5**.

> Source of truth. Every assignment pulls its game, loop, agents, and constraints from here.
> **Current design = v3 (post-stress-test).** Do not revert to earlier versions.

---

## 0. DESIGN HISTORY (so we don't loop)
- **v1 (original idea):** two parallel modes — play a dog *or* a robot dog. Cut.
- **v2 (pivot):** ONE game. You are the dog; the robot dog is the climactic boss driven by a
  real reasoning agent (the Nemesis). **This is what shipped as A1 and scored 10/10.**
- **v3 (current — A2 final):** same game, corrected spec. Driven by (a) instructor feedback
  that the Chronicler was under-specified, and (b) a three-persona agent stress test that
  found six executable exploits, two of which made the fight unloseable.

### Instructor feedback on A1 (10/10)
- **Strength to protect:** the *PLAYER SEES* discipline — every agent behavior anchored to a
  concrete sensory moment. Keep doing this in every future deliverable.
- **Improve:** push the Chronicler to Nemesis-level specificity — show concrete example
  narration lines alongside the conditions that trigger them. → **Done in v3.**
- **Scope:** build the last level first, leave the starting area for later. → **Confirmed as
  the plan of record.**
- **Engine:** if never used Unreal, look at other indie options before committing. → Open;
  see §9.

---

## 1. THE ONE WOW — "The Nemesis"
Lead with the behavior, never the word "reasoning" (it must land in ~4 sec): every other
game's enemy chases you; the robot dog in the final fight **cuts you off**. It runs to where
you're *about to go* — not where you are — reports the **read** it took off your movement
(*"target favored left breaks four times in twenty"*), and shuts down the escape you keep
reusing until you learn to stop being predictable.

*Three on-screen tells a scripted chaser could never do:* (1) it moves to an *empty* tile
ahead of you; (2) a one-line read appears as it does; (3) it stops falling for your repeated
trick — and falls for it again later once memory decay makes it "forget."

**Test every feature against:** *"This agent [does X] when [trigger], and the player sees [Y]."*

---

## 2. STRUCTURE
- **Acts 1–2 — The Journey (authored spine, minimal AI):** shelter escape → alley chase →
  freight-train leap → the coast seen through the open boxcar door → the family's street.
  These run on **the same tile-step-and-telegraph grammar as the boss fight**, against a
  pursuer that telegraphs but never adapts. Act 1 is therefore the tutorial for Act 3.
- **Act 3 — The Confrontation:** a pursuit-evasion boss fight in a compact UE5 arena on
  NavMesh, with a coarse tactical grid overlaid for the agent. **15 rounds, 3 phases.**

---

## 3. BOSS MECHANICS (v3 — post-exploit-fix)
Each round: you move → the Nemesis perceives your position + movement statistics, predicts
your next tile, moves to intercept, and reports what it learned.

**Phases:** at 33% / 66% approach the arena advances (yard → fence gap → train yard) and
re-lays exits and cover. **Checkpoints at the gates** — retry keeps the meter *and* the move
history, so the first read after a loss references the failed run ("you tried the fence").

**Your skill = pattern-breaking,** via two levers:
- **The machine forgets** (4-move sliding window) — a specific juke works again once decayed.
  Its *statistics* do not decay, so cycling doesn't work.
- **The machine tires** (solar/battery) — sprinting drains charge and forces a pause. Read
  register shifts with charge: clinical >60%, confident 30–60%, strained <30%.

**Stamina:** drains 1/round unconditionally (the kid's window is closing), plus 1 for every
round ending with the robot adjacent.
**Approach meter:** positional, not accumulated — `approach = 1 − dist(dog,kid)/dist_max`.
**Win:** fill approach before stamina empties → the kid switches the robot off, recognizes you.
**Loss:** stamina empty → retry from last phase gate.
**Ending:** the eye flicker plays **before** the reunion image, and **only the dog sees it**.
The last shot in the game is the dog. *(Changed in v3 — see §10.)*

### The six exploits that were fixed (do not reintroduce)
1. **Read-line oracle** — the read announced the plan before the player's input. Now
   past-tense diagnosis only, never intent; input for round N+1 resolves simultaneously
   with round N's read.
2. **The leash** — targeting the *predicted* tile let the player walk the robot into a corner.
   Unreal now rejects any `intercept_move` that increases true distance to the dog's current
   tile, substituting a chase step.
3. **No fail state** — equal speed + guaranteed escape routes made capture impossible. Fixed
   by the unconditional stamina clock, adjacency drain, and a 2-tile sprint at
   `aggression > 0.6` paid from battery.
4. **Approach ratchet** — step-in/step-out banked free progress. Fixed by the positional
   formula above.
5. **Window aliasing** — a 5-beat cycle never repeats inside a 4-move window. Fixed with two
   engine-computed scalars: direction frequency over 20 moves, and a periodicity score.
6. **Mid-fight dead zone (rounds 8–20)** — fixed by the 15-round cap and the 3-phase gates.

---

## 4. THE DEV CREW (3 agents)

### Agent 1 — NEMESIS  *(THE One Wow · adversarial · goal-oriented)*
- **Does:** drives the boss — predicts the dog's next tile, chooses an intercept, reports the
  read. **Also speaks the boss taunts** (moved here from Chronicler: one agent, one voice).
- **Player sees:** the robot cut off where it thinks they'll go, with a read that gets terser
  and more strained as its battery drains.
- **Fires:** once per round, 15 rounds.
- **Never receives the journey.** Input is only what a lawn robot could observe.
- **In:**
  ```json
  { "dog_tile":[4,6], "dog_recent_moves":["left","left","up","left"],
    "dir_freq_20":{"left":0.45,"right":0.15,"up":0.25,"down":0.15},
    "periodicity":0.72, "dog_observable":{"gait":"limping","collar":true},
    "phase":2, "exits":[[0,6],[9,2]], "cover_tiles":[[3,5],[5,7]],
    "self_charge_pct":48, "approach_meter":0.6, "prior_attempt":"fence_gap" }
  ```
- **Out:**
  ```json
  { "predicted_tile":[3,6], "intercept_move":[3,5],
    "read":"Target favored left breaks four times in twenty.",
    "read_category":"sealing_left", "aggression":0.7 }
  ```
- **UI rule:** suppress any line whose `read_category` matches the last shown → ~15 lines
  become 8–10 surfaced ones, so the drumbeat escalates instead of becoming wallpaper.

### Agent 2 — CHRONICLER  *(narrative spine — rewritten in v3)*
- **Does:** writes the journey's travel narration, and *only* that. Fires at **8 fixed beat
  markers** (trigger volumes / Sequencer events), never per frame.
- **Player sees:** two or three lines at the moments the journey turns, each referring to
  something that actually happened to them.

| Beat ID | Fires when | Words | Example line |
|---|---|---|---|
| `first_street` | player crosses the shelter threshold onto open pavement | 40 | "No leash. No hand on the collar. Just pavement going further than the yard ever did, and the whole grey smell of it saying: pick a direction." |
| `alley_escape` | GAUNTLET returns `outcome:"escaped"` | 25 | "Something gave up behind you two corners ago. You keep running anyway, because stopping is a thing you do at home." |
| `train_leap` | player capsule lands in the boxcar volume | 20 | "The boxcar door yawns open. Behind you, paws on gravel. You jump." |
| `boxcar_night` | first dusk lighting transition in the moving car | 30 | "Two nights of this now. The floor hums north. You sleep in the shape you slept in at the foot of a bed, and it doesn't fit anymore." |
| `coast_from_car` | open door frames the ocean at speed | 25 | "Water on the left for an hour. You have never seen this much of anything. It does not smell like her." |
| `fed_by_stranger` | player interacts with the diner back door | 25 | "A hand you don't know puts down a paper tray. You eat first and decide about the hand after. That's new." |
| `limp_onset` | `condition` flips to "limping" after the third hazard | 20 | "The back leg has opinions now. You tell it the same thing you told the gate: not yet." |
| `the_street` | player enters the cul-de-sac; the house comes into view | 30 | "Nine days. The porch light is the same. So is the shape moving behind the window — and it is not the shape of you." |

- **In:**
  ```json
  { "beat":"the_street", "act":2, "word_budget":30,
    "tone_target":"bittersweet", "days_traveled":9,
    "journey_memory":[ {"fact":"left_behind","day":0},
                       {"fact":"escaped_alley","day":1},
                       {"fact":"rode_train_2_nights","day":4},
                       {"fact":"fed_by_stranger","day":6} ],
    "condition":{ "state":"limping","since_day":7,"expires_day":null },
    "bible_entries":[ "dog: no name is ever given; the kid called her 'girl'",
                      "family: mother, and Theo, 9",
                      "robot: REX-line, solar, warranty sticker on the flank",
                      "banned words: destiny, journey, heart, soul, forever" ] }
  ```
- **Out:**
  ```json
  { "beat":"the_street",
    "narration":"Nine days. The porch light is the same. So is the shape moving behind the window — and it is not the shape of you.",
    "tone":"bittersweet", "callback":"days_traveled", "word_count":26 }
  ```
- **Grounding (the RAG surface, = Assignment #4):** a **Story Bible** of ~30 short entries
  embedded at build time; each call retrieves the 3–5 relevant to its beat. The **journey
  ledger** carries what already happened, with day stamps, so a beat can only reference
  established facts *and* can be checked for contradicting them.
- **Validation (Generator → Evaluator → Refiner):**
  ```
  R1  word_count <= word_budget
  R2  the dog never speaks in human first-person dialogue
  R3  no fact absent from bible_entries + journey_memory
  R4  no fact that CONTRADICTS journey_memory          // added in v3
  R5  prose scored against 3 authored exemplars for the target tone;
      structural bans: no abstract noun in final position, no "not X, but Y",
      no line that is only a sentence fragment
  ```
  Fail → one refine pass → second fail → hand-authored DataTable fallback. The player never
  sees broken text, **and the game ships even if the API is down.**
- **HARD RULE — three beats are never generated:** `shelter_adoption`, `nemesis_reveal`,
  `switch_off`. They are the three images the game exists to deliver; generating them makes
  the ending a dice roll and means no two players see the same film. Hand-authored,
  permanently. The generated beats exist to make the authored ones feel earned.

### Agent 3 — GAUNTLET  *(journey hazards — now also the tutorial)*
- **Does:** drives Act 1–2 chase/obstacle beats using the boss fight's own tile-step-and-
  telegraph rules, with a pursuer that telegraphs but never adapts.
- **Player sees:** the chase closing, the near-misses, the jump barely made — and learns the
  exact grammar the Nemesis will use against them in Act 3, without being told.
- **Out:** `{ "hazard":"alley_chase", "pursuer_tile":[2,2], "telegraph":"lunging right", "window_turns":3, "outcome":"escaped" }`

---

## 5. AI DEV PIPELINE & ENGINE INTEGRATION (UE5)
```
UE5 game state ──(HTTP, async, off the game thread)──> Claude agents ──JSON──> UE5

Journey beat → CHRONICLER → generate → evaluate (5 rules) → refine? → DataTable fallback
                                                          → {narration,tone} → UMG
Chase beat   → GAUNTLET   → {telegraph,window,outcome}    → drives the pursuer pawn
Boss round   → NEMESIS    → {predicted_tile,intercept_move} → engine distance check
                                                          → Behavior Tree → NavMesh MoveTo
  → loop 15 rounds, phase-gated at 33% / 66% approach
```
**Division of labour:** Claude = the **BRAIN** (high-level intent). Unreal's NavMesh +
Behavior Tree + EQS = the **BODY**. The LLM never touches geometry or animation.
**Every agent output passes an engine-side validity check before it can affect play.**

---

## 6. CONSTRAINTS (each explained)
1. **Adversarial balance / winnability** — capped prediction accuracy, ≥2 escape routes per
   phase, a decay cycle, and the engine-side rule that the robot may never move further from
   the dog than it already is.
2. **Memory decay as a feature — and its loophole** — the 4-move window keeps prompts small
   and lets old jukes work again, but alone it let any 5-beat cycle hide forever. Closed by
   the two engine-computed scalars.
3. **Latency is a design element; jitter is a bug** — a fixed **600 ms "tell" animation**
   (head scan, ear twitch) fires the instant the player commits; an early response is held,
   a late one loops the scan. Constant beat, plus headroom for a slow call.
4. **Rate limit (~60 req/min)** — one Nemesis call per round in a turn-based fight is well
   inside the limit; Chronicler calls fire at scene transitions, never during play.
5. **Graceful degradation** — authored fallback per Chronicler beat, chase-step default per
   Nemesis output. A dropped request costs flavor, never a frame.
6. **UE5 is heavy (honest scope cost)** — controlled by staying greybox and leaning on
   Unreal's built-in AI framework; Claude supplies only strategy on top.

---

## 7. TOKEN BUDGET & PROJECTION (v3)
**Assumptions:** Claude **Haiku 4.5**, **$1/M input, $5/M output** (Anthropic, Jul 2026).
A playthrough ≈ 8 generated journey beats + one 15-round boss fight.

| Agent | calls | input | output |
|---|---|---|---|
| NEMESIS (15 boss rounds) | 15 | ~10,500 | ~900 |
| CHRONICLER (8 beats: gen + eval + ~2 refines) | 18 | ~13,000 | ~690 |
| GAUNTLET (journey chases) | 10 | ~2,500 | ~400 |
| **Total** | **43** | **~26,000** | **~1,990** |

- **Cost/playthrough:** ≈ **$0.036**. 1,000/mo ≈ **$36**; 10,000 ≈ **$360**.
- *v2 was $0.05 / $52 / $520.* The corrected design is ~30% **cheaper** because both major
  fixes were subtractive: the fight halved (30→15 rounds) and three beats became authored.

---

## 8. SCOPE / BUILD PLAN (solo, ~4 weeks) — instructor-endorsed
Build the last level first; leave the starting area for later.
- **Slice 1 (weeks 1–2, the Wow):** greybox arena + NavMesh + pursuing robot pawn +
  **Nemesis** over HTTP, with the engine-side distance check and the 600 ms tell.
  *Success condition: the fight is fun before anything else exists.*
- **Slice 2 (week 3, voice):** **Chronicler** with bible, ledger, evaluator + the three
  hand-authored climax beats + the switch-off.
- **Slice 3 (week 4, scope valve):** authored journey levels + **Gauntlet** chases. This is
  the slice that shrinks if time runs out — which is exactly why it is last.

**Course mapping:** 3 agents = CrewAI crew (A3) · Story Bible + retrieval + consistency rules
= RAG content pipeline (A4) · Nemesis (perception, competing goals of intercept vs charge
conservation, memory decay) = the goal-oriented agent (A5).

---

## 9. OPEN DECISIONS
- **Engine.** Instructor: look at other indie options *if you've never used Unreal*. UE5 is
  the plan of record. Decide by the end of Slice 1: if the greybox arena + NavMesh + pursuing
  pawn is not standing up inside week 1, that is the signal to move — and the design is
  engine-portable because all the AI lives behind an HTTP/JSON boundary.
- **Boss win condition** — positional approach meter confirmed on paper; verify in playtest.
- **Round count** — 15 is the stress-tested target; tune against a player arriving 40 minutes
  into the game, not a fresh tester.

---

## 10. THE ENDING (changed in v3)
The Narrative reviewer's argument, accepted: the story's thesis is that the replacement could
not love and the kid chooses the dog. Ending on the robot's eye moves the final beat onto the
machine, reframes the kid's choice as a mistake, and asserts a *will* the fight never
established — bittersweet turns into franchise horror in two seconds. **Keep the shot, move
it:** the flicker plays *before* the final reunion image, and only the dog sees it. The game
ends on the dog.
