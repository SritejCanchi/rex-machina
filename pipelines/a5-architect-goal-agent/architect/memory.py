"""Persistent state via markdown.

Class 7 slide 15: the agent records what has been built, what failed, what is
left, and why it chose one approach over another. Slide 16: no databases, just
readable and editable text files that can be fed back into the next session.

Failures matter as much as successes here. A recorded failure is what stops the
next run attempting the same dead end.
"""
import os
from datetime import datetime, timezone

STATE = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "state")

FILES = {"built": "BUILT.md", "failed": "FAILED.md",
         "next": "NEXT.md", "decisions": "DECISIONS.md"}

HEADERS = {
    "built": "# BUILT\n\nFeatures this agent has written into the game.\n",
    "failed": "# FAILED\n\nAttempts that did not survive verification. "
              "The agent reads this before choosing, so it does not repeat them.\n",
    "next": "# NEXT\n\nOpen gaps in GDD priority order, refreshed every run.\n",
    "decisions": "# DECISIONS\n\nWhy the agent picked what it picked.\n",
}


def _path(kind):
    os.makedirs(STATE, exist_ok=True)
    return os.path.join(STATE, FILES[kind])


def read(kind):
    p = _path(kind)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else HEADERS[kind]


def append(kind, block):
    p = _path(kind)
    body = read(kind).rstrip() + "\n\n" + block.rstrip() + "\n"
    open(p, "w", encoding="utf-8").write(body)


def replace(kind, block):
    open(_path(kind), "w", encoding="utf-8").write(
        HEADERS[kind] + "\n" + block.rstrip() + "\n")


def stamp(run_id):
    return "_run %s, %s UTC_" % (
        run_id, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))


def previously_failed():
    """Feature keys the agent has already tried and failed to build."""
    keys = set()
    for line in read("failed").splitlines():
        if line.startswith("## "):
            keys.add(line[3:].strip().split()[0])
    return keys


def previously_built():
    keys = set()
    for line in read("built").splitlines():
        if line.startswith("## "):
            keys.add(line[3:].strip().split()[0])
    return keys
