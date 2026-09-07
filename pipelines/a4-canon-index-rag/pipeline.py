"""
pipeline.py — REX MACHINA: THE CANON INDEX
Assignment #4, Dynamic Content Pipeline.

    KB (the GDD, verbatim)
      -> chunk -> TF-IDF vector index
      -> per content type: query -> top-k chunks
      -> GENERATOR  (grounded only in the retrieved chunks)
      -> CRITIC     (finds lore breaks and tone drift, cites rule + chunk)
      -> REPAIR     (fixes only what the critic cited; may not rewrite freely)
      -> GATE       (validators.py, deterministic; the only thing that can stop a row)
      -> out/DT_*.json + .csv, out/F*.h, out/retrieval_traces.md, out/run_report.json

Usage
    python pipeline.py                  # replay the recorded transcript, offline
    python pipeline.py --live           # call claude-haiku-4-5 (needs ANTHROPIC_API_KEY)
    python pipeline.py --type nemesis_read
    python pipeline.py --dump-prompts   # write every prompt without calling anything
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from kb import Index, build_index, Hit
from llm import TranscriptMiss, get_provider
from specs import SPECS, ContentSpec, seed_query
from validators import Violation, check_row, check_table

ROOT = Path(__file__).parent
OUT = ROOT / "out"
BATCH = 8


# ==========================================================================
# prompt construction
# ==========================================================================

PREAMBLE = """\
You are writing content for REX MACHINA, a game about a shelter dog that walks
home to the family that gave it away and must outwit the robot dog they
replaced it with. Unreal Engine 5, greybox, solo developer.

You know nothing about this game except the RETRIEVED CANON below. Do not use
general knowledge about dogs, robots, or games to fill a gap. If the canon does
not settle something, choose the option that contradicts the least canon and
stay concrete.

RETRIEVED CANON
===============
{chunks}
"""


def render_chunks(hits: list[Hit]) -> str:
    parts = []
    for rank, h in enumerate(hits, 1):
        parts.append(
            f"[{rank}] chunk={h.chunk.id} score={h.score:.4f} "
            f"kind={h.chunk.kind}\n"
            f"    section: {h.chunk.heading}\n"
            f"{h.chunk.text}\n"
        )
    return "\n".join(parts)


def generator_prompt(spec: ContentSpec, hits: list[Hit], keys: list[dict]) -> str:
    # Emit nothing at all when a spec has no closed vocabularies, so adding
    # field notes to one content type does not perturb the others' prompts.
    notes = f"\n{spec.field_help}" if spec.field_help else ""
    return PREAMBLE.format(chunks=render_chunks(hits)) + f"""
TASK
====
Write rows for the Unreal DataTable {spec.table} ({spec.title}).

The gap being filled: {spec.gap}

Fields, in this order: {', '.join(spec.fields)}
{notes}
Hard rules. Every row is machine-checked against these after you answer; a row
that fails is thrown away and a hand-authored fallback ships instead.
{chr(10).join('  ' + r for r in spec.rules)}

Produce exactly {len(keys)} rows, one for each key below, in this order:
{json.dumps(keys, indent=2)}

Answer with a JSON array of {len(keys)} objects and nothing else. No prose, no
code fence, no commentary.
"""


def critic_prompt(spec: ContentSpec, hits: list[Hit], rows: list[dict]) -> str:
    return PREAMBLE.format(chunks=render_chunks(hits)) + f"""
TASK
====
You are the CONTINUITY CRITIC. You did not write the rows below and you may not
rewrite them. Your job is to find lore breaks and tone drift and to cite, for
each one, the rule it violates and the chunk id that proves it.

The rules:
{chr(10).join('  ' + r for r in spec.rules)}

A lore break is a statement that contradicts the retrieved canon, or that
requires knowledge the speaker cannot have. Tone drift is prose that is
technically consistent but does not sound like this game: reaching for grandeur,
naming an abstraction, explaining a feeling the player should infer.

Be specific. "Feels off" is not a finding. Quote the offending span.

