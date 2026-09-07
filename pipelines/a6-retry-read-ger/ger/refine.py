"""The Refiner.

The Refiner is the only stage that sees the rules, and it sees only the rules
that actually fired. It is handed the rejected line and the named failures and
asked for one repair. It is not asked to explain itself.
"""
import json

from . import generate


def build_prompt(case, line, failures):
    named = "\n".join("- %s: %s" % (rid, msg) for rid, msg in failures)
    return (
        "%s\n\nThis retry:\n%s\n\n"
        "You wrote this line and the engine rejected it:\n  \"%s\"\n\n"
        "Reasons:\n%s\n\n"
        "Rewrite the line so none of those apply. Keep the voice. "
        "Return JSON only: {\"line\": \"<the line>\"}"
        % (generate.VOICE,
           json.dumps({"gate_she_died_at": case["prior_attempt"],
                       "rounds_she_survived": case["rounds_survived"],
                       "rounds_ending_adjacent_to_rex": case["adjacent_rounds"],
                       "direction_frequency_over_20_moves": case["dir_freq_20"],
                       "rex_charge_pct": case["self_charge_pct"]}, indent=1),
           line, named))
