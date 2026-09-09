"""Print every BP_FightManager variable's name, type and GUID.

Run it from the editor's Python field (bottom bar), which executes in the
running editor rather than opening a second one:

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_dump_varguids.py

Then read the lines back out of RexMachinaUE/Saved/Logs/RexMachina.log.

A K2Node_VariableGet serialises as

    VariableReference=(MemberName="Moves",MemberGuid=70CB...,bSelfContext=True)

and the GUID is per variable and assigned when the variable is created, so it
cannot be derived -- it has to be read off the asset. This is the last thing
`tools/bp_gen.py` needed before it could emit variable access, which every
remaining function depends on.
"""
import unreal

L = unreal.log
BP = "/Game/Blueprints/BP_FightManager.BP_FightManager"


def main():
    bp = unreal.load_asset(BP)
    if bp is None:
        unreal.log_error("could not load %s" % BP)
        return
    try:
        variables = bp.get_editor_property("new_variables")
    except Exception as exc:
        unreal.log_error("new_variables not readable: %s" % str(exc)[:120])
        return

    L("---- RM_VARS begin ----")
    for v in variables:
        name = v.get_editor_property("var_name")
        vguid = v.get_editor_property("var_guid")
        vtype = v.get_editor_property("var_type")
        cat = vtype.get_editor_property("pin_category")
        sub = vtype.get_editor_property("pin_sub_category")
        obj = vtype.get_editor_property("pin_sub_category_object")
        container = vtype.get_editor_property("container_type")
        # UE prints an FGuid with dashes; the node text wants 32 bare hex chars
        flat = str(vguid).replace("-", "").upper()
        L("RM_VAR %s|%s|%s|%s|%s|%s"
          % (name, flat, cat, sub, obj.get_name() if obj else "None", container))
    L("---- RM_VARS end (%d) ----" % len(variables))


main()
