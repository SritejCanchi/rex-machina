"""Create the Enhanced Input assets for the Act 3 fight.

    "D:/Software/UE_5.5/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" ^
      "D:/Side Projects/AI Game Dev Course/RexMachinaUE/RexMachina.uproject" ^
      -run=pythonscript -script=".../tools/ue_make_input.py" -unattended -nopause

Headless. Re-runnable.

Five actions, not an axis pair. The fight is turn based: one key press is one
round, and a held key must not repeat. Digital (bool) actions with a Pressed
trigger are the honest shape for that -- an axis would invite continuous
movement, which the round loop cannot express.

Wait is a first-class action, not the absence of input. GDD 3 counts "wait" in
the move history: two waits inside the last four moves fire the
stall_detected read, so the robot notices you standing still. That only works
if standing still is something the player actively does.

These assets wire to nothing yet -- OnPlayerMove does not exist. They are the
half of input that can be built without the graph editor.
"""
import unreal

AT = unreal.AssetToolsHelpers.get_asset_tools()
L = unreal.log
E = unreal.log_error

PKG = "/Game/Input"
CONTEXT = "IMC_Fight"

#  action asset, keys, the string it appends to Moves in the spec
ACTIONS = [
    ("IA_MoveUp",    ["W", "Up"],    "up"),
    ("IA_MoveDown",  ["S", "Down"],  "down"),
    ("IA_MoveLeft",  ["A", "Left"],  "left"),
    ("IA_MoveRight", ["D", "Right"], "right"),
    ("IA_Wait",      ["SpaceBar"],   "wait"),
]


def make_action(name, move_string):
    path = "%s/%s" % (PKG, name)
    ia = unreal.load_asset(path + "." + name)
    if ia is None:
        ia = AT.create_asset(name, PKG, unreal.InputAction,
                             unreal.InputAction_Factory())
    if ia is None:
        E("  %-13s could not create" % name)
        return None
    try:
        ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
    except Exception as exc:
        L("  %-13s value_type not set (%s)" % (name, str(exc)[:60]))
    unreal.EditorAssetLibrary.save_asset(path)
    L("  %-13s digital, appends %r to Moves" % (name, move_string))
    return ia


def make_context(actions):
    path = "%s/%s" % (PKG, CONTEXT)
    imc = unreal.load_asset(path + "." + CONTEXT)
    if imc is None:
        imc = AT.create_asset(CONTEXT, PKG, unreal.InputMappingContext,
                              unreal.InputMappingContext_Factory())
    if imc is None:
        E("  %s could not create" % CONTEXT)
        return None

    mappings = []
    for ia, keys in actions:
        for k in keys:
            m = unreal.EnhancedActionKeyMapping()
            m.set_editor_property("action", ia)
            # unreal.Key takes no constructor arguments; build it empty and
            # set key_name, which is the FKey name ("W", "SpaceBar", "Up").
            key = unreal.Key()
            key.set_editor_property("key_name", k)
            m.set_editor_property("key", key)
            mappings.append(m)
    try:
        imc.set_editor_property("mappings", mappings)
    except Exception as exc:
        E("  %s could not set mappings: %s" % (CONTEXT, str(exc)[:100]))
        return None
    unreal.EditorAssetLibrary.save_asset(path)
    L("  %s: %d key mappings" % (CONTEXT, len(mappings)))
    return imc


def verify():
    """Read the context back and list what each key is actually bound to."""
    L("  ---- verify ----")
    imc = unreal.load_asset("%s/%s.%s" % (PKG, CONTEXT, CONTEXT))
    if imc is None:
        E("    %s MISSING" % CONTEXT)
        return
    try:
        got = imc.get_editor_property("mappings")
    except Exception as exc:
        E("    cannot read mappings: %s" % str(exc)[:80])
        return
    seen = {}
    for m in got:
        a = m.get_editor_property("action")
        k = m.get_editor_property("key")
        an = a.get_name() if a else "None"
        seen.setdefault(an, []).append(str(k.get_editor_property("key_name")))
    expect = len(ACTIONS)
    for name, keys, _ in ACTIONS:
        bound = seen.get(name, [])
        ok = len(bound) == len(keys)
        L("    %-13s -> %-18s %s" % (name, ", ".join(bound) or "(none)",
                                     "OK" if ok else "wanted %s" % ", ".join(keys)))
    L("  %s" % ("all %d actions bound" % expect if len(seen) == expect
                else "%d of %d actions bound" % (len(seen), expect)))


def main():
    L("---- Rex Machina input ----")
    unreal.EditorAssetLibrary.make_directory(PKG)
    pairs = []
    for name, keys, move_string in ACTIONS:
        ia = make_action(name, move_string)
        if ia is not None:
            pairs.append((ia, keys))
    make_context(pairs)
    verify()


main()
