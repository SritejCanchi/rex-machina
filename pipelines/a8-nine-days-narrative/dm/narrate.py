"""The NARRATOR agent: the Dungeon Master voice.

It receives the whole ledger every turn, so it cannot forget a tracked fact,
and the house style is the one Assignment 7 enforced. It is told to answer the
ledger rather than the last thing typed, which is the difference between a
reactive narrator and a chat bot with a memory.
"""
import json

STYLE = """Second person, addressed to the dog. Two or three sentences, never
more than 45 words. Plain and concrete: the feeling comes from the object
described, never from a word naming the feeling. No uplift. The dog has no
name and never speaks. Never use the words destiny, journey, heart, soul or
forever. Do not invent people, places or events that are not in the ledger or
the scene."""

PROMPT = """You are the narrator of a text game about a shelter dog walking
home over nine days.

%s

THE SCENE
Day %d, %s. %s

THE LEDGER. This is everything that has happened to her. Your narration must
be consistent with all of it, and it must be shaped by it rather than by the
last line the player typed.
%s

WHAT JUST CHANGED
%s

THE PLAYER'S ACTION
"%s"

Narrate the result. Where the ledger makes this moment different from how it
would read for a different dog, let that show without explaining it.

Return JSON only: {"narration": "<the text>"}"""


def build_prompt(led, action, changes):
    scene = led.scene()
    return PROMPT % (STYLE, led.day, scene["place"], scene["sees"],
                     json.dumps(led.as_dict(), indent=1),
                     ", ".join(changes) if changes else "nothing in the ledger",
                     action)
