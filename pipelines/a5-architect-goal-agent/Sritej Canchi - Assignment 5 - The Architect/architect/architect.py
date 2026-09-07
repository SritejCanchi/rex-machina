#!/usr/bin/env python3
"""The Architect. Reads the GDD, scans the game, scores the gaps, writes one.

Usage:
    python architect/architect.py                 replay mode, no key needed
    python architect/architect.py --live          real Haiku 4.5 calls
    python architect/architect.py --dry-run       reason and stop, write nothing
    python architect/architect.py --emit-prompt N dump the prompt for turn N

Raw orchestration throughout. Every model turn is one HTTPS call made in
llm.py, and every decision between turns is plain Python you can read.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from architect import build, gaps, gdd, llm, memory, score   # noqa: E402
from architect.scan import Codebase                          # noqa: E402

GAME = os.path.join(ROOT, "game")
GDD_PATH = os.path.join(ROOT, "docs", "gdd_rex_machina.md")

FEATURE_PROMPT = """You are the planning stage of a coding agent for a game called
Rex Machina. A deterministic parser has pulled every candidate requirement out of
the game design document. Your job is to turn that noisy list into a dependency
graph of runtime systems.

RULES
- Keep only things the running game must compute or simulate. Drop enum values
  (compass directions), drop tile coordinates, drop document furniture.
- Every feature must cite the GDD section it came from.
- requires lists features that must exist first. blocks lists features that
  cannot be built until this one exists. Use feature keys, not prose.
- priority is critical, high, medium or low. critical means the GDD names it as
  a constraint or a fix for a known exploit.
- detect lists lowercase substrings a code scanner should look for.

CANDIDATE REQUIREMENTS FROM THE GDD
{candidates}

MODULES THAT CURRENTLY EXIST
{modules}

OUTPUT CONTRACT
Reply with one JSON array and nothing else. Each element:
{{"key": "...", "name": "...", "gdd_section": "...", "detect": ["..."],
  "requires": ["..."], "blocks": ["..."], "priority": "...", "reason": "..."}}
"""


def feature_prompt(requirements, code):
    cand = "\n".join("- %s (%s, GDD %s): %s"
                     % (r.key, r.source, r.section, r.evidence[:110])
                     for r in requirements)
    mods = "\n".join("- %s" % m for m in sorted(code.modules))
    return FEATURE_PROMPT.format(candidates=cand, modules=mods)


def targets_for(gap, code):
    """Which files the code generator is allowed to touch."""
    explicit = gap.feature.get("targets")
    if explicit:
        return explicit
    touched = {s.module for tok in gap.feature.get("detect", [gap.key])
               for s in code.find(tok)}
    return sorted(touched) or ["rex/nemesis.py"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--emit-prompt", metavar="TURN")
    args = ap.parse_args()
    prov = llm.provider("live" if args.live else "auto")

    print("=" * 72)
    print("THE ARCHITECT   provider=%s" % prov.name)
    print("=" * 72)

    # 1. read the GDD -------------------------------------------------
    requirements = gdd.extract(GDD_PATH)
    print("\n[1] GDD  %s" % os.path.relpath(GDD_PATH, ROOT))
    print("    %d candidate requirements (%d from JSON contracts, %d from prose)"
          % (len(requirements),
             sum(1 for r in requirements if r.source == "contract"),
             sum(1 for r in requirements if r.source == "prose")))

    # 2. scan the codebase --------------------------------------------
    code = Codebase(GAME)
    s = code.summary()
    print("\n[2] CODEBASE  game/")
    print("    %d modules, %d symbols, %d stub functions"
          % (s["modules"], s["symbols"], s["stubs"]))
    for st in code.stubs:
        print("    stub: %s:%d %s()" % (st.module, st.lineno, st.name))

    # 3. plan ----------------------------------------------------------
    fprompt = feature_prompt(requirements, code)
    if args.emit_prompt == "features":
        print(fprompt)
        return
    features = llm.parse_json(prov.complete("features", fprompt, max_tokens=6000))
    print("\n[3] FEATURE GRAPH  %d runtime systems kept" % len(features))

    # 4. detect gaps ---------------------------------------------------
    found = gaps.detect(features, code)
    print("\n[4] GAP DETECTION")
    for g in found:
        print("    %-10s %-26s %s" % (g.status, g.key, g.evidence[:70]))

    # 5. score ---------------------------------------------------------
    ranked = score.score_all(gaps.open_gaps(found))
    print("\n[5] UTILITY SCORING   weights %s" % score.WEIGHTS)
    for g in ranked:
        print("    %-26s %s" % (g.key, score.explain(g)))

    skip = memory.previously_built() | memory.previously_failed()
    choice = next((g for g in ranked if g.key not in skip), None)
    if choice is None:
        print("\nno buildable gap left. see state/NEXT.md")
        return

    print("\n[6] SELECTED  %s" % choice.key)
    print("    %s" % choice.feature.get("reason", ""))
    memory.replace("next", "\n".join(
        "- **%s** score %.4f, %s, blocks %s"
        % (g.key, g.score, g.status, ", ".join(g.feature.get("blocks", [])) or "nothing")
        for g in ranked))

    if args.dry_run:
        print("\ndry run, stopping before generation.")
        return

    # 6. generate ------------------------------------------------------
    targets = targets_for(choice, code)
    evidence = "\n".join("- %s (GDD %s): %s" % (r.key, r.section, r.evidence[:140])
                         for r in requirements
                         if any(t in r.key or t in r.evidence.lower()
                                for t in choice.feature.get("detect", [choice.key])))
    if args.emit_prompt == "codegen":
        print(build.build_prompt(choice, evidence, code, targets))
        return

    print("\n[7] GENERATING into %s" % ", ".join(targets))
    result, prompt = build.generate(choice, evidence, code, targets, prov)
    ok, written, report = build.apply_and_verify(result, GAME, ROOT)
    print("    %s" % result.get("summary", ""))
    print("    files: %s" % ", ".join(written))
    print("\n[8] VERIFICATION\n%s" % "\n".join("    " + l for l in report.splitlines()))

    run_id = llm.key_for("run", prompt)[-8:]
    if ok:
        memory.append("built", "## %s  %s\n\n%s\n\nFiles: %s\n\nGDD: %s\n\n%s"
                      % (choice.key, choice.feature.get("name", ""),
                         result.get("summary", ""), ", ".join(written),
                         "; ".join(result.get("gdd_citations", [])),
                         memory.stamp(run_id)))
    else:
        memory.append("failed", "## %s\n\n%s\n\n```\n%s\n```\n\n%s"
                      % (choice.key, "verification failed, changes rolled back",
                         report, memory.stamp(run_id)))
    memory.append("decisions", "## %s  %s\n\nScore %.4f, %s\n\n%s\n\n%s"
                  % (choice.key, "selected" if ok else "attempted",
                     choice.score, score.explain(choice),
                     choice.feature.get("reason", ""), memory.stamp(run_id)))

    with open(os.path.join(ROOT, "state", "run_report.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"provider": prov.name, "features": len(features),
                   "gaps": [g.as_dict() for g in found],
                   "ranked": [g.as_dict() for g in ranked],
                   "selected": choice.key, "verified": ok,
                   "files": written, "report": report}, fh, indent=1)
    print("\n%s" % ("DONE. feature accepted." if ok else
                    "ROLLED BACK. see state/FAILED.md"))


if __name__ == "__main__":
    main()
