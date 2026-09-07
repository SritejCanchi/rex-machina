#!/usr/bin/env python3
"""One command for the live run. Everything except supplying the key.

    python run_live.py

Set ANTHROPIC_API_KEY in your shell first. This script never reads, prints,
stores or transmits the key beyond handing it to the agent's own provider, and
it will refuse to run if the key is not already in the environment.

What it does, in order:
  1. checks the key is present, without showing it
  2. backs up transcript/ to transcript_recorded/ so the shipped turns survive
  3. dry run, so you see the choice before anything is written
  4. the live run
  5. the test suite
  6. writes live_run_output.txt, which is the file to send back

Nothing here needs a network connection except step 4.
"""
import os
import shutil
import subprocess
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(ROOT, "live_run_output.txt")
lines = []


def say(text=""):
    print(text)
    lines.append(text)


def run(label, cmd):
    say("")
    say("=" * 70)
    say("%s   $ %s" % (label, " ".join(cmd[1:])))
    say("=" * 70)
    p = subprocess.run([sys.executable] + cmd[1:], cwd=ROOT,
                       capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    for line in out.rstrip().splitlines():
        say(line)
    return p.returncode


def main():
    say("Rex Machina, Assignment 5 live run")
    say(datetime.now().strftime("%Y-%m-%d %H:%M local"))
    say("python %s" % sys.version.split()[0])

    if not os.environ.get("ANTHROPIC_API_KEY"):
        say("")
        say("ANTHROPIC_API_KEY is not set in this shell.")
        say("")
        say("  PowerShell:  $env:ANTHROPIC_API_KEY = \"<your key>\"")
        say("  cmd.exe:     set ANTHROPIC_API_KEY=<your key>")
        say("  bash:        export ANTHROPIC_API_KEY=<your key>")
        say("")
        say("Then run this script again. Nothing was changed.")
        _write()
        return 1
    say("key: present in environment (value not read by this script)")

    src = os.path.join(ROOT, "transcript")
    dst = os.path.join(ROOT, "transcript_recorded")
    if os.path.isdir(src) and not os.path.isdir(dst):
        shutil.copytree(src, dst)
        say("backed up transcript/ to transcript_recorded/")
    else:
        say("transcript_recorded/ already present, leaving it alone")

    if run("STEP 1 of 3, dry run", ["py", "architect/architect.py", "--dry-run"]):
        say("\nDry run failed. Nothing was written. Stopping.")
        _write()
        return 1

    rc = run("STEP 2 of 3, live run", ["py", "architect/architect.py", "--live"])
    if rc:
        say("")
        say("The live run did not finish cleanly.")
        say("If the message mentions credit balance, the API needs credits.")
        say("A Max plan covers Claude.ai and Claude Code, not the API.")
        say("The game itself is untouched. state/FAILED.md has the detail if the")
        say("model replied but its code failed verification.")

    run("STEP 3 of 3, test suite", ["py", "tests/test_architect.py"])

    say("")
    say("=" * 70)
    say("Done. Send live_run_output.txt back. It contains no key.")
    say("=" * 70)
    _write()
    return 0


def _write():
    with open(LOG, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\nwrote %s" % LOG)


if __name__ == "__main__":
    sys.exit(main())
