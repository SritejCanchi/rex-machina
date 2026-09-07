"""
tools/drive_agents.py — multi-pass driver for recording real model turns.

The pipeline's prompts are built from prior stage output, so a critic prompt
cannot exist until the generator has answered. This driver runs the pipeline
repeatedly. On each pass it serves any reply already sitting in out/agent_out/
and, the first time it needs one that is missing, writes that prompt to
out/prompts/<role>.txt and stops.

    python tools/drive_agents.py          # advance one stage, report what is needed
    python tools/drive_agents.py --record # all replies present: write transcript/

Each reply in out/agent_out/ is produced by a separate agent that is given the
prompt file and nothing else. It cannot see validators.py, specs.py, the
fallback table or this driver, so the mistakes it makes are its own.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pipeline  # noqa: E402
from kb import build_index  # noqa: E402
from llm import prompt_hash  # noqa: E402
from specs import SPECS  # noqa: E402

AGENT_OUT = ROOT / "out" / "agent_out"
PROMPTS = ROOT / "out" / "prompts"
TRANSCRIPT = ROOT / "transcript"
RECORDED_BY = "claude-opus-5 (subagent, given only the prompt file)"


class Missing(RuntimeError):
    def __init__(self, role: str, path: Path):
        super().__init__(f"need a reply for {role}")
        self.role = role
        self.path = path


class DriverProvider:
    def __init__(self, record: bool):
        self.record = record
        self.needed: list[tuple[str, Path]] = []
        self.served = 0

    def complete(self, role: str, prompt: str, max_tokens: int = 2048) -> str:
        src = AGENT_OUT / f"{role}.json"
        if not src.exists():
            PROMPTS.mkdir(parents=True, exist_ok=True)
            p = PROMPTS / f"{role}.txt"
            p.write_text(prompt, encoding="utf-8")
            raise Missing(role, p)
        body = src.read_text(encoding="utf-8").strip()
        self.served += 1
        if self.record:
            h = prompt_hash(role, prompt)
            TRANSCRIPT.mkdir(parents=True, exist_ok=True)
            (TRANSCRIPT / f"{role}.{h}.json").write_text(json.dumps({
                "role": role,
                "model": None,
                "prompt_sha256_16": h,
                "prompt_chars": len(prompt),
                "response": body,
                "input_tokens": None,
                "output_tokens": None,
                "recorded_by": RECORDED_BY,
                "recorded_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "note": ("Produced by a subagent handed this prompt file and "
                         "nothing else. It could not see the gate, the specs "
                         "or the fallback table. No live Haiku 4.5 call."),
            }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true")
    args = ap.parse_args()

    if args.record:
        for stale in TRANSCRIPT.glob("*.json"):
            stale.unlink()

    index = build_index(ROOT / "data" / "kb")
    fallbacks = json.loads((ROOT / "data" / "fallbacks.json").read_text(encoding="utf-8"))
    provider = DriverProvider(record=args.record)

    missing = []
    for key in sorted(SPECS):
        try:
            pipeline.run_spec(SPECS[key], index, provider, fallbacks)
        except Missing as m:
            missing.append((m.role, m.path))

    if missing:
        print("prompts written, replies needed:")
        for role, p in missing:
            print(f"  {role:28} {p}")
        return 1

    print(f"all {provider.served} replies present"
          + (f"; transcript written to {TRANSCRIPT}" if args.record else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