ROWS UNDER REVIEW
{json.dumps(rows, indent=2)}

Answer with a JSON array, one object per row, in the same order:
  {{"index": <int>, "verdict": "pass" | "fail",
    "violations": [{{"rule": "<rule id>", "span": "<quoted text>",
                     "why": "<one sentence>", "chunk": "<chunk id>"}}]}}
Nothing else.
"""


def repair_prompt(spec: ContentSpec, hits: list[Hit],
                  jobs: list[dict]) -> str:
    return PREAMBLE.format(chunks=render_chunks(hits)) + f"""
TASK
====
You are the REPAIR pass. Each job below is one row the critic rejected, with
the violations it cited.

Fix ONLY the cited violations. Do not restyle anything the critic did not
mention. Do not change a field that carries no violation. If two fixes are
possible, take the one that changes fewer words.

The rules, for reference:
{chr(10).join('  ' + r for r in spec.rules)}

JOBS
{json.dumps(jobs, indent=2)}

Answer with a JSON array of the repaired row objects, same order, same field
names, and nothing else.
"""


# ==========================================================================
# parsing
# ==========================================================================

def parse_json_array(text: str, what: str) -> list:
    """Models sometimes fence JSON or prepend a sentence. Recover, but never
    guess at the content."""
    s = text.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s).strip()
    start, end = s.find("["), s.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"{what}: no JSON array in reply:\n{text[:400]}")
    try:
        data = json.loads(s[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(f"{what}: bad JSON ({exc}) in:\n{s[start:start+400]}") from exc
    if not isinstance(data, list):
        raise ValueError(f"{what}: expected a list, got {type(data).__name__}")
    return data


# ==========================================================================
# run
# ==========================================================================

def ask_for_rows(provider, role: str, prompt: str, want: int,
                 spec: ContentSpec, key_batch: list[dict],
                 fallbacks: dict) -> list[dict]:
    """Get `want` row objects out of the generator, and never take the run
    down trying.

    A live model occasionally returns eleven rows for a batch of eight, or
    fences its JSON, or drops a trailing brace. In replay that never happens,
    which is exactly why it needed handling before a key gets spent on a live
    run. One retry with the failure quoted back, then pad from the authored
    fallback table. A short batch costs a few authored rows. A raised
    exception costs the whole run.
    """
    last = ""
    for attempt in (1, 2):
        p = prompt if attempt == 1 else (
            prompt + f"\n\nYour previous answer could not be used: {last}\n"
                     f"Return a JSON array of exactly {want} objects, "
                     f"nothing else.")
        try:
            raw = provider.complete(role, p, max_tokens=4096)
            rows = [r for r in parse_json_array(raw, role) if isinstance(r, dict)]
        except (ValueError, KeyError) as exc:
            last = str(exc)[:200]
            if attempt == 2:
                rows = []
            else:
                print(f"  warn: {role} unusable ({last}); retrying once",
                      file=sys.stderr)
                continue
        if len(rows) == want:
            return rows
        last = f"expected {want} rows, got {len(rows)}"
        if attempt == 1:
            print(f"  warn: {role} {last}; retrying once", file=sys.stderr)
            continue
        # pad or trim, then let the gate judge every row on its merits
        print(f"  warn: {role} {last} after retry; padding from the "
              f"authored table", file=sys.stderr)
        rows = rows[:want]
        while len(rows) < want:
            rows.append(dict(fallbacks[spec.key][key_of(spec, key_batch[len(rows)])]))
        return rows
    return rows


def load_fallbacks() -> dict:
    path = ROOT / "data" / "fallbacks.json"
    return json.loads(path.read_text(encoding="utf-8"))


def key_of(spec: ContentSpec, key: dict) -> str:
    if spec.key == "nemesis_read":
        return f"{key['read_category']}|{key['charge_band']}"
    if spec.key == "journey_hazard":
        return key["hazard_id"]
    return key["phase_id"]


def batches(items: list, n: int) -> list[list]:
    return [items[i:i + n] for i in range(0, len(items), n)]


def retrieve(spec: ContentSpec, index: Index, keys: list[dict]) -> list[Hit]:
    """Two-stage retrieval: one shared query for the mechanics, plus a short
    seed query per row for the canon that row specifically needs.

    The shared-query hits are pinned. Only the seed-only additions compete for
    the remaining slots under `cap`. Without the pin, a content type with many
    rows generates enough seed hits to evict the mechanics chunks the shared
    query exists to fetch, which is the opposite of what the second stage is
    for. Caught by test_seed_queries_beat_the_shared_query_on_hazards.
    """
    pinned: dict[str, Hit] = {h.chunk.id: h for h in index.search(spec.query, spec.k)}
    extra: dict[str, Hit] = {}
    for key in keys:
        for h in index.search(seed_query(spec.key, key), spec.seed_k):
            if h.chunk.id in pinned:
                continue
            prev = extra.get(h.chunk.id)
            if prev is None or h.score > prev.score:
                extra[h.chunk.id] = h

    room = max(0, spec.cap - len(pinned))
    chosen = sorted(extra.values(), key=lambda h: (-h.score, h.chunk.id))[:room]
    return sorted([*pinned.values(), *chosen],
                  key=lambda h: (-h.score, h.chunk.id))


def run_spec(spec: ContentSpec, index: Index, provider, fallbacks: dict,
             dump_only: bool = False, prompt_dir: Path | None = None) -> dict:
    hits = retrieve(spec, index, spec.keys)
    report = {
        "content_type": spec.key,
        "table": spec.table,
        "gap": spec.gap,
        "query": spec.query,
        "retrieved": [{"rank": i, "chunk": h.chunk.id, "score": round(h.score, 4),
                       "kind": h.chunk.kind, "heading": h.chunk.heading,
                       "overlap_terms": h.overlap}
                      for i, h in enumerate(hits, 1)],
        "rows": [], "critic_findings": [], "gate_findings": [],
        "counts": {},
    }

    final_rows: list[dict] = []
    provenance: list[str] = []          # parallel to final_rows, by position
    critic_all: list[dict] = []
    gate_all: list[dict] = []
    before_after: list[dict] = []

    for bi, key_batch in enumerate(batches(spec.keys, BATCH)):
        gp = generator_prompt(spec, hits, key_batch)
        if dump_only:
            (prompt_dir / f"{spec.key}.gen{bi}.txt").write_text(gp, encoding="utf-8")
            continue

        rows = ask_for_rows(provider, f"gen.{spec.key}.{bi}", gp,
                            len(key_batch), spec, key_batch, fallbacks)

        cp = critic_prompt(spec, hits, rows)
        try:
            craw = provider.complete(f"critic.{spec.key}.{bi}", cp, max_tokens=4096)
            verdicts = parse_json_array(craw, f"critic {spec.key} batch {bi}")
        except (ValueError, KeyError) as exc:
            # A critic that fails to answer must not take the run down. The
            # gate still sees every row, so the floor is unchanged: nothing
            # ships without passing 21 deterministic checks.
            print(f"  warn: critic {spec.key}.{bi} unusable ({exc}); "
                  f"falling through to the gate", file=sys.stderr)
            verdicts = []
        vmap = {v.get("index", i): v for i, v in enumerate(verdicts)}

        jobs = []
        for i, row in enumerate(rows):
            v = vmap.get(i, {"verdict": "pass", "violations": []})
            for viol in v.get("violations", []):
                critic_all.append({"row": key_of(spec, key_batch[i]), **viol})
            if v.get("verdict") == "fail" and v.get("violations"):
                jobs.append({"index": i, "row": row,
                             "violations": v["violations"]})

        repaired: dict[int, dict] = {}
        if jobs:
            rp = repair_prompt(spec, hits, jobs)
            try:
                rraw = provider.complete(f"repair.{spec.key}.{bi}", rp,
                                         max_tokens=4096)
                fixed = parse_json_array(rraw, f"repair {spec.key} batch {bi}")
            except (ValueError, KeyError) as exc:
                print(f"  warn: repair {spec.key}.{bi} unusable ({exc}); "
                      f"the cited rows go to the gate unrepaired",
                      file=sys.stderr)
                fixed = []
            for job, row in zip(jobs, fixed):
                if isinstance(row, dict):
                    repaired[job["index"]] = row

        for i, key in enumerate(key_batch):
            candidate = repaired.get(i, rows[i])
            source = "repaired" if i in repaired else "generated"
            if i in repaired:
                before_after.append({"row": key_of(spec, key),
                                     "before": rows[i], "after": repaired[i]})
            viols = check_row(spec.key, candidate, key)
            kid = key_of(spec, key)
            if viols:
                for v in viols:
                    gate_all.append({"row": kid, "rule": v.rule,
                                     "detail": v.detail, "after": source})
                # copy: the fallback table is loaded once and must not pick up
                # a Provenance key from whichever run happened to use it
                candidate = dict(fallbacks[spec.key][kid])
                source = "authored_fallback"
            final_rows.append(candidate)
            provenance.append(source)

    if dump_only:
        return report

    # table-level rules run on the assembled table
    for v in check_table(spec.key, final_rows):
        gate_all.append({"row": "<table>", "rule": v.rule, "detail": v.detail,
                         "after": "assembled"})

    for row, src in zip(final_rows, provenance):
        row["Provenance"] = src

    report["rows"] = final_rows
    report["critic_findings"] = critic_all
    report["gate_findings"] = gate_all
    report["repairs"] = before_after
    report["counts"] = {
        "rows": len(final_rows),
        "generated": provenance.count("generated"),
        "repaired": provenance.count("repaired"),
        "authored_fallback": provenance.count("authored_fallback"),
        "critic_findings": len(critic_all),
        "gate_findings": len(gate_all),
    }
    return report


# ==========================================================================
# writers
# ==========================================================================

def write_datatable(spec: ContentSpec, rows: list[dict]) -> None:
    OUT.mkdir(exist_ok=True)
    cols = spec.fields + ["Provenance"]
    (OUT / f"{spec.table}.json").write_text(
        json.dumps([{c: r.get(c) for c in cols} for r in rows], indent=2),
        encoding="utf-8")
    with (OUT / f"{spec.table}.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["Name"] + cols, extrasaction="ignore")
        w.writeheader()
        for i, r in enumerate(rows):
            flat = {c: (json.dumps(r.get(c)) if isinstance(r.get(c), (list, dict))
                        else r.get(c)) for c in cols}
            w.writerow({"Name": f"{spec.table}_{i:02d}", **flat})


_UE_TYPE = {
    "WordCount": "int32", "Day": "int32", "Act": "int32",
    "WindowTurns": "int32", "PhaseIndex": "int32",
    "ApproachLow": "float", "ApproachHigh": "float",
    "CausesCondition": "bool",
    "ExitTiles": "TArray<FIntPoint>", "CoverTiles": "TArray<FIntPoint>",
    "Props": "TArray<FString>",
}


def struct_name(spec: ContentSpec) -> str:
    """nemesis_read -> FNemesisReadRow, matching the FJourneyBeatRow that
    Assignment #3's Beat Foundry already ships."""
    return "F" + "".join(p.capitalize() for p in spec.key.split("_")) + "Row"


