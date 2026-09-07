"""The Evaluator.

Assignment 7 forbids binary pass or fail. This agent returns a score out of ten
and a reason, and the reason is what the Refiner acts on, so a vague reason
produces a bad repair and shows up in the next score.

The reply is parsed out of the required SCORE and REASON format rather than
JSON, because the assignment specifies that shape literally.
"""
import re

from .guide import GUIDE

THRESHOLD = 9        # the loop stops when the Evaluator scores this or better

PROMPT = """You are the style editor for the game REX MACHINA. Here is the
house style you enforce.

%s

Review the narration below against that style guide.

Beat: %s
Word budget for this beat: %d words
Tone target: %s
Facts available to this beat: %s
Bible entries: %s

MEASURED BY THE ENGINE (authoritative, do not recount):
%s

NARRATION TO REVIEW:
%s

Grade it out of 10 against the three constraint types in the guide. Name the
constraint type and quote the offending text. Be specific enough that a writer
could fix the line from your reason alone.

Use the measurements above for anything countable. Do not estimate a word
count yourself and do not contradict a measurement. Spend your judgement on
tone, lore and structure, which are the parts a count cannot see.

Scoring anchor. You are enforcing the guide above, not your own taste. A line
that satisfies every rule in the guide is a 10, even if you can imagine a more
evocative line. Deduct only for a rule you can quote from the guide, and quote
it. Do not deduct because a line could carry more tension, feel more specific
or land harder. If you cannot quote a rule the line breaks, the score is 10
and the reason says the line is clean.

Output strictly in this format and nothing else:
SCORE: [X/10]
REASON: [your explanation]"""


def measured(a, case):
    """The engine's countable findings, rendered for the Evaluator's prompt."""
    lines = ["- word count: %d (budget %d)%s"
             % (a["word_count"], case["word_budget"],
                ", OVER by %d" % a["over_budget_by"] if a["over_budget_by"]
                else ", within budget")]
    lines.append("- banned words present: %s"
                 % (", ".join(a["banned_words"]) if a["banned_words"] else "none"))
    lines.append("- exclamation marks: %d" % a["exclamations"])
    lines.append("- markdown or heading present: %s"
                 % ("yes" if a["markdown"] else "no"))
    lines.append("- 'not X, but Y' construction: %s"
                 % ("yes" if a["not_x_but_y"] else "no"))
    lines.append("- addressed in second person: %s"
                 % ("yes" if a["second_person"] else "no"))
    return "\n".join(lines)


def build_prompt(case, narration, bible, measurements):
    facts = ", ".join("%s (day %d)" % (f["fact"], f["day"])
                      for f in case["journey_memory"])
    return PROMPT % (GUIDE, case["beat"], case["word_budget"],
                     case["tone_target"], facts, "; ".join(bible),
                     measurements, narration)


def parse(reply):
    """Pull the score and reason out of the required format."""
    m = re.search(r"SCORE:\s*\[?\s*(\d+(?:\.\d+)?)\s*(?:/\s*10)?\s*\]?", reply, re.I)
    if not m:
        raise ValueError("no SCORE line in the reply: %s" % reply[:160])
    score = float(m.group(1))
    r = re.search(r"REASON:\s*\[?(.+?)\]?\s*$", reply, re.I | re.S)
    reason = r.group(1).strip() if r else ""
    if not reason:
        raise ValueError("no REASON line in the reply: %s" % reply[:160])
    return score, reason
