# Bounded deterministic match-core proof

This implements only the first small M1 experiment from draft PR #24, authorized
by the user's “do the proof”. Base: `2251cc0a6b17f3c8ca9d9af7adf4772acd1eb8d0`.
It changes no production assembly, assets, rules, RNG policy or independent
contracts. Recorder, checkpoints, Shot Doctor UI and counterfactuals remain later
work. Independent review precedes merge; the parent coordinator assigns reviewers.

## Run

Use the normal pinned native tools and external legitimate Kickstart specified in
[the test guide](../tests/README.md). The additional CPU harness is machine68k
0.4.1 (Musashi); its source archive is hash-pinned separately from product tools.
For example, using a compiler-equipped Python 3.12 environment:

```sh
CC=gcc CXX=g++ python -m pip install --target .tools/proof-python \
  --require-hashes --no-binary=machine68k -r tests/match-core-proof-requirements.txt
PYTHONPATH=.tools/proof-python RUST_LOG=info python scripts/run_match_core_proof.py
PYTHONPATH=.tools/proof-python python scripts/run_match_core_proof.py \
  --replay build/tests/match-core-proof
```

The first command sequence boots the native game and compares it with an isolated
68000 CPU, then replays with differently filled RAM and registers. The second
invocation consumes the captured initial image and logical controls without
opening Copperline or a ROM. Expected states are read only for assertions.
Raw initial image, state, inputs, outputs and receipts stay in ignored `build/`.
They include private assets and are not portable save files or redistributable
fixtures. A new native run invalidates the earlier proof receipt before building.

## Boundary and identity

The native side uses the ordinary title, physical Delete selection, physical held
fire and live gameplay dispatcher. Its existing `DEMO_RECORDING` build option
selects seeded entropy while retaining live controls and reactive AI. This is an
explicit deterministic fixture variant, not a claim that today's ordinary live
CIA entropy is already deterministic. `game_new_match` seeds the existing 16-bit
LFSR once. The existing gameplay 8-bit PRNG is also retained in state.

At LoadSeg, every relocated hunk is verified against the fixture executable.
Both CPUs receive those same code/table bytes. Once the native game reaches its
first playing callback, the harness copies only inventoried mutable state into
its pristine loaded image. There are no later native-state transfers or expected
state injections. Its monotonically increasing host row index crosses the native
8-bit tick wrap.

Only `game_render_sprites` and `game_scene_present_fields` have their entry words
replaced by RTS in standalone memory. They are presentation sinks; all scene
construction, animation, status expiry, court-coordinate changes and audio
sequencing execute unchanged. Actual audio wrappers write the same six Paula
period/volume registers through a write-only sink. No Python gameplay model,
scoring oracle or captured callback-regime selection exists.

The native loop polls lifecycle between callbacks, handles keyboard/presentation
and elapsed time, then runs physical sampling, `ui_sample`, rendering, dispatcher
and scene publication. For this bounded live point, UI remains unpaused and does
not alter match state. Standalone uses these explicit phases:

1. Invoke `game_round_poll` twice; require unchanged full state and no outputs.
   Native polling is inert throughout this first-point path. This proves only
   this bounded domain, not round awards, result/title or restart idempotence.
2. Feed logical A/B held masks to the actual `game_store_pad` routines. They
   compute pressed/released edges and retire inherited action latches.
3. Run `game_tick_dispatch`: scene fields, control assignment, score, gameplay,
   scene finish; then clocks, full audio sequencing and scene service.
4. Compare every owned byte and ordered output writes at `complete_update`,
   before its completion counter increment. Require consecutive native counters.

Red fire is held on both controller ports and carried from selection; this does
not exercise the separate blue action buttons. Ten live updates must suppress
the held red actions; release clears both latches, and repress permits service.
A later release in point pause and repress in sound wait exercise transition sampling. The proof
requires a successful `game_return_vector` visit, actual entropy use, point pause,
sound wait and an advancing next serve. Inputs are recorded independently from
full-state assertions and reused for standalone replay.

## Ownership and completeness

The machine-checkable `OWNED` inventory in
[the runner](../scripts/run_match_core_proof.py) contains 307 bytes:

| Region | Bytes |
| --- | ---: |
| Gameplay and scoring packets | 88 |
| Scorer initialized flag and five auxiliary gameplay bytes | 6 |
| Held/pressed/released masks, player controls, owners and old action latches | 12 |
| Lifecycle, menu selection context and new-mode byte | 10 |
| Celebration state (retained but inactive here) | 8 |
| Three complete audio voices plus four sequencer globals | 100 |
| Scene objects and ball layer | 65 |
| Display adapter, dirty flag and six display fields | 15 |
| Entropy LFSR and demo flag | 3 |

