"""Prove each sound cue is wired, not just present.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_verify_sounds.py

create_asset succeeding says an asset exists. It does not say the cue has a
root node, that the root is the random selector, or that all five waves hang
off it -- and a cue with no first node is silent, which on a footstep reads as
"the audio did not get done" rather than as a bug.
"""
import unreal

L = unreal.log
E = unreal.log_error

CUES = ["SC_DogStep_Grass", "SC_DogStep_Concrete", "SC_RexStep", "SC_FenceRing",
        "SC_ArenaAdvance", "SC_ReadStinger", "SC_Lose"]
EXPECT_VARIANTS = 5

lib = unreal.EditorAssetLibrary
bad = 0

for name in CUES:
    path = "/Game/Audio/%s" % name
    if not lib.does_asset_exist(path):
        E("RM_SND | %-22s MISSING" % name)
        bad += 1
        continue
    cue = lib.load_asset(path)

    root = None
    for prop in ("first_node",):
        try:
            root = cue.get_editor_property(prop)
        except Exception:
            pass
    if root is None:
        E("RM_SND | %-22s has no root node, so it plays nothing" % name)
        bad += 1
        continue

    kind = root.get_class().get_name()
    kids = []
    try:
        kids = list(root.get_editor_property("child_nodes") or [])
    except Exception:
        pass

    waves = []
    for k in kids:
        w = None
        for prop in ("sound_wave_asset_ptr", "sound_wave"):
            try:
                w = k.get_editor_property(prop)
                if w:
                    break
            except Exception:
                continue
        waves.append(w.get_name() if w else "(empty)")

    ok = (kind == "SoundNodeRandom" and len(kids) == EXPECT_VARIANTS
          and all(w != "(empty)" for w in waves))
    if not ok:
        bad += 1
    L("RM_SND | %-22s %-16s %d child(ren)  %s  %s"
      % (name, kind, len(kids), "OK" if ok else "BAD",
         ", ".join(sorted(waves))[:70]))

L("RM_SND | ---- %d cues checked, %d bad ----" % (len(CUES), bad))
if bad:
    E("RM_SND | %d cue(s) would be silent" % bad)
