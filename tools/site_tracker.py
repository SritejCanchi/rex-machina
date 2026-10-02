"""Regenerate the Scope section and the Task tracker on the case-study page.

    python tools/site_tracker.py

Edit ROWS below (status: done, prog, todo) and re-run. The headline counts, the
status bar and the per-category tallies are computed from ROWS, so they cannot
drift from the table. Safe to re-run: it replaces the existing sections.
"""
import io, os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site", "index.html")

# (id, type, category, title, status, parent)
ROWS = [
    ("RM-1",  "Task", "Design",           "Design document as an engineering contract, rebuilt after a stress test", "done", None),
    ("RM-2",  "Task", "Content", "Retrieval over the design doc writes Rex's lines, the arenas and the encounters", "done", None),
    ("RM-3",  "Task", "Content", "Retry lines: draft, rule check, rewrite, with a circuit breaker", "done", None),
    ("RM-4",  "Task", "Content", "Narration scored by a style judge, calibrated over three runs", "done", None),
    ("RM-5",  "Task", "Content", "Narrative engine: two agents sharing one JSON ledger", "done", None),
    ("RM-6",  "Task", "Content", "End-to-end run: checksum sync, record and replay, cost audit", "done", None),
    ("RM-7",  "Task", "Gameplay",         "Rex as a goal-oriented agent: perceive, predict, intercept, veto", "done", None),
    ("RM-8",  "Task", "Gameplay",         "Random boards proven winnable by search before play", "done", None),
    ("RM-9",  "Task", "QA",               "Adversarial QA agent: 15 strategies, about 3,000 checks a run", "done", None),
    ("RM-10", "Bug",  "Content",          "RM-001: Rex named a direction the player never favoured", "done", None),
    ("RM-11", "Bug",  "Gameplay",         "RM-002: stamina could drop below zero", "done", None),
    ("RM-12", "Bug",  "Gameplay",         "RM-003: pressing into a wall gave no feedback", "done", None),
    ("RM-13", "Bug",  "Content",          "&ldquo;Same exit&rdquo; lines claim two approaches, the trigger fires on one", "todo", None),
    ("RM-14", "Bug",  "Content",          "A trigger threshold is 0.6 in the code and 0.65 in the table", "todo", None),
    ("RM-15", "Task", "QA",               "A human-scored set to calibrate the style judge", "todo", None),
    ("RM-16", "Task", "QA",               "Run every check on each push and pull request (GitHub Actions)", "done", None),
    ("RM-17", "Task", "Unreal port",      "Unreal 5.5 build driven by the same tables", "prog", None),
    ("RM-17.1", "Sub-task", "Unreal port", "18 Blueprint graphs generated as text, linted, self-tested", "done", "RM-17"),
    ("RM-17.2", "Sub-task", "Unreal port", "Windows package built from a script", "done", "RM-17"),
    ("RM-17.3", "Sub-task", "Unreal port", "Seven sound families imported and verified", "done", "RM-17"),
    ("RM-17.4", "Sub-task", "Unreal port", "Wire the sounds into the graphs", "todo", "RM-17"),
    ("RM-18", "Task", "Unity port",       "Unity 6.6 build, made with Unity AI", "prog", None),
    ("RM-18.1", "Sub-task", "Unity port", "Load the tables and build the first arena", "done", "RM-18"),
    ("RM-18.2", "Sub-task", "Unity port", "Port Rex's turn to C# with Plan, then Agent mode", "done", "RM-18"),
    ("RM-18.3", "Sub-task", "Unity port", "Parity replay against <code>game.js</code>: 48 of 48 turns", "done", "RM-18"),
    ("RM-18.4", "Bug",      "Unity port", "The C# port counted refused moves as turns", "done", "RM-18"),
    ("RM-18.5", "Sub-task", "Unity port", "Pixel-perfect camera, using a Unity plugin skill", "done", "RM-18"),
    ("RM-18.6", "Sub-task", "Unity port", "Project skill and the ten-run repeat check", "done", "RM-18"),
    ("RM-18.7", "Sub-task", "Unity port", "Pick a Rex sprite from three generated, remove its background", "prog", "RM-18"),
    ("RM-18.8", "Sub-task", "Unity port", "Voice Rex's 24 lines", "todo", "RM-18"),
    ("RM-18.9", "Sub-task", "Unity port", "Player input, HUD, win and lose", "todo", "RM-18"),
    ("RM-18.10","Sub-task", "Unity port", "The six road encounters", "todo", "RM-18"),
    ("RM-19", "Task", "Release",          "Browser build on itch.io", "done", None),
    ("RM-20", "Task", "Release",          "Windows build on itch.io", "todo", None),
    ("RM-21", "Task", "QA",               "Unit tests for Rex's logic and the tables: 27 cases", "done", None),
    ("RM-22", "Task", "QA",               "End-to-end test: the computer plays the whole game in Chromium", "done", None),
    ("RM-23", "Task", "QA",               "QA agent seeded so failures replay, and failing the run on any finding", "done", None),
    ("RM-24", "Bug",  "Content",          "Two table hashes depended on Windows line endings", "done", None),
    ("RM-25", "Bug",  "Release",          "The game page is 749 px wide on a 390 px phone", "todo", None),
]

