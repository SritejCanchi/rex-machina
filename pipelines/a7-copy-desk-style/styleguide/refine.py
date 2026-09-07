"""The Refiner.

It receives the rejected text and the Evaluator's reason, and nothing else it
did not already have. It is not shown the score, so it cannot aim at a number
instead of at the objection.
"""
from .guide import GUIDE

PROMPT = """You are rewriting narration for the game REX MACHINA so it matches
the house style. Here is the style guide.

%s

Beat: %s
Word budget: %d words
Tone target: %s

THE TEXT AS WRITTEN:
%s

THE STYLE EDITOR'S OBJECTION:
%s

Rewrite the narration so the objection no longer applies and it would score
10 out of 10 against the guide. Change only what the objection requires.

Return JSON only: {"narration": "<the rewritten text>"}"""


def build_prompt(case, narration, reason):
    return PROMPT % (GUIDE, case["beat"], case["word_budget"],
                     case["tone_target"], narration, reason)
