"""Check that Ended and LastCatIndex really exist, and set LastCatIndex to -1.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_verify_speech_vars.py

add_member_variable returns a bool rather than raising, so a try/except around
it reports success for a name that was rejected. This reads the compiled class
back instead, which is the only thing that proves a variable exists.
"""
import unreal

BEL = unreal.BlueprintEditorLibrary
L = unreal.log
E = unreal.log_error

PATH = "/Game/Blueprints/BP_FightManager.BP_FightManager"
WANTED = [("Ended", "bool", None), ("LastCatIndex", "int", -1),
          ("PendingLine", "string", None)]


def main():
    bp = unreal.load_asset(PATH)
    if bp is None:
        E("RM_CHK | cannot load")
        return

    for name, kind, _ in WANTED:
        ok = BEL.add_member_variable(bp, name, BEL.get_basic_type_by_name(kind))
        L("RM_CHK | add_member_variable(%-13s) returned %r" % (name, ok))

    BEL.compile_blueprint(bp)
    cls = bp.generated_class()
    L("RM_CHK | generated_class = %s" % (cls.get_name() if cls else "None"))
    # unreal.get_default_object(cls), NOT cls.get_default_object():
    # the latter hands back something whose properties never resolve.
    cdo = unreal.get_default_object(cls) if cls else None
    if cdo is None:
        E("RM_CHK | no CDO")
        return

    for name, kind, default in WANTED:
        try:
            cur = cdo.get_editor_property(name)
            L("RM_CHK | %-13s reads back as %r" % (name, cur))
            if default is not None and cur != default:
                cdo.set_editor_property(name, default)
                L("RM_CHK | %-13s set to %r" % (name, default))
        except Exception as exc:
            E("RM_CHK | %-13s NOT on the class: %s" % (name, str(exc)[:90]))

    BEL.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(PATH)
    cdo = unreal.get_default_object(bp.generated_class())
    for name, _, _ in WANTED:
        try:
            L("RM_CHK | final %-13s = %r" % (name, cdo.get_editor_property(name)))
        except Exception as exc:
            E("RM_CHK | final %-13s failed: %s" % (name, str(exc)[:90]))


main()
