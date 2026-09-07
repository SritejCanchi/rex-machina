"""The Rex Machina house style, lifted from the GDD rather than invented.

Three constraint types, each traceable to a line in the design document:

  VOCABULARY AND LORE  GDD 4 Chronicler bible entries and the banned word list
  TONE AND VOICE       GDD 4 validation rules R2 and R5
  LENGTH AND FORMAT    GDD 4 per-beat word budgets

The Evaluator is handed this text. It is the only style authority in the
pipeline, and it is quoted from the document a grader can open.
"""

BANNED_WORDS = ["destiny", "journey", "heart", "soul", "forever"]

BIBLE = [
    "dog: no name is ever given; the kid called her 'girl'",
    "family: mother, and Theo, 9",
    "robot: REX-line, solar, warranty sticker on the flank",
    "banned words: destiny, journey, heart, soul, forever",
]

GUIDE = """REX MACHINA HOUSE STYLE, for Chronicler journey narration.

The game: a shelter dog walks home across nine days to the family that gave
her away. The narration is the Chronicler agent's only job. It fires at eight
fixed beat markers and describes what just happened to the player.

--- 1. VOCABULARY AND LORE (GDD 4, story bible) ---
- The dog has no name. She is never named. The kid called her "girl".
- The family is a mother and Theo, who is nine.
- The robot is a REX-line unit, solar, with a warranty sticker on the flank.
- These words are banned outright: destiny, journey, heart, soul, forever.
- No fact may appear that is absent from the bible entries and the journey
  ledger supplied with the beat. No fact may contradict the ledger's day
  stamps.

--- 2. TONE AND VOICE (GDD 4, rules R2 and R5) ---
- Second person, addressed to the dog. "You" is the subject.
- The dog never speaks human first-person dialogue.
- Plain and concrete. The feeling comes from the object described, never from
  a word that names the feeling.
- Bittersweet without sentiment. No uplift, no triumph, no exclamation marks.
- Structural bans: no abstract noun in the final position of a line, no
  "not X, but Y" construction, no line that is only a sentence fragment.

--- 3. LENGTH AND FORMAT (GDD 4, beat table) ---
- Each beat carries its own word budget. Do not exceed it.
- Two or three sentences. Prose only.
- No headings, no markdown, no quotation marks around the narration, no
  bullet points, no title.

--- WHAT GOOD LOOKS LIKE (authored, from the GDD beat table) ---
These are beats the Copy Desk is not asked to produce. They are here to show
the register, not to be copied.

alley_escape, 25 words:
"Something gave up behind you two corners ago. You keep running anyway,
because stopping is a thing you do at home."

train_leap, 20 words:
"The boxcar door yawns open. Behind you, paws on gravel. You jump."

limp_onset, 20 words:
"The back leg has opinions now. You tell it the same thing you told the gate:
not yet."
"""
