#!/usr/bin/env python3
"""Record one model turn under the exact hash the pipeline will look for.

Used when a turn is answered outside the live API path. Builds the prompt
in-process, exactly as architect.py builds it, so the hash cannot drift.

    python tools/record_turn.py features path/to/response.json
    python tools/record_turn.py codegen  path/to/response.json
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from architect import architect as A                 # noqa: E402
from architect import build, gaps, gdd, llm, memory, score   # noqa: E402
from architect.scan import Codebase                  # noqa: E402


def features_prompt():
    return A.feature_prompt(gdd.extract(A.GDD_PATH), Codebase(A.GAME))


def codegen_prompt():
    reqs = gdd.extract(A.GDD_PATH)
    code = Codebase(A.GAME)
    feats = llm.parse_json(llm.ReplayProvider().complete("features", features_prompt()))
    ranked = score.score_all(gaps.open_gaps(gaps.detect(feats, code)))
    skip = memory.previously_built() | memory.previously_failed()
    choice = next(g for g in ranked if g.key not in skip)
    targets = A.targets_for(choice, code)
    evidence = "\n".join("- %s (GDD %s): %s" % (r.key, r.section, r.evidence[:140])
                         for r in reqs
                         if any(t in r.key or t in r.evidence.lower()
                                for t in choice.feature.get("detect", [choice.key])))
    return build.build_prompt(choice, evidence, code, targets), choice.key


def main():
    role = sys.argv[1]
    if role == "features":
        prompt, label = features_prompt(), "features"
    else:
        prompt, key = codegen_prompt()
        label = "codegen." + key
    if len(sys.argv) < 3:
        sys.stdout.write(prompt)
        return
    resp = open(sys.argv[2], encoding="utf-8").read()
    llm.parse_json(resp)
    k = llm.key_for(label, prompt)
    os.makedirs(llm.TRANSCRIPT, exist_ok=True)
    with open(os.path.join(llm.TRANSCRIPT, k + ".json"), "w", encoding="utf-8") as fh:
        json.dump({"role": label,
                   "model": "claude-opus-5, authored in session (README 6)",
                   "prompt": prompt, "response": resp}, fh, indent=1)
    print("recorded %s  (%d char prompt)" % (k, len(prompt)))


if __name__ == "__main__":
    main()
