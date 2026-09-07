"""Arena grid and phase gates.

GDD 3: the arena advances at 33% and 66% approach (yard -> fence gap ->
train yard) and re-lays exits and cover. Phase dressing is loaded from
DT_ArenaPhases.json, produced by the Assignment 4 pipeline.
"""
import json
import os

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def _load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


class Phase:
    def __init__(self, row):
        self.id = row["PhaseID"]
        self.index = row["PhaseIndex"]
        self.name = row["ArenaName"]
        self.low = row["ApproachLow"]
        self.high = row["ApproachHigh"]
        span = row.get("GridSpan", "10x10").lower().split("x")
        self.width, self.height = int(span[0]), int(span[1])
        self.exits = [tuple(t) for t in row["ExitTiles"]]
        self.cover = [tuple(t) for t in row["CoverTiles"]]
        self.light = row["Light"]
        self.sound = row["SoundBed"]
        self.props = row["Props"]
        self.gate = row["GateOpenMoment"]
        self.callback = row.get("CallbackBeat", "")

    def contains(self, approach):
        return self.low <= approach < self.high or (
            self.index == 3 and approach >= self.low)


class Arena:
    """Holds the three phases and reports which one a given approach is in."""

    def __init__(self):
        rows = sorted(_load("DT_ArenaPhases.json"), key=lambda r: r["PhaseIndex"])
        self.phases = [Phase(r) for r in rows]

    def phase_for(self, approach):
        for p in self.phases:
            if p.contains(approach):
                return p
        return self.phases[-1]


def in_bounds(tile, phase):
    x, y = tile
    return 0 <= x < phase.width and 0 <= y < phase.height


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


STEP = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}


def apply_step(tile, direction):
    dx, dy = STEP[direction]
    return (tile[0] + dx, tile[1] + dy)
