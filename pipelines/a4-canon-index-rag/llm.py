"""
llm.py — the model boundary.

Two providers, one interface.

  live    calls claude-haiku-4-5 through the Anthropic SDK. Used when
          ANTHROPIC_API_KEY is set and --live is passed.

  replay  looks the prompt up in transcript/ by SHA-256 and returns the
          recorded reply. Deterministic, offline, free, and the mode the
          shipped artefacts in out/ were produced in.

The replay key is a hash of the *whole* prompt, retrieved chunks included.
That is deliberate. If the knowledge base or the retriever changes, the hash
changes, replay misses, and the pipeline stops with the new prompt written to
disk rather than quietly serving a stale answer against fresh context.

PROVENANCE. Every transcript entry records which model produced it. The
entries shipped in this submission are marked
`claude-opus-5 (session, roleplaying the agent)`: no live Haiku 4.5 call has
been made from this project, exactly as was true of Assignment #3. What that
does and does not evidence is set out in the README under "Known limits".
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

MODEL_LIVE = "claude-haiku-4-5-20251001"
TRANSCRIPT_DIR = Path(__file__).parent / "transcript"
MISSING_DIR = TRANSCRIPT_DIR / "_missing"


def prompt_hash(role: str, prompt: str) -> str:
    return hashlib.sha256(f"{role}\n---\n{prompt}".encode("utf-8")).hexdigest()[:16]


class TranscriptMiss(RuntimeError):
    pass


class ReplayProvider:
    """Serves recorded replies. Never touches the network."""

    name = "replay"

    def __init__(self, directory: Path = TRANSCRIPT_DIR):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses: list[str] = []

    def complete(self, role: str, prompt: str, max_tokens: int = 2048) -> str:
        h = prompt_hash(role, prompt)
        path = self.dir / f"{role}.{h}.json"
        if not path.exists():
            MISSING_DIR.mkdir(parents=True, exist_ok=True)
            (MISSING_DIR / f"{role}.{h}.prompt.txt").write_text(
                prompt, encoding="utf-8")
            self.misses.append(f"{role}.{h}")
            raise TranscriptMiss(
                f"no recorded reply for {role}.{h}. The prompt was written to "
                f"{MISSING_DIR / f'{role}.{h}.prompt.txt'}. Either re-run with "
                f"--live and a key, or record a reply at {path}."
            )
        self.hits += 1
        return json.loads(path.read_text(encoding="utf-8"))["response"]

    def usage(self) -> dict:
        return {"provider": "replay", "calls": self.hits,
                "input_tokens": None, "output_tokens": None, "cost_usd": None}


class LiveProvider:
    """Calls Claude Haiku 4.5 and records every exchange into transcript/,
    so a live run reproduces offline afterwards."""

    name = "live"

    # Anthropic list pricing, Jul 2026, per the GDD §7 assumption block.
    PRICE_IN_PER_M = 1.00
    PRICE_OUT_PER_M = 5.00

    def __init__(self, model: str = MODEL_LIVE, record: bool = True):
        try:
            import anthropic
        except ImportError as exc:                       # pragma: no cover
            raise RuntimeError(
                "live mode needs the anthropic SDK: pip install anthropic"
            ) from exc
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("live mode needs ANTHROPIC_API_KEY in the environment")
        self.client = anthropic.Anthropic()
        self.model = model
        self.record = record
        self.calls = 0
        self.tok_in = 0
        self.tok_out = 0

    def complete(self, role: str, prompt: str, max_tokens: int = 2048) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        self.calls += 1
        self.tok_in += resp.usage.input_tokens
        self.tok_out += resp.usage.output_tokens
        if self.record:
            h = prompt_hash(role, prompt)
            TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
            (TRANSCRIPT_DIR / f"{role}.{h}.json").write_text(json.dumps({
                "role": role,
                "model": self.model,
                "prompt_sha256_16": h,
                "prompt_chars": len(prompt),
                "response": text,
                "input_tokens": resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens,
                "recorded_by": self.model,
                "recorded_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                 time.gmtime()),
            }, indent=2), encoding="utf-8")
        return text

    def usage(self) -> dict:
        cost = (self.tok_in / 1e6) * self.PRICE_IN_PER_M + \
               (self.tok_out / 1e6) * self.PRICE_OUT_PER_M
        return {"provider": "live", "model": self.model, "calls": self.calls,
                "input_tokens": self.tok_in, "output_tokens": self.tok_out,
                "cost_usd": round(cost, 5)}


def get_provider(live: bool = False):
    return LiveProvider() if live else ReplayProvider()
