# Making the robot speak

`SpeakRead` is the other half of the One Wow and the largest thing still
missing. This is the design, worked out against the data rather than guessed,
so the build is mechanical once the editor cooperates.

## What the data allows

Three findings that each remove a large amount of graph.

### 1. The row key is arithmetic, not a search

`game.js` searches the table:

```js
const row = DT.DT_NemesisReads.find(r => r.ReadCategory===cat && r.ChargeBand===band());
```

The imported table does not need searching. Its row names are positional and
the layout is perfectly regular -- eight categories, three bands, in a fixed
order:

    index = band_index * 8 + category_index
    row   = "DT_NemesisReads_" + two digits

    band_index      clinical 0, confident 1, strained 2
    category_index  sealing_direction 0, cover_habit 1, exit_fixation 2,
                    periodicity_called 3, stall_detected 4, gait_read 5,
                    charge_strain 6, prior_attempt 7

So the lookup is one `GetDataTableRow` with a computed name, not a scan. Zero
padding without a branch: `Right(Conv_IntToString(index + 100), 2)` gives
"00".."23".

This couples the graph to the row ordering in
`pipelines/a4-canon-index-rag/out/DT_NemesisReads.csv`. If that pipeline ever
reorders its output, the wrong line gets spoken with no error. Worth an
assertion that pins one known index to its expected line.

### 2. `Moves` never exceeds 15, so "the last 20" is the whole array

`FreqSpan` is 20 and `MaxRounds` is 15, and `Moves` only grows on an accepted
move. So `S.moves.slice(-FREQ)` is always all of `Moves` and `DirFreq` needs no
slicing.

**This holds only while `CheckEnd` stops the fight at 15 rounds.** Right now
nothing stops it, so the invariant is not yet true in the running build --
`CheckEnd` has to land with `DirFreq`, not after it.

### 3. Counting a direction needs no loop

With no slicing, the counts come out of one string:

    joined   = JoinStringArray(Moves, ",")
    count(d) = (Len(joined) - Len(Replace(joined, d, ""))) / Len(d)

None of left/right/up/down is a substring of another, and "wait" contains none
of them, so the four counts are exact and the non-wait total is their sum.

That is about 40 nodes. Unrolling twenty slots by four directions would have
been about 400, and a loop would have needed a macro-instance node class
captured. Neither is necessary.

The frequency threshold needs no division either --
`count / n >= 0.45` is `count * 100 >= 45 * n` in integers.

### 4. The direction guard collapses to one comparison

`qa/adversary.js` finding RM-001: the generated `sealing_direction` lines all
name "left", but the trigger fires whenever *any* direction dominates, so the
robot told a right-running dog it favoured left. `game.js` guards it with a
regex over the line text.

Checked against all 24 rows: **only `sealing_direction` lines name a direction,
and all three name "left"**. So the guard is exactly

    sealing_direction fires only when the dominant direction is "left"

which is one comparison instead of a regex. Data-shaped: if the reads are ever
regenerated with other directions, this has to become general again.

## Scope

Tier 0 is the four cheap categories, which reach 12 of the 24 lines:

| Category | Trigger | Cost |
|---|---|---|
| `sealing_direction` | max count * 100 >= 45 * n, and dominant is "left" | DirFreq |
| `stall_detected` | two or more "wait" in the last four | small |
| `charge_strain` | `Charge < BandConfident` | one compare |
| `gait_read` | `Limping` | free |

`periodicity_called`, `cover_habit` and `exit_fixation` are Tier 1 -- the first
needs `Periodicity`, the other two need the phase tile arrays parsed.

Priority order follows `game.js`: sealing_direction, stall_detected,
charge_strain, gait_read. First one that fires and is not `LastCategory` and
whose line is not already in `SpokenLines` wins.

## Build order

1. **Capture** `K2Node_GetDataTableRow`, `K2Node_BreakStruct` for
   `F_NemesisRead`, and the string nodes `JoinStringArray`, `Len`, `Replace`,
   plus `Array_Contains`. One editor pass, one Ctrl+C.
2. Add an `Ended` boolean variable.
3. Generate `DirFreq`, `SpeakRead`, `CheckEnd`.
4. Regenerate `OnPlayerMove` to call `SpeakRead` and `CheckEnd`, and to guard
   its branch on `Ended`. It currently calls neither, so this is a re-paste,
   not an edit.
5. Assertions: a known row index maps to its expected line; a seeded `Moves`
   produces the expected dominant direction; the direction guard suppresses a
   right-running dog; `CheckEnd` wins on arrival and loses at 15 rounds.

Everything except step 1 is generator work and needs no editor decisions.

---

## What got built

All five steps are done and the six assertions from step 5 pass, along with
the twenty-eight that were already there. Three things came out differently
from the plan and are worth recording.

**`GetDataTableRow` was never needed.** Step 1 assumed a struct read and a
Break node whose pin names would be GUID-suffixed and therefore unguessable
from outside the editor. `GetDataTableColumnAsString` returns the whole `Line`
column as a plain string array instead, so the read is an Array_Get on an
index, and no node had to be captured at all.

**`DirFreq` and `FiringCategories` were not built as functions.** Both still
exist on the Blueprint as empty stubs. The direction counts are four Replace
and Len pairs inlined in `SpeakRead`, and the category selection is the
`RM_SrSel*` / `RM_SrSeen*` chain, also inlined. Splitting either one out would
mean returning an array across a function boundary for no gain at this size --
`SpeakRead` is 146 nodes and every one of them is reachable from a single
entry. If a second caller ever needs the counts, `DirFreq` is where they go.
Until then the stubs are dead names on the class, and that is the honest
description of them.

**The tail order is load-bearing, and both wrong orders shipped.**
`chosen_line` and `chosen_cat` are pure, so they are recomputed wherever they
are used, and both read `LastCatIndex` and `SpokenLines` -- exactly the two
things the tail writes. Writing `LastCatIndex` first made the winning category
ineligible on the recompute, so the print fell back to row 0 while the record
was correct; appending to `SpokenLines` first did the mirror image. The fix is
a `PendingLine` string variable: latch the line while the state is still
clean, write `LastCatIndex` next (it still reads clean state), then print and
append from the latch. Neither wrong version failed to compile and neither
logged anything.
