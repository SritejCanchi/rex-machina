"""
tools/build_fallbacks.py — emit data/fallbacks.json.

Every row here is hand-authored. These are what ship when a generated row
fails the gate, and they double as the tone exemplars the critic is asked to
measure drift against. Regenerate with:

    python tools/build_fallbacks.py

The script computes ReadID and WordCount rather than trusting a human to count,
because N1 and N6 are word-count rules and a miscount in the fallback would put
a gate failure into the very rows that exist to survive the gate.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from specs import CHARGE_BANDS, READ_CATEGORIES  # noqa: E402


def wc(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9'’\-]+", text))


# --------------------------------------------------------------------------
# type 1 — 24 read lines, 8 categories x 3 charge bands
# clinical  : telemetry, no second person, no contractions
# confident : addresses the target as "you"
# strained  : five words or fewer
# --------------------------------------------------------------------------

READ_LINES = {
    "sealing_direction": {
        "clinical":  "Target favored left breaks four times in twenty.",
        "confident": "You broke left four times in twenty.",
        "strained":  "Left again. Twenty moves.",
    },
    "cover_habit": {
        "clinical":  "Three of the last five rounds ended in cover.",
        "confident": "You keep ending your rounds behind cover.",
        "strained":  "Cover again. Same crate.",
    },
    "exit_fixation": {
        "clinical":  "Two consecutive runs at the same exit tile.",
        "confident": "You ran that same gap twice.",
        "strained":  "Same exit. Twice.",
    },
    "periodicity_called": {
        "clinical":  "The pattern repeats on a five beat cycle.",
        "confident": "Your loop is five beats long.",
        "strained":  "Loop again. Five beats.",
    },
    "stall_detected": {
        "clinical":  "Two of the last four moves cancelled out.",
        "confident": "You stepped out and stepped back.",
        "strained":  "Stepped back. Twice.",
    },
    "gait_read": {
        "clinical":  "Gait uneven. The back leg lands short.",
        "confident": "Your back leg lands short now.",
        "strained":  "Leg short. Uneven.",
    },
    "charge_strain": {
        "clinical":  "Charge crossed thirty. Reserve draw increased.",
        "confident": "You cost me half my charge.",
        "strained":  "Charge low. Sun gone.",
    },
    "prior_attempt": {
        "clinical":  "The fence was tried last run. It failed.",
        "confident": "You tried the fence already. It held.",
        "strained":  "Fence again. Tried before.",
    },
}


def build_reads() -> dict:
    out = {}
    for cat, observable, trigger in READ_CATEGORIES:
        for band, _rng, _reg in CHARGE_BANDS:
            line = READ_LINES[cat][band]
            out[f"{cat}|{band}"] = {
                "ReadID": f"{cat}__{band}",
                "ReadCategory": cat,
                "ChargeBand": band,
                "Line": line,
                "WordCount": wc(line),
                "ObservableCited": observable,
                "TriggerCondition": trigger,
            }
    return out


# --------------------------------------------------------------------------
# type 2 — 6 journey hazards
# Damaging hazards, in day order: alley_chase (1), train_leap (3),
# fence_line (7). The third lands on day 7, which is where the GDD dates
# limp_onset. That is rule H5 and it is why fence_line exists.
# --------------------------------------------------------------------------

HAZARDS = [
    {
        "HazardID": "shelter_gate", "Day": 0, "Act": 1,
        "Location": "the kennel yard, chain gate, a gravel apron before open pavement",
        "PursuerType": "a kennel hand with a slip lead, not angry, just quick",
        "Telegraph": "lead swinging wide",
        "WindowTurns": 3, "TileSpan": "6x8",
        "EscapeCondition": "reach the gap in the gate on the beat the lead swings away",
        "FailCondition": "the lead lands on the collar and the run restarts at the pen",
        "CausesCondition": False,
        "Teaches": "telegraph reading",
        "PlayerSees": "The hand lifts. The lead swings. For one beat there is nothing between the gap and the gravel.",
    },
    {
        "HazardID": "alley_chase", "Day": 1, "Act": 1,
        "Location": "a brick alley behind a row of shops, bins down both sides",
        "PursuerType": "a loose yard dog, bigger, faster in a straight line and only in a straight line",
        "Telegraph": "lunging right",
        "WindowTurns": 3, "TileSpan": "8x6",
        "EscapeCondition": "put two bins between the pursuer and the dog, then break the opposite way",
        "FailCondition": "taken on the shoulder; the run continues on a shorter stamina bar",
        "CausesCondition": True,
        "Teaches": "cover use",
        "PlayerSees": "It commits to the right. The bins on the left stop being scenery.",
    },
    {
        "HazardID": "road_crossing", "Day": 2, "Act": 1,
        "Location": "four lanes, no signal, a raised kerb on the far side",
        "PursuerType": "none; the traffic is the hazard and it is not interested",
        "Telegraph": "gap opening left",
        "WindowTurns": 2, "TileSpan": "10x4",
        "EscapeCondition": "cross on the second gap, because the first one closes early",
        "FailCondition": "driven back to the kerb; one full cycle is lost and the light is going",
        "CausesCondition": False,
        "Teaches": "window timing",
        "PlayerSees": "Two gaps arrive. The first is wide and short. The second is narrow and long enough.",
    },
    {
        "HazardID": "train_leap", "Day": 3, "Act": 2,
        "Location": "the freight line at the edge of the yard, gravel siding, cars moving at a walk",
        "PursuerType": "a yard dog working the siding, close but committed to the ground",
        "Telegraph": "cutting the gravel",
        "WindowTurns": 4, "TileSpan": "12x5",
        "EscapeCondition": "match the boxcar for three tiles and commit to the open door",
        "FailCondition": "the door passes; the next car is a flat and the approach restarts",
        "CausesCondition": True,
        "Teaches": "gap commitment",
        "PlayerSees": "The door is a moving hole. It is open for four steps and then it is a wall again.",
    },
    {
        "HazardID": "diner_yard", "Day": 6, "Act": 2,
        "Location": "the back lot of a roadside diner, one propped door, a stack of crates",
        "PursuerType": "none; a cook who has not decided about the dog yet",
        "Telegraph": "door propping open",
        "WindowTurns": 5, "TileSpan": "7x7",
        "EscapeCondition": "hold inside the window without breaking cover and the tray comes out",
        "FailCondition": "break early and the door shuts; no food, no damage, no second offer",
        "CausesCondition": False,
        "Teaches": "stamina management",
        "PlayerSees": "Nothing is chasing. The cost of running is that the door closes.",
    },
    {
        "HazardID": "fence_line", "Day": 7, "Act": 2,
        "Location": "a chain link run behind the last houses, one gap dug under the bottom rail",
        "PursuerType": "two dogs on the far side, working the wire in step with each other",
        "Telegraph": "pacing the rail",
        "WindowTurns": 3, "TileSpan": "9x4",
        "EscapeCondition": "take the gap on the beat when both dogs are moving the same way",
        "FailCondition": "the wire takes the back leg; the limp starts here and does not clear",
        "CausesCondition": True,
        "Teaches": "pattern breaking",
        "PlayerSees": "Two dogs pacing one wire, in step. In step means there is a beat when neither is at the gap.",
    },
]


# --------------------------------------------------------------------------
# type 3 — 3 arena phases
# Phase 2 reuses the exact exits and cover tiles from the GDD §4 Nemesis input
# contract, so the worked example in the GDD is a real board position.
# Each phase calls back to one journey beat the player has already had.
# --------------------------------------------------------------------------

PHASES = [
    {
        "PhaseID": "phase_yard", "PhaseIndex": 1,
        "ApproachLow": 0.0, "ApproachHigh": 0.33,
        "ArenaName": "yard", "GridSpan": "10x10",
        "ExitTiles": [[0, 4], [9, 7]],
        "CoverTiles": [[3, 3], [6, 5], [4, 7]],
        "Light": "one warm cone from the house, wet grass inside it, everything outside it blue",
        "SoundBed": "a television two rooms away, and a cooling fan that is not a dog",
        "Props": ["a hose coiled on its reel", "a bike on its side",
                  "a low chain fence at the property line",
                  "a rubber ball gone flat with age"],
        "GateOpenMoment": "at 33% the side gate swings and the warm light stops reaching",
        "PlayerSees": "The one shape of ground the dog already knows, and the machine knows it better.",
        "CallbackBeat": "the_street",
        "NemesisPressure": "low; it holds the middle and lets the fence do the work",
    },
    {
        "PhaseID": "phase_fence_gap", "PhaseIndex": 2,
        "ApproachLow": 0.33, "ApproachHigh": 0.66,
        "ArenaName": "fence gap", "GridSpan": "10x10",
        "ExitTiles": [[0, 6], [9, 2]],
        "CoverTiles": [[3, 5], [5, 7]],
        "Light": "no house light past the gate, one neighbour's lamp on a motion timer that keeps guessing wrong",
        "SoundBed": "chain link ringing whenever either animal touches it",
        "Props": ["a chain link run between two yards",
                  "a gap dug under the bottom rail",
                  "a stack of paving slabs", "a lamp pole with a dead sensor"],
        "GateOpenMoment": "at 66% the far panel is already down and the ground turns to ballast",
        "PlayerSees": "The same shape of gap that took the back leg, with the machine standing in it.",
        "CallbackBeat": "limp_onset",
        "NemesisPressure": "rising; it sprints once a phase and pays for it out of charge",
    },
    {
        "PhaseID": "phase_train_yard", "PhaseIndex": 3,
        "ApproachLow": 0.66, "ApproachHigh": 1.0,
        "ArenaName": "train yard", "GridSpan": "10x10",
        "ExitTiles": [[4, 0], [0, 9], [9, 9]],
        "CoverTiles": [[2, 4], [7, 3], [5, 6]],
        "Light": "sodium floods on tall poles, hard shadows that swing when nothing has moved",
        "SoundBed": "an idling engine out of sight, couplings taking up slack one at a time",
        "Props": ["a line of stationary flatcars", "a switch stand with its lamp lit",
                  "ballast gravel", "one boxcar with the door standing open"],
        "GateOpenMoment": "no gate; this phase ends the fight one way or the other",
        "PlayerSees": "An open boxcar door, the same shape that saved the dog once, and this time the machine is in front of it.",
        "CallbackBeat": "train_leap",
        "NemesisPressure": "highest; charge is low, the reads are clipped, and it stops covering both exits",
    },
]


def main() -> int:
    data = {
        "nemesis_read": build_reads(),
        "journey_hazard": {h["HazardID"]: h for h in HAZARDS},
        "arena_phase": {p["PhaseID"]: p for p in PHASES},
    }
    out = Path(__file__).resolve().parents[1] / "data" / "fallbacks.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {out}: "
          f"{len(data['nemesis_read'])} reads, "
          f"{len(data['journey_hazard'])} hazards, "
          f"{len(data['arena_phase'])} phases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
