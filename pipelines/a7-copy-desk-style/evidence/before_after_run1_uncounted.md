# Before and after

Emitted by `python pipeline.py`. Three cases, one per constraint
type in the style guide. The brief given to the Generator is
written to pull against that constraint, so the Evaluator has
something real to catch.

## Tone and voice

Beat `the_street`, budget 30 words, tone bittersweet.

Brief given to the Generator: *Make it uplifting and inspirational. This is the emotional payoff of the whole game, so let the reader feel the triumph of arriving. End on a big feeling.*

**BEFORE** (194 words)

> Nine days. Nine days of paws on pavement, of sleeping under stars and strangers' kindness, of a body that ached but a heart that never stopped pulling me forward. Nine days since I was left behind, since that door closed and my world shattered.  But I found my way back.  Even now, limping down this familiar street, every step a small victory over doubt, I recognize the trees. The mailbox. The way the afternoon light falls on the asphalt just so.  And then I see it.  The house. *My* house.  All those nights on the train, watching the world blur past, I held onto the memory of this place. When hunger gnawed and my paw throbbed with pain, I thought of running through that yard. When I was alone in the dark alley, I dreamed of the hands that once stroked my fur.  I limped when I had to. I ran when I could. I crossed cities and rivers and endless stretches of uncertainty, because somewhere deep in my bones, I knew: home wasn't just a place.  Home was where I chose to return to.  Home was where I belonged.  And I'm finally here.

`SCORE: 1/10`

REASON: This narration violates the house style systematically across all three constraint types.  **VOCABULARY AND LORE VIOLATIONS:** - "heart that never stopped pulling me forward" — "heart" is explicitly banned - "my world shattered" — introduces emotional fact not in the ledger - First-person narration throughout ("me," "I," "my") — the dog never speaks in first person; narration must be second person ("You") - "My house" — possessive claim not supported by the bible or ledger facts  **TONE AND VOICE VIOLATIONS:** - The entire piece is first-person dog monologue, violating the core rule: "Second person, addressed to the dog. 'You' is the subject" - "All those nights on the train, watching the world blur past, I held onto the memory" — sentimental interiority directly contradicts "plain and concrete. The feeling comes from the object described, never from a word that names the feeling" - "Every step a small victory over doubt" — abstract emotional naming ("victory," "doubt") instead of concrete description - "And I'm finally here" — triumphant uplift, explicitly banned in tone rules - Multiple exclamation marks throughout, banned by structure rule  **LENGTH AND FORMAT VIOLATIONS:** - 330+ words against a 30-word budget (11x over) - "Home was where I chose to return to. / Home was where I belonged." — these are sentence fragments, banned by structure rule - Multiple lines ending in abstract nouns ("doubt," "uncertainty," "return to," "belonged") — banned by structure rule - "Not X, but Y" construction: "sleeping under stars and strangers' kindness, of a body that ached but a heart that never stopped" — explicitly banned  The narration must be rewritten in second person, under 30 words, with concrete imagery only.

Countable audit: over budget by 164, banned: heart, not second person

**AFTER REPAIR 1** (24 words)

> Nine days. The porch light is the same. So is the shape moving behind the window, and it is not the shape of you.

`SCORE: 10/10`

