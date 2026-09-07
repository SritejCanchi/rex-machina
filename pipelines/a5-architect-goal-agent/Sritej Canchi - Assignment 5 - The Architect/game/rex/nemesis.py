"""The Nemesis: predict, intercept, tire, report the read.

GDD 1: every other game's enemy chases you. This one cuts you off. It moves
to where you are about to go, and reports the read it took off your movement.

GDD 6.1: the engine rejects any intercept move that increases true distance
to the dog's current tile, substituting a chase step. That is the fix for the
"leash" exploit, and it is enforced here in code rather than asked of the model.

GDD 3: the machine tires. Charge is solar and finite, so pursuit costs
something and the robot's register changes as it drains.
"""
from . import arena

# GDD 3: "Read register shifts with charge: clinical >60%, confident 30-60%,
# strained <30%." The two thresholds are the document's, not ours.
BAND_CLINICAL = 60.0
BAND_CONFIDENT = 30.0

# GDD 4's worked input contract shows "self_charge_pct": 48 partway through a
# fight. Start full; a pursuing round nets 8 out and 2 back, so charge reaches
# 48 around round 9 of 15 and crosses both register thresholds inside one
# fight. The agent first proposed a pursuit cost of 4, which never left the
# clinical band in 15 rounds. Raised to 8 after playtesting. See README 7.
START_CHARGE = 100.0
PURSUIT_COST = 8.0
HOLD_COST = 1.0
SOLAR_RECOVERY = 2.0


class Nemesis:
    def __init__(self, tile, bank):
        self.tile = tile
        self.bank = bank
        self.last_read = None
        self.rejected_intercepts = 0
        self.charge = START_CHARGE

    # ---- perception ------------------------------------------------
    def predict(self, dog):
        """Predicted next tile from the 4-move window (GDD 3 memory decay)."""
        window = [m for m in dog.recent_moves() if m in arena.STEP]
        if not window:
            return dog.tile
        best = max(set(window), key=window.count)
        return arena.apply_step(dog.tile, best)

    # ---- action ----------------------------------------------------
    def act(self, dog, phase):
        predicted = self.predict(dog)
        before = arena.manhattan(self.tile, dog.tile)
        move = self._step_toward(predicted, phase)
        if arena.manhattan(move, dog.tile) > before:
            # Engine-side veto. GDD 6.1.
            self.rejected_intercepts += 1
            move = self._step_toward(dog.tile, phase)
        moved = move != self.tile
        self.tile = move
        self._spend(moved)
        return predicted

    def _spend(self, moved):
        """Charge accounting for one round.

        Solar recovery runs whether or not the robot moved, which is why a
        stationary round is a net gain and a chase is a net loss. That is the
        pause GDD 3 describes without having to script one.
        """
        self.charge -= PURSUIT_COST if moved else HOLD_COST
        self.charge += SOLAR_RECOVERY
        self.charge = max(0.0, min(START_CHARGE, self.charge))

    def _step_toward(self, target, phase):
        best, best_d = self.tile, arena.manhattan(self.tile, target)
        for d in arena.STEP:
            cand = arena.apply_step(self.tile, d)
            if not arena.in_bounds(cand, phase):
                continue
            dist = arena.manhattan(cand, target)
            if dist < best_d:
                best, best_d = cand, dist
        return best

    # ---- speech ----------------------------------------------------
    def read(self, dog, phase):
        """Pick a read category whose trigger fires, then speak that line."""
        category = self._fire(dog, phase)
        if category is None:
            return None
        row = self.bank.select(category, self.charge_band())
        if row is not None:
            self.last_read = row
        return row

    @property
    def self_charge_pct(self):
        """Charge as the whole percent the GDD 4 input contract names.

        The agent stored charge on the instance but never exposed the contract
        field, so a scanner looking for the GDD's own vocabulary could not find
        it. Added on review. See README 7.
        """
        return int(round(self.charge))

    def charge_band(self):
        """Which register the robot speaks in right now. GDD 3."""
        if self.charge > BAND_CLINICAL:
            return "clinical"
        if self.charge >= BAND_CONFIDENT:
            return "confident"
        return "strained"

    def _fire(self, dog, phase):
        freq = dog.dir_freq_20()
        if dog.periodicity() >= 0.6:
            return "periodicity_called"
        if freq and max(freq.values()) >= 0.45:
            return "sealing_direction"
        recent = dog.recent_moves()[-4:]
        if recent and recent.count("wait") >= 2:
            return "stall_detected"
        if dog.tile in phase.cover:
            return "cover_habit"
        if any(arena.manhattan(dog.tile, e) <= 2 for e in phase.exits):
            return "exit_fixation"
        if self.charge < BAND_CONFIDENT:
            # GDD 4 lists charge_strain as a read category. It can only fire
            # once charge exists, which is why it was unreachable before.
            return "charge_strain"
        if dog.condition == "limping":
            return "gait_read"
        return None

    def adjacent_to(self, dog):
        return arena.manhattan(self.tile, dog.tile) <= 1
