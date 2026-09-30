# Native widget renderer baseline

Six renderer-unit cases compare all38 point/game/status/mode selector values
through the shared live native backend: seven per point/game/status field and
three modes. Thirty-two field/value contexts use original rasters at that exact
column. Six use the opposite column's captured glyph with verified shared-font
equivalence. They are additional font-unit checks, not original game-scene
observations. All38 comparisons are green.

## Original references and explicit shared-font scope

`scripts/widget_reference.py` validates the frozen P1 recipe, both media and
raster-association manifest hashes, source parent hashes and cartridge hash.
Every selected original PNG is checked by its RGB hash. Its associated VDP
register/VRAM bytes are checked independently. Actual captured tile records
identify the source selector. Native field definitions must exactly equal the
verified cartridge records. A static glyph decode is an eligibility filter for
visible sprite obscuration/partial writes; expected pixels come from the original
cropped raster, never the decoder or native asset generator.

Directly observed contexts are:

| Field | Source selectors |
|---|---|
| point_a | 0,1,2,3,4,5 |
| point_b | 0,1,2,3,5,6 |
| games_a | 0,1,4 |
| games_b | 0,1,2,3,4,5,6 |
| status | 0,1,2,3,4,5,6 |
| mode | 0,1,2 |

Additional shared-font checks are point_a6 from point_b6, point_b4 from point_a4,
and games_a2/3/5/6 from games_b2/3/5/6. The paired fields use identical ROM tile
records, dimensions, row position/GraphicsII pattern and colour bank, and native
variable/fixed planes. Only their horizontal destination differs. Reports retain
the donor column and explicit equivalence. Original opposite-winner/scene
contexts remain separate reference requirements. Alias score selectors such as
3/5 still test their current native table routes even when the glyphs coincide;
the final native implementation may collapse such aliases with an adapter mapping.

## Actual native backend and buffer transitions

The private unit wrapper uses the existing application's initial graphics,
four-plane display, eight sprite channels, converted assets,
`upload_sprite_attributes`, `patch_score_pointers` and `poll_presentation`.
It replaces the game-loop dispatch with a renderer request loop. The debugger
supplies only six native field selectors and a request byte; no source-game RAM,
SG device writes or expected intermediate game states are injected. No game
callbacks execute. This is a graphics backend test, not gameplay integration.

Seven asymmetric selector tuples visit every value while separating each field
from neighbouring fields. Each selection prepares the inactive Copper list.
The full displayed list is byte-for-byte unchanged before commit; the actual
front address then alternates between the two buffers. All commits occur in
blanking. Capture waits for the entire frame using that committed generation,
including a second physical beam wrap when commit is after the visible area.
The existing exact palette/viewport mapping compares original/native pixels
without image fitting or interpolation.

All pixels outside the six field rectangles remain identical across seven
scenes. This checks pointer restoration and prevents a matching cropped glyph
from concealing changes elsewhere in the row/display. Source sprites are fixed
throughout this unit test; game-driven sprite/field interaction and ordinary
workload deadlines remain P1/P3 work.

## Actual executable sensitivity and reproduction

Two temporary backend mutations assemble separate executable/capture directories:
select bank0 for every variable descriptor, and read the adjacent field's selector.
Both are detected in every one of the six field cases. The asymmetric tuples
make cross-field wiring errors observable. Normal backend/product source and
original frozen references remain unchanged. All normal/mutation capture hashes
and retained native screenshot hashes verified after the complete suite.

Run `python scripts/run_widget_tests.py --all --self-test`, or
`--case p1-widget-status` (and other registered widget cases). The aggregate
runs one shared batch and classifies six reports separately, removes stale
reports, and rejects failed/incomplete batches as tool errors.

Full aggregate baseline/self-test:83 cases,48 green,35 exact known red, no
unexplained failures/tool errors. Four missing requirement groups still cause
failure. Renderer-unit selector coverage is complete; stop equivalent font-bank
snapshot variants. Next compare game-driven status appearance/expiry using
retained original transitions, live-produced selections and committed pixels.
Point/mode/round/result/restart timing, other P1 scenes, P2 audio, P3 ordinary
input/cadence/deadlines and focused F2/F4/F5 behaviours remain in full scope.
These unit cases may migrate to another native renderer interface without
retaining source selector encodings, bank layout or Copper-list structure.