LABEL = {"done": "Done", "prog": "In progress", "todo": "To do"}
n = len(ROWS)
cnt = {k: sum(1 for r in ROWS if r[4] == k) for k in LABEL}
bugs_open = sum(1 for r in ROWS if r[1] == "Bug" and r[4] != "done")
bugs_all = sum(1 for r in ROWS if r[1] == "Bug")
cats = []
for r in ROWS:
    if r[2] not in cats: cats.append(r[2])

def pct(k): return round(100 * cnt[k] / n, 1)

rows_html = []
for rid, typ, cat, title, st, parent in ROWS:
    cls = ' class="sub"' if parent else ""
    t = '<span class="ty bug">Bug</span>' if typ == "Bug" else f'<span class="ty">{typ}</span>'
    rows_html.append(f'    <tr{cls}><td class="id">{rid}</td><td>{title}</td><td>{t}</td><td>{cat}</td><td><span class="st st-{st}">{LABEL[st]}</span></td></tr>')

cat_rows = []
for c in cats:
    g = [r for r in ROWS if r[2] == c]
    d = sum(1 for r in g if r[4] == "done")
    cat_rows.append(f'<li><strong>{c}</strong> {d} of {len(g)} done</li>')

section = f'''
<h2 id="scope">Scope</h2>
<p><strong>Purpose.</strong> A capstone for a seven-week course on multi-agent AI for game development. The aim was to learn, on one small game built end to end, where agents earn a place in a game team's workflow, what they cost, and how to check them. The Unity work carries the same questions into AI built into an editor.</p>
<div class="scope">
  <div>
    <h3>Covered</h3>
    <ul>
      <li>Agent pipelines that write all of the game's text, with a record of where each row came from</li>
      <li>Rex's decision logic, and the rules that keep its lines true</li>
      <li>An adversarial QA agent, and checks on the checkers</li>
      <li>Model choice and cost, measured rather than estimated</li>
      <li>Ports to Unreal 5.5 and Unity 6.6, both reading the same tables</li>
      <li>Unity AI used on real tasks and evaluated</li>
    </ul>
  </div>
  <div>
    <h3>Not covered</h3>
    <ul>
      <li>Generated art or sound in a shipped build. The art is drawn in code or comes from free Kenney asset kits</li>
      <li>Model calls during play</li>
      <li>Playtests or player data at scale</li>
      <li>Multiplayer, mobile or monetization</li>
      <li>Automated builds, and blocking a merge when a check fails</li>
      <li>Production polish. The Unreal and Unity builds are prototypes</li>
    </ul>
  </div>
</div>
<h3>Current work</h3>
<ul>
  <li>Finishing the Unity port: player input, the HUD, and the six road encounters</li>
  <li>Fixing the two content-rule mismatches the Unity evaluation found in the shipped game</li>
  <li>Choosing Rex's sprite and voicing its 24 lines</li>
</ul>

<h2 id="tracker">Task tracker</h2>
<div class="tracker-head">
  <p class="headline"><mark>{cnt["done"]} of {n} items done, {cnt["prog"]} in progress, {cnt["todo"]} to do.</mark> All ten course assignments and the browser release are complete. The open work is the two ports and three bugs.</p>
  <div class="bar" role="img" aria-label="{cnt['done']} done, {cnt['prog']} in progress, {cnt['todo']} to do">
    <span class="b-done" style="width:{pct('done')}%"></span><span class="b-prog" style="width:{pct('prog')}%"></span><span class="b-todo" style="width:{pct('todo')}%"></span>
  </div>
  <p class="legend"><span class="st st-done">Done {cnt["done"]}</span> <span class="st st-prog">In progress {cnt["prog"]}</span> <span class="st st-todo">To do {cnt["todo"]}</span> <span class="sep">&middot;</span> Bugs: {bugs_all} logged, {bugs_open} open</p>
  <ul class="cats">{"".join(cat_rows)}</ul>
</div>
<div class="scroll">
<table class="t-map tracker">
  <thead><tr><th>ID</th><th>Item</th><th>Type</th><th>Category</th><th>Status</th></tr></thead>
  <tbody>
{chr(10).join(rows_html)}
  </tbody>
</table>
</div>
<p class="note">Sub-tasks sit under their parent task. Bugs RM-001 to RM-003 were found by the QA agent, RM-13 and RM-14 by the Unity AI evaluation, RM-18.4 by the parity replay, RM-24 by the data test and RM-25 by the end-to-end test.</p>

'''

