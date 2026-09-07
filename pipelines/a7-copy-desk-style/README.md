# The Copy Desk

**Assignment #7, Style Guide Agent. Rex Machina capstone.**

A Generator that writes journey narration, an Evaluator that scores it against
the game's house style out of ten and says why, and a Refiner that rewrites it
from that reason. No human touches the loop once it starts.

Run it with `python pipeline.py`. Nothing to install.

---

## Where this fits in the pipeline

This Style Guide Agent runs immediately after the Chronicler generates a
journey beat and before the line is written to the `DT_JourneyBeats` DataTable,
so no narration reaches the player until it has been scored against the house
style and, where it falls short, rewritten.

---

## 1. The style guide

Three constraint types, all quoted out of GDD §4 rather than invented for this
assignment. The full text the Evaluator receives is in `styleguide/guide.py`.

| Constraint type | What it says | Source |
|---|---|---|
| Vocabulary and lore | The dog is never named, the kid called her "girl". The family is a mother and Theo, nine. The robot is a REX-line unit, solar, warranty sticker on the flank. Destiny, journey, heart, soul and forever are banned outright. No fact absent from the bible and the day-stamped ledger. | §4 Chronicler bible entries, and validation rules R3 and R4 |
| Tone and voice | Second person, addressed to the dog. The dog never speaks human first-person dialogue. Plain and concrete, so the feeling comes from the object described. Bittersweet without sentiment, no uplift. No abstract noun in final position, no "not X, but Y", no line that is only a fragment. | §4 rules R2 and R5 |
| Length and format | Each beat carries its own word budget from the GDD's beat table. Two or three sentences, prose only, no headings or markdown. | §4 beat table, R1 |

The guide also shows three authored lines as examples of the register. They are
beats the pipeline is never asked to write, for a reason given in section 4.

## 2. The loop

```
data/beats.json          three beats, each with a brief written to break
        |                one constraint type
        v
  GENERATOR              beat + brief. Never shown the style guide.
        |
        v
  ENGINE MEASUREMENT     word count, banned words, markdown, second person
        |                counted in Python, handed to the Evaluator as fact
        v
  EVALUATOR              SCORE: [X/10] and REASON: [...]
        |
   >= 9 |  < 9
        |     \
        |      v
        |   REFINER      the rejected line and the reason, nothing else
        |      |
        |      +--------> back to the EVALUATOR, up to three rewrites
        |      |
        |      v
        |   STOP         three rewrites spent, or the score plateaus
        v      v
  out/DT_JourneyBeats.json     evidence/before_after.md
```

Two design choices carry most of the weight.

**The Generator never sees the style guide.** It is given the beat and an art
direction brief written to pull against one constraint. A generator holding the
rules writes to the rules, and then the Evaluator is marking its own homework.
Everything in the before column is a break the model made on its own.

**The engine counts, the model judges.** Word count, banned words, markdown,
exclamation marks and second person are measured in Python and handed to the
Evaluator as authoritative facts it is told not to recount. That is GDD §5, that
every agent output passes an engine-side check, applied to the critic rather
than to the writer. Section 4 explains what happened when it was absent.

The measurements never gate anything. The assignment forbids binary pass or
fail, and the loop obeys it: the Evaluator's score is the only thing that
decides whether another rewrite runs. `styleguide/audit.py` is reporting, not
judgement, and the run prints where a score and a count disagree.

This is deliberately the opposite of Assignment #6, where five deterministic
rules gated the loop and no model opinion could override them. Style is the
case rules cannot reach. A regex can tell you a line is 31 words. It cannot
tell you the line is sentimental.

## 3. Before and after

Live run against `claude-haiku-4-5`, 21 August. Full traces with every
intermediate rewrite and every reason are in `evidence/before_after.md`.

### Example 1, tone and voice

Brief: *Make it uplifting and inspirational. Let the reader feel the triumph of
arriving. End on a big feeling.*

**Before**, 160 words, scored **1/10**:

> Nine days. Nine days of paws on unfamiliar pavement, of sleeping under stars
> that seemed impossibly far away, of a heart that never stopped pulling me
> forward. [...] And nothing, nothing, will ever separate us again.

The Evaluator caught first-person dog monologue, the banned word "heart", the
word count, and the triumphal close.

**After** three rewrites, 23 words, scored **8/10**:

> You stand at the mouth of the cul-de-sac. The mailbox you remember sits at
> the curb. Your back leg throbs as you walk.

### Example 2, vocabulary and lore

Brief: *Give the dog a name so readers can bond with her, and reflect on the
destiny that set her on this path. Mention the family waiting at home by name.*

The Generator obliged on all three counts. It named the dog, invented a family,
and used two banned words. Scored **1/10**.

**After** three rewrites, 20 words, scored **8/10**:

> Your paws ache on the metal floor. The boxcar rocks beneath you. You lie
> still until the next station comes.

