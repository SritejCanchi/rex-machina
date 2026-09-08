"""Read BP_FightManager back and check every variable and default.

A write is not proof. This loads the compiled class default object and compares
each constant against docs/UNREAL-BLUEPRINT-SPEC.md, then confirms every state
variable exists.
"""
import unreal
L=unreal.log; E=unreal.log_error
bp=unreal.load_asset("/Game/Blueprints/BP_FightManager.BP_FightManager")
EXPECT=[("MaxRounds",15),("StartCharge",100.0),("PursuitCost",8.0),("HoldCost",1.0),
        ("SolarRecovery",2.0),("BandClinical",60.0),("BandConfident",30.0),("MoveWindow",4),
        ("FreqSpan",20),("TileSize",200.0),("KidTile",(7.0,4.0)),("DogSpawn",(0.0,0.0)),
        ("RexSpawn",(5.0,5.0)),("StartStamina",15)]
STATE=["DogTile","RexTile","Stamina","Round","Charge","Moves","SpokenLines",
       "LastCategory","PhaseIndex","Limping"]
L("=== BP_FightManager verify ===")
if bp is None:
    E("  asset not found"); raise SystemExit
cdo=unreal.get_default_object(bp.generated_class())
bad=0
for name,want in EXPECT:
    try:
        got=cdo.get_editor_property(name)
        if isinstance(want,tuple):
            ok=abs(got.x-want[0])<1e-6 and abs(got.y-want[1])<1e-6
            shown="(%g, %g)"%(got.x,got.y)
        else:
            ok=abs(float(got)-float(want))<1e-6
            shown=str(got)
        L("  %-14s = %-12s %s"%(name,shown,"OK" if ok else "WANT %s"%(want,)))
        if not ok: bad+=1
    except Exception as exc:
        E("  %-14s MISSING: %s"%(name,exc)); bad+=1
for name in STATE:
    try:
        cdo.get_editor_property(name); L("  %-14s present"%name)
    except Exception as exc:
        E("  %-14s MISSING: %s"%(name,exc)); bad+=1
L("  %s"%("all 24 variables correct" if not bad else "%d problem(s)"%bad))
