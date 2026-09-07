# BUILT

Features this agent has written into the game.

## self_charge_pct  Solar charge and battery drain

Added solar charge state to the Nemesis, drained by pursuit and recovered each
round, and wired charge_band to the GDD's three registers.

Files: rex/nemesis.py

GDD: GDD 3 'The machine tires (solar/battery)'; GDD 3 register thresholds 60 and
30 taken verbatim; GDD 4 input contract self_charge_pct 48.

Reviewer changed pursuit cost 4 to 8 before accepting, and added the
self_charge_pct property. See README 4.

_run e4fee9e9_
