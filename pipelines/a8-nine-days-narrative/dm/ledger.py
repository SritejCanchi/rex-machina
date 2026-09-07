"""The facts ledger, and the engine-side rules that decide what may enter it.

GDD 4 already specifies this structure for the Chronicler: a journey memory of
day-stamped facts plus a condition with a since_day. This is that object, made
writable by play rather than authored in advance.

The tracker agent proposes a patch. Nothing here trusts it. Every field is
range-checked, every fact is checked against what the world knows and against
what the ledger already holds, and a rejected patch is recorded rather than
silently dropped.
"""
import json
import os
import re

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data", "world.json")
FACT_RE = re.compile(r"^[a-z][a-z_]{2,39}$")

# An action can be phrased as a refusal, and a tracker reading it quickly
# records the thing that was refused. Live run 1 did exactly that: "back away
# from it and wait" was recorded as took_food_from_stranger. This is the
# engine-side check for it.
NEGATION_RE = re.compile(
    r"\b(back away|backs away|backed away|refuse|refuses|refused|avoid|avoids"
    r"|do ?n[o']t|does ?n[o']t|did ?n[o']t|wo ?n[o']t|never|leave it|left it"
    r"|stay away|keep away|walk away|turn away|ignore|ignores|ignored)\b",
    re.I)


def world():
    with open(DATA, encoding="utf-8") as fh:
        return json.load(fh)


class Ledger:
    def __init__(self, w=None):
        self.w = w or world()
        self.day = 0
        self.condition = {"state": "sound", "since_day": 0}
        self.hunger = 1              # 0 fed, 4 starving
        self.trust_in_humans = 0     # -2 to 2
        self.facts = []              # [{"fact": str, "day": int}]
        self.places_seen = []
        self.flags = {}
        self.rejected = []           # every patch field the engine refused

    # ---- reading -----------------------------------------------------
    def as_dict(self):
        return {
            "day": self.day,
            "condition": self.condition,
            "hunger": self.hunger,
            "trust_in_humans": self.trust_in_humans,
            "facts": self.facts,
            "places_seen": self.places_seen,
            "flags": self.flags,
        }

    def fact_ids(self):
        return [f["fact"] for f in self.facts]

    def has(self, fact):
        return fact in self.fact_ids()

    def day_of(self, fact):
        for f in self.facts:
            if f["fact"] == fact:
                return f["day"]
        return None

    def scene(self):
        for d in self.w["days"]:
            if d["day"] == self.day:
                return d
        return self.w["days"][-1]

    # ---- writing -----------------------------------------------------
    def apply(self, patch, action=""):
        """Apply a proposed patch. Returns the list of changes actually made.

        `action` is the raw text the player typed. It is used only to catch a
        tracker that recorded the opposite of what was done.
        """
        made = []
        if not isinstance(patch, dict):
            self.rejected.append(("patch", "not an object"))
            return made

        for fact in self._correct_negation(patch.get("add_facts") or [], action):
            ok, why = self._fact_allowed(fact)
            if not ok:
                self.rejected.append((fact, why))
                continue
            self.facts.append({"fact": fact, "day": self.day})
            made.append("fact %s" % fact)

        for k, v in (patch.get("set_flags") or {}).items():
            if not FACT_RE.match(str(k)):
                self.rejected.append((k, "flag name is not a snake_case token"))
                continue
            if not isinstance(v, bool):
                self.rejected.append((k, "flag value is not a boolean"))
                continue
            self.flags[k] = v
            made.append("flag %s=%s" % (k, v))

        made += self._nudge(patch, "hunger_delta", "hunger", 0, 4)
        made += self._nudge(patch, "trust_delta", "trust_in_humans", -2, 2)

        cond = patch.get("condition")
        if cond in ("sound", "limping", "hurt"):
            if cond != self.condition["state"]:
                # An injury that worsens is the same injury. Run 3 escalated
                # limping to hurt on day 7 and lost the day 4 onset with it.
                onset = (self.condition["since_day"]
                         if self.condition["state"] != "sound" and cond != "sound"
                         else self.day)
                self.condition = {"state": cond, "since_day": onset}
                made.append("condition %s since day %d" % (cond, onset))
        elif cond is not None:
            self.rejected.append(("condition", "unknown state %r" % (cond,)))

        place = self.scene()["place"]
        if place not in self.places_seen:
            self.places_seen.append(place)
        return made

    def advance_day(self):
        if self.day < self.w["days"][-1]["day"]:
            self.day += 1
        return self.day

    # ---- the engine's rules -----------------------------------------
    def _correct_negation(self, facts, action):
        """Swap a fact for its opposite when the action was a refusal."""
        if not action or not NEGATION_RE.search(action):
            return facts
        pairs = self.w.get("negation_pairs", {})
        out = []
        for f in facts:
            if f in pairs:
                self.rejected.append(
                    (f, "the action reads as a refusal (%r), so %s was recorded "
                        "instead" % (NEGATION_RE.search(action).group(0), pairs[f])))
                out.append(pairs[f])
            else:
                out.append(f)
        return out

    def _fact_allowed(self, fact):
        if not isinstance(fact, str) or not FACT_RE.match(fact):
            return False, "not a snake_case fact id"
        if self.has(fact):
            return False, "already recorded on day %d" % self.day_of(fact)
        for a, b in self.w["contradictions"]:
            if fact == a and self.has(b):
                return False, "contradicts %s, recorded on day %d" % (b, self.day_of(b))
            if fact == b and self.has(a):
                return False, "contradicts %s, recorded on day %d" % (a, self.day_of(a))
        return True, ""

    def _nudge(self, patch, key, attr, lo, hi):
        d = patch.get(key)
        if d in (None, 0):
            return []
        if not isinstance(d, int) or abs(d) > 2:
            self.rejected.append((key, "delta %r is not an integer within 2" % (d,)))
            return []
        before = getattr(self, attr)
        setattr(self, attr, max(lo, min(hi, before + d)))
        after = getattr(self, attr)
        return ["%s %d->%d" % (attr, before, after)] if after != before else []
