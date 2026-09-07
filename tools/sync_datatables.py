#!/usr/bin/env python3
"""Copy every pipeline output into the web build, unmodified, and prove it.

This is the engine integration step. No hand editing, no reformatting: the
JSON the pipelines emit is the JSON the game loads. The script copies each
file, records a sha256 of the source and the destination, and refuses to
finish if any pair differs.

    python tools/sync_datatables.py --pipelines "..\\Deliverables"
"""
import argparse
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# where each table comes from, by assignment
SOURCES = [
    ("DT_NemesisReads.json",  "Sritej Canchi - Assignment 4 - The Canon Index/out",
     "A4 Canon Index", "24 boss read lines, 8 categories x 3 charge bands"),
    ("DT_ArenaPhases.json",   "Sritej Canchi - Assignment 4 - The Canon Index/out",
     "A4 Canon Index", "3 Act 3 arena phases with exits and cover"),
    ("DT_JourneyHazards.json", "Sritej Canchi - Assignment 4 - The Canon Index/out",
     "A4 Canon Index", "6 Act 1-2 chase encounters with telegraphs and windows"),
    ("DT_RetryReads.json",    "Sritej Canchi - Assignment 6 - The Retry Read/out",
     "A6 Retry Read", "6 lines the boss speaks when you respawn"),
    ("DT_JourneyBeats.json",  "Sritej Canchi - Assignment 7 - The Copy Desk/out",
     "A7 Copy Desk", "3 journey beats, style-checked"),
]


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pipelines", default=os.path.join(HERE, "..", "Deliverables"),
                    help="folder holding the assignment output folders")
    args = ap.parse_args()

    dest_dir = os.path.join(HERE, "data")
    os.makedirs(dest_dir, exist_ok=True)
    manifest, failed = [], 0

    for name, rel, origin, what in SOURCES:
        src = os.path.join(args.pipelines, rel, name)
        dst = os.path.join(dest_dir, name)
        if not os.path.exists(src):
            print("  MISSING  %-24s expected at %s" % (name, src))
            failed += 1
            continue
        shutil.copyfile(src, dst)
        a, b = sha(src), sha(dst)
        rows = len(json.load(open(dst, encoding="utf-8")))
        ok = a == b
        failed += 0 if ok else 1
        print("  %s %-24s %2d rows  from %s" % ("copied " if ok else "MISMATCH",
                                                name, rows, origin))
        manifest.append({"file": name, "rows": rows, "from": origin,
                         "contains": what, "sha256": a, "identical": ok})

    with open(os.path.join(dest_dir, "MANIFEST.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print("\n%d tables, %d problems. Every byte in data/ came from a pipeline run."
          % (len(manifest), failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
