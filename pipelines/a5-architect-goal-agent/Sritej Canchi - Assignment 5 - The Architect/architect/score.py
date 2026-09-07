"""Utility scoring for development priorities.

Class 7 slide 11 names the four factors a scoring system must account for:

    dependency order   what must exist first
    blockers           what is preventing other work
    project priority   what the GDD marks as critical
    current state      what is partially built versus untouched

Each is scored 0 to 1, then weighted. The weights are a design decision and
they are printed with every run so a reviewer can disagree with them.
"""
WEIGHTS = {"dependency": 0.30, "blocking": 0.30, "priority": 0.25, "state": 0.15}

STATE_SCORE = {"stubbed": 1.0, "mentioned": 0.7, "absent": 0.4, "implemented": 0.0}
PRIORITY_SCORE = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}


def dependency_ready(gap, by_key):
    """1.0 when every prerequisite already exists, 0.0 when none do.

    A feature whose prerequisites are missing cannot be built first, however
    valuable it is. This is the factor that stops the agent writing the shop UI
    before the inventory system.
    """
    reqs = gap.feature.get("requires", [])
    if not reqs:
        return 1.0
    met = sum(1 for r in reqs
              if by_key.get(r) and by_key[r].status == "implemented")
    return met / len(reqs)


def blocking_weight(gap, all_gaps):
    """How much other unbuilt work this feature is holding up, normalised."""
    blocks = set(gap.feature.get("blocks", []))
    if not blocks:
        return 0.0
    open_keys = {g.key for g in all_gaps if g.status != "implemented"}
    counts = [len(set(g.feature.get("blocks", [])) & open_keys) for g in all_gaps]
    top = max(counts) if counts else 0
    if top == 0:
        return 0.0
    return len(blocks & open_keys) / top


def score_all(gaps):
    by_key = {g.key: g for g in gaps}
    for g in gaps:
        dep = dependency_ready(g, by_key)
        blk = blocking_weight(g, gaps)
        pri = PRIORITY_SCORE.get(g.feature.get("priority", "medium"), 0.5)
        sta = STATE_SCORE.get(g.status, 0.0)
        g.breakdown = {"dependency": round(dep, 3), "blocking": round(blk, 3),
                       "priority": round(pri, 3), "state": round(sta, 3)}
        g.score = round(WEIGHTS["dependency"] * dep + WEIGHTS["blocking"] * blk
                        + WEIGHTS["priority"] * pri + WEIGHTS["state"] * sta, 4)
    return sorted(gaps, key=lambda g: (-g.score, g.key))


def explain(gap):
    b = gap.breakdown
    parts = ["%s %.2f x %.2f" % (k, b[k], WEIGHTS[k]) for k in
             ("dependency", "blocking", "priority", "state")]
    return "  ".join(parts) + "  =  %.4f" % gap.score
