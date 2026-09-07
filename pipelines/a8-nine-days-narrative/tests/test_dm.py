#!/usr/bin/env python3
"""Ledger rules, consistency checks and one full turn, all without a model."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dm import consistency, session                           # noqa: E402
from dm.ledger import Ledger                                  # noqa: E402
import ab_test                                                # noqa: E402

passed = failed = 0


def ok(cond, label):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print("  FAIL", label)


# ---- the ledger accepts what it should ------------------------------
led = Ledger()
made = led.apply({"add_facts": ["left_behind"], "hunger_delta": 1,
                  "trust_delta": -1, "condition": "limping"})
ok(led.has("left_behind"), "a known fact is recorded")
ok(led.day_of("left_behind") == 0, "the fact carries the current day")
ok(led.hunger == 2 and led.trust_in_humans == -1, "deltas are applied")
ok(led.condition == {"state": "limping", "since_day": 0}, "condition stamps the day")
ok("shelter_yard" in led.places_seen, "the place is recorded")

# ---- and refuses what it should -------------------------------------
led2 = Ledger()
led2.apply({"add_facts": ["took_food_from_stranger"]})
before = len(led2.facts)
led2.apply({"add_facts": ["refused_the_hand"]})
ok(len(led2.facts) == before, "a contradicting fact is refused")
ok(any("contradicts" in why for _, why in led2.rejected), "and the reason names it")

led2.apply({"add_facts": ["took_food_from_stranger"]})
ok(any("already recorded" in why for _, why in led2.rejected), "a duplicate is refused")
led2.apply({"add_facts": ["Took Food"]})
ok(any("snake_case" in why for _, why in led2.rejected), "a malformed id is refused")
led2.apply({"trust_delta": 9})
ok(led2.trust_in_humans <= 2, "an oversized delta cannot move the value")
led2.apply({"condition": "radiant"})
ok(any("unknown state" in why for _, why in led2.rejected), "an unknown condition is refused")
led2.apply({"set_flags": {"ate_today": "yes"}})
ok(any("boolean" in why for _, why in led2.rejected), "a non-boolean flag is refused")

led3 = Ledger()
for _ in range(20):
    led3.advance_day()
ok(led3.day == 8, "the day cannot run past the end of the world")

# ---- consistency ----------------------------------------------------
led4 = Ledger()
led4.apply({"add_facts": ["took_food_from_stranger"]})
codes = lambda t: [c for c, _ in consistency.check(t, led4)]
ok("BANNED_WORD" in codes("Your soul is tired but you walk."), "banned word caught")
ok("BANNED_WORD" not in codes("You walk. The road is cold."), "clean line passes")
ok("NOT_SECOND_PERSON" in codes("The dog walks on. Gravel underfoot."), "third person caught")
ok("INVENTED_NAME" in codes("You wait. Maya is at the window."), "invented name caught")
ok("INVENTED_NAME" not in codes("Theo is not at the window. You wait."),
   "a name the world owns is allowed")
ok("INVENTED_NAME" not in codes("Gravel under you. The boxcar door is open."),
   "an ordinary word opening a sentence is not a name")
ok("CONTRADICTS_LEDGER" in codes("You refused the hand and walked on."),
   "a line contradicting the ledger is caught")
ok(consistency.check("You ate what was set down. The door stays open.", led4) == [],
   "a line agreeing with the ledger is clean")


# ---- one full turn, no model ----------------------------------------
class Scripted:
    name = "scripted"

    def __init__(self, patch, narration):
        self.patch, self.narration = patch, narration

    def complete(self, role, prompt, max_tokens=500):
        if role.startswith("track"):
            return json.dumps(self.patch)
        return json.dumps({"narration": self.narration})


led5 = Ledger()
rec = session.turn(
    Scripted({"add_facts": ["escaped_the_gate"], "hunger_delta": 1,
              "advance_day": True, "why": "she left"},
             "You put your shoulder to the gap and the gate gives. Gravel, then pavement."),
    led5, "push through the gate")
ok(rec["changes"] and led5.has("escaped_the_gate"), "a turn writes to the ledger")
ok(rec["flags"] == [], "a clean narration passes the checks")
ok(led5.day == 1, "advance_day moves the day after the turn is recorded")
ok(rec["ledger"]["day"] == 0, "the record shows the ledger as it was during the turn")

rec2 = session.turn(
    Scripted({"add_facts": ["nonsense id"]}, "The dog keeps going."),
    Ledger(), "wander")
ok(rec2["changes"] == [], "a refused patch changes nothing")
ok("NOT_SECOND_PERSON" in [c for c, _ in rec2["flags"]],
   "the checker still runs on a turn that changed nothing")

# ---- the A/B fixture differs in exactly one decision -----------------
a, b = ab_test.build(True), ab_test.build(False)
ok(a.has("took_food_from_stranger") and b.has("refused_the_hand"),
   "the two A/B ledgers hold opposite day 3 facts")
ok(a.day == b.day == 6, "both A/B ledgers sit on day 6")
ok(a.trust_in_humans != b.trust_in_humans, "trust differs between them")
ok(a.condition == b.condition, "everything else about them matches")

# ---- regressions from live run 1 ------------------------------------
led6 = Ledger()
led6.apply({"add_facts": ["took_food_from_stranger"]},
           "the hand puts a plate down. back away from it and wait")
ok(led6.has("refused_the_hand"), "a refusal is not recorded as the thing refused")
ok(not led6.has("took_food_from_stranger"), "and the affirmative fact is not stored")
ok(any("reads as a refusal" in why for _, why in led6.rejected),
   "the swap is logged with its reason")

led7 = Ledger()
led7.apply({"add_facts": ["took_food_from_stranger"]}, "eat what the hand set down")
ok(led7.has("took_food_from_stranger"), "an affirmative action is untouched")

led8 = Ledger()
led8.apply({"condition": "limping"})
c8 = [c for c, _ in consistency.check("Your left front leg throbs.", led8)]
ok(c8.count("WRONG_BODY_PART") == 1, "the wrong leg is caught once, not twice")
ok(consistency.check("Your back leg throbs.", led8) == [], "the canon leg passes")
ok("INVENTED_NAME" not in [c for c, _ in
   consistency.check("Metal floor cold under your paws, and you keep going.", led8)],
   "an ordinary noun opening a sentence is not a name")

led9 = Ledger()
session.turn(Scripted({"advance_day": False}, "You wait. The road is cold."),
             led9, "wait", force_advance=True)
ok(led9.day == 1, "the scripted session advances the day whatever the tracker says")

# ---- regressions from live run 3 ------------------------------------
led10 = Ledger()
led10.apply({"condition": "limping"})
c10 = [c for c, _ in consistency.check("Your front left leg throbs.", led10)]
ok("WRONG_BODY_PART" in c10, "a reordered wrong leg is caught")
ok("WRONG_BODY_PART" in [c for c, _ in
   consistency.check("Your foreleg drags.", led10)], "foreleg is caught")
ok(consistency.check("Your back leg drags and you keep going.", led10) == [],
   "the canon leg still passes")

led11 = Ledger()
led11.apply({"add_facts": ["refused_the_hand"]})
c11 = [c for c, _ in consistency.check(
    "Grease-smell thickens and you watch the plate on the concrete.", led11)]
ok("INVENTED_NAME" not in c11, "a hyphenated ordinary word is not a name")
ok("CONTRADICTS_LEDGER" not in c11, "naming the plate is not eating from it")
ok("CONTRADICTS_LEDGER" in [c for c, _ in consistency.check(
    "You ate what the hand set down.", led11)], "eating still contradicts a refusal")

led12 = Ledger()
led12.day = 4
led12.apply({"condition": "limping"})
led12.day = 7
led12.apply({"condition": "hurt"})
ok(led12.condition == {"state": "hurt", "since_day": 4},
   "an injury that worsens keeps its onset day")
led13 = Ledger()
led13.day = 3
led13.apply({"condition": "limping"})
ok(led13.condition["since_day"] == 3, "a new injury stamps the day it began")

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
