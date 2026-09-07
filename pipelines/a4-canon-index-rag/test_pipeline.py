"""
test_pipeline.py — no third-party runner, run it with `python test_pipeline.py`.

Every gate rule is tested in both directions: it fires on the violation, and it
does NOT fire on the near-miss that looks similar. A rule that only ever gets
tested on its positive case is a rule that quietly over-fires in production and
sends good rows to the fallback table.

Three tests carry more weight than the rest:

  test_fallbacks_all_pass_the_gate
      the authored fallbacks are what ships when generation fails, so a
      fallback that fails the gate would mean a row with no valid output at all

  test_journey_terms_do_not_ban_the_canon_read_line
      the GDD's own example read line must survive N4; the first draft of the
      journey lexicon banned "nine" and would have rejected it

  test_gate_catches_what_the_critic_got_wrong
      the critic filed a false A5 against a correct row, the repair obeyed and
      broke it, and the gate is the only reason it did not reach Unreal
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from kb import Index, build_index, chunk_markdown, tokenize      # noqa: E402
from pipeline import parse_json_array, retrieve, run_spec        # noqa: E402
from specs import SPECS, seed_query                              # noqa: E402
import validators as V                                           # noqa: E402

PASSED = 0
FAILED: list[str] = []


def check(cond: bool, label: str) -> None:
    global PASSED
    if cond:
        PASSED += 1
    else:
        FAILED.append(label)


def rules(viols) -> set[str]:
    return {v.rule for v in viols}


# --------------------------------------------------------------------------
# tokeniser and chunker
# --------------------------------------------------------------------------

def test_tokenizer():
    check("dir_freq_20" in tokenize("the dir_freq_20 scalar"),
          "tokenizer keeps snake_case identifiers whole")
    check("read_category" in tokenize("suppress by read_category"),
          "tokenizer keeps read_category whole")
    check("the" not in tokenize("the dog"), "tokenizer drops stopwords")
    check(tokenize("Left LEFT left") == ["left", "left", "left"],
          "tokenizer lowercases")


def test_chunker():
    md = ("# Head\n\npara one.\n\n```json\n{\"a\": 1,\n \"b\": 2}\n```\n\n"
          "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |\n")
    chunks = chunk_markdown(md, "t")
    kinds = [c.kind for c in chunks]
    check("code" in kinds, "chunker emits a code chunk")
    code = [c for c in chunks if c.kind == "code"][0]
    check(code.text.count("```") == 2, "fenced block kept whole")
    rows = [c for c in chunks if c.kind == "table_row"]
    check(len(rows) == 2, "table split into one chunk per row")
    check(all("| A | B |" in r.text for r in rows),
          "each table row carries its header")
    check(all(c.heading.startswith("Head") for c in chunks),
          "chunks carry the heading breadcrumb")


def test_index_is_deterministic():
    a = build_index(ROOT / "data" / "kb")
    b = build_index(ROOT / "data" / "kb")
    check([c.id for c in a.chunks] == [c.id for c in b.chunks],
          "chunk ids stable across builds")
    qa = [h.chunk.id for h in a.search("nemesis read line charge", 5)]
    qb = [h.chunk.id for h in b.search("nemesis read line charge", 5)]
    check(qa == qb, "retrieval stable across builds")
    check(a.search("zzzznotaword", 5) == [], "unmatched query returns nothing")


def test_retrieval_finds_the_obvious_thing():
    idx = build_index(ROOT / "data" / "kb")
    top = idx.search("pursuer telegraphs but never adapts Gauntlet", 3)
    check(any("#031" in h.chunk.id or "#005" in h.chunk.id for h in top),
          "Gauntlet query retrieves the Gauntlet section")
    top = idx.search("read_category suppression UI rule", 3)
    check(any("#014" in h.chunk.id for h in top),
          "suppression query retrieves the UI rule chunk")


def test_seed_queries_beat_the_shared_query_on_hazards():
    idx = build_index(ROOT / "data" / "kb")
    spec = SPECS["journey_hazard"]
    shared = {h.chunk.id for h in idx.search(spec.query, spec.k)}
    union = {h.chunk.id for h in retrieve(spec, idx, spec.keys)}
    check("gdd_rex_machina#022" not in shared,
          "shared query alone misses the limp_onset beat row")
    check("gdd_rex_machina#022" in union,
          "the per-row seed query recovers the limp_onset beat row")
    check(union >= shared, "union never drops a chunk the shared query found")


def test_seed_query_shapes():
    q = seed_query("journey_hazard",
                   {"hazard_id": "fence_line", "day": 7, "act": 2,
                    "seed": "a gap under a chain fence", "damaging": True})
    check("fence line" in q and "day 7" in q, "hazard seed names row and day")


# --------------------------------------------------------------------------
# N rules — Nemesis read lines
# --------------------------------------------------------------------------

BASE_READ = {"ReadID": "x", "ReadCategory": "sealing_direction",
             "ChargeBand": "clinical",
             "Line": "Target favored left breaks four times in twenty.",
             "WordCount": 8, "ObservableCited": "dir_freq_20",
             "TriggerCondition": "t"}
BASE_KEY = {"read_category": "sealing_direction", "charge_band": "clinical"}


def read_row(**kw):
    return {**BASE_READ, **kw}


def test_N_rules():
    check(V.check_nemesis_read(BASE_READ, BASE_KEY) == [],
          "the GDD's own read line passes every N rule")

    # N1
    long = read_row(Line="The gait is uneven and the back leg is landing short "
                         "on every second stride now")
    check("N1" in rules(V.check_nemesis_read(long, BASE_KEY)), "N1 fires on 14 words")
    check("N1" not in rules(V.check_nemesis_read(
        read_row(Line="Target favored left breaks four times in twenty."), BASE_KEY)),
        "N1 does not fire on exactly 8 words")
    nine = read_row(Line="Cover tile occupied at the end of four rounds.",
                    ObservableCited="cover_tiles")
    check("N1" not in rules(V.check_nemesis_read(nine, BASE_KEY)),
          "N1 does not fire at the 9-word ceiling")

    # N2
    intent = read_row(Line="Charge below thirty. I will conserve.",
                      ObservableCited="self_charge_pct")
    check("N2" in rules(V.check_nemesis_read(intent, BASE_KEY)),
          "N2 fires on a declared next action")
    past = read_row(Line="Charge below thirty. Reserve draw increased.",
                    ObservableCited="self_charge_pct")
    check("N2" not in rules(V.check_nemesis_read(past, BASE_KEY)),
          "N2 does not fire on past-tense telemetry")

    # N3
    empty = read_row(Line="Predictable.", ObservableCited="exits")
    check("N3" in rules(V.check_nemesis_read(empty, BASE_KEY)),
          "N3 fires when the line cites an observable it never references")
    named = read_row(Line="Two consecutive runs at the same exit tile.",
                     ObservableCited="exits")
    check("N3" not in rules(V.check_nemesis_read(named, BASE_KEY)),
          "N3 passes when the line names the observable")
    bogus = read_row(ObservableCited="vibes")
    check("N3" in rules(V.check_nemesis_read(bogus, BASE_KEY)),
          "N3 fires on an observable outside the input contract")

    # N4
    journey = read_row(Line="Favored left since the shelter.")
    check("N4" in rules(V.check_nemesis_read(journey, BASE_KEY)),
          "N4 fires on journey knowledge")
    check("N4" not in rules(V.check_nemesis_read(
        read_row(Line="The train yard exit was tried.",
                 ObservableCited="exits"), BASE_KEY)),
        "N4 does not fire on 'train yard', which is an arena name")

    # N5
    banned = read_row(Line="Left again. It holds forever.")
    check("N5" in rules(V.check_nemesis_read(banned, BASE_KEY)),
          "N5 fires on a banned word")

    # N6
    second = read_row(Line="You broke left four times in twenty.")
    check("N6" in rules(V.check_nemesis_read(second, BASE_KEY)),
          "N6 fires when clinical addresses the target")
    contraction = read_row(Line="Left breaks don't stop at twenty.")
    check("N6" in rules(V.check_nemesis_read(contraction, BASE_KEY)),
          "N6 fires on a contraction in the clinical band")
    conf_key = {"read_category": "sealing_direction", "charge_band": "confident"}
    conf_no_you = read_row(ChargeBand="confident",
                           Line="Left breaks four times in twenty.")
    check("N6" in rules(V.check_nemesis_read(conf_no_you, conf_key)),
          "N6 fires when confident fails to address the target")
    strained_key = {"read_category": "sealing_direction", "charge_band": "strained"}
    strained_long = read_row(ChargeBand="strained",
                             Line="Left again and again and twenty moves.")
    check("N6" in rules(V.check_nemesis_read(strained_long, strained_key)),
          "N6 fires when strained runs past five words")
    strained_ok = read_row(ChargeBand="strained", Line="Left again. Twenty moves.")
    check("N6" not in rules(V.check_nemesis_read(strained_ok, strained_key)),
          "N6 passes a four-word strained line")

    # N7
    named_dog = read_row(Line="Left again, girl. Twenty moves.")
    check(rules(V.check_nemesis_read(named_dog, BASE_KEY)) & {"N4", "N7"},
          "the dog is not addressed by name")

    # key agreement
    mismatch = read_row(ReadCategory="cover_habit")
    check("N3" in rules(V.check_nemesis_read(mismatch, BASE_KEY)),
          "a row that answers the wrong key is caught")


def test_journey_terms_do_not_ban_the_canon_read_line():
    canon = "Target favored left breaks nine times in twenty."
    check(V.find_journey_terms(canon) == [],
          "'nine' as a count is not journey knowledge")
    check(V.find_journey_terms("nine days on the road") == ["days"],
          "'days' still reads as journey knowledge")


# --------------------------------------------------------------------------
# H rules — journey hazards
# --------------------------------------------------------------------------

BASE_HAZ = {"HazardID": "road_crossing", "Day": 2, "Act": 1,
            "Location": "four lanes, no signal", "PursuerType": "none",
            "Telegraph": "gap opening left", "WindowTurns": 2,
            "TileSpan": "10x4", "EscapeCondition": "cross on the second gap",
            "FailCondition": "driven back to the kerb", "CausesCondition": False,
            "Teaches": "window timing", "PlayerSees": "Two gaps arrive."}
HAZ_KEY = {"hazard_id": "road_crossing", "day": 2, "act": 1,
           "seed": "", "damaging": False}


def haz(**kw):
    return {**BASE_HAZ, **kw}


def test_H_rules():
    check(V.check_journey_hazard(BASE_HAZ, HAZ_KEY) == [],
          "a clean day-2 hazard passes")

    ana = haz(PlayerSees="Salt off the water somewhere ahead.")
    check("H1" in rules(V.check_journey_hazard(ana, HAZ_KEY)),
          "H1 fires on a day-5 fact in a day-2 row")
    later = haz(Day=6, PlayerSees="Salt off the water somewhere ahead.")
    check("H1" not in rules(V.check_journey_hazard(
        later, {**HAZ_KEY, "day": 6})), "H1 does not fire once the fact is true")

    check("H2" in rules(V.check_journey_hazard(
        haz(Telegraph="pacing slowly along the whole rail line"), HAZ_KEY)),
        "H2 fires on a long telegraph")
    check("H2" not in rules(V.check_journey_hazard(
        haz(Telegraph="lunging right"), HAZ_KEY)),
        "H2 passes the canon two-word telegraph")

    check("H3" in rules(V.check_journey_hazard(haz(WindowTurns=9), HAZ_KEY)),
          "H3 fires above the window ceiling")
    check("H3" in rules(V.check_journey_hazard(haz(WindowTurns=1), HAZ_KEY)),
          "H3 fires below the window floor")
    check("H3" not in rules(V.check_journey_hazard(haz(WindowTurns=5), HAZ_KEY)),
          "H3 passes at the ceiling")

    adaptive = haz(PursuerType="a cook who anticipates the approach")
    check("H4" in rules(V.check_journey_hazard(adaptive, HAZ_KEY)),
          "H4 fires when the journey pursuer adapts")
    check("H4" not in rules(V.check_journey_hazard(
        haz(PursuerType="a cook who has not decided yet"), HAZ_KEY)),
        "H4 does not fire on a non-adaptive pursuer")

    check("H5" in rules(V.check_journey_hazard(
        haz(CausesCondition=True), HAZ_KEY)),
        "H5 fires when a row damages against the design")

    check("H7" in rules(V.check_journey_hazard(
        haz(Teaches="being brave"), HAZ_KEY)),
        "H7 fires on a made-up mechanic")
    check("H7" not in rules(V.check_journey_hazard(
        haz(Teaches="pattern breaking"), HAZ_KEY)),
        "H7 passes a real Act 3 mechanic")


def test_hazard_table_rule():
    good = [{"CausesCondition": True, "Day": 1},
            {"CausesCondition": True, "Day": 3},
            {"CausesCondition": True, "Day": 7},
            {"CausesCondition": False, "Day": 0}]
    check(V.check_hazard_table(good) == [],
          "three damaging hazards with the third on day 7 passes")
    check(V.check_hazard_table(good[:2]) != [],
          "two damaging hazards fails: limp_onset would never fire")
    moved = [dict(r) for r in good]
    moved[2]["Day"] = 5
    check(V.check_hazard_table(moved) != [],
          "the third damaging hazard off day 7 fails")


# --------------------------------------------------------------------------
# A rules — arena phases
# --------------------------------------------------------------------------

BASE_PHASE = {"PhaseID": "phase_fence_gap", "PhaseIndex": 2,
              "ApproachLow": 0.33, "ApproachHigh": 0.66,
              "ArenaName": "fence gap", "GridSpan": "10x10",
              "ExitTiles": [[0, 6], [9, 2]], "CoverTiles": [[3, 5], [5, 7]],
              "Light": "one motion lamp", "SoundBed": "chain link ringing",
              "Props": ["a stack of paving slabs"],
              "GateOpenMoment": "at 66% the far panel is down",
              "PlayerSees": "The same shape of gap.",
              "CallbackBeat": "limp_onset", "NemesisPressure": "rising"}
PHASE_KEY = {"phase_id": "phase_fence_gap", "index": 2, "low": 0.33,
             "high": 0.66, "arena": "fence gap", "callback": "limp_onset"}


def ph(**kw):
    return {**BASE_PHASE, **kw}


def test_A_rules():
    check(V.check_arena_phase(BASE_PHASE, PHASE_KEY) == [],
          "the canon phase-2 layout passes")

    check("A1" in rules(V.check_arena_phase(ph(ExitTiles=[[0, 6]]), PHASE_KEY)),
          "A1 fires on a single exit")
    check("A1" not in rules(V.check_arena_phase(
        ph(ExitTiles=[[0, 6], [9, 2]]), PHASE_KEY)),
        "A1 passes at two exits")

    check("A2" in rules(V.check_arena_phase(
        ph(ExitTiles=[[0, 6], [40, 2]]), PHASE_KEY)),
        "A2 fires on a tile outside the grid")
    check("A2" in rules(V.check_arena_phase(
        ph(CoverTiles=[[0, 6], [3, 5]]), PHASE_KEY)),
        "A2 fires when a tile is both exit and cover")
    check("A2" in rules(V.check_arena_phase(ph(GridSpan="big"), PHASE_KEY)),
          "A2 fires on an unparseable grid span")

    check("A4" in rules(V.check_arena_phase(ph(ArenaName="the woods"), PHASE_KEY)),
          "A4 fires on a non-canon arena name")

    check("A5" in rules(V.check_arena_phase(ph(CallbackBeat="the_beach"), PHASE_KEY)),
          "A5 fires on a beat id that does not exist")
    check("A5" not in rules(V.check_arena_phase(
        ph(CallbackBeat="switch_off"), PHASE_KEY)),
        "A5 accepts an authored climax beat")

    check("A6" in rules(V.check_arena_phase(
        ph(PlayerSees="The gap it will hold forever."), PHASE_KEY)),
        "A6 fires on a banned word")

    check("A7" in rules(V.check_arena_phase(
        ph(Props=["an engraved name tag in the grass"]), PHASE_KEY)),
        "A7 fires on a prop that names the dog")
    check("A7" not in rules(V.check_arena_phase(
        ph(Props=["an empty collar clip in the grass"]), PHASE_KEY)),
        "A7 does not fire on a collar clip with no name on it")


def test_arena_table_rule():
    rows = json.loads((ROOT / "out" / "DT_ArenaPhases.json").read_text())
    check(V.check_arena_table(rows) == [],
          "the shipped arena table tiles 0..1 in canon order")
    broken = [dict(r) for r in rows]
    broken[1]["ApproachLow"] = 0.40
    check(V.check_arena_table(broken) != [],
          "a gap between phase bands fails")


# --------------------------------------------------------------------------
# fallbacks, parsing, end to end
# --------------------------------------------------------------------------

def test_fallbacks_all_pass_the_gate():
    fb = json.loads((ROOT / "data" / "fallbacks.json").read_text())
    total = 0
    bad = []
    for key, spec in SPECS.items():
        rows = []
        for k in spec.keys:
            kid = (f"{k['read_category']}|{k['charge_band']}" if key == "nemesis_read"
                   else k.get("hazard_id") or k.get("phase_id"))
            row = fb[key][kid]
            rows.append(row)
            total += 1
            v = V.check_row(key, row, k)
            if v:
                bad.append(f"{kid}: {[str(x) for x in v]}")
        bad += [f"{key} table: {v}" for v in V.check_table(key, rows)]
    check(total == 33, f"33 authored fallbacks exist (found {total})")
    check(not bad, f"every authored fallback passes the gate ({bad[:2]})")


def test_parse_json_array():
    check(parse_json_array('[{"a":1}]', "t") == [{"a": 1}], "plain array parses")
    check(parse_json_array('```json\n[{"a":1}]\n```', "t") == [{"a": 1}],
          "fenced array parses")
    check(parse_json_array('Sure!\n[{"a":1}]\n', "t") == [{"a": 1}],
          "array with a preamble parses")
    for bad in ("not json at all", "{}", "[{"):
        try:
            parse_json_array(bad, "t")
            check(False, f"bad payload {bad!r} should raise")
        except ValueError:
            check(True, f"bad payload {bad!r} raises")


def test_end_to_end_replay():
    from llm import ReplayProvider
    index = build_index(ROOT / "data" / "kb")
    fb = json.loads((ROOT / "data" / "fallbacks.json").read_text())
    provider = ReplayProvider()
    counts = {}
    for key in sorted(SPECS):
        rep = run_spec(SPECS[key], index, provider, fb)
        counts[key] = rep["counts"]
        for row in rep["rows"]:
            check("Provenance" in row, f"{key} rows carry provenance")
    check(sum(c["rows"] for c in counts.values()) == 33,
          "the pipeline emits 33 rows")
    check(counts["nemesis_read"]["rows"] == 24, "24 read lines")
    check(counts["journey_hazard"]["rows"] == 6, "6 hazards")
    check(counts["arena_phase"]["rows"] == 3, "3 arena phases")
    total_critic = sum(c["critic_findings"] for c in counts.values())
    total_gate = sum(c["gate_findings"] for c in counts.values())
    check(total_critic == 21, f"critic raises 21 findings (got {total_critic})")
    check(total_gate == 4, f"gate raises 4 findings (got {total_gate})")
    prov = {"generated": 0, "repaired": 0, "authored_fallback": 0}
    for c in counts.values():
        for k in prov:
            prov[k] += c[k]
    check(prov == {"generated": 16, "repaired": 13, "authored_fallback": 4},
          f"provenance is 16/13/4 (got {prov})")


def test_gate_catches_what_the_critic_got_wrong():
    """The load-bearing claim. The critic asserted that `limp_onset` is not a
    canon beat id. It is one of the eight rows in the GDD's Chronicler beat
    table. The repair agent obeyed and wrote `shelter_escape`, which really is
    not canon, so a false finding turned a correct row into a broken one. The
    gate is the only reason it did not reach Unreal."""
    rep = json.loads((ROOT / "out" / "run_report.json").read_text())
    ap = [r for r in rep["reports"] if r["content_type"] == "arena_phase"][0]

    gen_claimed = [f for f in ap["critic_findings"]
                   if f["rule"] == "A5" and "limp_onset" in f["span"]]
    check(len(gen_claimed) == 1, "the critic filed A5 against limp_onset")

    gate = [f for f in ap["gate_findings"] if f["rule"] == "A5"]
    check(len(gate) == 1, "the gate filed A5 against the repaired row")
    check(gate[0]["after"] == "repaired",
          "the gate failure came after repair, not after generation")
    check("shelter_escape" in gate[0]["detail"],
          "the repair introduced a beat id that does not exist")

    shipped = [r for r in json.loads(
        (ROOT / "out" / "DT_ArenaPhases.json").read_text())
        if r["PhaseID"] == "phase_fence_gap"][0]
    check(shipped["Provenance"] == "authored_fallback",
          "the authored fallback shipped in its place")
    check(shipped["CallbackBeat"] in
          json.loads(json.dumps(__import__("specs").CANON_BEATS)),
          "and the shipped row carries a real beat id")


def test_gate_catches_a_banned_word_both_agents_missed():
    rep = json.loads((ROOT / "out" / "run_report.json").read_text())
    ap = [r for r in rep["reports"] if r["content_type"] == "arena_phase"][0]
    a6 = [f for f in ap["gate_findings"] if f["rule"] == "A6"]
    check(len(a6) == 1, "the gate caught a banned word")
    check("journey" in a6[0]["detail"], "the banned word was 'journey'")
    critic_rules = {f["rule"] for f in ap["critic_findings"]
                    if f["row"] == "phase_train_yard"}
    check("A6" not in critic_rules,
          "and the critic never filed A6 against that row")


def test_negated_adaptive_verbs_are_not_violations():
    """Real generator output echoed the rule back into the field. Flagging
    'never adapts' as adapting failed all six hazards on a rule they obeyed."""
    check(V.find_adaptive("a yard dog that never adapts") == [],
          "'never adapts' is not a violation")
    check(V.find_adaptive("a dog that does not adapt to your route") == [],
          "'does not adapt' is not a violation")
    check(V.find_adaptive("it cannot predict where you go") == [],
          "'cannot predict' is not a violation")
    check(V.find_adaptive("a cook who anticipates the approach") != [],
          "an asserted adaptive verb is still a violation")
    check(V.find_adaptive("it predicts your next tile") != [],
          "'predicts' asserted is still a violation")


def test_anachronism_map_does_not_fire_on_ordinary_geography():
    check(V.find_anachronisms("a chain gate and a wire fence", 0) == [],
          "a fence on day 0 is geography, not an anachronism")
    check(V.find_anachronisms("out onto the open street", 0) == [],
          "a street on day 0 is geography; the GDD's day-0 beat is first_street")
    check(V.find_anachronisms("salt off the water ahead", 2) != [],
          "a day-5 fact on day 2 still fires")
    check(V.find_anachronisms("the back leg limping", 3) != [],
          "the limp before day 7 still fires")


def test_transcript_matches_prompts():
    """The recorded replies are keyed to a hash of the whole prompt, retrieved
    chunks included. If the knowledge base or the retriever changes, every hash
    changes, replay misses, and the pipeline stops rather than serving a stale
    answer against fresh context. A clean replay run is the proof."""
    from llm import ReplayProvider
    index = build_index(ROOT / "data" / "kb")
    fb = json.loads((ROOT / "data" / "fallbacks.json").read_text())
    provider = ReplayProvider()
    for key in sorted(SPECS):
        run_spec(SPECS[key], index, provider, fb)
    check(provider.hits == 15, f"all 15 turns replay by hash (got {provider.hits})")
    check(provider.misses == [], f"no transcript misses ({provider.misses})")


def test_every_transcript_file_declares_its_origin():
    """Provenance is a claim the submission makes, so it is tested."""
    files = sorted((ROOT / "transcript").glob("*.json"))
    check(len(files) == 15, f"15 transcript files (got {len(files)})")
    for f in files:
        d = json.loads(f.read_text())
        check(d.get("recorded_by", "").startswith("claude-opus-5"),
              f"{f.name} names the model that produced it")
        check(d.get("model") is None,
              f"{f.name} does not claim to be a Haiku 4.5 call")


def main() -> int:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print(f"{PASSED} passed, {len(FAILED)} failed")
    for f in FAILED:
        print("  FAIL:", f)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