css = """
  .scope{display:grid;grid-template-columns:1fr 1fr;gap:6px 28px}
  .scope h3{margin-top:14px}
  .scope ul{padding-left:20px;margin:0}
  .scope li{margin:0 0 6px}
  .tracker-head{background:var(--soft);border:1px solid var(--line);border-radius:6px;padding:14px 18px 8px;margin:10px 0 12px}
  .headline{margin:0 0 10px}
  .bar{display:flex;height:10px;border-radius:5px;overflow:hidden;background:var(--todo-bg);margin:0 0 10px}
  .bar span{display:block;height:100%}
  .b-done{background:var(--done-fg)} .b-prog{background:var(--prog-fg)} .b-todo{background:var(--todo-bg)}
  .legend{font-size:14px;color:var(--muted);margin:0 0 8px}
  .legend .sep{margin:0 4px}
  .cats{list-style:none;padding:0;margin:0 0 4px;display:flex;flex-wrap:wrap;gap:4px 16px;font-size:13.5px;color:var(--muted)}
  .cats strong{color:var(--text);font-weight:600;margin-right:4px}
  .st{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12.5px;font-weight:600;white-space:nowrap}
  .st-done{background:var(--done-bg);color:var(--done-fg)}
  .st-prog{background:var(--prog-bg);color:var(--prog-fg)}
  .st-todo{background:var(--todo-bg);color:var(--todo-fg)}
  .tracker td{font-size:15px}
  .tracker td.id{font-variant-numeric:tabular-nums;color:var(--muted);font-size:13.5px}
  table.tracker td.id,table.tracker td:nth-child(4){white-space:nowrap}
  .tracker tr.sub td:nth-child(2){padding-left:18px;position:relative}
  .tracker tr.sub td:nth-child(2)::before{content:"\\21B3";position:absolute;left:2px;color:var(--muted)}
  .ty{font-size:13.5px;color:var(--muted);white-space:nowrap}
  .ty.bug{color:var(--bug);font-weight:600}
"""

s = io.open(P, encoding="utf-8").read()
if 'id="scope"' in s:
    a = s.index('<h2 id="scope">'); b = s.index('<h2 id="cost">')
    s = s[:a] + s[b:]
    s = s.replace(css, "", 1)
    s = s.replace("    .scope{grid-template-columns:1fr}\n    .tracker th:nth-child(4),.tracker td:nth-child(4){display:none}\n", "", 1)
i = s.index('<h2 id="cost">')
s = s[:i] + section.strip() + "\n\n" + s[i:]
s = s.replace("  .note{font-size:14.5px;color:var(--muted)}", "  .note{font-size:14.5px;color:var(--muted)}" + css, 1)
s = s.replace("    .pair{grid-template-columns:1fr}\n", "    .pair{grid-template-columns:1fr}\n    .scope{grid-template-columns:1fr}\n    .tracker th:nth-child(4),.tracker td:nth-child(4){display:none}\n", 1)
io.open(P, "w", encoding="utf-8").write(s)
print(n, cnt, "bugs", bugs_all, "open", bugs_open, cats)
