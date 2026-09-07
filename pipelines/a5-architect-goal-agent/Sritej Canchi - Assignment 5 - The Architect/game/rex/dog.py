"""The player dog: position, stamina, move history, approach meter.

GDD 3: stamina drains 1 per round unconditionally, plus 1 for every round
that ends with the robot adjacent. Approach is positional, not accumulated:
approach = 1 - dist(dog, kid) / dist_max.
"""
from . import arena

WINDOW = 4        # GDD 3: the machine forgets, 4-move sliding window
FREQ_SPAN = 20    # GDD 3: direction frequency over 20 moves
START_STAMINA = 15


class Dog:
    def __init__(self, tile, kid_tile):
        self.tile = tile
        self.kid_tile = kid_tile
        self.dist_max = arena.manhattan(tile, kid_tile)
        self.stamina = START_STAMINA
        self.moves = []          # full history, oldest first
        self.condition = "limping"   # GDD 4: the dog arrives limping

    # ---- movement -------------------------------------------------
    def step(self, direction, phase):
        target = arena.apply_step(self.tile, direction)
        if not arena.in_bounds(target, phase):
            return False
        self.tile = target
        self.moves.append(direction)
        return True

    def wait(self):
        self.moves.append("wait")

    # ---- observables the Nemesis is allowed to see ----------------
    def recent_moves(self):
        return self.moves[-WINDOW:]

    def dir_freq_20(self):
        span = [m for m in self.moves[-FREQ_SPAN:] if m in arena.STEP]
        if not span:
            return {d: 0.0 for d in arena.STEP}
        return {d: round(span.count(d) / len(span), 3) for d in arena.STEP}

    def periodicity(self):
        """Highest self-similarity at lags 2..5 over the last 20 moves."""
        span = self.moves[-FREQ_SPAN:]
        if len(span) < 4:
            return 0.0
        best = 0.0
        for lag in range(2, 6):
            pairs = [(span[i], span[i - lag]) for i in range(lag, len(span))]
            if not pairs:
                continue
            hits = sum(1 for a, b in pairs if a == b)
            best = max(best, hits / len(pairs))
        return round(best, 3)

    # ---- meters ---------------------------------------------------
    @property
    def approach(self):
        if self.dist_max == 0:
            return 1.0
        d = arena.manhattan(self.tile, self.kid_tile)
        return max(0.0, min(1.0, 1.0 - d / self.dist_max))

    def drain(self, robot_adjacent):
        self.stamina -= 1
        if robot_adjacent:
            self.stamina -= 1
        return self.stamina
