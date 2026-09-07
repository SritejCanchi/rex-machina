# Retrieval traces

One section per content type: the query that was issued, the chunks the
vector index returned with their cosine scores, and a row that came out
the other end. Regenerate with `python pipeline.py`.

## DT_ArenaPhases (arena_phase)

**Gap.** The only level being built first is described in six words.

### Query

```
Act 3 boss arena phases 33% 66% approach gates yard fence gap train yard re-lays exits and cover tiles, compact UE5 arena NavMesh coarse tactical grid, at least two escape routes per phase, checkpoints at the gates, greybox
```

### Retrieved

**1. `gdd_rex_machina#006`**, cosine 0.2573, prose, section `MY CAPSTONE — Source of Truth > 3. BOSS MECHANICS (v3 — post-exploit-fix)`  
shared terms: `yard`, `fence`, `gates`, `arena`, `yard_re`, `yard_fence`

**2. `gdd_rex_machina#005`**, cosine 0.2014, prose, section `MY CAPSTONE — Source of Truth > 2. STRUCTURE`  
shared terms: `act`, `arena`, `ue5_arena`, `tactical_grid`, `tactical`, `navmesh_coarse`

**3. `gdd_rex_machina#032`**, cosine 0.0783, code, section `MY CAPSTONE — Source of Truth > 5. AI DEV PIPELINE & ENGINE INTEGRATION (UE5)`  
shared terms: `ue5`, `66_approach`, `66`, `33_66`, `33`, `phase`

**4. `gdd_rex_machina#027`**, cosine 0.0631, code, section `MY CAPSTONE — Source of Truth > 4. THE DEV CREW (3 agents) > Agent 2 — CHRONICLER  *(narrative spine — rewritten in v3)*`  
shared terms: `beat_the_street`, `the_street`, `beat`

**5. `gdd_rex_machina#034`**, cosine 0.0609, prose, section `MY CAPSTONE — Source of Truth > 6. CONSTRAINTS (each explained)`  
shared terms: `per`, `routes_per`, `per_phase`, `routes`, `escape_routes`, `greybox`

**6. `gdd_rex_machina#043`**, cosine 0.0492, prose, section `MY CAPSTONE — Source of Truth > 9. OPEN DECISIONS`  
shared terms: `arena`, `greybox`, `arena_navmesh`, `navmesh`, `approach`, `ue5`

**7. `gdd_rex_machina#011`**, cosine 0.0485, code, section `MY CAPSTONE — Source of Truth > 4. THE DEV CREW (3 agents) > Agent 1 — NEMESIS  *(THE One Wow · adversarial · goal-oriented)*`  
shared terms: `cover_tiles`, `fence_gap`, `exits`, `phase`

### Output row (first)

```json
{
  "PhaseID": "phase_yard",
  "PhaseIndex": 1,
  "ApproachLow": 0.0,
  "ApproachHigh": 0.33,
  "ArenaName": "yard",
  "GridSpan": "10x10",
  "ExitTiles": [
    [
      0,
      4
    ],
    [
      9,
      7
    ]
  ],
  "CoverTiles": [
    [
      3,
      5
    ],
    [
      6,
      2
    ]
  ],
  "Light": "Late afternoon, low sun across the grass; the porch light is already on and throws one long rectangle over tiles 4-6 of the near row.",
  "SoundBed": "Wind in a chain-link fence, a screen door knocking in its frame, the robot's servo whine held at a steady clinical pitch.",
  "Props": [
    "chain-link fence line",
    "porch steps",
    "coiled garden hose",
    "tipped plastic wheelbarrow",
    "greybox shed block"
  ],
  "GateOpenMoment": "The yard gate at the fence line unlatches and swings the moment the approach meter crosses 0.33; the checkpoint fires as the player steps through, keeping the meter and the four-move history.",
  "PlayerSees": "Home ground turned into a ring. The robot dog stands between you and the house, head scanning for 600 ms every time you commit a step, and the porch light shows you exactly how much yard is left.",
  "CallbackBeat": "the_street",
  "NemesisPressure": "Charge above 60 percent. It intercepts on the straight read of your last four moves and reports in a flat clinical register; it never sprints, so its pauses are rare and its predictions are its only weapon.",
  "Provenance": "generated"
}
```

