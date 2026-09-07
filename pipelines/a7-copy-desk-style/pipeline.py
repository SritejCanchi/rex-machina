#!/usr/bin/env python3
"""Rex Machina, Assignment 7. The Copy Desk: Generator, Evaluator, Refiner.

    python pipeline.py            recorded turns, no key, no network
    python pipeline.py --live     real calls against claude-haiku-4-5

Three cases, each briefed to break one constraint type. The loop runs without
intervention: generate, score, rewrite from the reason, score again, stop when
the Evaluator gives 9 or better or after three repairs.

Writes evidence/before_after.md, out/DT_JourneyBeats.{json,csv,h} and
out/run_report.json.
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from styleguide import audit, evaluate, generate, guide, llm, refine   # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
EVID = os.path.join(ROOT, "evidence")
MAX_REPAIRS = 3


def ask_text(prov, role, prompt):
    reply = prov.complete(role, prompt, max_tokens=700)
    data = llm.parse_json(reply)
    text = (data.get("narration") or "").strip() if isinstance(data, dict) else ""
    if not text:
        raise ValueError("no narration field in the reply: %s" % reply[:160])
    return text


def score_it(prov, role, case, text, a):
    """The engine measures, the model judges. GDD 5, in one function."""
    prompt = evaluate.build_prompt(case, text, guide.BIBLE,
                                   evaluate.measured(a, case))
    return evaluate.parse(prov.complete(role, prompt, max_tokens=700))


def run_case(prov, case):
    """Generate, score, repair from the reason, score again. No intervention."""
    cid = case["case_id"]
    text = ask_text(prov, "gen.%s" % cid, generate.build_prompt(case))
    history = []
    for attempt in range(MAX_REPAIRS + 1):
        a = audit.audit(text, case)
        score, reason = score_it(prov, "eval%d.%s" % (attempt, cid), case,
                                 text, a)
        history.append({"text": text, "score": score, "reason": reason,
                        "audit": a})
        if score >= evaluate.THRESHOLD:
            return history, "accepted"
        # Plateau detector. Two rewrites that move the score nowhere mean the
        # Evaluator's remaining objection is not something a rewrite can
        # answer, so paying for a third is waste. Assignment 6 taught this.
        if len(history) >= 3 and history[-1]["score"] == history[-2]["score"] \
                == history[-3]["score"]:
            return history, ("evaluator plateaued at %.0f/10 across %d rewrites"
                             % (score, len(history) - 1))
        if attempt == MAX_REPAIRS:
            return history, "stopped at the repair limit"
        text = ask_text(prov, "ref%d.%s" % (attempt + 1, cid),
                        refine.build_prompt(case, text, reason))
    return history, "stopped at the repair limit"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    prov = llm.provider("live" if args.live else "replay")

    cases = json.load(open(os.path.join(ROOT, "data", "beats.json"),
                           encoding="utf-8"))
    print("=" * 72)
    print("THE COPY DESK   provider=%s   %d cases" % (prov.name, len(cases)))
    print("=" * 72)

    results, rows = [], []
    for case in cases:
        history, outcome = run_case(prov, case)
        results.append((case, history, outcome))
        first, last = history[0], history[-1]
        print("\n  %s  (%s)" % (case["case_id"], case["violation_class"]))
        print("    before  %.0f/10  %d words  %s"
              % (first["score"], first["audit"]["word_count"],
                 _flags(first["audit"])))
        print("    after   %.0f/10  %d words  %s   [%d repairs, %s]"
              % (last["score"], last["audit"]["word_count"],
                 _flags(last["audit"]), len(history) - 1, outcome))
        rows.append({
            "RowName": case["beat"],
            "Beat": case["beat"],
            "ViolationClass": case["violation_class"],
            "WordBudget": case["word_budget"],
            "ToneTarget": case["tone_target"],
            "Narration": last["text"],
            "WordCount": last["audit"]["word_count"],
            "ScoreBefore": first["score"],
            "ScoreAfter": last["score"],
            "Repairs": len(history) - 1,
            "Outcome": outcome,
        })

    _write_table(rows)
    _write_demo(results)
    lifted = sum(1 for _, h, _ in results if h[-1]["score"] > h[0]["score"])
    disagree = sum(1 for _, h, _ in results
                   if h[-1]["score"] >= evaluate.THRESHOLD
                   and not audit.clean(h[-1]["audit"]))
    print("\n%d of %d lines scored higher after the loop. %d final lines the "
          "Evaluator accepted still fail a countable check."
          % (lifted, len(results), disagree))
    json.dump({"provider": prov.name, "cases": len(rows), "lifted": lifted,
               "accepted_but_countably_wrong": disagree, "rows": rows},
              open(os.path.join(OUT, "run_report.json"), "w"), indent=1)
    return 0


def _flags(a):
    bits = []
    if a["over_budget_by"]:
        bits.append("over budget by %d" % a["over_budget_by"])
    if a["banned_words"]:
        bits.append("banned: " + ",".join(a["banned_words"]))
    if a["exclamations"]:
        bits.append("%d exclamation" % a["exclamations"])
    if a["markdown"]:
        bits.append("markdown")
    if a["not_x_but_y"]:
        bits.append("not X but Y")
    if not a["second_person"]:
        bits.append("not second person")
    return ", ".join(bits) if bits else "countably clean"


def _write_table(rows):
    os.makedirs(OUT, exist_ok=True)
    json.dump(rows, open(os.path.join(OUT, "DT_JourneyBeats.json"), "w",
                         encoding="utf-8"), indent=1)
    with open(os.path.join(OUT, "DT_JourneyBeats.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    open(os.path.join(OUT, "DT_JourneyBeats.h"), "w",
         encoding="utf-8").write(HEADER)


def _write_demo(results):
    os.makedirs(EVID, exist_ok=True)
    out = ["# Before and after", "",
           "Emitted by `python pipeline.py`. Three cases, one per constraint",
           "type in the style guide. The brief given to the Generator is",
           "written to pull against that constraint, so the Evaluator has",
           "something real to catch.", ""]
    for case, history, outcome in results:
        out += ["## %s" % case["violation_class"],
                "",
                "Beat `%s`, budget %d words, tone %s."
                % (case["beat"], case["word_budget"], case["tone_target"]),
                "",
                "Brief given to the Generator: *%s*" % case["off_brand_brief"],
                ""]
        for i, step in enumerate(history):
            label = "BEFORE" if i == 0 else "AFTER REPAIR %d" % i
            out += ["**%s** (%d words)" % (label, step["audit"]["word_count"]),
                    "",
                    "> %s" % step["text"].replace("\n", " "),
                    "",
                    "`SCORE: %.0f/10`" % step["score"],
                    "",
                    "REASON: %s" % step["reason"].replace("\n", " "),
                    "",
                    "Countable audit: %s" % _flags(step["audit"]),
                    ""]
        out += ["Outcome: %s after %d repair(s)." % (outcome, len(history) - 1),
                "", "---", ""]
    open(os.path.join(EVID, "before_after.md"), "w",
         encoding="utf-8").write("\n".join(out) + "\n")


HEADER = '''// DT_JourneyBeats.h  Assignment 7, Rex Machina.
// Row struct for Chronicler journey narration after the Copy Desk pass.
#pragma once
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "DT_JourneyBeats.generated.h"

USTRUCT(BlueprintType)
struct FJourneyBeatRow : public FTableRowBase
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Beat;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString ViolationClass;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32   WordBudget = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString ToneTarget;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Narration;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32   WordCount = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float   ScoreBefore = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) float   ScoreAfter = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32   Repairs = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Outcome;
};
'''

if __name__ == "__main__":
    sys.exit(main())