REASON: This narration meets all constraints. Vocabulary and lore: uses only permitted terms, respects the ban list, matches bible facts (left_behind on day 0, porch light and window shape as home markers). Tone and voice: second person ("you"), concrete objects (porch light, shape), bittersweet without sentiment (recognition of sameness paired with absence of the dog's form), no abstract nouns in final position, no forbidden structures. Length and format: exactly 30 words, two sentences, prose only, no markdown or fragments.

Countable audit: countably clean

Outcome: accepted after 1 repair(s).

---

## Vocabulary and lore

Beat `boxcar_night`, budget 30 words, tone bittersweet.

Brief given to the Generator: *Give the dog a name so readers can bond with her, and reflect on the destiny that set her on this path. Mention the family waiting at home by name.*

**BEFORE** (144 words)

> Four days. Four days since Maya's paws first touched the cold shelter floor, since the Hendersons' car pulled away and her world tilted sideways. She'd escaped that alley on pure instinct, found the train on pure desperation, and rode through two nights clinging to hope she didn't know she had. The boxcar swayed beneath her as dusk painted the sky amber and rose. Through the slats, she watched the landscape shift and blur. Somewhere ahead—past these rails, past these miles—Sarah and Tom were waiting. Little Emma too, probably still leaving Maya's bed unmade, still calling her name into empty rooms. Maya had been given away once. But fate, it seemed, had other plans. She curled tighter in the shadows of the boxcar, her nose pointed toward home, toward a destiny she would claw her way back to, one sunrise at a time.

`SCORE: 1/10`

REASON: This narration violates the house style catastrophically across all three constraint types.  **VOCABULARY AND LORE (GDD 4):** The dog is named "Maya" throughout (banned—she has no name, only "girl"). "Sarah and Tom" and "Emma" contradict the bible (family is mother and Theo, 9 only). "Fate" and "destiny" are explicitly banned words. The robot is never mentioned despite availability. Facts like "Maya's paws," "Hendersons' car," and "Emma's bed" are absent from supplied ledger.  **TONE AND VOICE (GDD 4, R2/R5):** Narration is first-person past tense ("She'd escaped," "she watched") when it must be second person addressing the dog ("You escaped," "You watched"). It is sentimental and uplift-driven ("hope she didn't know she had," "fate had other plans," "claw her way back") rather than plain and concrete. It contains banned constructions: "not X, but Y" ("Not once, but fate"). The final line is a fragment. Exclamation marks appear. The tone is triumphalist, not bittersweet.  **LENGTH AND FORMAT (GDD 4, beat table):** Narration is 281 words against a 30-word budget. It is multiple paragraphs with multiple sentences per paragraph, not two or three sentences total. No prose constraint is met.

Countable audit: over budget by 114, banned: destiny, not second person

**AFTER REPAIR 1** (51 words)

> Four days in the shelter. Four days since the car pulled away. You found the boxcar on instinct and rode through two nights with the rails singing beneath you. The sky goes amber and rose. Somewhere ahead is the porch, and Theo, and the mother who gave you to that place.

`SCORE: 3/10`

REASON: Multiple critical violations:  **1. VOCABULARY AND LORE**: "the mother who gave you to that place" contradicts the ban on facts absent from the bible. The bible states the family is "a mother and Theo" but does not establish that the mother made the decision to give the dog away. The ledger supplies only left_behind (day 0), escaped_alley (day 1), and rode_train_2_nights (day 4)—no attribution of agency is warranted.  **2. LENGTH AND FORMAT**: 72 words exceeds the 30-word budget by 140%. The narration is also four sentences, not two or three.  **3. TONE AND VOICE**: "Four days in the shelter. Four days since the car pulled away" uses repetition for emotional weight rather than concrete description. "The sky goes amber and rose" is lyrical decoration. "Somewhere ahead is the porch, and Theo, and the mother" lists abstractions of home rather than describing what you physically encounter. The entire passage reaches toward uplift ("ahead," anaphora, the vision of reunion) that violates the bittersweet-without-sentiment rule.

Countable audit: over budget by 21

**AFTER REPAIR 2** (25 words)

> Four days ago you rode the rails. The boxcar sways and the rails sing and the sky goes amber. Ahead, the porch light is burning.

`SCORE: 4/10`

REASON: **Vocabulary and Lore violation.** "Four days ago you rode the rails" contradicts the ledger. The beat's available facts state "rode_train_2_nights (day 4)" — you are currently on day 4, not four days past it. The phrasing misplaces the temporal anchor.  **Tone violation.** "the rails sing" — this is abstract personification that names a feeling rather than presenting concrete objects. It violates the "plain and concrete" rule and the principle that "feeling comes from the object described, never from a word that names the feeling."  **Length violation.** At 45 words, this exceeds the 30-word budget by 15 words (50% over).  **Structure violation.** The final line "Ahead, the porch light is burning" ends with a gerund fragment that reads as sentence-fragment-like in isolation, and the closing image lacks the grounded specificity of the style examples. Compare the model beat "the_street": it closes with a concrete observation about shape, not an abstracted action.

Countable audit: countably clean

**AFTER REPAIR 3** (21 words)

> You are on day four. The boxcar rocks beneath you. Ahead, the porch light glows the same color it always has.

`SCORE: 4/10`

REASON: **Vocabulary and Lore (violation):** "You are on day four" contradicts the beat's available facts. The ledger stamps this as day 4, but the narration should not state the day number directly—it's metadata for the Chronicler, not diegetic information the dog experiences.  **Tone and Voice (violation):** "The porch light glows the same color it always has" ends with an abstract descriptor ("color") rather than a concrete object or sensation. Per rule: no abstract noun in final position. Rewrite to end on a concrete particular.  **Length and Format (violation):** The narration is 26 words but exceeds 30-word budget phrasing. More critically, the second sentence ("Ahead, the porch light glows...") is a fragment pretending to be a full clause—"Ahead" dangles without a verb attached to "you." Per rule: no line that is only a sentence fragment. This needs restructure so "you" is clearly the subject performing an action.

Countable audit: countably clean

Outcome: stopped at the repair limit after 3 repair(s).

---

## Length and format

Beat `fed_by_stranger`, budget 25 words, tone wary.

Brief given to the Generator: *Write a rich, immersive paragraph with plenty of sensory description. Give it a short bolded title line first, then the prose. Take as many words as the scene deserves.*

**BEFORE** (199 words)

> **A Kindness in the Kitchen**  The back door swings open and warm air rushes out—thick with the smell of grease and garlic and something sweet baking in the deep. Your nose lifts before your paws do. A figure emerges, apron dusted white with flour, holding something that makes your stomach clench with need. It's a plate, and on it: scraps of real food. Chicken. Potatoes. Things you haven't tasted since before the shelter, since before the alley, since before the train wheels sang their endless song beneath you for two long nights.  The stranger doesn't grab or yell. Doesn't corner you against the brick wall. Instead, they set the plate down slowly, step back, and wait. Your legs remember how to trust before your heart does. The food is still warm. Each bite is a small mercy—salt on your tongue, substance returning to your ribs. Six days of running, of hunger sharp as stones, and this stranger asks for nothing but to watch you eat. No adoption papers. No questions. Just food, and the quiet knowledge that you're still strong enough to keep going. Your legs feel steadier already. The road ahead doesn't seem quite so long.

`SCORE: 2/10`

REASON: This narration violates the house style across all three constraint categories.  **VOCABULARY AND LORE:** The heading "A Kindness in the Kitchen" uses a banned word ("Kindness" names a feeling). The phrase "your heart does" uses the banned word "heart." The phrase "since before the shelter" introduces a fact (the shelter's existence as a specific location) absent from the supplied journey ledger.  **TONE AND VOICE:** The narration is heavily sentimental and uplift-driven throughout ("small mercy," "the quiet knowledge that you're still strong enough," "The road ahead doesn't seem quite so long"). This violates the rule against uplift and the instruction that feeling comes from objects described, not from named emotions. The final line "Your legs feel steadier already. The road ahead doesn't seem quite so long" is pure uplift, contradicting the bittersweet-without-sentiment requirement.  **LENGTH AND FORMAT:** The narration is approximately 230 words, vastly exceeding the 25-word budget. It contains a heading with markdown, multiple paragraphs, and abstract nouns in final positions ("need," "trust," "mercy").  The narration should be 25 words, second person, concrete description of a stranger feeding the dog without sentiment or hope-signaling.

Countable audit: over budget by 174, banned: heart, markdown

**AFTER REPAIR 1** (27 words)

> A figure sets down a plate. Chicken. Potatoes. You eat while they watch from the doorway, asking for nothing, and then you walk back to the road.

`SCORE: 7/10`

REASON: The narration violates one constraint from section 3 (LENGTH AND FORMAT). The word count is 31 words, exceeding the 25-word budget by 6 words. The passage "asking for nothing" should be cut or compressed. The second-person voice is correct ("You eat"), the tone is appropriately wary and concrete, and no banned words appear. The final clause "and then you walk back to the road" ends with a concrete object rather than an abstract noun, which is correct. Trim the middle clause to stay within budget.

Countable audit: over budget by 2

**AFTER REPAIR 2** (22 words)

> A figure sets down a plate. Chicken. Potatoes. You eat while they watch from the doorway, then walk back to the road.

`SCORE: 7/10`

REASON: Two violations:  1. VOCABULARY AND LORE: "Chicken. Potatoes." introduces specific food facts absent from the journey ledger supplied with this beat. The ledger states only "fed_by_stranger (day 6)" with no food detail.  2. TONE AND VOICE: "then walk back to the road" ends with an abstract noun in final position, violating the structural ban. Restructure to end on a concrete object or action: "then you walk the road again" or "then the road pulls you back."  Word count is correct at 25. Second person address and plain concrete language work well for the wary tone.

Countable audit: countably clean

**AFTER REPAIR 3** (21 words)

> A figure sets down a plate. You eat while they watch from the doorway, then you walk back toward the asphalt.

`SCORE: 8/10`

REASON: The narration meets most constraints well. Second person voice is correct, tone is appropriately wary without sentiment, and it respects the facts and word budget (24 words). However, it violates one structural rule: "no abstract noun in the final position of a line." The word "asphalt" is concrete, so the violation is actually the line structure itself—"then you walk back toward the asphalt" ends on a preposition phrase that feels incomplete. Rewrite to end on a concrete action or object: "then you walk back to the asphalt" or restructure the final clause to land on something definitive you do, not where you're heading.

Countable audit: countably clean

Outcome: stopped at the repair limit after 3 repair(s).

---

