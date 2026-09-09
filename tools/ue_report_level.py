"""Say what is actually in the editor's level right now.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_report_level.py

A self-test that passes proves the functions. It does not prove the level:
the manager has to be placed, it has to be receiving input, and the three
actors it moves have to exist. This reports all four.
"""
import unreal

L = unreal.log
world = unreal.EditorLevelLibrary.get_editor_world()
L("RM_LVL | world = %s" % (world.get_path_name() if world else "(none)"))

subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
counts = {}
for a in subsys.get_all_level_actors():
    counts[a.get_class().get_name()] = counts.get(a.get_class().get_name(), 0) + 1
for name in sorted(counts):
    L("RM_LVL | %-28s x%d" % (name, counts[name]))

for a in subsys.get_all_level_actors():
    if a.get_class().get_name().startswith("BP_FightManager"):
        L("RM_LVL | manager auto_receive_input = %s"
          % a.get_editor_property("auto_receive_input"))
