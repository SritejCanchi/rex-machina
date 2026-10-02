---
name: rex-machina-reads
description: Use for any question about Rex's Nemesis Reads, what Rex says or when, the boss turn, or porting boss logic in the Rex Machina project. Enforces that every spoken line is true of the running game, verified by simulation.
required_editor_version: ">=6000.0.0"
---
### Rex Machina: reads must be true of the running game

Rex is the boss agent. It speaks lines from `Assets/RexMachina/Data/NemesisReads.asset`
(source: `Assets/RexMachina/Data/DT_NemesisReads.json`). The turn logic lives in
`Assets/RexMachina/Scripts/NemesisTurnLogic.cs`, ported from
`Assets/RexMachina/Reference/game.js.txt`.

The rule that matters more than any other: **a line Rex says must be true of what the
player actually did.** A read that misreports the observable it cites is worse than silence.

When answering a question about which reads fire, or when changing boss logic:

1. Do not answer from the JSON alone. The JSON `TriggerCondition` column is the design
   intent; the code is what runs. Read `NemesisTurnLogic.FiringCategories` and `SpeakRead`.
2. Never assume the game substitutes words into a line at runtime. It does not. Lines are
   spoken verbatim or not at all.
3. Rule RM-001: a line that names a compass direction is held back unless that direction is
   the player's dominant one (`GetDominantDirection`).
4. A refused move (into the fence, or onto Rex's tile) is not a turn: nothing is recorded,
   Rex does not act, nothing is spoken.
5. Verify by simulation. Run `NemesisTurnLogic.ExecuteTurn` on a fresh `NemesisTurnState`
   for the move sequence in question and report the lines actually returned, turn by turn.
   Start from the scene's values unless the user gives others: dog (4,6), Rex (4,3),
   charge 100, stamina 17, exits (0,4) and (9,7), cover (3,5) and (6,2), grid 10x10.
6. For every line that is spoken, check that its words are true of the move history. Flag any
   line whose claim the trigger does not establish (for example a line that says something
   happened "twice" when the trigger fires on one occurrence).
7. End the answer with one line: `Verified by simulation: yes` or `Verified by simulation: no`,
   and if no, say why.
