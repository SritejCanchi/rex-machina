# Build the two caption files from the shot list, timed to the recordings.
# Part 1 timings come from the demo log (wall clock of each STEP line minus
# the moment ffmpeg started); part 2 is fixed by the demo mode's own clock.
# ASS rather than SRT, so the canvas size is stated and the font size means
# what it says at 1080p.
import json, os
V = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
TRIM1 = 3.5   # seconds cut from the front of part 1 (empty terminal)

def secs(hms):
    h, m, s = hms.split(":"); return int(h)*3600 + int(m)*60 + float(s)

t = json.load(open(os.path.join(V, "times1.json")))
t0 = secs(t["t0"]); end1 = t["end"] - TRIM1
marks = {}
for line in open(os.path.join(V, "demo.log"), encoding="utf-8", errors="replace"):
    stamp = line[:12]
    try: at = secs(stamp) - t0 - TRIM1
    except ValueError: continue
    body = line[13:]
    if "pipeline run, prompt to engine" in body: marks.setdefault("title", at)
    for n in range(1, 7):
        if f"STEP {n} " in body: marks.setdefault(f"s{n}", at)
print("marks", {k: round(v, 1) for k, v in marks.items()}, "end", round(end1, 1))

P1 = [
  ("title", "s1", ["Rex Machina. This is the pipeline that made every line and every number in the game, run end to end.",
                   "Nothing here is typed. The script runs each stage in order."]),
  ("s1", "s2", ["Step 1, the Retry Read: the line the robot speaks after you lose.",
                "A generator drafts it. An evaluator checks it against five rules from the design document.",
                "A refiner rewrites from the rule that fired. A circuit breaker stops a line that will not converge.",
                "Six of six first drafts broke a rule. One escalated to the breaker."]),
  ("s2", "s3", ["Step 2, the Copy Desk: the style-guide agent.",
                "It scores journey narration out of ten against the house voice and rewrites from the reason.",
                "The generator never sees the style guide, so every catch is a break the model made on its own."]),
  ("s3", "s4", ["Step 3, engine integration. Each table the pipelines wrote is copied into the build byte for byte.",
                "The script hashes both ends and refuses to finish if any pair differs.",
                "No transform, no hand edit. The bytes the agent wrote are the bytes the game loads."]),
  ("s4", "s5", ["Step 4, headless tests. The game is played without a browser.",
                "A winning line exists from every journey outcome, the robot's veto holds,",
                "and every line it speaks is in a generated table. 29 tests, run before every deploy."]),
  ("s5", "s6", ["Step 5, the adversarial QA agent. It re-attempts the exploits the design document closed,",
                "then fuzzes three hundred fights. Fifteen hundred checks.",
                "It found three real bugs in an earlier build. They are fixed."]),
  ("s6", None, ["Step 6. A static server, and the game loading those exact files."]),
]
P2 = [
  (0.3, 8.3, ["The game, in the browser. The footer states what it loaded: 42 rows across 5 DataTables, unmodified."]),
  (8.6, 13.5, ["Act 3. The arena, the robot's reads and its retry lines all come from those tables."]),
  (13.8, 34.0, ["Watch the computer: a search over the robot's own decision model, playing the shortest line and saying why.",
                "The robot goes where you are about to be, not where you are. Every move is graded by that same search."]),
  (34.3, 47.5, ["Fifteen hundred checks, twenty-nine tests, five tables, one game.",
                "Every pipeline replays from recorded model turns, so all of this reproduces from a clean checkout with no key."]),
  (47.8, 57.5, ["Total cost of every model call across every pipeline for the whole capstone: twenty-five cents."]),
]

HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Segoe UI,36,&H00D2E6F0,&H00FFFFFF,&H6028140A,&H00000000,0,0,0,0,100,100,0,0,3,12,0,2,200,200,42,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def fmt(s):
    s = max(0.0, s); h = int(s // 3600); m = int(s % 3600 // 60); sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"

def write_ass(path, blocks):
    out = [HEAD]
    for a, b, lines in blocks:
        span = b - a; gap = 0.25
        each = (span - gap * (len(lines) - 1)) / len(lines)
        for i, text in enumerate(lines):
            s = a + i * (each + gap); e = s + each
            out.append(f"Dialogue: 0,{fmt(s)},{fmt(e)},Cap,,0,0,0,,{text}\n")
    open(path, "w", encoding="utf-8").write("".join(out))

blocks1 = []
for a, b, lines in P1:
    start = marks[a]; stop = marks[b] if b else end1
    blocks1.append((start + 0.3, stop - 0.3, lines))
write_ass(os.path.join(V, "p1.ass"), blocks1)
write_ass(os.path.join(V, "p2.ass"), P2)
print("wrote p1.ass and p2.ass")
