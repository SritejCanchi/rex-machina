# Retrieval evaluation

Index: 39 chunks, 2471 terms, k=6. Gold sets are hand-labelled; see `evaluate_retrieval.py`.

| content type | query | P@6 | R@6 | first gold | MAP |
|---|---|---:|---:|---:|---:|
| arena_phase | naive | 0.75 | 0.50 | 1 | 0.69 |
| arena_phase | tuned | 0.67 | 0.67 | 1 | 0.57 |
| arena_phase | union (shipped) | 0.57 | 0.67 | 1 | 0.53 |
| journey_hazard | naive | 0.17 | 0.14 | 1 | 0.17 |
| journey_hazard | tuned | 0.50 | 0.43 | 1 | 0.50 |
| journey_hazard | union (shipped) | 0.70 | 1.00 | 1 | 1.00 |
| nemesis_read | naive | 0.67 | 0.57 | 1 | 0.67 |
| nemesis_read | tuned | 1.00 | 0.86 | 1 | 1.00 |
| nemesis_read | union (shipped) | 0.86 | 0.86 | 1 | 0.86 |

**naive mean** — P@6 0.53, R@6 0.40, MAP 0.51
**tuned mean** — P@6 0.72, R@6 0.65, MAP 0.69
**union (shipped) mean** — P@6 0.71, R@6 0.84, MAP 0.80

## What each query actually returned

### arena_phase — naive

`arena phases`

1. HIT  `gdd_rex_machina#005`
2. HIT  `gdd_rex_machina#006`
3. miss `gdd_rex_machina#043`
4. HIT  `gdd_rex_machina#042`

gold not retrieved: `gdd_rex_machina#007`, `gdd_rex_machina#011`, `gdd_rex_machina#034`

### arena_phase — tuned

`Act 3 boss arena phases 33% 66% approach gates yard fence gap train yard re-lays exits and cover tiles, compact UE5 arena NavMesh coarse tactical grid, at least two escape routes per phase, checkpoints at the gates, greybox`

1. HIT  `gdd_rex_machina#006`
2. HIT  `gdd_rex_machina#005`
3. miss `gdd_rex_machina#032`
4. HIT  `gdd_rex_machina#034`
5. miss `gdd_rex_machina#043`
6. HIT  `gdd_rex_machina#011`

gold not retrieved: `gdd_rex_machina#007`, `gdd_rex_machina#042`

### arena_phase — union (shipped)

`Act 3 boss arena phases 33% 66% approach gates yard fence gap train yard re-lays exits and cover tiles, compact UE5 arena NavMesh coarse tactical grid, at least two escape routes per phase, checkpoints at the gates, greybox  ++ 3 per-row seed queries`

1. HIT  `gdd_rex_machina#006`
2. HIT  `gdd_rex_machina#005`
3. miss `gdd_rex_machina#032`
4. miss `gdd_rex_machina#027`
5. HIT  `gdd_rex_machina#034`
6. miss `gdd_rex_machina#043`
7. HIT  `gdd_rex_machina#011`

gold not retrieved: `gdd_rex_machina#007`, `gdd_rex_machina#042`

### journey_hazard — naive

`journey hazards`

1. HIT  `gdd_rex_machina#031`
2. miss `gdd_rex_machina#039`
3. miss `gdd_rex_machina#015`
4. miss `gdd_rex_machina#036`
5. miss `gdd_rex_machina#028`
6. miss `gdd_rex_machina#032`

gold not retrieved: `gdd_rex_machina#005`, `gdd_rex_machina#016`, `gdd_rex_machina#017`, `gdd_rex_machina#018`, `gdd_rex_machina#021`, `gdd_rex_machina#022`

### journey_hazard — tuned

`Gauntlet journey hazard chase obstacle Act 1 Act 2 tile-step and telegraph grammar pursuer telegraphs but never adapts, window_turns outcome escaped, shelter escape alley chase freight train leap boxcar coast diner limp onset day stamps tutorial for Act 3`

1. HIT  `gdd_rex_machina#005`
2. HIT  `gdd_rex_machina#031`
3. HIT  `gdd_rex_machina#017`
4. miss `gdd_rex_machina#039`
5. miss `gdd_rex_machina#032`
6. miss `gdd_rex_machina#028`

gold not retrieved: `gdd_rex_machina#016`, `gdd_rex_machina#018`, `gdd_rex_machina#021`, `gdd_rex_machina#022`

### journey_hazard — union (shipped)

`Gauntlet journey hazard chase obstacle Act 1 Act 2 tile-step and telegraph grammar pursuer telegraphs but never adapts, window_turns outcome escaped, shelter escape alley chase freight train leap boxcar coast diner limp onset day stamps tutorial for Act 3  ++ 6 per-row seed queries`

1. HIT  `gdd_rex_machina#005`
2. HIT  `gdd_rex_machina#031`
3. HIT  `gdd_rex_machina#018`
4. HIT  `gdd_rex_machina#016`
5. HIT  `gdd_rex_machina#021`
6. HIT  `gdd_rex_machina#022`
7. HIT  `gdd_rex_machina#017`
8. miss `gdd_rex_machina#039`
9. miss `gdd_rex_machina#032`
10. miss `gdd_rex_machina#028`

### nemesis_read — naive

`Nemesis read lines`

1. HIT  `gdd_rex_machina#013`
2. HIT  `gdd_rex_machina#014`
3. HIT  `gdd_rex_machina#010`
4. HIT  `gdd_rex_machina#004`
5. miss `gdd_rex_machina#015`
6. miss `gdd_rex_machina#003`

gold not retrieved: `gdd_rex_machina#006`, `gdd_rex_machina#008`, `gdd_rex_machina#011`

### nemesis_read — tuned

`Nemesis boss read line: predicts the dog's next tile, reports the read it took off movement, read_category suppression, register shifts clinical confident strained as battery charge drains, past-tense diagnosis never intent, dir_freq_20 periodicity cover_tiles exits gait collar prior_attempt fence`

1. HIT  `gdd_rex_machina#010`
2. HIT  `gdd_rex_machina#006`
3. HIT  `gdd_rex_machina#008`
4. HIT  `gdd_rex_machina#011`
5. HIT  `gdd_rex_machina#004`
6. HIT  `gdd_rex_machina#013`

gold not retrieved: `gdd_rex_machina#014`

### nemesis_read — union (shipped)

`Nemesis boss read line: predicts the dog's next tile, reports the read it took off movement, read_category suppression, register shifts clinical confident strained as battery charge drains, past-tense diagnosis never intent, dir_freq_20 periodicity cover_tiles exits gait collar prior_attempt fence  ++ 24 per-row seed queries`

1. HIT  `gdd_rex_machina#010`
2. HIT  `gdd_rex_machina#006`
3. HIT  `gdd_rex_machina#008`
4. HIT  `gdd_rex_machina#011`
5. HIT  `gdd_rex_machina#004`
6. HIT  `gdd_rex_machina#013`
7. miss `gdd_rex_machina#021`

gold not retrieved: `gdd_rex_machina#014`