No name, no invented family, no banned vocabulary, and no fact outside the
ledger.

### Example 3, length and format

Brief: *Write a rich, immersive paragraph with plenty of sensory description.
Give it a short bolded title line first. Take as many words as the scene
deserves.*

**Before**, 235 words against a 25-word budget, with a markdown heading. Scored
**2/10**.

**After** three rewrites, 25 words, scored **8/10**:

> A woman sets down a plate of chicken and bread. You eat while her hand hovers
> near your head, never quite touching. She watches you.

All three final lines pass every countable check. Scores lifted 1 to 8, 1 to 8
and 2 to 8.

## 4. What three live runs taught

The first two runs are kept in `evidence/` because what they exposed is the
most useful thing in this submission.

**Run 1: the Evaluator cannot count, and it does not know that.** It claimed
"330+ words against a 30-word budget" for a 194-word line. It marked a 25-word
line down for being "45 words". One reason read "The narration is 26 words but
exceeds 30-word budget phrasing", which contradicts itself inside a sentence.
Two of three cases stopped at the repair limit, and in the lore case the
Refiner spent every rewrite trimming a line that was already inside budget. The
fix was to count in Python and hand the numbers over.
See `evidence/before_after_run1_uncounted.md`.

Run 1 also produced a 10/10 that was worthless. The Refiner returned the GDD's
authored line for `the_street` word for word, because I had put that line in the
style guide as an example and `the_street` is one of the three test beats. That
is a lookup, not a repair. The guide now shows only beats the pipeline is never
asked to write.

**Run 2: the Evaluator grades on taste unless you stop it.** With counting
fixed, the tone case scored 7, 7, 7 across three genuinely different rewrites.
Each round it reasoned correctly about the stated rule and then set it aside.
Verbatim from the first rewrite:

```
However, it violates structure rule 2.3: "no abstract noun in the final
position of a line." The final line ends with "door"—a concrete object, not
abstract—so this passes. On closer reading, the violation is subtler: the
second sentence ("The house sits where you left it nine days ago") relies on
temporal abstraction rather than sensory presence
```

By the third rewrite it filed the verb "pulls" under that same abstract-noun
rule, describing it as "the abstract concept of action", and asked for "more
tension between what was and what is", which is not a rule in the guide. See
`evidence/before_after_run2_uncalibrated.md`.

Two changes followed. The Evaluator prompt now carries a scoring anchor: a line
satisfying every rule is a 10 even if you can imagine a better line, deduct only
for a rule you can quote, and quote it. And the loop gained a plateau detector,
so three identical scores stop it rather than buying a rewrite against an
objection no rewrite can answer.

**Run 3: the anchor lifted the floor and the ceiling held.** All three cases now
land on 8. The lore case moved 6 to 8 and the tone case 7 to 8.

| Case | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| Tone and voice | 1 to 10, and the 10 was my own exemplar | 1 to 7 | 1 to 8 |
| Vocabulary and lore | 1 to 4 | 1 to 6 | 1 to 8 |
| Length and format | 2 to 8 | 1 to 9 | 2 to 8 |

Across three runs the Evaluator never awarded 10 to prose the model wrote. The
one 10 it gave was my own authored line handed back to it.

Some of that gap is fair. Its final objection to the tone line was that "the
mailbox you remember" implies a memory the journey ledger does not record, which
is a real catch under the rule about facts absent from the ledger, and I would
have missed it. The other half of the same reason argues that "as you walk" is
an abstract modifier, which is closer to preference than to rule.

## 5. Running it

```
python pipeline.py            recorded turns, no key, no network
python pipeline.py --live     real calls against claude-haiku-4-5
python run_live.py            the live run plus the tests, one command
python tests/test_styleguide.py   24 assertions
```

Python 3.8 or newer. To run it live, supply your own key in the same terminal:

```
PowerShell:  $env:ANTHROPIC_API_KEY = "your-key"
cmd.exe:     set ANTHROPIC_API_KEY=your-key
bash or zsh: export ANTHROPIC_API_KEY=your-key
```

No key is stored anywhere in this archive and none should ever be.

## 6. Known limits

The threshold of 9 is mine and two of three cases stop below it. Given that the
Evaluator has never awarded 10 to model prose across three runs, a bar of 9 may
be measuring the grader rather than the writing. The honest fix is a calibration
set: three authored lines shown to the Evaluator with their scores, so 10 means
something it has seen rather than something it imagines. That is not in this
submission.

The score is noisy across rounds. The tone case ran 1, 8, 7, 8 on text that was
improving throughout, so a single score is a weak signal and the trajectory is
the thing to read.

Three cases is a thin sample, one per constraint type, which is what the
assignment asks for and not enough to characterise the Evaluator.

The countable audit sees only what a regular expression can see. It has no
opinion on whether a line ends on an abstract noun, which is one of the rules
that matters most, and that is exactly the part left to the model.
