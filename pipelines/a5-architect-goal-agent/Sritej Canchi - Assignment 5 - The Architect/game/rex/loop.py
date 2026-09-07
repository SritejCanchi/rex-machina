"""The 15-round Act 3 loop.

GDD 3: each round the player moves, the Nemesis perceives, predicts, moves to
intercept, and reports what it learned. Phase gates fire at 33 and 66 percent
approach. Win by filling approach before stamina empties.
"""
from . import arena
from .dog import Dog
from .nemesis import Nemesis
from .reads import ReadBank

MAX_ROUNDS = 15


class Game:
    def __init__(self, seed_moves=None):
        self.arena = arena.Arena()
        first = self.arena.phases[0]
        self.kid_tile = (7, 4)   # 11 tiles from the start, inside a 15-round clock
        self.dog = Dog((0, 0), self.kid_tile)
        self.bank = ReadBank()
        self.nemesis = Nemesis((first.width // 2, first.height // 2), self.bank)
        self.round = 0
        self.phase = first
        self.log = []
        self.outcome = None
        for m in (seed_moves or []):
            self.dog.moves.append(m)

    # ---- one round --------------------------------------------------
    def play_round(self, direction):
        self.round += 1
        if direction == "wait":
            self.dog.wait()
        else:
            self.dog.step(direction, self.phase)

        predicted = self.nemesis.act(self.dog, self.phase)
        row = self.nemesis.read(self.dog, self.phase)
        adjacent = self.nemesis.adjacent_to(self.dog)
        self.dog.drain(adjacent)

        gate = self._check_gate()
        entry = {
            "round": self.round,
            "dog": self.dog.tile,
            "nemesis": self.nemesis.tile,
            "predicted": predicted,
            "read": row["Line"] if row else None,
            "read_category": row["ReadCategory"] if row else None,
            "charge_band": row["ChargeBand"] if row else None,
            "approach": round(self.dog.approach, 3),
            "stamina": self.dog.stamina,
            "adjacent": adjacent,
            "gate": gate,
        }
        self.log.append(entry)
        self._check_end()
        return entry

    def _check_gate(self):
        nxt = self.arena.phase_for(self.dog.approach)
        if nxt.id != self.phase.id:
            self.phase = nxt
            return nxt.id
        return None

    def _check_end(self):
        if self.dog.approach >= 1.0:
            self.outcome = "win"
        elif self.dog.stamina <= 0:
            self.outcome = "loss"
        elif self.round >= MAX_ROUNDS:
            self.outcome = "loss"

    @property
    def over(self):
        return self.outcome is not None
