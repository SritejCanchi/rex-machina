"""What can SubobjectDataSubsystem actually do? Rebuilding a component tree
needs delete and re-parent, and neither is in any stub on this machine."""
import unreal

sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
names = [n for n in dir(sds) if not n.startswith("_")]
for n in sorted(names):
    unreal.log("RM_SDS | %s" % n)
