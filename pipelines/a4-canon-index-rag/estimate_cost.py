"""
estimate_cost.py — produce the cost figure rather than assert it.

Input is measured exactly: every prompt the pipeline builds is assembled and
its characters counted. Output is projected, not measured, because no live run
has been made; the projection uses the recorded reply lengths, which are real
JSON of the right shape but were authored rather than sampled.

    python estimate_cost.py
"""

from __future__ import annotations

import json
from pathlib import Path

from kb import build_index
from llm import prompt_hash
from pipeline import (batches, critic_prompt, generator_prompt, key_of,
                      parse_json_array, repair_prompt, retrieve, BATCH)
from specs import SPECS

ROOT = Path(__file__).parent
PRICE_IN, PRICE_OUT = 1.00, 5.00          # $/M tokens, Haiku 4.5, Jul 2026
CHARS_PER_TOKEN = (3.5, 4.0)              # the usual English band


def main() -> int:
    index = build_index(ROOT / "data" / "kb")
    tdir = ROOT / "transcript"
    recorded = {}
    for p in tdir.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        recorded[(d["role"], d["prompt_sha256_16"])] = d["response"]

    in_chars = out_chars = calls = 0
    per_type = {}

    for key in sorted(SPECS):
        spec = SPECS[key]
        hits = retrieve(spec, index, spec.keys)
        t_in = t_out = t_calls = 0

        for bi, kb_ in enumerate(batches(spec.keys, BATCH)):
            gp = generator_prompt(spec, hits, kb_)
            graw = recorded[(f"gen.{key}.{bi}", prompt_hash(f"gen.{key}.{bi}", gp))]
            rows = parse_json_array(graw, "gen")
            t_in += len(gp); t_out += len(graw); t_calls += 1

            cp = critic_prompt(spec, hits, rows)
            craw = recorded[(f"critic.{key}.{bi}", prompt_hash(f"critic.{key}.{bi}", cp))]
            verdicts = parse_json_array(craw, "critic")
            t_in += len(cp); t_out += len(craw); t_calls += 1

            jobs = [{"index": i, "row": rows[i], "violations": v["violations"]}
                    for i, v in enumerate(verdicts)
                    if v.get("verdict") == "fail" and v.get("violations")]
            if jobs:
                rp = repair_prompt(spec, hits, jobs)
                rraw = recorded[(f"repair.{key}.{bi}",
                                 prompt_hash(f"repair.{key}.{bi}", rp))]
                t_in += len(rp); t_out += len(rraw); t_calls += 1

        per_type[key] = (t_calls, t_in, t_out)
        calls += t_calls; in_chars += t_in; out_chars += t_out

    print("chars measured from the assembled prompts and the recorded replies\n")
    print(f"{'content type':18} {'calls':>6} {'in chars':>10} {'out chars':>10}")
    for k, (c, i, o) in per_type.items():
        print(f"{k:18} {c:>6} {i:>10,} {o:>10,}")
    print(f"{'TOTAL':18} {calls:>6} {in_chars:>10,} {out_chars:>10,}\n")

    for lo_hi, cpt in (("high", CHARS_PER_TOKEN[1]), ("low", CHARS_PER_TOKEN[0])):
        ti, to = in_chars / cpt, out_chars / cpt
        cost = ti / 1e6 * PRICE_IN + to / 1e6 * PRICE_OUT
        print(f"at {cpt} chars/token ({lo_hi} estimate): "
              f"{ti/1000:.1f}k in, {to/1000:.1f}k out -> ${cost:.4f}")

    lo = (in_chars / 4.0) / 1e6 * PRICE_IN + (out_chars / 4.0) / 1e6 * PRICE_OUT
    hi = (in_chars / 3.5) / 1e6 * PRICE_IN + (out_chars / 3.5) / 1e6 * PRICE_OUT
    print(f"\nfull content build: ${lo:.4f} to ${hi:.4f} at Haiku 4.5 "
          f"(${PRICE_IN:.0f}/M in, ${PRICE_OUT:.0f}/M out).")
    print("This is a build-time cost paid once by the developer. It is separate "
          "from\nthe ~$0.036 per-playthrough runtime budget in GDD §7.")
    print("\nLower bound. It assumes one pass per stage and counts only the "
          "prompts this\npipeline builds. It excludes retries and any SDK "
          "framing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
