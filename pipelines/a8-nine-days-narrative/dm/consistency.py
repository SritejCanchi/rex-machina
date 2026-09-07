"""Deterministic checks on the narration, run every turn.

The rubric asks that the agent not contradict itself or forget tracked facts
across five or more turns. An assertion that it did not is worth less than a
check that would have caught it, so this runs on every line and its findings
go into the session log whether or not anything fired.
"""
import re

BANNED = ["destiny", "journey", "heart", "soul", "forever"]

# Words that may legitimately appear capitalised at the start of a sentence in
# this world's vocabulary. Anything else that is capitalised reads as a name.
ORDINARY = set("""
the a an and but or nor for yet so then now here there this that these those
you your yours she her hers he him his it its they them their we us our
behind ahead above below beside beyond across along around under over
water salt gravel grass glass brick rain wind light dark night day morning
dusk cold heat road street verge yard alley boxcar door gate step steps
porch mailbox curb kerb corner window fence rail rails train truck car van
hand hands plate food bread chicken bowl leash collar paw paws leg legs
back nose ear ears fur ribs mouth tongue teeth belly
something someone nothing everything anything
your body every each some most many few both all none one two three four
five six seven eight nine ten first second third last next
when where what who how why while after before until since because
walk walking walked run running ran stand standing stood sit sitting sat
sleep sleeping slept eat eating ate drink drinking drank wait waiting waited
keep keeping kept take taking took give giving gave stop stopping stopped
turn turning turned move moving moved cross crossing crossed
is are was were be been being has have had do does did
not no yes still again already almost enough more less
inside outside open closed empty full quiet loud slow fast
metal rust grain dust concrete asphalt pavement gravel smoke steam
above beneath underfoot ahead behind past toward towards
somewhere nowhere everywhere afterwards later sometimes often\ngrease salt smell smells sound sounds air breath breathing\ndoorway threshold brick coat claws bones ribs stomach belly\nshade sun shadow slats lines hum humming engine wheels tyres\ntrucks cars people hands voices footsteps weight warmth
""".split())


def check(text, led):
    """Return a list of (code, detail). Empty means the line is consistent."""
    found = []
    low = text.lower()
    w = led.w

    for b in BANNED:
        if re.search(r"\b%s\b" % b, low):
            found.append(("BANNED_WORD", b))

    if not re.search(r"\byou\b|\byour\b", low):
        found.append(("NOT_SECOND_PERSON", "no 'you' in the line"))

    # A proper name the world does not have. A capitalised word is only
    # innocent if it is an ordinary word that happens to open a sentence, so
    # the check is against a vocabulary rather than against position. It can
    # false-positive on an unusual noun, which is why it reports rather than
    # blocks.
    for token in re.findall(r"\b[A-Z][a-z]{2,}\b", text.replace("-", " ")):
        if token in w.get("allowed_names", []):
            continue
        if token.lower() in ORDINARY:
            continue
        found.append(("INVENTED_NAME", token))

    # The injured leg is canon. GDD 4's limp_onset beat names the back leg,
    # and live run 1 moved it to the front twice in four turns.
    body = w.get("canon_body", {})
    if led.condition["state"] in ("limping", "hurt"):
        # Run 3 wrote "front left leg", which a fixed phrase list missed.
        m = re.search(r"\b(fore ?legs?|(?:front|fore)\b[\w\s]{0,14}?\blegs?)\b", low)
        if m:
            found.append(("WRONG_BODY_PART",
                          "says %r; the ledger's injury is the %s"
                          % (m.group(0), body.get("hurt_part", "back leg"))))

    # The line claims something the ledger has already ruled out.
    triggers = w.get("denial_triggers", {})
    for a, b in w["contradictions"]:
        for held, denied in ((a, b), (b, a)):
            if led.has(held):
                for phrase in triggers.get(denied, []):
                    if re.search(r"\b%s\b" % re.escape(phrase), low):
                        found.append((
                            "CONTRADICTS_LEDGER",
                            "says %r, but the ledger holds %s from day %d"
                            % (phrase, held, led.day_of(held))))
    return found