def write_header(spec: ContentSpec) -> None:
    struct = struct_name(spec)
    lines = [
        "// Generated by the Canon Index pipeline. Regenerate; do not hand-edit.",
        "#pragma once", "",
        '#include "CoreMinimal.h"',
        '#include "Engine/DataTable.h"',
        f'#include "{struct}.generated.h"', "",
        "USTRUCT(BlueprintType)",
        f"struct {struct} : public FTableRowBase",
        "{", "\tGENERATED_BODY()", "",
    ]
    for f in spec.fields + ["Provenance"]:
        t = _UE_TYPE.get(f, "FString")
        lines.append("\tUPROPERTY(EditAnywhere, BlueprintReadOnly)")
        lines.append(f"\t{t} {f};")
        lines.append("")
    lines.append("};")
    (OUT / f"{struct}.h").write_text("\n".join(lines), encoding="utf-8")


def write_evidence(reports: list[dict], usage: dict, kb: dict) -> None:
    """out/EVIDENCE.md — the rubric's evidence, assembled from the run itself.

    Regenerated on every run, live or replay, so a live run documents itself
    instead of leaving the README describing a different one. Nothing in here
    is hand-written: query, chunks, before/after repairs, critic findings and
    gate findings all come out of run_report.json.
    """
    tot = {"rows": 0, "generated": 0, "repaired": 0, "authored_fallback": 0,
           "critic_findings": 0, "gate_findings": 0}
    for r in reports:
        for k in tot:
            tot[k] += r["counts"][k]

    L = ["# Evidence", "",
         "Generated by `python pipeline.py`. Every number and quotation below "
         "comes from this run.", "",
         f"- provider: `{usage.get('provider')}`"
         + (f", model `{usage.get('model')}`" if usage.get("model") else ""),
         f"- knowledge base: {kb['chunks']} chunks, {kb['vocabulary']} terms, "
         f"source `{', '.join(kb['sources'])}`",
         f"- calls: {usage.get('calls')}",
         (f"- tokens: {usage['input_tokens']:,} in, {usage['output_tokens']:,} out, "
          f"${usage['cost_usd']}" if usage.get("input_tokens") else
          "- tokens: not measured in replay mode; see `estimate_cost.py`"),
         "",
         f"**{tot['rows']} rows: {tot['generated']} generated, "
         f"{tot['repaired']} repaired, {tot['authored_fallback']} authored "
         f"fallback. Critic raised {tot['critic_findings']} findings; the gate "
         f"raised {tot['gate_findings']}.**", ""]

    for r in reports:
        c = r["counts"]
        L += ["---", "", f"## {r['table']}", "",
              f"**Gap.** {r['gap']}", "",
              f"{c['rows']} rows: {c['generated']} generated, {c['repaired']} "
              f"repaired, {c['authored_fallback']} authored fallback.", "",
              "### Query and retrieved context", "", "```", r["query"], "```", ""]
        for h in r["retrieved"][:6]:
            L += [f"{h['rank']}. `{h['chunk']}` cosine {h['score']}, "
                  f"{h['kind']}, section `{h['heading']}`  ",
                  f"   shared terms: `{'`, `'.join(h['overlap_terms'])}`"]
        L += ["", "### One output row", "", "```json",
              json.dumps(r["rows"][0], indent=2) if r["rows"] else "{}", "```", ""]

        if r.get("repairs"):
            L += ["### What the critic caught, and the repair that followed", ""]
            by_row = {f["row"]: [] for f in r["critic_findings"]}
            for f in r["critic_findings"]:
                by_row[f["row"]].append(f)
            for rep in r["repairs"]:
                L += [f"**`{rep['row']}`**", ""]
                for f in by_row.get(rep["row"], []):
                    L += [f"- `{f['rule']}` on {f['span']!r}  ",
                          f"  {f.get('why','')}  ",
                          f"  cited chunk: `{f.get('chunk','')}`"]
                changed = [k for k in rep["after"]
                           if rep["before"].get(k) != rep["after"].get(k)]
                L += ["", "```"]
                for k in changed:
                    L += [f"{k}:",
                          f"  before  {json.dumps(rep['before'].get(k), ensure_ascii=False)}",
                          f"  after   {json.dumps(rep['after'].get(k), ensure_ascii=False)}"]
                L += ["```", ""]

        unrepaired = [f for f in r["critic_findings"]
                      if f["row"] not in {x["row"] for x in r.get("repairs", [])}]
        if unrepaired:
            L += ["### Critic findings on rows that were not repaired", ""]
            for f in unrepaired:
                L += [f"- `{f['row']}` `{f['rule']}` on {f['span']!r}"]
            L += [""]

        if r["gate_findings"]:
            L += ["### What the gate stopped after the agents had finished", "",
                  "| row | rule | stage | detail |", "|---|---|---|---|"]
            for f in r["gate_findings"]:
                L += [f"| `{f['row']}` | {f['rule']} | {f['after']} | "
                      f"{f['detail']} |"]
            L += ["",
                  "Rows listed here were discarded and replaced by the "
                  "hand-authored fallback.", ""]
        else:
            L += ["### Gate", "", "Every row passed the gate on this run.", ""]

    (OUT / "EVIDENCE.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def write_traces(reports: list[dict]) -> None:
    """The rubric asks for query, retrieved chunk and output side by side.
    This is that file."""
    L = ["# Retrieval traces",
         "",
         "One section per content type: the query that was issued, the chunks the",
         "vector index returned with their cosine scores, and a row that came out",
         "the other end. Regenerate with `python pipeline.py`.",
         ""]
    for r in reports:
        L += [f"## {r['table']} ({r['content_type']})", "",
              f"**Gap.** {r['gap']}", "",
              "### Query", "", "```", r["query"], "```", "",
              "### Retrieved", ""]
        for h in r["retrieved"]:
            # Headings are quoted verbatim from the GDD and go in backticks:
            # they are literal identifiers, not prose written for this file.
            L += [f"**{h['rank']}. `{h['chunk']}`**, cosine {h['score']}, "
                  f"{h['kind']}, section `{h['heading']}`  ",
                  f"shared terms: `{'`, `'.join(h['overlap_terms'])}`", ""]
        L += ["### Output row (first)", "", "```json",
              json.dumps(r["rows"][0], indent=2) if r["rows"] else "{}",
              "```", ""]
    (OUT / "retrieval_traces.md").write_text("\n".join(L), encoding="utf-8")


# ==========================================================================
# main
# ==========================================================================

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="REX MACHINA canon-grounded content pipeline")
    ap.add_argument("--live", action="store_true",
                    help="call claude-haiku-4-5 instead of replaying the transcript")
    ap.add_argument("--type", action="append", choices=sorted(SPECS),
                    help="restrict to one content type (repeatable)")
    ap.add_argument("--dump-prompts", action="store_true",
                    help="write every prompt to out/prompts/ and make no calls")
    args = ap.parse_args(argv)

    index = build_index(ROOT / "data" / "kb")
    print(f"knowledge base: {json.dumps(index.stats())}")

    chosen = [SPECS[k] for k in (args.type or sorted(SPECS))]

    if args.dump_prompts:
        pd = OUT / "prompts"
        pd.mkdir(parents=True, exist_ok=True)
        for spec in chosen:
            run_spec(spec, index, None, {}, dump_only=True, prompt_dir=pd)
        print(f"prompts written to {pd}")
        return 0

    provider = get_provider(live=args.live)
    fallbacks = load_fallbacks()
    OUT.mkdir(exist_ok=True)

    reports = []
    for spec in chosen:
        try:
            rep = run_spec(spec, index, provider, fallbacks)
        except TranscriptMiss as exc:
            print(f"\nreplay miss for {spec.key}:\n  {exc}", file=sys.stderr)
            return 2
        write_datatable(spec, rep["rows"])
        write_header(spec)
        reports.append(rep)
        c = rep["counts"]
        print(f"  {spec.table:22} {c['rows']:>3} rows  "
              f"gen {c['generated']} / repaired {c['repaired']} / "
              f"fallback {c['authored_fallback']}  "
              f"critic {c['critic_findings']} gate {c['gate_findings']}")

    usage = provider.usage()
    write_traces(reports)
    write_evidence(reports, usage, index.stats())
    (OUT / "run_report.json").write_text(json.dumps({
        "kb": index.stats(), "usage": usage,
        "reports": reports,
    }, indent=2), encoding="utf-8")
    print(f"usage: {json.dumps(usage)}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
