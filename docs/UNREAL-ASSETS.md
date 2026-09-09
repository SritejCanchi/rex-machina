# Assets for the Unreal build

Every source below was licence-checked before use, because this is coursework
being submitted. Downloaded packs live in
`RexMachinaUE/RawAssets/` -- deliberately outside `Content/` so UE does not
auto-import them, and outside this repo so binaries do not bloat it.

**Tier 0 needs none of this.** The grey box uses `Engine/BasicShapes` only.
Everything here is Tier 1 dressing and Tier 2 polish.

## Downloaded

All three are **CC0** -- public domain, no attribution, commercial use fine.

| Pack | Size | Contents | Serves |
|---|---|---|---|
| `kenney_city-kit-industrial_2.0.zip` | 4.9 MB | 37 FBX + OBJ + GLB, 48 textures | the train yard: the industrial silhouette behind phase 3 |
| `kenney_factory-kit_3.0.zip` | 4.4 MB | FBX + OBJ + GLB | pipes, tanks, walkways -- prop set for phases 2 and 3 |
| `kenney_impact-sounds.zip` | 783 KB | 130 OGG, 26 families x 5 variants | see the sound map below |

Source: [kenney.nl](https://kenney.nl/assets) -- everything there is CC0, direct
download, no account.

### The sound map

The impact pack lines up with the `SoundBed` strings the A4 pipeline authored,
which is why it was picked over a generic library:

| GDD moment | Family | Why |
|---|---|---|
| dog's paw step, phase 1 yard | `footstep_grass` | "low sun across the grass" |
| dog's paw step, phase 2 street | `footstep_concrete` | paving slabs and ballast |
| Rex's step | `impactMetal_light` | servo whine's percussive partner |
| chain-link ring when either animal touches it | `impactPlate_light` | phase 2's stated sound |
| couplings taking up slack, phase 3 | `impactMetal_heavy` | phase 3's stated sound |
| a read fires | `impactBell_heavy` | one clean stinger under the line |
| loss | `impactSoft_heavy` | |

Five variants per family means round-robin playback, so repeated steps do not
machine-gun.

**One conversion caveat:** these are `.ogg`. UE's import path is built around
`.wav`, so convert before importing (ffmpeg: `ffmpeg -i in.ogg out.wav`).
Confirm on one file before batch converting all 130.

## Still needed, and where to get it

### The dog and the robot -- Quaternius, CC0

[quaternius.com](https://quaternius.com) publishes everything under CC0 with
attribution explicitly not required, confirmed on their FAQ. Three packs matter:

- **Ultimate Animated Animal Pack** -- 12 animals, 12+ animations each. The dog.
- **Animated Robot Pack** -- Rex.
- **Modular Streets Pack** -- the cul-de-sac and the fence gap.

These are gated behind a JavaScript download modal rather than a direct link, so
they need a couple of clicks in a browser; they cannot be fetched by script.

### Ambient beds

The three phase beds -- wind in a chain-link fence, a lamp on a motion timer, an
idling engine -- are the one thing the impact pack cannot supply.

- [gamesounds.xyz](https://gamesounds.xyz/) -- public domain, direct download,
  no account. Try here first.
- [freesound.org](https://freesound.org) -- has exactly these, but downloads
  need a free account.
- [Sonniss GameAudioGDC](https://sonniss.com/gameaudiogdc/) -- professional,
  royalty-free, no attribution. Enormous (tens of GB per year bundle); pull a
  single year only if the above fail.

### Fab

[Fab's Limited-Time Free](https://www.fab.com/limited-time-free) rotates free
paid assets every two weeks, and claimed items are kept permanently. Claiming
requires signing in to an Epic account, so it has to be done by hand -- no
script and no agent can do it for you. Worth a look for a nicer robot, but
nothing in the plan depends on it.

## Other CC0 sources worth knowing

Consistently recommended, all CC0 or CC0-filterable:

- [Poly Pizza](https://poly.pizza) -- 10,600+ models including the archived
  Google Poly library
- [Poly Haven](https://polyhaven.com) -- HDRIs and PBR textures
- [KayKit](https://kaylousberg.itch.io) -- character and environment kits
- [OpenGameArt](https://opengameart.org) -- oldest archive still running; use the
  advanced search with only CC0 ticked, quality varies wildly otherwise

## Licence position

Everything downloaded so far is CC0, so the build carries no attribution
obligation. That said, crediting Kenney and Quaternius in the itch page costs
nothing and is the norm. If any non-CC0 asset is added later, record it in this
file at the time -- not at submission.
