# DECISIONS

Why the agent picked what it picked.

## self_charge_pct  selected

Score 0.9100, dependency 1.00 x 0.30  blocking 1.00 x 0.30  priority 1.00 x 0.25  state 0.40 x 0.15  =  0.9100

The only open feature with no unmet prerequisites. Three others sit behind it:
charge_band_reads, aggression and sprint_move all scored 0.00 on dependency
because they were waiting on charge to exist.

_run e4fee9e9_
