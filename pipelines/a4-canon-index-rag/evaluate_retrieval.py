"""
evaluate_retrieval.py — measure the retriever instead of asserting it.

Three queries, two versions each: the one-liner I wrote first (`naive_query` in
specs.py) and the one the pipeline ships (`query`). Gold chunk sets below are
hand-labelled: I read all 39 chunks and marked the ones a human writing that
content type would actually need.

    python evaluate_retrieval.py            # print the table
    python evaluate_retrieval.py --write    # also write out/retrieval_eval.md

Metrics, all at k=6, which is the k the pipeline uses:
  P@6      of the six chunks returned, how many are gold
  R@6      of the gold chunks, how many were returned
  first    rank of the first gold chunk (1 is best)
  MAP      mean average precision over the returned list
"""

from __future__ import annotations

import argparse
from pathlib import Path

from kb import build_index
from pipeline import retrieve
from specs import SPECS

ROOT = Path(__file__).parent

# Hand-labelled. A chunk is gold if writing this content type without it would
# mean guessing at something the GDD already settles.
GOLD: dict[str, set[str]] = {
    "nemesis_read": {
        "gdd_rex_machina#004",  # the One Wow: what a read line is and does
        "gdd_rex_machina#006",  # register shifts with charge; phases
        "gdd_rex_machina#008",  # exploit fixes, incl. the read-line oracle
        "gdd_rex_machina#010",  # never receives the journey
        "gdd_rex_machina#011",  # input contract: the observables
        "gdd_rex_machina#013",  # output contract: read, read_category
        "gdd_rex_machina#014",  # UI rule: suppression by category
    },
    "journey_hazard": {
        "gdd_rex_machina#005",  # Acts 1-2 spine; telegraphs but never adapts
        "gdd_rex_machina#016",  # first_street beat: the shelter threshold
        "gdd_rex_machina#017",  # alley_escape beat: GAUNTLET outcome escaped
        "gdd_rex_machina#018",  # train_leap beat: the boxcar
        "gdd_rex_machina#021",  # fed_by_stranger beat: the diner back door
        "gdd_rex_machina#022",  # limp_onset beat: after the third hazard
        "gdd_rex_machina#031",  # Gauntlet agent and output contract
    },
    "arena_phase": {
        "gdd_rex_machina#005",  # compact UE5 arena, coarse tactical grid
        "gdd_rex_machina#006",  # phase gates at 33% and 66%; the three arenas
        "gdd_rex_machina#007",  # approach meter, stamina, win and loss
        "gdd_rex_machina#011",  # exits and cover_tiles as real coordinates
        "gdd_rex_machina#034",  # >= 2 escape routes per phase
        "gdd_rex_machina#042",  # Slice 1 builds this arena first
    },
}

K = 6


def score(hits, gold: set[str]) -> dict:
    ids = [h.chunk.id for h in hits]
    rel = [i in gold for i in ids]
    n_rel = sum(rel)
    first = next((i + 1 for i, r in enumerate(rel) if r), None)
    hit_count = 0
    prec_sum = 0.0
    for i, r in enumerate(rel, 1):
        if r:
            hit_count += 1
            prec_sum += hit_count / i
    return {
        "p_at_k": n_rel / len(ids) if ids else 0.0,
        "r_at_k": n_rel / len(gold) if gold else 0.0,
        "first": first,
        "map": prec_sum / min(len(gold), len(ids)) if gold and ids else 0.0,
        "ids": ids,
        "rel": rel,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    index = build_index(ROOT / "data" / "kb")
    lines: list[str] = []

    def out(s: str = ""):
        print(s)
        lines.append(s)

    out("# Retrieval evaluation")
    out()
    out(f"Index: {index.N} chunks, {len(index.df)} terms, k={K}. "
        f"Gold sets are hand-labelled; see `evaluate_retrieval.py`.")
    out()
    out("| content type | query | P@6 | R@6 | first gold | MAP |")
    out("|---|---|---:|---:|---:|---:|")

    totals = {"naive": [], "tuned": [], "union (shipped)": []}
    details = []
    for key in sorted(SPECS):
        spec = SPECS[key]
        gold = GOLD[key]
        runs = [
            ("naive", spec.naive_query, index.search(spec.naive_query, K)),
            ("tuned", spec.query, index.search(spec.query, K)),
            ("union (shipped)",
             f"{spec.query}  ++ {len(spec.keys)} per-row seed queries",
             retrieve(spec, index, spec.keys)),
        ]
        for label, q, hits in runs:
            s = score(hits, gold)
            totals[label].append(s)
            details.append((key, label, q, s, gold))
            out(f"| {key} | {label} | {s['p_at_k']:.2f} | {s['r_at_k']:.2f} | "
                f"{s['first'] if s['first'] else '—'} | {s['map']:.2f} |")

    out()
    for label in ("naive", "tuned", "union (shipped)"):
        rows = totals[label]
        out(f"**{label} mean** — P@6 {sum(r['p_at_k'] for r in rows)/len(rows):.2f}, "
            f"R@6 {sum(r['r_at_k'] for r in rows)/len(rows):.2f}, "
            f"MAP {sum(r['map'] for r in rows)/len(rows):.2f}")
    out()

    out("## What each query actually returned")
    out()
    for key, label, q, s, gold in details:
        out(f"### {key} — {label}")
        out()
        out(f"`{q}`")
        out()
        for rank, (cid, r) in enumerate(zip(s["ids"], s["rel"]), 1):
            out(f"{rank}. {'HIT ' if r else 'miss'} `{cid}`")
        missed = sorted(gold - set(s["ids"]))
        if missed:
            out()
            out(f"gold not retrieved: {', '.join('`'+m+'`' for m in missed)}")
        out()

    if args.write:
        p = ROOT / "out" / "retrieval_eval.md"
        p.parent.mkdir(exist_ok=True)
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
