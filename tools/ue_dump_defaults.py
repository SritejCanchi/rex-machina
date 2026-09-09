"""Print BP_FightManager's class defaults, so the self-test can assert against
the real numbers instead of remembered ones.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_dump_defaults.py

Reads the CDO, which is the only place a Blueprint variable's default lives.
"""
import unreal

L = unreal.log
PATH = "/Game/Blueprints/BP_FightManager.BP_FightManager"
WANTED = ["DogSpawn", "RexSpawn", "KidTile", "DogTile", "RexTile",
          "StartCharge", "StartStamina", "Stamina", "Charge", "Round",
          "MaxRounds", "BandClinical", "BandConfident", "PursuitCost",
          "HoldCost", "SolarRecovery", "MoveWindow", "FreqSpan",
          "Limping", "Ended", "LastCatIndex", "PhaseIndex",
          "Moves", "SpokenLines"]


def main():
    bp = unreal.load_asset(PATH)
    cdo = unreal.get_default_object(bp.generated_class())
    for name in WANTED:
        try:
            L("RM_DEF | %-14s = %r" % (name, cdo.get_editor_property(name)))
        except Exception as exc:
            L("RM_DEF | %-14s -- absent (%s)" % (name, str(exc)[:60]))


main()
