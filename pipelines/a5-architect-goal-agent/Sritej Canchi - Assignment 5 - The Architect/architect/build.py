"""Take action: write the code for the top-scored gap, then verify it.

The prompt carries three things the model must respect:
  1. the GDD evidence for the feature, so the code implements the document
  2. the real source of every file it is allowed to touch, so the generated
     code follows existing patterns rather than inventing a house style
  3. an explicit output contract, so the reply can be parsed without guessing

Verification is not optional and is not the model's opinion. The generated
files must import, the existing test suite must pass, and the slice must still
be winnable. Anything less is recorded as a failure and rolled back.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

from . import llm

PROMPT = """You are a coding agent working inside an existing Python game.

THE GAME
Rex Machina, Act 3 vertical slice. A shelter dog crosses a tile arena to reach
a child while a robot dog predicts and intercepts. Standard library only. No
third-party imports are permitted.

THE FEATURE YOU ARE BUILDING
{name} ({key})

WHY IT WAS SELECTED
{reason}

WHAT THE GDD SAYS
{gdd}

CURRENT STATE IN THE CODEBASE
{status}: {evidence}

FILES YOU MAY MODIFY OR CREATE
{filelist}

CURRENT SOURCE OF THOSE FILES
{sources}

RULES
- Standard library only.
- Match the surrounding style: module docstring citing the GDD section, short
  comments explaining why rather than what, four-space indent, no type hints.
- Do not rename or delete anything that exists. Other modules import it.
- Do not leave hardcoded test values or debug prints.
- Every number you introduce must be traceable to the GDD text above.

OUTPUT CONTRACT
Reply with one JSON object and nothing else:
{{
  "files": [{{"path": "<relative path>", "contents": "<full new file text>"}}],
  "summary": "<one sentence on what changed>",
  "gdd_citations": ["<GDD section or quoted line per decision>"]
}}
Every file you list is written in full, so include unchanged parts too.
"""


def build_prompt(gap, gdd_evidence, code, targets):
    sources = "\n\n".join(
        "### %s\n```python\n%s\n```" % (t, code.modules.get(t, "(new file)"))
        for t in targets)
    return PROMPT.format(
        name=gap.feature.get("name", gap.key), key=gap.key,
        reason=gap.feature.get("reason", "highest utility score this run"),
        gdd=gdd_evidence, status=gap.status, evidence=gap.evidence,
        filelist="\n".join("- " + t for t in targets), sources=sources)


def generate(gap, gdd_evidence, code, targets, prov):
    prompt = build_prompt(gap, gdd_evidence, code, targets)
    reply = prov.complete("codegen." + gap.key, prompt, max_tokens=8000)
    return llm.parse_json(reply), prompt


def apply_and_verify(result, game_root, repo_root):
    """Write files into a scratch copy, verify, and only then commit them."""
    backup = tempfile.mkdtemp(prefix="architect-rollback-")
    shutil.copytree(game_root, os.path.join(backup, "game"))
    written = []
    try:
        for f in result["files"]:
            dest = os.path.join(game_root, f["path"])
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(f["contents"])
            written.append(f["path"])
        ok, report = verify(repo_root)
        if not ok:
            shutil.rmtree(game_root)
            shutil.copytree(os.path.join(backup, "game"), game_root)
            return False, written, report
        return True, written, report
    finally:
        shutil.rmtree(backup, ignore_errors=True)


def verify(repo_root):
    """Import check, then the test suite. Both must pass."""
    steps = [
        ("import", [sys.executable, "-c",
                    "import sys; sys.path.insert(0,'game'); import rex.loop"]),
        ("tests", [sys.executable, os.path.join("tests", "smoke.py")]),
    ]
    lines = []
    for label, cmd in steps:
        p = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
        lines.append("%s: %s" % (label, "pass" if p.returncode == 0 else "FAIL"))
        if p.returncode != 0:
            lines.append((p.stderr or p.stdout).strip()[-1200:])
            return False, "\n".join(lines)
    return True, "\n".join(lines)
