# Project Overview
- **Game Title:** Rex Machina
- **High-Level Concept:** A shelter dog journeys home to the family that gave it away, facing off in a climactic pursuit-evasion showdown against the high-tech robot dog that replaced it. The robot dog (Rex) doesn't just chase—it predicts player movement patterns, cuts off escape routes, and vocalizes tactical reads of player habits.
- **Players:** Single-player (Player Dog vs. AI Nemesis Boss).
- **Inspiration / Reference Games:** Turn-based tactical grid games (Invisigun, Crypt of the NecroDancer, Into the Breach) and pursuit-evasion AI prototypes.
- **Tone / Art Direction:** Melancholic yet tense narrative with minimalist 2D pixel/grid arena aesthetics.
- **Target Platform:** StandaloneWindows64 (PC).
- **Screen Orientation / Resolution:** Landscape 1920x1080 (Orthographic 2D camera).
- **Render Pipeline:** Universal Render Pipeline (URP 2D).

---

# Game Mechanics
## Core Gameplay Loop
The boss encounter is a turn-based tactical pursuit-evasion duel on a discrete 10x10 grid across 15 rounds (capped to prevent dead zones):
1. **Player Move:** The player commits a movement step (`"left"`, `"right"`, `"up"`, `"down"`) or holds position (`"wait"`).
2. **Boss Perception & Prediction:** Rex computes movement metrics over a sliding window (`CFG.window = 4`) and frequency history (`FREQ = 20`), predicting the player's next destination tile (`predict`).
3. **Nemesis Intercept Move:** Rex selects an adjacent tile that minimizes distance to the predicted tile (`stepToward`), constrained by arena bounds and non-overlapping solidity.
4. **Leash Veto (GDD Exploit #2):** If the intercept move would increase Manhattan distance to the dog compared to Rex's current position, Rex substitutes a direct chase step towards the dog.
5. **Battery / Charge Dynamics:** Moving costs charge (`-pursuit = -8`), holding costs minimal charge (`-hold = -1`), and solar panels provide passive recharge (`+solar = +2`), clamped between 0 and 100. Charge levels dictate Rex's cognitive/dialogue band: `clinical` (>60%), `confident` (30–60%), or `strained` (<30%).
6. **Nemesis Read Dialogue (`speakRead`):** Rex evaluates tactical trigger conditions (`firingCategories`). If valid reads exist, Rex selects the highest priority available read row from `NemesisReadTable`, filtering out repeated categories from the previous round (suppression) and already-spoken lines.
7. **Rule RM-001 Enforcement:** Any candidate read line naming a compass direction (e.g., `"left"`) is held back unless that direction matches the player's dominant movement direction (`dominantDir`). If held back, Rex falls through to the next live trigger condition rather than staying silent or reciting false data.
8. **Stamina & Adjacency Drain (RM-002):** Player stamina drains by 1 unconditionally each round, plus an extra 1 point if Rex ends the round adjacent to the dog (Manhattan distance <= 1).

## Controls and Input Methods
Turn input takes discrete cardinal moves (`"left"`, `"right"`, `"up"`, `"down"`, `"wait"`). The boss turn logic operates deterministically upon receipt of each committed move signal. (UI menus and HUD updates are excluded per scope; turn resolution logs directly to the console and updates scene actor transforms).

---

# UI
*(Per project scope: Boss turn logic only, no UI, no new art.)*
- No UI canvas, HUD, or interactive widgets will be created.
- Verification and turn observations are logged to the Unity Console and visualized via existing scene transforms in `BossArena.unity` (`Dog (player)`, `Rex (boss agent)`, `Rex_PredictedTile`).

---

# Key Asset & Context
### Existing Assets & Files
- `Assets/RexMachina/Reference/game.js.txt`: Authoritative JavaScript implementation (`predict`, `stepToward`, `rexAct`, `dirFreq`, `periodicity`, `dominantDir`, `namesDirection`, `firingCategories`, `speakRead`).
- `Assets/RexMachina/gdd_rex_machina.md`: Game Design Document detailing the Nemesis architecture, 15-round cap, charge bands, and the 6 exploit fixes (including GDD 6.1 Leash veto and RM-001).
- `Assets/RexMachina/Data/NemesisReads.asset`: `NemesisReadTable` ScriptableObject holding the 24 authored boss read lines across 8 categories and 3 charge bands (`clinical`, `confident`, `strained`).
- `Assets/RexMachina/Scripts/NemesisReadTable.cs`: Data contract for `NemesisRead` and `NemesisReadTable` with `Pick(category, band)`.
- `Assets/RexMachina/Scenes/BossArena.unity`: Scene containing `Arena_Yard_10x10` (grid with `Exit_0_4`, `Exit_9_7`, `Cover_3_5`, `Cover_6_2`), `Actors/Dog (player)` at (4,6), `Actors/Rex (boss agent)` at (4,3), `Actors/Kid` at (6,7), and `Actors/Rex_PredictedTile` at (5,6).

### New Code Assets to Create
1. `Assets/RexMachina/Scripts/NemesisTurnLogic.cs`:
   - Pure C# static logic class containing exact ports of `predict`, `stepToward`, `rexAct`, `dirFreq`, `periodicity`, `dominantDir`, `namesDirection`, `firingCategories`, and `speakRead`.
   - Data structures: `NemesisConfig`, `NemesisTurnState`, `NemesisArenaData`, `NemesisTurnResult`.
   - Enforces Rule RM-001, GDD Exploit #2 (Leash Veto), and category suppression.
2. `Assets/RexMachina/Scripts/RexBossAgent.cs`:
   - Scene `MonoBehaviour` attached to `Actors/Rex (boss agent)`.
   - References `Dog (player)`, `Rex_PredictedTile`, and `NemesisReadTable`.
   - Executes turn steps, updates grid transforms, and logs the read lines and state.
3. `Assets/RexMachina/Scripts/Editor/RexBossTurnVerification.cs`:
   - Editor tool accessible via `Rex Machina/Verify Boss Turn Logic` menu item.
   - Comprehensive test harness validating each mathematical and logical component against the JS source of truth.

---

# Implementation Steps

### Step 1: Implement Pure Core Algorithms (`NemesisTurnLogic.cs`)
- **Description**: Port math, perception, and prediction algorithms from `game.js.txt` into pure static C# methods with no engine dependencies:
  - Manhattan distance: `Manhattan(Vector2Int a, Vector2Int b)`
  - Coordinate steps: `left` (-1,0), `right` (1,0), `up` (0,1), `down` (0,-1), `wait` (0,0).
  - Direction Frequency (`dirFreq`): Last 20 directional moves normalized frequencies.
  - Periodicity (`periodicity`): Lags 2..5 pattern match ratio over last 20 moves.
  - Dominant Direction (`dominantDir`): Highest frequency direction with strict JS tie-break order (`left`, `right`, `up`, `down`).
  - Prediction (`predict`): Direction mode across last 4 directional moves added to dog position.
  - Path Intercept (`stepToward`): Neighbor minimization of Manhattan distance, bound checking, dog tile obstruction.
  - Leash Veto & Charge (`rexAct`): Exploit #2 distance rejection, battery drain (`-pursuit + solar` or `-hold + solar`), clamped `[0, 100]`.
  - Charge Bands: `clinical` (>60), `confident` (30..60), `strained` (<30).
- **Assigned role**: developer
- **Dependencies**: None
- **Parallelizable**: No

### Step 2: Implement Dialogue Triggers and Rule RM-001 (`NemesisTurnLogic.cs`)
- **Description**: Port category evaluation and dialogue selection logic:
  - `firingCategories`: Priority order evaluation:
    1. `periodicity_called` (periodicity >= 0.6)
    2. `sealing_direction` (max dir freq >= 0.45)
    3. `stall_detected` (>= 2 wait moves in last 4)
    4. `cover_habit` (dog currently on a cover tile)
    5. `exit_fixation` (dog within Manhattan distance <= 2 of an exit tile)
    6. `charge_strain` (charge < 30)
    7. `gait_read` (dog limping == true)
  - `namesDirection`: Regex `\b(left|right|up|down)\b` (case-insensitive) extracting directional mentions from line text.
  - `speakRead` with **Rule RM-001**:
    - Suppress same category as last round (`cat == lastCat`).
    - Skip already spoken lines (`spokenLines.Contains(line)`).
    - **RM-001 Check**: If line names any compass direction, verify that `dominantDir` is one of those directions. If not, hold the line back and fall through to the next candidate category in `firingCategories`.
    - Record chosen line in `spokenLines` and update `lastCat`.
  - Stamina Drain: Unconditional -1 + adjacency drain (-1 if Manhattan dist <= 1), clamped >= 0 (RM-002).
- **Assigned role**: developer
- **Dependencies**: Step 1
- **Parallelizable**: No

### Step 3: Implement Scene Component (`RexBossAgent.cs`)
- **Description**: Create the MonoBehaviour bridging `NemesisTurnLogic` to scene actors:
  - Serialized fields: `dogTransform`, `predictedTileTransform`, `readTable` (`NemesisReadTable`), `gridSpan` (10x10), `coverTiles` [(3,5), (6,2)], `exitTiles` [(0,4), (9,7)].
  - Runtime state tracking: Rex position, dog position, charge (starts at 100), move history, spoken lines, stamina (starts at 17), limping flag.
  - `ExecuteTurn(string playerMove)`:
    - Commits player move to history.
    - Runs `NemesisTurnLogic.ExecuteTurn(...)`.
    - Updates Rex transform position and `Rex_PredictedTile` transform position in the scene.
    - Emits structured debug logs formatted as: `REX: "<Line>" [Category: X, Band: Y, Charge: Z%]`.
- **Assigned role**: developer
- **Dependencies**: Step 1, Step 2
- **Parallelizable**: No

### Step 4: Wire Component into `BossArena.unity`
- **Description**: Add `RexBossAgent` component to `Actors/Rex (boss agent)` in `BossArena.unity`. Assign references to `Dog (player)`, `Rex_PredictedTile`, and `Assets/RexMachina/Data/NemesisReads.asset`. Populate Yard phase cover and exit coordinates.
- **Assigned role**: developer
- **Dependencies**: Step 3
- **Parallelizable**: No

### Step 5: Implement Comprehensive Verification Harness (`RexBossTurnVerification.cs`)
- **Description**: Create an editor script under `Assets/RexMachina/Scripts/Editor/` providing automated verification:
  - Run via Editor menu: `Rex Machina/Verify Boss Turn Logic`.
  - Verifies:
    1. Metric calculations (`dirFreq`, `periodicity`, `dominantDir`).
    2. Prediction & Intercept step with Leash Veto substitution.
    3. Charge drain and band classification (`clinical` -> `confident` -> `strained`).
    4. **Rule RM-001 Rule Validation**:
       - Setup sequence where player moves Right repeatedly -> `sealing_direction` fires, candidate line names "left" -> Held back, falls through to next category or silence.
       - Setup sequence where player moves Left repeatedly -> candidate line names "left" -> Line accepted and spoken.
    5. Category suppression (no category spoken twice consecutively).
    6. Full round step in active scene, verifying transform updates.
- **Assigned role**: developer
- **Dependencies**: Step 1, Step 2, Step 3, Step 4
- **Parallelizable**: No

---

# Verification & Testing

### Automated Editor Tests (Menu: `Rex Machina/Verify Boss Turn Logic`)
1. **Rule RM-001 Verification**:
   - *Test A (Rightward bias)*: Provide 10 `"right"` moves. Verify `dominantDir == "right"`. Trigger `sealing_direction`. Candidate line `"Target favored left nine of twenty recorded moves."` names `"left"`. Verify line is held back and not spoken.
   - *Test B (Leftward bias)*: Provide 10 `"left"` moves. Verify `dominantDir == "left"`. Candidate line names `"left"`. Verify line is approved and spoken.
2. **Exploit #2 Leash Veto Verification**:
   - Place Dog at (4,6), Rex at (4,3). Force predicted tile to (4,1) (behind Rex).
   - Moving toward (4,1) would increase distance to Dog from 3 to 4.
   - Verify Leash Veto fires: Rex moves toward Dog (4,4) instead of (4,2).
3. **Periodicity Verification**:
   - Feed repeating 2-step cycle: `["up", "right", "up", "right", "up", "right"]`.
   - Verify lag 2 computes `hits/n = 1.0` -> `periodicity_called` added to firing categories.
4. **Suppression & Fall-Through Verification**:
   - Turn N speaks category `sealing_direction`.
   - Turn N+1 triggers both `sealing_direction` and `stall_detected`.
   - Verify `sealing_direction` is suppressed and Rex speaks `stall_detected`.
5. **Charge & Band Transitions**:
   - Start at 100. Simulate 7 moves (7 * -6 = -42 -> charge 58). Verify band transitions from `clinical` to `confident`.
   - Simulate 5 more moves (charge 28). Verify band transitions to `strained`.
6. **In-Scene Execution Check**:
   - Run turn step on `RexBossAgent` in `BossArena.unity`.
   - Verify `Actors/Rex (boss agent)` and `Actors/Rex_PredictedTile` world coordinates update to match grid coordinates.
