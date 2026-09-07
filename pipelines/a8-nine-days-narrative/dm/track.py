"""The TRACKER agent: what the player did, as a patch to the ledger.

It never writes narration and it never sees the narrator's output. Its only
job is to turn one free-text action into structured change, so the ledger
updates from what the player did rather than from what the story said.

Its patch is a proposal. `Ledger.apply` decides what survives.
"""
import json

PROMPT = """You track state for a text game. The player is a dog walking home.

THE WORLD
%s

WHERE SHE IS NOW
Day %d, %s. %s

THE LEDGER AS IT STANDS
%s

FACT IDS THIS WORLD ALREADY KNOWS (prefer these; you may coin a new one in
the same snake_case style if nothing fits)
%s

THE PLAYER JUST DID THIS
"%s"

Record what that action changed. Only record what the action actually did.
Do not record intentions, and do not record anything the player only looked at.

Return JSON only:
{"add_facts": ["fact_id"], "set_flags": {"flag_name": true},
 "hunger_delta": 0, "trust_delta": 0, "condition": null,
 "advance_day": false, "why": "one short sentence"}

hunger_delta and trust_delta are integers from -2 to 2. condition is one of
"sound", "limping", "hurt", or null for no change. advance_day is true only if
the action ends the day."""


def build_prompt(led, action):
    w = led.w
    scene = led.scene()
    return PROMPT % (w["premise"], led.day, scene["place"], scene["sees"],
                     json.dumps(led.as_dict(), indent=1),
                     ", ".join(w["known_facts"]), action)