## DT_JourneyHazards (journey_hazard)

**Gap.** Acts 1 and 2 span nine days and the GDD names one hazard.

### Query

```
Gauntlet journey hazard chase obstacle Act 1 Act 2 tile-step and telegraph grammar pursuer telegraphs but never adapts, window_turns outcome escaped, shelter escape alley chase freight train leap boxcar coast diner limp onset day stamps tutorial for Act 3
```

### Retrieved

**1. `gdd_rex_machina#005`**, cosine 0.38, prose, section `MY CAPSTONE — Source of Truth > 2. STRUCTURE`  
shared terms: `act`, `tutorial_act`, `telegraph_grammar`, `shelter_escape`, `leap`, `freight_train`

**2. `gdd_rex_machina#031`**, cosine 0.3204, prose, section `MY CAPSTONE — Source of Truth > 4. THE DEV CREW (3 agents) > Agent 3 — GAUNTLET  *(journey hazards — now also the tutorial)*`  
shared terms: `act`, `chase`, `telegraph`, `window_turns_outcome`, `window_turns`, `obstacle`

**3. `gdd_rex_machina#018`**, cosine 0.1938, table_row, section `MY CAPSTONE — Source of Truth > 4. THE DEV CREW (3 agents) > Agent 2 — CHRONICLER  *(narrative spine — rewritten in v3)*`  
shared terms: `boxcar`, `gravel`, `train_leap`, `boxcar_door`, `door`, `open`

**4. `gdd_rex_machina#016`**, cosine 0.1485, table_row, section `MY CAPSTONE — Source of Truth > 4. THE DEV CREW (3 agents) > Agent 2 — CHRONICLER  *(narrative spine — rewritten in v3)*`  
shared terms: `pavement`, `shelter`, `open_pavement`, `yard`, `open`

**5. `gdd_rex_machina#021`**, cosine 0.1094, table_row, section `MY CAPSTONE — Source of Truth > 4. THE DEV CREW (3 agents) > Agent 2 — CHRONICLER  *(narrative spine — rewritten in v3)*`  
shared terms: `diner`, `diner_back`, `back`, `player`

**6. `gdd_rex_machina#022`**, cosine 0.1054, table_row, section `MY CAPSTONE — Source of Truth > 4. THE DEV CREW (3 agents) > Agent 2 — CHRONICLER  *(narrative spine — rewritten in v3)*`  
shared terms: `leg`, `back_leg`, `hazard`, `back`, `line`

**7. `gdd_rex_machina#017`**, cosine 0.0529, table_row, section `MY CAPSTONE — Source of Truth > 4. THE DEV CREW (3 agents) > Agent 2 — CHRONICLER  *(narrative spine — rewritten in v3)*`  
shared terms: `outcome_escaped`, `escaped`, `outcome`, `gauntlet`

**8. `gdd_rex_machina#039`**, cosine 0.0503, table_row, section `MY CAPSTONE — Source of Truth > 7. TOKEN BUDGET & PROJECTION (v3)`  
shared terms: `gauntlet_journey`, `gauntlet`, `journey`

**9. `gdd_rex_machina#032`**, cosine 0.0491, code, section `MY CAPSTONE — Source of Truth > 5. AI DEV PIPELINE & ENGINE INTEGRATION (UE5)`  
shared terms: `chase`, `telegraph`, `pursuer`, `outcome`, `gauntlet`, `journey`

**10. `gdd_rex_machina#028`**, cosine 0.0466, prose, section `MY CAPSTONE — Source of Truth > 4. THE DEV CREW (3 agents) > Agent 2 — CHRONICLER  *(narrative spine — rewritten in v3)*`  
shared terms: `stamps`, `day_stamps`, `day`, `journey`

### Output row (first)

