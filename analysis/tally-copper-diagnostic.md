# Tally Copper timing diagnostic

Diagnostic candidate based on master `233727868b152b8a9c8add3d4dfd289e3d5ef027`.
The user subsequently validated visible tally behavior in WinUAE; this was
a user-run test, not local WinUAE execution. The original failure was blank enhanced
tallies on WinUAE 6.0.2 (2025.12.21), including a fresh cycle-exact Full run,
with PAL OCS 68000, 512 KB chip and 512 KB slow RAM. Configuration is not an
established cause. The absent GAME marker is also not independently explained.

## User follow-up

The user initially reported a win added to the tally column and match-end
music followed by return to the menu. They then explicitly identified the
artifact and clarified: "I was testing diagnostic enhanced. saw win text in
column, with6wins toai resulting in game music iirc". This resolves the earlier
artifact ambiguity and validates the reported visible tally behavior on the
user's confirmed WinUAE6.0.2 setup. The six AI wins/music detail is recalled
with uncertainty; it is not a captured six-win trace or a locally executed
WinUAE receipt. The runtime result does not measure the DMA collision itself
or independently establish all original-layout/both-side target behavior.

Read-only artifact verification confirms the diagnostic enhanced ADF remains
`500eb5c732c0d837f6a8cd9a718c372eb3a1acc99000c7a6078f10311345711f`, embedding
executable `80969eb5e05666e6eb3b7256c17b89985e2928ade69ebfd1f6249cbb32411e45`.
It contains exactly the96 WAIT-byte changes against the reviewed baseline and
no menu/demo code. The parent's independent source reviewer cleared product
head49e018a; subsequent commits only document user follow-ups. Feature worker
integration is authorized for combined review; this branch remains unmerged.
The user's earlier demo observation stays with that worker and does not expand
this tally repair's scope.

## Minimal candidate

Only games_a/games_b WAIT positions in the existing offline Copper generator
move two color clocks earlier: original $3d/$9d to $3b/$9b, enhanced $4d/$ad
to $4b/$ab. Pointer offsets 2/26, all other fields, and row restore WAIT $d1
remain unchanged. Offset26 deliberately fetches x208 before x224; changing
it would be a separate layout change. Each executable changes exactly 96
bytes, all these WAIT bytes reduced by two; executable sizes are unchanged.

## Primary source and evidence boundary

