"""
specs.py — the three content types this pipeline generates, and the canon
lexicons the gate checks them against.

Each spec names a gap in the GDD, states the retrieval query, declares the
output schema, and carries a hand-authored fallback row per key. The fallback
is what ships when generation or repair fails the gate, which is the same
discipline the GDD's §4 Chronicler validation promises and the same one the
Beat Foundry (Assignment #3) shipped.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ==========================================================================
# canon lexicons — shared by the gate and the critic prompt
# ==========================================================================

# GDD §4, Chronicler bible_entries.
BANNED_WORDS = ["destiny", "journey", "heart", "soul", "forever"]

# GDD §4 Nemesis: "Never receives the journey. Input is only what a lawn robot
# could observe." Anything on this list in a Nemesis read line is a lore break:
# the machine has no way to know it.
JOURNEY_ONLY_TERMS = [
    "shelter", "boxcar", "ocean", "coast", "diner", "stranger", "highway",
    "adopted", "adoption", "rescue", "pound", "kennel", "owner", "family",
    "mother", "theo", "girl", "home", "days", "nights", "travelled",
    "traveled", "leash", "bed", "porch", "window", "kid", "boy", "love",
]
# "nine" is deliberately NOT on that list. It reads as journey knowledge in
# "nine days", but it is also a legitimate count in "broke left nine times in
# twenty", which is the canon read line's own shape. Banning the bare numeral
# would fail correct rows; "days" and "nights" carry the journey sense on their
# own. Found while authoring the fallback lines, not in review.

# Phrases that contain a banned token but are legitimate arena geometry.
# "train yard" is the phase-3 arena name (GDD §3); "train" alone is journey.
JOURNEY_ALLOW_PHRASES = ["train yard", "fence gap", "the yard"]

# GDD §3 exploit fix #1: "past-tense diagnosis only, never intent". A read line
# that states what the robot is about to do hands the player next round's answer.
INTENT_MARKERS = [
    "will ", "i'll", "i will", "shall", "gonna", "going to", "about to",
    "next move", "next turn", "i am moving", "i'm moving", "watch me",
    "now i", "prepare", "expect me",
]

# GDD §4 Gauntlet: the journey pursuer "telegraphs but never adapts". Adaptive
# verbs belong to the Nemesis alone; in a hazard row they are a lore break.
ADAPTIVE_VERBS = [
    "predict", "predicts", "predicted", "learn", "learns", "learned",
    "adapt", "adapts", "adapted", "remember", "remembers", "remembered",
    "anticipate", "anticipates", "anticipated", "cuts you off", "cut off",
    "intercept", "intercepts", "reads your", "counters",
]

# Anachronism map: a term may not appear in content dated earlier than the day
# the fact becomes true. Days from the GDD §4 journey_memory and beat table.
FACT_DAY = {
    "alley": 1, "train": 3, "boxcar": 3, "rails": 3, "freight": 3,
    "ocean": 5, "sea": 5, "coast": 5, "water": 5, "salt": 5,
    "diner": 6, "stranger": 6, "tray": 6, "fed": 6,
    "limp": 7, "limping": 7,
    "porch": 9, "cul-de-sac": 9,
}
# Two terms were removed from that map after real generator output was run
# through the gate. "fence" was dated to day 7 and fired on a day-0 kennel
# yard, a day-3 rail siding and a day-6 back lot, all of which can obviously
# have fences; what day 7 dates is the injury, not the existence of wire.
# "street" was dated to day 9 and fired on Act 1, where the GDD's own beat is
# called `first_street`. What day 9 dates is the family's street. An
# anachronism rule that fires on ordinary geography sends good rows to the
# fallback table, which is worse than missing a subtle one.

# Act 3 mechanics a journey hazard is allowed to claim it teaches.
ACT3_MECHANICS = [
    "telegraph reading", "cover use", "exit choice", "pattern breaking",
    "stamina management", "gap commitment", "adjacency cost", "window timing",
]

# The eight Chronicler beat ids (GDD §4) plus the three authored climax beats.
CANON_BEATS = [
    "first_street", "alley_escape", "train_leap", "boxcar_night",
    "coast_from_car", "fed_by_stranger", "limp_onset", "the_street",
    "shelter_adoption", "nemesis_reveal", "switch_off",
]

# Observables the Nemesis actually receives (GDD §4 input contract). A read
# line must lean on one of these; the lexicon is how the gate checks that the
# prose actually references the field the row claims.
OBSERVABLE_LEXICON = {
    "dir_freq_20": ["left", "right", "up", "down", "break", "breaks", "twenty",
                    "favoured", "favored", "four", "three", "five", "six",
                    "seven", "eight", "nine", "ten", "eleven", "twelve"],
    "periodicity": ["cycle", "loop", "repeat", "repeats", "beat", "beats",
                    "pattern", "rhythm", "every", "same", "order"],
    "cover_tiles": ["cover", "shadow", "shade", "behind", "crate", "post"],
    "exits": ["exit", "exits", "gap", "opening", "gate", "mouth", "corner"],
    "dog_recent_moves": ["moves", "step", "steps", "stepped", "turn", "turned",
                         "juke", "cut", "twice", "again"],
    "dog_observable": ["gait", "limp", "limping", "leg", "collar", "drag",
                       "favouring", "favoring", "short", "uneven"],
    "self_charge_pct": ["charge", "cell", "power", "sun", "solar", "reserve",
                        "draw", "amps", "low", "dim"],
    "approach_meter": ["closer", "close", "distance", "near", "nearer",
                       "ground", "metres", "meters"],
    "prior_attempt": ["tried", "last", "before", "again", "already", "twice"],
}


# ==========================================================================
# spec objects
# ==========================================================================

@dataclass
class ContentSpec:
    key: str
    table: str
    title: str
    gap: str                     # the "my game is thin on X" sentence
    evidence: str                # what in the GDD proves the gap
    query: str                   # the retrieval query, tuned (see evaluate_retrieval.py)
    naive_query: str             # the first query I wrote, kept for the A/B
    k: int                       # top-k for the shared spec-level query
    fields: list[str]
    rules: list[str]
    seed_k: int = 2              # top-k for each per-row seed query
    cap: int = 10                # ceiling on the unioned context
    field_help: str = ""         # closed vocabularies and field types
    keys: list[dict] = field(default_factory=list)   # the row keys to generate
    fallbacks: dict[str, dict] = field(default_factory=dict)


def seed_query(content_type: str, key: dict) -> str:
    """The second retrieval stage.

    One shared query per content type retrieves the mechanics. It does not
    reliably retrieve the one canon fact a *particular* row needs: querying
    "journey hazards" pulls the Gauntlet contract but not the `limp_onset`
    beat row that dates the third damaging hazard to day 7. A short query
    built from the row's own key pulls that row's beat at rank 1.

    Measured: see evaluate_retrieval.py. Hazard recall at k=6 goes from 0.43
    on the shared query alone to 0.86 on the union.
    """
    if content_type == "nemesis_read":
        return (f"{key['read_category']} {key['observable']} "
                f"{key['trigger']} charge {key['charge_range']} "
                f"{key['register']} read line")
    if content_type == "journey_hazard":
        return (f"{key['hazard_id'].replace('_', ' ')} day {key['day']} "
                f"act {key['act']} {key['seed']}")
    return (f"{key['phase_id'].replace('_', ' ')} arena {key['arena']} "
            f"phase {key['index']} approach {key['low']} to {key['high']} "
            f"beat {key['callback']} exits cover")


READ_CATEGORIES = [
    ("sealing_direction", "dir_freq_20",
     "one compass direction dominates dir_freq_20"),
    ("cover_habit", "cover_tiles",
     "the dog has ended three of the last five rounds on a cover tile"),
    ("exit_fixation", "exits",
     "two consecutive runs at the same exit tile"),
    ("periodicity_called", "periodicity",
     "periodicity > 0.65"),
    ("stall_detected", "dog_recent_moves",
     "two of the last four moves cancelled each other"),
    ("gait_read", "dog_observable",
     "dog_observable.gait == limping"),
    ("charge_strain", "self_charge_pct",
     "self_charge_pct crossed below a band boundary this round"),
    ("prior_attempt", "prior_attempt",
     "first round after a checkpoint retry, prior_attempt is set"),
]

CHARGE_BANDS = [
    # band, charge range, register rule (a design decision, see README)
    ("clinical", ">60", "telemetry register, no second person, no contractions"),
    ("confident", "30-60", "addresses the target directly as 'you'"),
    ("strained", "<30", "five words or fewer, clipped, may drop articles"),
]


NEMESIS_READS = ContentSpec(
    key="nemesis_read",
    table="DT_NemesisReads",
    title="Nemesis read lines",
    gap="The fight surfaces 8 to 10 read lines per playthrough and the GDD "
        "contains one.",
    evidence="GDD §4 gives a single read, \"Target favored left breaks four "
            "times in twenty.\", and one read_category, sealing_left. GDD §4 "
            "UI rule requires suppression by category, which needs a category "
            "set. GDD §6.5 promises graceful degradation with a chase-step "
            "default for the move and says nothing about the line, so an "
            "offline fight is currently silent.",
    query=("Nemesis boss read line: predicts the dog's next tile, reports the "
           "read it took off movement, read_category suppression, register "
           "shifts clinical confident strained as battery charge drains, "
           "past-tense diagnosis never intent, dir_freq_20 periodicity "
           "cover_tiles exits gait collar prior_attempt fence"),
    naive_query="Nemesis read lines",
    k=6,
    fields=["ReadID", "ReadCategory", "ChargeBand", "Line", "WordCount",
            "ObservableCited", "TriggerCondition"],
    rules=["N1 word count <= 9",
           "N2 no statement of intent or future tense (exploit fix #1)",
           "N3 the line must reference the observable it cites",
           "N4 no journey knowledge the machine cannot observe",
           "N5 no banned word",
           "N6 register must match the charge band",
           "N7 the dog is never named and never speaks"],
    # Band-major order, so each batch of 8 is one register. A generator asked
    # for eight clinical lines writes a more consistent register than one
    # asked to switch register every row.
    keys=[{"read_category": cat, "observable": obs, "trigger": trig,
           "charge_band": band, "charge_range": rng, "register": reg}
          for band, rng, reg in CHARGE_BANDS
          for cat, obs, trig in READ_CATEGORIES],
)

JOURNEY_HAZARDS = ContentSpec(
    key="journey_hazard",
    table="DT_JourneyHazards",
    title="Gauntlet journey hazards",
    gap="Acts 1 and 2 span nine days and the GDD names one hazard.",
    evidence="GDD §4 Gauntlet ships a single example output, hazard "
            "\"alley_chase\". GDD §2 says Act 1 is the tutorial for Act 3, so "
            "every hazard owes the player one piece of the Act 3 grammar, and "
            "the GDD never says which teaches what. GDD §4 also requires the "
            "limp to flip after the third hazard, which is unsatisfiable with "
            "one hazard on the books.",
    query=("Gauntlet journey hazard chase obstacle Act 1 Act 2 tile-step and "
           "telegraph grammar pursuer telegraphs but never adapts, "
           "window_turns outcome escaped, shelter escape alley chase freight "
           "train leap boxcar coast diner limp onset day stamps tutorial for "
           "Act 3"),
    naive_query="journey hazards",
    k=6,
    fields=["HazardID", "Day", "Act", "Location", "PursuerType", "Telegraph",
            "WindowTurns", "TileSpan", "EscapeCondition", "FailCondition",
            "CausesCondition", "Teaches", "PlayerSees"],
    rules=["H1 no fact dated later than the hazard's own day",
           "H2 telegraph is four words or fewer",
           "H3 window_turns between 2 and 5",
           "H4 the pursuer never adapts",
           "H5 exactly three hazards damage, and the third falls on day 7",
           "H6 no banned word",
           "H7 Teaches names a real Act 3 mechanic"],
    # The nemesis and arena specs hand the model its closed values inside each
    # key ("observable", "callback"), so it cannot get them wrong. The hazard
    # keys carry no equivalent hint, and real generator output duly invented a
    # sentence for Teaches on all six rows and wrote the string "none" into a
    # boolean. The gate was right and the prompt was incomplete.
    field_help=(
        "FIELD NOTES\n"
        "  Teaches          pick exactly one of: telegraph reading, cover use,\n"
        "                   exit choice, pattern breaking, stamina management,\n"
        "                   gap commitment, adjacency cost, window timing.\n"
        "                   One value, verbatim, no explanation appended.\n"
        "  CausesCondition  JSON boolean true or false. Set it to the key's\n"
        "                   \"damaging\" value. Never the string \"none\".\n"
        "  WindowTurns      JSON integer.\n"
        "  Day, Act         JSON integers, copied from the key.\n"
    ),
    keys=[
        {"hazard_id": "shelter_gate", "day": 0, "act": 1,
         "seed": "the shelter yard gate, the moment before open pavement",
         "damaging": False},
        {"hazard_id": "alley_chase", "day": 1, "act": 1,
         "seed": "the canon alley chase, GDD §4 example output", "damaging": True},
        {"hazard_id": "road_crossing", "day": 2, "act": 1,
         "seed": "four lanes of moving traffic, an obstacle not a pursuer",
         "damaging": False},
        {"hazard_id": "train_leap", "day": 3, "act": 2,
         "seed": "gravel, a moving freight, the open boxcar door", "damaging": True},
        {"hazard_id": "diner_yard", "day": 6, "act": 2,
         "seed": "the diner back lot, a hazard the player may choose to fail",
         "damaging": False},
        {"hazard_id": "fence_line", "day": 7, "act": 2,
         "seed": "a gap under a chain fence; this is the hazard that costs the "
                 "back leg and the geometry the phase 2 arena reuses",
         "damaging": True},
    ],
)

ARENA_PHASES = ContentSpec(
    key="arena_phase",
    table="DT_ArenaPhases",
    title="Act 3 arena phase dressing",
    gap="The only level being built first is described in six words.",
    evidence="GDD §3 gives the three phases as \"yard → fence gap → train "
            "yard\" and says the arena \"re-lays exits and cover\" at 33% and "
            "66%, without saying where. GDD §6.1 requires at least two escape "
            "routes per phase, which is a claim about a layout that does not "
            "exist yet. GDD §8 Slice 1 builds this arena before anything else.",
    query=("Act 3 boss arena phases 33% 66% approach gates yard fence gap "
           "train yard re-lays exits and cover tiles, compact UE5 arena "
           "NavMesh coarse tactical grid, at least two escape routes per "
           "phase, checkpoints at the gates, greybox"),
    naive_query="arena phases",
    k=6,
    fields=["PhaseID", "PhaseIndex", "ApproachLow", "ApproachHigh",
            "ArenaName", "GridSpan", "ExitTiles", "CoverTiles", "Light",
            "SoundBed", "Props", "GateOpenMoment", "PlayerSees",
            "CallbackBeat", "NemesisPressure"],
    rules=["A1 at least two exit tiles per phase",
           "A2 every exit and cover tile inside the grid span",
           "A3 approach bands tile 0 to 1 with no gap or overlap",
           "A4 arena names are yard, fence gap, train yard in that order",
           "A5 CallbackBeat is a canon beat id",
           "A6 no banned word",
           "A7 no prop that contradicts canon"],
    keys=[
        {"phase_id": "phase_yard", "index": 1, "low": 0.0, "high": 0.33,
         "arena": "yard", "callback": "the_street"},
        {"phase_id": "phase_fence_gap", "index": 2, "low": 0.33, "high": 0.66,
         "arena": "fence gap", "callback": "limp_onset"},
        {"phase_id": "phase_train_yard", "index": 3, "low": 0.66, "high": 1.0,
         "arena": "train yard", "callback": "train_leap"},
    ],
)

SPECS = {s.key: s for s in (NEMESIS_READS, JOURNEY_HAZARDS, ARENA_PHASES)}