```json
{
  "HazardID": "shelter_gate",
  "Day": 0,
  "Act": 1,
  "Location": "shelter yard, the gate seam between kennel run and open pavement",
  "PursuerType": "shelter handler with a catch pole, fixed loop along the fence",
  "Telegraph": "catch pole swings left",
  "WindowTurns": 4,
  "TileSpan": "5x3",
  "EscapeCondition": "step through the gate seam on the turn after the pole swings, and cross the threshold onto pavement",
  "FailCondition": "stand on the gate tile while the pole reaches it; the handler walks you back to the run and the loop restarts unchanged",
  "CausesCondition": false,
  "Teaches": "telegraph reading",
  "PlayerSees": "The yard gate stands open a dog's width, and a man with a catch pole walks the fence on the same slow loop he has walked all morning. The pole tips left before it comes down, every pass. You wait out his turn, slip the gap, and the pavement keeps going further than the yard ever did.",
  "Provenance": "generated"
}
```

## DT_NemesisReads (nemesis_read)

**Gap.** The fight surfaces 8 to 10 read lines per playthrough and the GDD contains one.

### Query

```
Nemesis boss read line: predicts the dog's next tile, reports the read it took off movement, read_category suppression, register shifts clinical confident strained as battery charge drains, past-tense diagnosis never intent, dir_freq_20 periodicity cover_tiles exits gait collar prior_attempt fence
```

### Retrieved

**1. `gdd_rex_machina#010`**, cosine 0.1578, prose, section `MY CAPSTONE — Source of Truth > 4. THE DEV CREW (3 agents) > Agent 1 — NEMESIS  *(THE One Wow · adversarial · goal-oriented)*`  
shared terms: `read`, `strained_battery`, `predicts_dog`, `dog_next`, `strained`, `reports_read`

**2. `gdd_rex_machina#006`**, cosine 0.1542, prose, section `MY CAPSTONE — Source of Truth > 3. BOSS MECHANICS (v3 — post-exploit-fix)`  
shared terms: `fence`, `read`, `charge`, `shifts`, `register_shifts`, `register`

**3. `gdd_rex_machina#008`**, cosine 0.1103, prose, section `MY CAPSTONE — Source of Truth > 3. BOSS MECHANICS (v3 — post-exploit-fix) > The six exploits that were fixed (do not reintroduce)`  
shared terms: `read`, `tense_diagnosis`, `tense`, `read_line`, `past_tense`, `past`

**4. `gdd_rex_machina#011`**, cosine 0.0985, code, section `MY CAPSTONE — Source of Truth > 4. THE DEV CREW (3 agents) > Agent 1 — NEMESIS  *(THE One Wow · adversarial · goal-oriented)*`  
shared terms: `prior_attempt`, `gait`, `dir_freq_20`, `cover_tiles`, `periodicity`, `exits`

**5. `gdd_rex_machina#004`**, cosine 0.0911, prose, section `MY CAPSTONE — Source of Truth > 1. THE ONE WOW — "The Nemesis"`  
shared terms: `read`, `took_off`, `took`, `read_took`, `off`, `reports_read`

**6. `gdd_rex_machina#013`**, cosine 0.042, code, section `MY CAPSTONE — Source of Truth > 4. THE DEV CREW (3 agents) > Agent 1 — NEMESIS  *(THE One Wow · adversarial · goal-oriented)*`  
shared terms: `read`, `read_category`, `nemesis`

**7. `gdd_rex_machina#021`**, cosine 0.0392, table_row, section `MY CAPSTONE — Source of Truth > 4. THE DEV CREW (3 agents) > Agent 2 — CHRONICLER  *(narrative spine — rewritten in v3)*`  
shared terms: `after`, `first`, `words`, `line`

### Output row (first)

```json
{
  "ReadID": "nemesis_read_sealing_direction_clinical",
  "ReadCategory": "sealing_direction",
  "ChargeBand": "clinical",
  "Line": "Target favored left nine of twenty recorded moves.",
  "WordCount": 8,
  "ObservableCited": "dir_freq_20",
  "TriggerCondition": "one compass direction dominates dir_freq_20",
  "Provenance": "generated"
}
```
