"""Import the seven sound families the GDD names, and build a cue for each.

    D:/Side Projects/AI Game Dev Course/rex-machina/tools/ue_import_sounds.py

The Kenney impact pack ships 26 families of 5 variants. Only 7 of them have a
job, listed below against the GDD moment that asked for them, so the other 95
files stay out of the project.

Five variants per family is the whole point: a cue that plays the same wave on
every step machine-guns. Each cue is a Random node over its five waves with
repeats suppressed, so a run of steps sounds like steps.

Re-runnable. Existing assets are overwritten rather than suffixed _1.
"""
import unreal

L = unreal.log
E = unreal.log_error

RAW = ("D:/Side Projects/AI Game Dev Course/RexMachinaUE/RawAssets/unzipped"
       "/kenney_impact-sounds/Audio")
WAVE_DIR = "/Game/Audio/Waves"
CUE_DIR = "/Game/Audio"

#  family -> (cue name, what it is for). Straight from docs/UNREAL-ASSETS.md.
FAMILIES = [
    ("footstep_grass",    "SC_DogStep_Grass",    "dog's paw, phase 1 yard"),
    ("footstep_concrete", "SC_DogStep_Concrete", "dog's paw, phases 2 and 3"),
    ("impactMetal_light", "SC_RexStep",          "Rex's step"),
    ("impactPlate_light", "SC_FenceRing",        "a move refused at the fence"),
    ("impactMetal_heavy", "SC_ArenaAdvance",     "couplings, the arena advances"),
    ("impactBell_heavy",  "SC_ReadStinger",      "a read fires"),
    ("impactSoft_heavy",  "SC_Lose",             "the porch light is still on"),
]
VARIANTS = 5

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary


def import_family(stem):
    """Import family_000..004 as SoundWaves. Returns the loaded assets."""
    tasks = []
    for i in range(VARIANTS):
        src = "%s/%s_%03d.ogg" % (RAW, stem, i)
        t = unreal.AssetImportTask()
        t.filename = src
        t.destination_path = WAVE_DIR
        t.destination_name = "SW_%s_%03d" % (stem, i)
        t.automated = True
        t.replace_existing = True
        t.save = True
        tasks.append(t)
    tools.import_asset_tasks(tasks)

    waves = []
    for t in tasks:
        path = "%s/%s" % (WAVE_DIR, t.destination_name)
        a = lib.load_asset(path) if lib.does_asset_exist(path) else None
        if a is None:
            E("RM_SND | import failed: %s" % t.filename)
        else:
            waves.append(a)
    return waves


def set_first(obj, names, value):
    """Editor property names move between engine versions. Try each."""
    for n in names:
        try:
            obj.set_editor_property(n, value)
            return n
        except Exception:
            continue
    return None


def build_cue(cue_name, waves):
    path = "%s/%s" % (CUE_DIR, cue_name)
    if lib.does_asset_exist(path):
        lib.delete_asset(path)
    cue = tools.create_asset(cue_name, CUE_DIR, unreal.SoundCue,
                             unreal.SoundCueFactoryNew())
    if cue is None:
        E("RM_SND | could not create cue %s" % cue_name)
        return None

    players = []
    for w in waves:
        p = unreal.new_object(unreal.SoundNodeWavePlayer, cue)
        # new name first: 'sound_wave' still works in 5.5 but warns
        used = set_first(p, ["sound_wave_asset_ptr", "sound_wave"], w)
        if used is None:
            E("RM_SND | no sound wave property on SoundNodeWavePlayer")
            return None
        players.append(p)

    if len(players) == 1:
        root = players[0]
    else:
        root = unreal.new_object(unreal.SoundNodeRandom, cue)
        set_first(root, ["child_nodes"], players)
        # do not repeat a variant until the others have had a turn
        set_first(root, ["should_exclude_from_branch_culling"], False)
        try:
            root.set_editor_property("preselect_at_level_load", 0)
        except Exception:
            pass
        try:
            root.set_editor_property("randomize_without_replacement", True)
        except Exception:
            pass
        try:
            root.set_editor_property("weights", [1.0] * len(players))
        except Exception:
            pass

    set_first(cue, ["first_node"], root)
    try:
        cue.set_editor_property("all_nodes", ([root] + players) if root not in players else players)
    except Exception:
        pass
    lib.save_loaded_asset(cue)
    return cue


made, failed = [], []
for stem, cue_name, why in FAMILIES:
    waves = import_family(stem)
    if len(waves) != VARIANTS:
        failed.append((cue_name, "only %d of %d waves imported" % (len(waves), VARIANTS)))
        continue
    cue = build_cue(cue_name, waves)
    if cue is None:
        failed.append((cue_name, "cue build failed"))
    else:
        made.append((cue_name, why))

L("RM_SND | ---- sound import ----")
for name, why in made:
    L("RM_SND | built %-22s  %s" % (name, why))
for name, why in failed:
    E("RM_SND | FAILED %-21s  %s" % (name, why))
L("RM_SND | %d cues, %d waves, %d failures"
  % (len(made), len(made) * VARIANTS, len(failed)))
