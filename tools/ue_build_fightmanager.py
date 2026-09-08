"""Create BP_FightManager: parent class, every variable, every function stub.

Run headless with UnrealEditor-Cmd.exe, -run=pythonscript -script=<this file>,
against RexMachinaUE/RexMachina.uproject. Idempotent: re-running reuses the
existing asset.

Values come from docs/UNREAL-BLUEPRINT-SPEC.md and are the numbers
tests/sim.js passes against.

Two UE 5.5 traps this works around. get_basic_type_by_name does NOT know
"float", "integer" or "boolean" -- it silently defaults them to int and only
warns, so a variable you meant to be a float becomes an int with no error. The
names that resolve are "bool", "int", "real", "string". And
create_blueprint_asset_with_parent returns None on this build, so the asset is
created with BlueprintFactory instead.

What this cannot do is build the node graphs. UE exposes no K2Node API to
Python, so the functions are empty stubs and the logic in the spec has to be
wired by hand.
"""
import unreal
BEL = unreal.BlueprintEditorLibrary
L = unreal.log
E = unreal.log_error

PKG = "/Game/Blueprints"
NAME = "BP_FightManager"
PATH = "%s/%s" % (PKG, NAME)

V2D = unreal.load_object(None, "/Script/CoreUObject.Vector2D")
T_INT = BEL.get_basic_type_by_name("int")
T_REAL = BEL.get_basic_type_by_name("real")
T_STR = BEL.get_basic_type_by_name("string")
T_BOOL = BEL.get_basic_type_by_name("bool")
T_V2D = BEL.get_struct_type(V2D)
T_STRARR = BEL.get_array_type(BEL.get_basic_type_by_name("string"))

# name, pin type, default value (None = leave at type default)
CONSTANTS = [
    ("MaxRounds",      T_INT,  15),
    ("StartCharge",    T_REAL, 100.0),
    ("PursuitCost",    T_REAL, 8.0),
    ("HoldCost",       T_REAL, 1.0),
    ("SolarRecovery",  T_REAL, 2.0),
    ("BandClinical",   T_REAL, 60.0),
    ("BandConfident",  T_REAL, 30.0),
    ("MoveWindow",     T_INT,  4),
    ("FreqSpan",       T_INT,  20),
    ("TileSize",       T_REAL, 200.0),
    ("KidTile",        T_V2D,  unreal.Vector2D(7.0, 4.0)),
    ("DogSpawn",       T_V2D,  unreal.Vector2D(0.0, 0.0)),
    ("RexSpawn",       T_V2D,  unreal.Vector2D(5.0, 5.0)),
    ("StartStamina",   T_INT,  15),
]

STATE = [
    ("DogTile",      T_V2D,    None),
    ("RexTile",      T_V2D,    None),
    ("Stamina",      T_INT,    None),
    ("Round",        T_INT,    None),
    ("Charge",       T_REAL,   None),
    ("Moves",        T_STRARR, None),
    ("SpokenLines",  T_STRARR, None),
    ("LastCategory", T_STR,    None),
    ("PhaseIndex",   T_INT,    None),
    ("Limping",      T_BOOL,   None),
]

FUNCTIONS = ["TileToWorld", "Manhattan", "InBounds", "Approach", "Band", "DirFreq",
             "Periodicity", "StepToward", "Predict", "RexAct", "SpeakRead",
             "FiringCategories", "CheckGate", "CheckEnd", "OnPlayerMove"]


def main():
    unreal.EditorAssetLibrary.make_directory(PKG)

    bp = unreal.load_asset(PATH + "." + NAME)
    if bp is None:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Actor)
        bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            NAME, PKG, unreal.Blueprint, factory)
    if bp is None:
        try:
            bp = BEL.create_blueprint_asset_with_parent(PATH, unreal.Actor)
        except Exception as exc:
            E("fallback create failed: %s" % exc)
    if bp is None:
        E("could not create %s" % PATH)
        return

    L("---- BP_FightManager variables ----")
    added = 0
    for label, group in (("constant", CONSTANTS), ("state", STATE)):
        for name, pin, _default in group:
            try:
                BEL.add_member_variable(bp, name, pin)
                BEL.set_blueprint_variable_instance_editable(bp, name, True)
                added += 1
            except Exception as exc:
                E("  %-14s FAILED: %s" % (name, exc))

    BEL.compile_blueprint(bp)

    # Defaults go on the compiled class default object.
    cdo, defaulted = None, 0
    try:
        cdo = unreal.get_default_object(bp.generated_class())
    except Exception as exc:
        E("  no CDO, defaults skipped: %s" % exc)
    if cdo is not None:
        for name, _pin, default in CONSTANTS:
            if default is None:
                continue
            try:
                cdo.set_editor_property(name, default)
                defaulted += 1
            except Exception as exc:
                E("  default %-14s FAILED: %s" % (name, exc))

    graphs = 0
    for fn in FUNCTIONS:
        try:
            BEL.add_function_graph(bp, fn)
            graphs += 1
        except Exception as exc:
            E("  graph %-16s FAILED: %s" % (fn, str(exc)[:90]))

    BEL.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(PATH)
    L("  %d variables added, %d defaults set, %d function graphs"
      % (added, defaulted, graphs))
    L("  saved %s" % PATH)


main()
