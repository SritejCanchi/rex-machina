#!/usr/bin/env python3
"""Play it yourself. Needs a key, because every turn is a real call.

    python play.py

Type what you do. `ledger` prints the state, `q` quits.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dm import llm, session                                   # noqa: E402
from dm.ledger import Ledger                                  # noqa: E402


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY first. Every turn here is a live call.")
        return 1
    prov = llm.provider("live")
    led = Ledger()
    print("=" * 62)
    print("REX MACHINA, the nine days")
    print("=" * 62)
    print(led.w["premise"])
    n = 0
    while True:
        scene = led.scene()
        print("\n  day %d, %s" % (led.day, scene["place"]))
        print("  %s" % scene["sees"])
        raw = input("\n  > ").strip()
        if raw.lower() in ("q", "quit"):
            return 0
        if raw.lower() == "ledger":
            import json
            print(json.dumps(led.as_dict(), indent=1))
            continue
        if not raw:
            continue
        n += 1
        rec = session.turn(prov, led, raw, tag=".live%d" % n)
        print("\n  %s" % rec["narration"])
        if rec["changes"]:
            print("\n  [ledger: %s]" % ", ".join(rec["changes"]))
        if rec["flags"]:
            print("  [consistency: %s]"
                  % "; ".join("%s %s" % f for f in rec["flags"]))


if __name__ == "__main__":
    sys.exit(main())
