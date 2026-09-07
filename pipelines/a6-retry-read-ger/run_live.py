#!/usr/bin/env python3
"""One command for the live run. Everything except supplying the key.

    python run_live.py

Set ANTHROPIC_API_KEY in your shell first. This script never reads, prints or
stores the key. Child output streams as it arrives, so a slow call looks slow
rather than looking hung.
"""
import os
import subprocess
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(ROOT, "live_run_output.txt")
lines = []


def say(text=""):
    print(text, flush=True)
    lines.append(text)


def run(label, cmd):
    say("")
    say("=" * 70)
    say("%s   $ %s" % (label, " ".join(cmd)))
    say("=" * 70)
    p = subprocess.Popen([sys.executable, "-u"] + cmd, cwd=ROOT,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    for line in p.stdout:
        say(line.rstrip())
    p.wait()
    return p.returncode


def main():
    say("Rex Machina, Assignment 6 live run")
    say(datetime.now().strftime("%Y-%m-%d %H:%M local"))
    say("python %s" % sys.version.split()[0])

    if not os.environ.get("ANTHROPIC_API_KEY"):
        say("")
        say("ANTHROPIC_API_KEY is not set in this shell.")
        say('  PowerShell:  $env:ANTHROPIC_API_KEY = "your-key"')
        say("  cmd.exe:     set ANTHROPIC_API_KEY=your-key")
        say("  bash or zsh: export ANTHROPIC_API_KEY=your-key")
        say("")
        say("Then run this again. Nothing was changed.")
        _write()
        return 1
    say("key: present in environment (value not read by this script)")

    rc = run("STEP 1 of 2, the GER pipeline", ["pipeline.py", "--live"])
    if rc:
        say("")
        say("The pipeline did not finish cleanly.")
        say("If the message mentions credit balance, the API needs credits.")
        say("A Max plan covers Claude.ai and Claude Code, not the API.")

    run("STEP 2 of 2, the rule tests", ["tests/test_ger.py"])

    say("")
    say("=" * 70)
    say("Done. Send live_run_output.txt back. It contains no key.")
    say("=" * 70)
    _write()
    return 0


def _write():
    with open(LOG, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\nwrote %s" % LOG, flush=True)


if __name__ == "__main__":
    sys.exit(main())
