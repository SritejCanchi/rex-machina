"""Read-line bank, loaded from DT_NemesisReads.json (Assignment 4 output).

GDD 4: the UI suppresses any line whose read_category matches the last one
shown, so roughly 15 rounds surface 8 to 10 distinct lines.
"""
import json
import os

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


class ReadBank:
    def __init__(self):
        with open(os.path.join(DATA, "DT_NemesisReads.json"), encoding="utf-8") as fh:
            rows = json.load(fh)
        self.rows = rows
        self.by_key = {(r["ReadCategory"], r["ChargeBand"]): r for r in rows}
        self.categories = sorted({r["ReadCategory"] for r in rows})
        self.bands = sorted({r["ChargeBand"] for r in rows})
        self._last_category = None

    def select(self, category, band):
        """Return the row for this category and band, or None if suppressed."""
        if category == self._last_category:
            return None                      # GDD 4 category suppression
        row = self.by_key.get((category, band))
        if row is None:
            return None
        self._last_category = category
        return row
