"""Add the variables the speech pass needs to BP_FightManager.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_add_speech_vars.py

Run from the editor's Python console. Re-runnable; adding a name that already
exists is reported, not fatal.

`LastCatIndex` exists because GDD 4's suppression rule -- never the same read
category twice running -- has to compare something, and comparing the category
*index* is one integer compare where comparing `LastCategory`'s string would
mean materialising the category name in the graph just to compare it. It
starts at -1 so that sealing_direction, which is index 0, is not suppressed on
the first round it fires.
"""
import unreal

BEL = unreal.BlueprintEditorLibrary
L = unreal.log
E = unreal.log_error

PATH = "/Game/Blueprints/BP_FightManager.BP_FightManager"

#  name, basic type, default (None = leave at the type's zero)
WANTED = [
    ("Ended", "bool", None),
    ("LastCatIndex", "int", -1),
    # SpeakRead latches the chosen line here before it writes LastCatIndex or
    # SpokenLines, because both of those writes change what the chosen line is
    # computed from. See the comment at the end of speakread() in bp_gen.py.
    ("PendingLine", "string", ""),
]


def main():
    bp = unreal.load_asset(PATH)
    if bp is None:
        E("RM_VARS | cannot load %s" % PATH)
        return

    for name, kind, default in WANTED:
        try:
            BEL.add_member_variable(bp, name, BEL.get_basic_type_by_name(kind))
            L("RM_VARS | added %s (%s)" % (name, kind))
        except Exception as exc:
            L("RM_VARS | %s not added: %s" % (name, str(exc)[:100]))

    BEL.compile_blueprint(bp)

    # Defaults live on the class default object, not on the variable
    # description, so they can only be set after a compile has produced a CDO.
    # unreal.get_default_object(cls), NOT cls.get_default_object():
    # the latter hands back something whose properties never resolve.
    cdo = unreal.get_default_object(bp.generated_class())
    for name, kind, default in WANTED:
        if default is None:
            continue
        try:
            cdo.set_editor_property(name, default)
            L("RM_VARS | %s default = %r" % (name, default))
        except Exception as exc:
            E("RM_VARS | %s default failed: %s" % (name, str(exc)[:100]))

    BEL.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(PATH)

    # Read back, because a create is not proof.
    # unreal.get_default_object(cls), NOT cls.get_default_object():
    # the latter hands back something whose properties never resolve.
    cdo = unreal.get_default_object(bp.generated_class())
    for name, kind, default in WANTED:
        try:
            L("RM_VARS | verify %-13s = %r" % (name, cdo.get_editor_property(name)))
        except Exception as exc:
            E("RM_VARS | verify %s failed: %s" % (name, str(exc)[:100]))


main()
