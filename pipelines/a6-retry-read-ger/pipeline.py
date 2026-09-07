#!/usr/bin/env python3
"""Rex Machina, Assignment 6. Generator, Evaluator, Refiner, Circuit Breaker.

    python pipeline.py            recorded turns, no key, no network
    python pipeline.py --live     real calls against claude-haiku-4-5

Writes out/DT_RetryReads.{json,csv,h}, evidence/ger_trace.md and
evidence/escalations.md. Nothing here is hand-written after the fact: the
evidence files are emitted by the run.
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ger import breaker, generate, llm, refine, rules      # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(ROOT, "data", "retry_cases.json")
OUT = os.path.join(ROOT, "out")
EVID = os.path.join(ROOT, "evidence")


def ask(prov, role, prompt):
    reply = prov.complete(role, prompt, max_tokens=300)
    data = llm.parse_json(reply)
    line = (data.get("line") or "").strip() if isinstance(data, dict) else ""
    if not line:
        raise ValueError("no line field in the reply: %s" % reply[:120])
    return line


def run_case(prov, case, trace):
    br = breaker.Breaker(case)
    line = None
    attempt = 0
    while True:
        attempt += 1
        role = "gen.%s" % case["case_id"] if attempt == 1 else \
               "ref%d.%s" % (attempt - 1, case["case_id"])
        prompt = (generate.build_prompt(case) if attempt == 1
                  else refine.build_prompt(case, line, failures))
        try:
            line = ask(prov, role, prompt)
        except SystemExit as err:
            br.provider_failed(err)
            trace.append((case, br, None, "escalated"))
            return br.fallback(), br, "authored_fallback"
        failures = rules.check(line, case)
        br.record(line, failures)
        if not failures:
            trace.append((case, br, line, "accepted"))
            kind = "model" if attempt == 1 else "model_refined"
            return line, br, kind
        if br.should_stop():
            trace.append((case, br, None, "escalated"))
            return br.fallback(), br, "authored_fallback"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    prov = llm.provider("live" if args.live else "replay")

    cases = json.load(open(CASES, encoding="utf-8"))
    print("=" * 72)
    print("THE RETRY READ   provider=%s   %d cases" % (prov.name, len(cases)))
    print("=" * 72)

    trace, rows = [], []
    for case in cases:
        line, br, provenance = run_case(prov, case, trace)
        fired = sorted({r for _, fs in br.attempts for r, _ in fs})
        rows.append({
            "RowName": case["case_id"],
            "Gate": case["prior_attempt"],
            "Phase": case["phase"],
            "ChargeBand": case["charge_band"],
            "Line": line,
            "WordCount": len(rules.words(line)),
            "Attempts": len(br.attempts),
            "RulesFired": "|".join(fired),
            "Provenance": provenance,
        })
        mark = "OK " if provenance != "authored_fallback" else "ESC"
        print("  %s %-26s attempts %d  fired %-28s %s"
              % (mark, case["case_id"], len(br.attempts),
                 ",".join(fired) or "-", line))

    _write_table(rows)
    _write_trace(trace)
    _write_escalations(trace)

    caught = sum(1 for r in rows if r["RulesFired"])
    esc = sum(1 for r in rows if r["Provenance"] == "authored_fallback")
    print("\n%d of %d first drafts broke a rule. %d escalated to the breaker."
          % (caught, len(rows), esc))
    json.dump({"provider": prov.name, "cases": len(rows), "caught": caught,
               "escalated": esc, "rows": rows},
              open(os.path.join(OUT, "run_report.json"), "w"), indent=1)
    return 0


def _write_table(rows):
    os.makedirs(OUT, exist_ok=True)
    json.dump(rows, open(os.path.join(OUT, "DT_RetryReads.json"), "w",
                         encoding="utf-8"), indent=1)
    with open(os.path.join(OUT, "DT_RetryReads.csv"), "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(OUT, "DT_RetryReads.h"), "w", encoding="utf-8") as fh:
        fh.write(HEADER)


def _write_trace(trace):
    os.makedirs(EVID, exist_ok=True)
    out = ["# GER trace", "",
           "Emitted by `python pipeline.py`. Every attempt below is a real",
           "model reply. The Generator never sees the rule list, so each",
           "failure is a break the model made on its own.", ""]
    for case, br, final, status in trace:
        out.append("## %s" % case["case_id"])
        out.append("")
        out.append("Gate `%s`, phase %d, register %s, charge %d percent."
                   % (case["prior_attempt"], case["phase"],
                      case["charge_band"], case["self_charge_pct"]))
        out.append("")
        for i, (line, failures) in enumerate(br.attempts, 1):
            label = "Generator" if i == 1 else "Refiner %d" % (i - 1)
            out.append("**%s.** `%s`" % (label, line))
            out.append("")
            if failures:
                for rid, msg in failures:
                    out.append("- REJECTED %s. %s" % (rid, msg))
            else:
                out.append("- accepted")
            out.append("")
        if status == "escalated":
            out.append("**Circuit breaker tripped.** %s" % br.reason)
            out.append("")
            out.append("Shipped the authored fallback: `%s`" % br.fallback())
            out.append("")
    open(os.path.join(EVID, "ger_trace.md"), "w", encoding="utf-8").write(
        "\n".join(out) + "\n")


def _write_escalations(trace):
    esc = [t for t in trace if t[3] == "escalated"]
    out = ["# Escalations", "",
           "Rows the loop could not repair. Each one still ships, with an",
           "authored line and a Provenance value that says so. GDD 6",
           "constraint 5: a dropped request costs flavor, never a frame.", ""]
    if not esc:
        out.append("No escalations in the last run.")
    for case, br, _, _ in esc:
        out.append("## %s" % case["case_id"])
        out.append("")
        out.append("Reason: %s" % br.reason)
        out.append("")
        for i, (line, failures) in enumerate(br.attempts, 1):
            out.append("%d. `%s`  ->  %s"
                       % (i, line, ", ".join(r for r, _ in failures) or "clean"))
        out.append("")
        out.append("Shipped: `%s`" % br.fallback())
        out.append("")
    open(os.path.join(EVID, "escalations.md"), "w", encoding="utf-8").write(
        "\n".join(out) + "\n")


HEADER = '''// DT_RetryReads.h  Assignment 6, Rex Machina.
// Row struct for the retry read DataTable. One row per phase gate and register.
#pragma once
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "DT_RetryReads.generated.h"

USTRUCT(BlueprintType)
struct FRetryReadRow : public FTableRowBase
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Gate;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32   Phase = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString ChargeBand;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Line;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32   WordCount = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) int32   Attempts = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString RulesFired;
    UPROPERTY(EditAnywhere, BlueprintReadWrite) FString Provenance;
};
'''

if __name__ == "__main__":
    sys.exit(main())
