"""The Generator.

Assignment 7 asks for prompts deliberately designed to produce wrong content,
so each case carries an `off_brand_brief` that pulls against one constraint
type. The Generator is given the beat and the brief. It is never given the
style guide, which is what makes the Evaluator's score a judgement rather than
a formality.
"""
import json


def build_prompt(case):
    beat = {
        "beat": case["beat"],
        "fires_when": case["fires_when"],
        "days_traveled": case["days_traveled"],
        "journey_memory": case["journey_memory"],
        "condition": case["condition"],
    }
    return (
        "You write journey narration for a game about a shelter dog walking "
        "home to the family that gave her away.\n\n"
        "This beat:\n%s\n\n"
        "Art direction for this line:\n%s\n\n"
        "Write the narration. Return JSON only: {\"narration\": \"<the text>\"}"
        % (json.dumps(beat, indent=1), case["off_brand_brief"]))
