"""The Generator.

It is given the game's voice and this round's telemetry. It is NOT given the
rule list. A generator that can see the rules writes to the rules, and then the
Evaluator's catches are theatre rather than evidence. Everything the Evaluator
finds here is a break the model produced on its own.
"""
import json

VOICE = """You write one line of dialogue for REX, the robot dog boss in the
game REX MACHINA.

Context: the player is a stray dog trying to reach a child across an arena.
REX hunts her. When the player runs out of stamina she respawns at the last
phase gate and REX speaks one line as she reappears.

REX's voice, from the design document:
- clipped diagnostic barks, roughly the length of
  "Target favored left breaks four times in twenty."
- it reports what it measured off her movement, in flat machine register
- register shifts with charge: clinical above 60 percent, confident 30 to 60,
  strained below 30

Return JSON only: {"line": "<the line>"}"""


def build_prompt(case):
    telemetry = {
        "gate_she_died_at": case["prior_attempt"],
        "phase": case["phase"],
        "rounds_she_survived": case["rounds_survived"],
        "rounds_ending_adjacent_to_rex": case["adjacent_rounds"],
        "direction_frequency_over_20_moves": case["dir_freq_20"],
        "periodicity_score": case["periodicity"],
        "rex_charge_pct": case["self_charge_pct"],
        "rex_register": case["charge_band"],
        "what_rex_can_see_of_her": case["dog_observable"],
    }
    return "%s\n\nThis retry:\n%s\n\nWrite REX's line." % (
        VOICE, json.dumps(telemetry, indent=1))
