"""One turn: track what was done, apply it under the engine's rules, narrate
the world that results, then check the narration against the ledger.

    action -> TRACKER -> patch -> Ledger.apply -> NARRATOR -> consistency

The tracker and the narrator never see each other's output. The ledger is the
only thing that passes between them, which is what makes the narration a
function of what the player did rather than of what was last said.
"""
from . import consistency, llm, narrate, track


def turn(prov, led, action, tag="", force_advance=False):
    patch = llm.parse_json(prov.complete("track%s" % tag,
                                         track.build_prompt(led, action),
                                         max_tokens=500))
    if not isinstance(patch, dict):
        patch = {}
    changes = led.apply(patch, action)
    rejected_now = list(led.rejected)
    reply = llm.parse_json(prov.complete("narrate%s" % tag,
                                         narrate.build_prompt(led, action, changes),
                                         max_tokens=500))
    text = (reply.get("narration") or "").strip() if isinstance(reply, dict) else ""
    if not text:
        raise ValueError("the narrator returned no narration")
    flags = consistency.check(text, led)
    record = {
        "day": led.day,
        "action": action,
        "patch": patch,
        "changes": changes,
        "narration": text,
        "flags": flags,
        "ledger": led.as_dict(),
    }
    # The calendar is engine state. In the scripted session one action is one
    # day, so the day is not left to the tracker's judgement. Live run 1 let
    # the model decide and it spent three turns on day 0, which put the
    # narrator in the boxcar while the script had reached the street.
    if force_advance or patch.get("advance_day"):
        led.advance_day()
    record["rejected_total"] = len(rejected_now)
    return record