Reserved packet/voice bytes and audio pointers/cursors are compared too. Audio
`AV_DONE` means the last note was loaded, not that its duration expired; retaining
only a cue-complete Boolean would lose future sequencing. The renderer's prepared
banks, UI state, hardware keys and clock/presentation counters are outside this
bounded core; state comparisons check that the ordinary integration preserves
the proposed separation over the observed path.

Every standalone write must target owned state, bounded stack, or an allowed
Paula output. The return trap permits only its 16-bit read/fetch; CPU writes
to it are rejected. Other reads must target the loaded image or stack; a final
audit
further restricts observed reads to owned state, executed instruction bytes and
an explicit immutable table inventory (`READONLY`). This captures scoring field
maps, pose/animation tables and audio score/period/envelope tables. No blanket
permission for unlisted mutable globals is used in that final audit. These are
observed-path completeness checks, not proof of all unreachable branches.

Ordered scene-object, ball-layer, display-field and Paula writes are compared,
including repeated writes. Registers and unused working RAM receive different
fills on replay. Negative controls omit initial audio state, remove the tick
clock from writable ownership, force the actual CIA-read instruction into
the entropy path, and execute a forbidden word write to the return trap. Each
must fail for its stated reason.

Audio pointers remain native relocated addresses in this experiment. A future
canonical snapshot must replace them with validated table IDs/offsets and define
build/schema compatibility. The capture binds executable/hunk/initial-image
hashes and is usable only with this proof's exact code/layout. It is not yet a
checkpoint schema. Different counterfactual RNG call order remains unresolved;
a same-seed experiment is not a paired-randomness guarantee.

## Evidence and resource limits

The bounded PAL, A500, 68000, OCS, 512 KB chip, no-expansion run compares 362
updates, including one successful AI return. All 307 owned bytes and output
sequences agree at every boundary. Poisoned replay and all four negative
controls pass. The separately invoked standalone replay also agrees.

The ordinary development executable remains byte-identical to the base product:
`c90fd520ac214a08d315f5dd4c993f3afb54f4f63edb6ad87ba4aa6d3650cf54`.
The deterministic fixture is
`164a0eaf7752466335f251923f0455b37f4cd27f65e491657ae19d326ce603f4`.
Production code/data/BSS deltas are zero. 307 bytes is the inventoried mutable
payload, not a proposed allocation or total standalone executable size.

Observed maxima in the bounded run (not execution-time guarantees):

| Workload | Updates | Dispatcher cycles | Step cycles | Native callback CCK |
| --- | ---: | ---: | ---: | ---: |
| All | 362 | 24,162 | 25,282 | 26,475 |
| Fresh pressed/released edges | 4 | 13,664 | 14,784 | 21,073 |
| Active flight | 118 | 24,162 | 25,282 | 26,338 |
| Point/sound wait | 200 | 11,836 | 12,956 | 26,475 |

Observed standalone stack use is 128 bytes, including call return addresses.
182 distinct owned bytes were written; all 307 were compared. Read auditing
covered 5,213 distinct addresses, including code and immutable tables.

The receipt records per-update dispatcher CPU cycles, total standalone step CPU
cycles (including two polls and input sampling), observed standalone stack depth,
and native callback CCK. Musashi CPU cycles omit Amiga contention and renderer
work; native callback CCK includes ordinary UI/render/publication preparation and
interrupts. These measurements are not interchangeable or worst-case bounds.
Review fresh input, active rallies and point/sound transitions separately. This
short run cannot establish resource ceilings for unbounded rallies/deuce or full
match lifecycle. The repository's incomplete global resource report is unchanged.

## Review gate and next decision

- [x] Execute the actual shared routines without production extraction.
- [x] Compare complete inventoried state and ordered outputs through next serve.
- [x] Exercise held suppression, edges, transition release/repress and audio wait.
- [x] Audit observed reads/writes; run poisoned replay and negative controls.
- [ ] Independent core/state and native/resource review of this bounded proof.
- [ ] Approve broader extraction and deterministic live entropy policy separately.

The implementation owner integrates review fixes; the parent assigns independent
reviewers. Expansion must inventory round/result/restart polling and input phases
before assuming this boundary generalizes. The next architecture decision is
whether to retain scene/audio semantics inside core state or extract equivalent
semantic state while preserving timing. This proof deliberately does not make
that migration or approve a recorder/UI rollout.
