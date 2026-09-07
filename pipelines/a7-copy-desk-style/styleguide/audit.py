"""A deterministic audit that runs beside the Evaluator and never gates it.

Assignment 7 forbids binary pass or fail grading, and the loop obeys that: the
Evaluator's score is the only thing that decides whether another repair runs.
This module exists so the README can say something honest about how well a
scored judgement tracks the countable parts of the guide. It measures the three
constraints a machine can measure exactly, and the run reports where the score
and the count disagree.
"""
import re

from .guide import BANNED_WORDS

MARKDOWN = [r"^#", r"\*\*", r"^\s*[-*]\s", r"^\s*\d+\.\s"]


def words(text):
    return re.findall(r"[A-Za-z'’-]+", text)


def audit(text, case):
    """Countable facts about one line. No verdict, just measurements."""
    n = len(words(text))
    low = text.lower()
    return {
        "word_count": n,
        "over_budget_by": max(0, n - case["word_budget"]),
        "banned_words": [w for w in BANNED_WORDS
                         if re.search(r"\b%s\b" % w, low)],
        "exclamations": text.count("!"),
        "markdown": any(re.search(p, text, re.M) for p in MARKDOWN),
        "not_x_but_y": bool(re.search(r"\bnot\s+[^.,;]{1,40},\s*but\b", low)),
        "second_person": bool(re.search(r"\byou\b|\byour\b", low)),
    }


def clean(a):
    """True when nothing countable is wrong. Used for reporting, not gating."""
    return (a["over_budget_by"] == 0 and not a["banned_words"]
            and a["exclamations"] == 0 and not a["markdown"]
            and not a["not_x_but_y"] and a["second_person"])