[WinUAE 5.0 source at 975a167](https://github.com/tonioni/WinUAE/blob/975a167c7636d563db1c8b3292f690b6f30e71d2/custom.cpp#L8809)
explicitly ignores a Copper pointer-half write when the following DMA slot
belongs to that plane. Its test does not depend on CPU cycle-exact settings.
This supported the initial hypothesis, but is **not** the user's implementation.

[WinUAE 6.0.2 tag6020 at 1bfce014](https://github.com/tonioni/WinUAE/blob/1bfce014bf802c31a1dd4d7ec04b4963bf0f72bf/custom.cpp#L3696)
has simple PTH/PTL merge handlers instead. Its `do_cck` calls
`bitplane_rga_ptmod` before `handle_rga_out`: DMA snapshots the pointer through
`write_rga_update` before that clock's Copper write. Later DMA completion
increments and writes the snapshot back. The independent exact-version source
review derives right-side old WAIT$ad writes at$b2/$b6, a DMA snapshot at$b6,
and fetch/writeback at$b7, overwriting the late PTL. Candidate WAIT$ab writes
at$b0/$b4, after the previous fetch$af and before snapshot$b6. This supports
the candidate for6.0.2, but is static reasoning, not an executed failing or
repaired WinUAE run. The mechanism is DMA writeback overwriting a late write,
not the5.0 explicit-drop handler. Do not transfer Copperline clock coordinates
to WinUAE as runtime proof.

Installed Copperline 1.0.0-rc.1 source is pinned at
`e65a9584ccd0c86e678661ed5d2c18622da63fd4`. `src/bus/custom_regs.rs`
1284–1317 merges pointer halves into the live DMA pointer without the 5.0
rejection. `src/chipset/agnus.rs` defines lores fetch order
8,4,6,2,7,3,5,1. Copperline therefore does not independently reproduce the
user's blank-tally failure.

Fresh complete-frame Copperline slot traces at physical line116 measure:

| Layout/side | Baseline PTH/PTL | Candidate PTH/PTL | BPL2 surrounding fetches |
| --- | --- | --- | --- |
| enhanced left | $4e/$52 | $4c/$50 | $4b/$53 |
| enhanced right | $ae/$b2 | $ac/$b0 | $ab/$b3 |
| original left | $3e/$42 | $3c/$40 | $3b/$43 |
| original right | $9e/$a2 | $9c/$a0 | $9b/$a3 |

Restore writes remain $d2/$d6. The candidate halves fit between fetches;
the earlier suggested right WAIT $a9 would straddle the preceding fetch.
These are measured Copperline coordinates, not measured WinUAE coordinates.

## Bounded runtime checks

Before regeneration, existing private output was preserved under ignored
`build/tally-diagnostic/preserved/`; byte-identical reviewed baseline builds
and packages are under `before/`. Missing title media was restored using the
existing repeated `capture_mode_reference.py`, then the existing offline
asset preparation ran. Only Copper commands/tables were regenerated for the
candidate. The recognized pinned package builder dependency amitools0.8.1
was restored locally; no new emulator was installed.

Both flavors and both ordinary physical modes ran through two successive
awards before and after. One-player counters/fields/banks progress 0/0,
0/1,0/2; two-player runs progress 0/0,1/0,1/1. The observer only supplies
physical mode/fire inputs and reads state. Custom-register snapshots confirm
hardware COP1LC equals inspected presentation_copper; the actual selected
pointer's full 1536-byte bank matches its selected variant. This covers zero
and nonzero tally on both sides. Sampling is bounded and does not claim every
callback, full-match acceptance, or cycle equivalence.

All 24 paired tally crops are byte-identical before/after. One tally mark has
23 source-sized gold pixels (46 in the native doubled-width raster); two marks
have46/92. The existing candidate command
`RUST_LOG=info python scripts/run_ordinary_round_tests.py --mode=one --interface=enhanced`
passes1861 consecutive observations: award1799, pause1928, resume2064,
advancing next serve2161. The baseline command also passes at those milestones.
Both existing package commands with `--self-test` pass two-clean reproducibility.

Ignored receipts: `build/tally-diagnostic/runtime-index.json`,
`crop-comparison.json`, `byte-and-slot-evidence.json`, each complete probe's
`report.json`/`profile-*/tally-line116.json`, and `candidate-ordinary-guard.log`.
The small private observer `tally_probe.py` reuses NativeControlSession and
native_state_observation; it is not a new tracked test framework. Initial
partial-frame/profile-already-running attempts were corrected and are retained
separately; they do not certify complete slot/award evidence. A direct read of
the write-only COP1LC register produced $ffffffff; hardware selection uses
the actual custom-register snapshot instead, with the raw attempt retained.

| Artifact | SHA256 |
| --- | --- |
| baseline enhanced ADF | 9367da9f2781236f7aa2d0deb96d58178e93c4a4dda36d50288f5a376d92b303 |
| candidate enhanced executable | 80969eb5e05666e6eb3b7256c17b89985e2928ade69ebfd1f6249cbb32411e45 |
| candidate enhanced ADF | 500eb5c732c0d837f6a8cd9a718c372eb3a1acc99000c7a6078f10311345711f |
| candidate original executable | 1d7421946c8e3de8fbf7ccc7b5bff95ee68d83017ea237a47fc74d0104812829 |
| candidate original ADF | 7f6dcacb2746d2c3fe6c60bbd0faa6845539d8b9ed63303ff51f1daad822dad6 |

No WinUAE execution is available locally. The private user-test ADF is
`build/tally-diagnostic/ctennis-enhanced-tally-diagnostic.adf`; supported Library
upload preparation through the current Library helper failed with a network
error. No upload or attachment success is claimed. Private media, ROMs,
generated banks, executables, ADFs and captures stay out of Git.

Next: the authorized feature worker integrates the independently reviewed
tally change for combined review. Preserve user-run target validation separately
from local Copperline measurements. No additional tally tests or merge are
performed by this worker.
