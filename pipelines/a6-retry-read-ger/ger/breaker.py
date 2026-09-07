"""The Circuit Breaker.

GDD 6 constraint 5: graceful degradation. "A dropped request costs flavor,
never a frame." The loop is allowed three attempts. It stops early when it can
see it is not making progress, and it stops immediately when the provider
itself fails, because retrying a dead key is not self-correction.

When it trips, the row still ships. It ships with an authored fallback line and
a Provenance value that says so, so nothing downstream has to guess whether a
line came from the model.
"""

MAX_ATTEMPTS = 3          # one generation plus two repairs

# Authored per gate, past tense, inside the same rules the model is held to.
# These are the "authored fallback" the GDD promises, written once, by hand.
FALLBACK = {
    "yard": "Last run ended in the open yard. No cover taken.",
    "fence_gap": "Last run ended at the fence gap. Repeated left.",
    "train_yard": "Last run ended in the train yard. Legs gave out.",
}


class Tripped(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


class Breaker:
    def __init__(self, case):
        self.case = case
        self.attempts = []          # list of (line, failures)
        self.reason = None

    def record(self, line, failures):
        self.attempts.append((line, failures))

    def should_stop(self):
        """True when another model call is not worth making."""
        # Order matters. A specific reason is more useful to a reader than
        # "budget spent", so the no-progress checks run first.
        if len(self.attempts) >= 2:
            last, prev = self.attempts[-1], self.attempts[-2]
            if last[0].strip().lower() == prev[0].strip().lower():
                self.reason = "refiner returned the same line twice"
                return True
            if len(self.attempts) >= 3 and self._same_rules(last, prev):
                self.reason = "same rule failing on consecutive repairs"
                return True
        if len(self.attempts) >= MAX_ATTEMPTS:
            self.reason = "attempt budget of %d exhausted" % MAX_ATTEMPTS
            return True
        return False

    @staticmethod
    def _same_rules(a, b):
        return set(r for r, _ in a[1]) == set(r for r, _ in b[1])

    def provider_failed(self, err):
        self.reason = "provider error, no retry: %s" % str(err).splitlines()[0]

    def fallback(self):
        return FALLBACK[self.case["prior_attempt"]]
