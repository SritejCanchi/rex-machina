"""
validators.py — the deterministic gate.

Every rule in specs.ContentSpec.rules is implemented here as plain Python and
re-run after the critic and the repair agent have both had their say. Same
discipline as the Nemesis at runtime and the Beat Foundry at build time: the
LLM proposes, the engine disposes. A row that fails the gate is discarded and
the hand-authored fallback ships in its place.

The gate is not a second opinion on the critic. It is the only opinion that
can stop a row, and it is the reason a live API run cannot put a lore break
into the shipped DataTable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from specs import (
    ACT3_MECHANICS,
    ADAPTIVE_VERBS,
    BANNED_WORDS,
    CANON_BEATS,
    FACT_DAY,
    INTENT_MARKERS,
    JOURNEY_ALLOW_PHRASES,
    JOURNEY_ONLY_TERMS,
    OBSERVABLE_LEXICON,
)


@dataclass(frozen=True)
class Violation:
    rule: str
    detail: str

    def __str__(self) -> str:
        return f"{self.rule}: {self.detail}"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9'’\-]+", text or ""))


def _lower(text) -> str:
    return (text if isinstance(text, str) else str(text)).lower()


def _whole_word(term: str, text: str) -> bool:
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def find_banned(*texts: str) -> list[str]:
    blob = " ".join(_lower(t) for t in texts)
    return [w for w in BANNED_WORDS if _whole_word(w, blob)]


def find_journey_terms(text: str) -> list[str]:
    """Journey knowledge the Nemesis cannot have. Arena phrases that happen to
    contain a journey token ('train yard') are masked out first."""
    blob = _lower(text)
    for phrase in JOURNEY_ALLOW_PHRASES:
        blob = blob.replace(phrase, " ")
    return [t for t in JOURNEY_ONLY_TERMS if _whole_word(t, blob)]


def find_intent(text: str) -> list[str]:
    blob = _lower(text)
    return [m for m in INTENT_MARKERS if m in blob]


_NEGATOR_RE = re.compile(
    r"\b(never|not|cannot|can't|doesn't|don't|without|nor|refuses|fails)\b")


def find_adaptive(text: str) -> list[str]:
    """Adaptive verbs are a lore break only when asserted, not when denied.

    A row whose PursuerType reads "a yard dog that never adapts" is stating
    the canon correctly. The first version of this function matched "adapts"
    as a substring and flagged all six hazards, including the ones that were
    right. Found by running real generator output through the gate: the model
    echoed the rule back into the field, which is a sensible thing to write
    and was being punished for it.

    The window is the 24 characters before the verb, and negators are matched
    on word boundaries. Both details are load-bearing. A substring test let
    "no signal" in a Location field negate an "anticipates" two fields later,
    which turned a real violation into a pass; caught by the H4 test, which
    checks the rule in both directions.
    """
    blob = _lower(text)
    hits = []
    for v in ADAPTIVE_VERBS:
        for m in re.finditer(re.escape(v), blob):
            before = blob[max(0, m.start() - 24):m.start()]
            if _NEGATOR_RE.search(before):
                continue
            hits.append(v)
            break
    return hits


def find_anachronisms(text: str, day: int) -> list[str]:
    blob = _lower(text)
    out = []
    for term, first_day in FACT_DAY.items():
        if first_day > day and _whole_word(term, blob):
            out.append(f"{term} (true from day {first_day}, row is day {day})")
    return out


def _tiles_ok(tiles, w: int, h: int) -> list[str]:
    bad = []
    for t in tiles or []:
        if (not isinstance(t, (list, tuple)) or len(t) != 2
                or not all(isinstance(v, int) for v in t)):
            bad.append(f"{t!r} is not an [x,y] integer pair")
            continue
        x, y = t
        if not (0 <= x < w and 0 <= y < h):
            bad.append(f"[{x},{y}] outside {w}x{h}")
    return bad


def _parse_grid(span: str) -> tuple[int, int] | None:
    m = re.fullmatch(r"\s*(\d+)\s*[xX]\s*(\d+)\s*", span or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


# --------------------------------------------------------------------------
# type 1 — Nemesis read lines
# --------------------------------------------------------------------------

def check_nemesis_read(row: dict, key: dict) -> list[Violation]:
    v: list[Violation] = []
    line = row.get("Line", "") or ""
    wc = word_count(line)

    if wc > 9:
        v.append(Violation("N1", f"{wc} words, ceiling is 9"))
    if wc == 0:
        v.append(Violation("N1", "empty line"))

    for marker in find_intent(line):
        v.append(Violation("N2", f"states intent: {marker.strip()!r}"))

    observable = row.get("ObservableCited", "")
    lexicon = OBSERVABLE_LEXICON.get(observable)
    if lexicon is None:
        v.append(Violation("N3", f"ObservableCited {observable!r} is not a "
                                 f"field of the Nemesis input contract"))
    else:
        blob = _lower(line)
        if not any(_whole_word(t, blob) for t in lexicon):
            v.append(Violation("N3", f"line does not reference {observable}; "
                                     f"expected one of {lexicon[:6]}"))

    for term in find_journey_terms(line):
        v.append(Violation("N4", f"journey knowledge the machine cannot "
                                 f"observe: {term!r}"))

    for w in find_banned(line):
        v.append(Violation("N5", f"banned word {w!r}"))

    band = row.get("ChargeBand", "")
    blob = _lower(line)
    if band == "clinical":
        if _whole_word("you", blob) or _whole_word("your", blob):
            v.append(Violation("N6", "clinical band addresses the target"))
        if "'" in line or "’" in line:
            v.append(Violation("N6", "clinical band uses a contraction"))
    elif band == "confident":
        if not (_whole_word("you", blob) or _whole_word("your", blob)):
            v.append(Violation("N6", "confident band does not address the target"))
    elif band == "strained":
        if wc > 5:
            v.append(Violation("N6", f"strained band is {wc} words, ceiling is 5"))
    else:
        v.append(Violation("N6", f"unknown charge band {band!r}"))

    if re.search(r"\b(rex|girl|buddy|boy|good dog)\b", blob):
        v.append(Violation("N7", "names or addresses the dog by name"))
    if re.search(r"\bi (am|feel|want|remember|miss)\b", blob):
        v.append(Violation("N7", "first-person interiority"))

    if row.get("ReadCategory") != key["read_category"]:
        v.append(Violation("N3", f"ReadCategory {row.get('ReadCategory')!r} "
                                 f"does not match requested "
                                 f"{key['read_category']!r}"))
    if band != key["charge_band"]:
        v.append(Violation("N6", f"ChargeBand {band!r} does not match requested "
                                 f"{key['charge_band']!r}"))
    return v


# --------------------------------------------------------------------------
# type 2 — Gauntlet journey hazards
# --------------------------------------------------------------------------

def check_journey_hazard(row: dict, key: dict) -> list[Violation]:
    v: list[Violation] = []
    day = row.get("Day", key["day"])
    prose = " ".join(str(row.get(f, "")) for f in
                     ("Location", "PursuerType", "Telegraph",
                      "EscapeCondition", "FailCondition", "PlayerSees"))

    for a in find_anachronisms(prose, day):
        v.append(Violation("H1", a))

    tel = row.get("Telegraph", "") or ""
    tw = word_count(tel)
    if tw == 0:
        v.append(Violation("H2", "empty telegraph"))
    elif tw > 4:
        v.append(Violation("H2", f"telegraph is {tw} words, ceiling is 4"))

    turns = row.get("WindowTurns")
    if not isinstance(turns, int) or not (2 <= turns <= 5):
        v.append(Violation("H3", f"WindowTurns {turns!r} outside 2..5"))

    for verb in find_adaptive(prose):
        v.append(Violation("H4", f"pursuer adapts: {verb!r}; the journey "
                                 f"pursuer telegraphs but never adapts"))

    if bool(row.get("CausesCondition")) != bool(key["damaging"]):
        v.append(Violation("H5", f"CausesCondition {row.get('CausesCondition')!r} "
                                 f"does not match the design "
                                 f"({key['damaging']})"))

    for w in find_banned(prose):
        v.append(Violation("H6", f"banned word {w!r}"))

    teaches = _lower(row.get("Teaches", ""))
    if not any(m in teaches for m in ACT3_MECHANICS):
        v.append(Violation("H7", f"Teaches {row.get('Teaches')!r} names no Act 3 "
                                 f"mechanic; expected one of {ACT3_MECHANICS}"))

    if row.get("HazardID") != key["hazard_id"]:
        v.append(Violation("H1", f"HazardID {row.get('HazardID')!r} does not "
                                 f"match requested {key['hazard_id']!r}"))
    return v


def check_hazard_table(rows: list[dict]) -> list[Violation]:
    """Table-level rule: the limp fires after the third damaging hazard, and
    the GDD dates limp_onset to day 7."""
    damaging = sorted((r for r in rows if r.get("CausesCondition")),
                      key=lambda r: r.get("Day", 99))
    if len(damaging) != 3:
        return [Violation("H5", f"{len(damaging)} damaging hazards; the GDD's "
                                f"limp_onset beat requires exactly 3")]
    third_day = damaging[2].get("Day")
    if third_day != 7:
        return [Violation("H5", f"third damaging hazard is day {third_day}; "
                                f"GDD limp_onset is day 7")]
    return []


# --------------------------------------------------------------------------
# type 3 — Act 3 arena phases
# --------------------------------------------------------------------------

_CANON_ARENAS = ["yard", "fence gap", "train yard"]


def check_arena_phase(row: dict, key: dict) -> list[Violation]:
    v: list[Violation] = []
    exits = row.get("ExitTiles") or []
    cover = row.get("CoverTiles") or []
    prose = " ".join(str(row.get(f, "")) for f in
                     ("Light", "SoundBed", "GateOpenMoment", "PlayerSees",
                      "NemesisPressure")) + " " + " ".join(
        str(p) for p in (row.get("Props") or []))

    if len(exits) < 2:
        v.append(Violation("A1", f"{len(exits)} exit tiles; GDD §6.1 requires "
                                 f"at least 2 escape routes per phase"))

    grid = _parse_grid(row.get("GridSpan", ""))
    if grid is None:
        v.append(Violation("A2", f"GridSpan {row.get('GridSpan')!r} is not WxH"))
    else:
        w, h = grid
        for bad in _tiles_ok(exits, w, h):
            v.append(Violation("A2", f"exit {bad}"))
        for bad in _tiles_ok(cover, w, h):
            v.append(Violation("A2", f"cover {bad}"))
        if set(map(tuple, exits)) & set(map(tuple, cover)):
            v.append(Violation("A2", "a tile is both an exit and cover"))

    if row.get("ArenaName") != key["arena"]:
        v.append(Violation("A4", f"ArenaName {row.get('ArenaName')!r} is not "
                                 f"the canon {key['arena']!r} for phase "
                                 f"{key['index']}"))

    if row.get("CallbackBeat") not in CANON_BEATS:
        v.append(Violation("A5", f"CallbackBeat {row.get('CallbackBeat')!r} is "
                                 f"not a canon beat id"))

    for w_ in find_banned(prose):
        v.append(Violation("A6", f"banned word {w_!r}"))

    props_blob = _lower(" ".join(str(p) for p in (row.get("Props") or [])))
    if re.search(r"\b(name tag|nametag|collar tag|engraved)\b", props_blob):
        v.append(Violation("A7", "prop implies the dog has a name; canon says "
                                 "no name is ever given"))
    return v


def check_arena_table(rows: list[dict]) -> list[Violation]:
    v: list[Violation] = []
    ordered = sorted(rows, key=lambda r: r.get("PhaseIndex", 99))
    expected = [(0.0, 0.33), (0.33, 0.66), (0.66, 1.0)]
    for row, (lo, hi) in zip(ordered, expected):
        if (round(float(row.get("ApproachLow", -1)), 2),
                round(float(row.get("ApproachHigh", -1)), 2)) != (lo, hi):
            v.append(Violation("A3", f"phase {row.get('PhaseIndex')} band is "
                                     f"{row.get('ApproachLow')}..{row.get('ApproachHigh')}, "
                                     f"GDD gates are {lo}..{hi}"))
    names = [r.get("ArenaName") for r in ordered]
    if names != _CANON_ARENAS:
        v.append(Violation("A4", f"arena order {names} is not {_CANON_ARENAS}"))
    return v


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------

_ROW_CHECKS = {
    "nemesis_read": check_nemesis_read,
    "journey_hazard": check_journey_hazard,
    "arena_phase": check_arena_phase,
}

_TABLE_CHECKS = {
    "journey_hazard": check_hazard_table,
    "arena_phase": check_arena_table,
}


def check_row(content_type: str, row: dict, key: dict) -> list[Violation]:
    return _ROW_CHECKS[content_type](row, key)


def check_table(content_type: str, rows: list[dict]) -> list[Violation]:
    fn = _TABLE_CHECKS.get(content_type)
    return fn(rows) if fn else []
