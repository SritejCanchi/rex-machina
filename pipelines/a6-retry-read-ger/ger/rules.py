"""The Evaluator. Five deterministic rules, each traceable to a line in the GDD.

The model proposes, the engine disposes. An LLM critic gives an opinion; a rule
that fires gives a name, a rule ID and a line you can put in a table next to the
repaired version. Every rule here is checkable without a second model call.
"""
import re

# GDD 3, exploit 1 "Read-line oracle": the read announced the plan before the
# player's input. Fixed by "past-tense diagnosis only, never intent". These are
# the tokens that turn a diagnosis back into an announcement.
FUTURE_MARKERS = [
    r"\bwill\b", r"\bwon'?t\b", r"\bshall\b", r"\bi'?ll\b", r"\bwe'?ll\b",
    r"\byou'?ll\b", r"\bit'?ll\b", r"\bgoing to\b", r"\bgonna\b",
    r"\bnext time\b", r"\bthis time\b", r"\bfrom now\b", r"\bfrom here\b",
    r"\bexpect\b", r"\bexpects\b", r"\banticipate\b", r"\bintend\b",
    r"\bplan\b", r"\bplans\b", r"\bpredict\b", r"\bpredicts\b",
    r"\bnow i\b", r"\bthis run\b", r"\bagain you'?ll\b", r"\btry again\b",
]

# GDD 4, Nemesis: "Never receives the journey. Input is only what a lawn robot
# could observe." Plus the story bible's banned words. Arena vocabulary such as
# "yard", "fence" and "train yard" is deliberately absent from this list.
JOURNEY_WORDS = [
    "shelter", "alley", "boxcar", "coast", "ocean", "highway", "diner",
    "stranger", "family", "mother", "theo", "kid", "porch", "collar's owner",
    "journey", "days", "day", "destiny", "heart", "soul", "forever", "home",
]

# GDD 3: "the first read after a loss references the failed run
# ('you tried the fence')". The read has to name the gate the player died at.
GATE_TOKENS = {
    "yard": ["yard"],
    "fence_gap": ["fence"],
    "train_yard": ["train"],
}

WORD_BUDGET = 12          # GDD 1 exemplar is 8 words. Barks, not sentences.

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
}


def words(line):
    return [w for w in re.findall(r"[A-Za-z']+", line)]


def allowed_numbers(case):
    """Every number the robot is actually holding this round."""
    allowed = {case["rounds_survived"], case["adjacent_rounds"],
               case["self_charge_pct"], 20, case["phase"]}
    for count in case["dir_freq_20"].values():
        allowed.add(int(round(count * 20)))
    return allowed


def check(line, case):
    """Return a list of (rule_id, message). Empty list means the line passes."""
    failures = []
    low = line.lower()

    # R1 -------------------------------------------------------------
    hits = [p for p in FUTURE_MARKERS if re.search(p, low)]
    if hits:
        shown = ", ".join(h.strip("\\b").replace("\\", "") for h in hits[:3])
        failures.append(("R1_TENSE",
                         "future or intent language (%s). GDD 3 exploit 1: "
                         "past-tense diagnosis only, never intent." % shown))

    # R2 -------------------------------------------------------------
    tokens = GATE_TOKENS[case["prior_attempt"]]
    if not any(t in low for t in tokens):
        failures.append(("R2_PRIOR_REF",
                         "does not name the gate the player lost at (%s). "
                         "GDD 3: the first read after a loss references the "
                         "failed run." % "/".join(tokens)))

    # R3 -------------------------------------------------------------
    n = len(words(line))
    if n > WORD_BUDGET:
        failures.append(("R3_BUDGET",
                         "%d words, budget is %d. GDD 1 reads are barks."
                         % (n, WORD_BUDGET)))

    # R4 -------------------------------------------------------------
    ok = allowed_numbers(case)
    seen = set(int(d) for d in re.findall(r"\b\d+\b", line))
    for w in words(line):
        if w.lower() in NUMBER_WORDS:
            seen.add(NUMBER_WORDS[w.lower()])
    invented = sorted(seen - ok)
    if invented:
        failures.append(("R4_INVENTED_NUMBER",
                         "cites %s, which is not in this round's telemetry. "
                         "GDD 5: every agent output passes an engine-side "
                         "validity check."
                         % ", ".join(str(i) for i in invented)))

    # R5 -------------------------------------------------------------
    leaks = [w for w in JOURNEY_WORDS if re.search(r"\b%s\b" % w, low)]
    if leaks:
        failures.append(("R5_JOURNEY_LEAK",
                         "uses %s. GDD 4: the Nemesis never receives the "
                         "journey and can only observe what a lawn robot sees."
                         % ", ".join(leaks[:3])))

    return failures
