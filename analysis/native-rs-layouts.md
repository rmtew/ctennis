# Native RS layouts: byte-identical refactor

The approved follow-on changes field declarations to `RSSET 0` and typed
`RS.B/W/L`, with zero-count end labels calculating each `*_SIZE`. It is
stacked on PR12's receipt correction at5e835d81d9f4c7376a61e2508a7ade8e373afa8b.
It changes no runtime instruction, allocation, initializer or interface.

| Layout | Size | Explicit preserved padding |
| --- | ---: | --- |
| Player P | 10 | none |
| Gameplay G | 60 | byte59 |
| Scoring S | 28 | bytes5,12,27 |
| Audio voice AV | 32 | bytes20–31 |
| Scene object O | 8 | bytes6–7 |
| Display packet D | 8 | byte7 |

Points/games remain pairs of byte cells; `S_POINTS` stays even at6 for the
existing word clear. `AV_NEXT` is long, `AV_PERIOD` and `O_FRAME` are word
fields. The unchanged storage declarations still allocate all bytes, including
three32-byte voices, eight8-byte objects and the reserved padding. RS defines
offsets; it does not allocate storage. No implicit alignment is assumed: the
actual pinned vasm flags omit `-align` and `-devpac`. A tiny assembler probe
confirmed a byte followed by `RS.W` has word offset1, not2. Each layout resets
the counter explicitly. Address aliases, enums, masks, hardware constants and
original-capture offsets remain EQU.

## Programmatic verification

Before and after, run the same existing command for each flavor:

```sh
RUST_LOG=info python scripts/build_native_game.py --interface=original
RUST_LOG=info python scripts/build_native_game.py --interface=enhanced
```

Before artifacts are retained under `build/layout-refactor/before/<flavor>/`;
after artifacts under `after/`. Full executable byte comparison, SHA256 and all
emitted listing symbol maps match. Original has1255 emitted symbols and
enhanced1260; all115 tracked layout constants match. Sizes are10/60/28/32/8/8.

| Flavor | Before = after executable SHA256 |
| --- | --- |
| Original | `b3ac773721e62f2cabe7806523f5650192386e4bc99e2e4a30aa880260d1d492` |
| Enhanced | `b5ed3d68c5a169e526cf8887e98887d8d91b55c6251f8aad9afd883dc83c6eee` |

Both `build_native_adf.py --interface=<flavor> --self-test` runs also pass two
clean deterministic packages. Full before/after ADF bytes match: original
`aff2a3df026ba888724a6f32ae3c055184829b425ecd97ae06cbfcf347934401`, enhanced
`9367da9f2781236f7aa2d0deb96d58178e93c4a4dda36d50288f5a376d92b303`.
The ignored `build/layout-refactor/byte-identity-report.json` retains checks,
symbol maps and both source/asset/executable/build-tool provenance snapshots.
A mismatch raises rather than being declared equivalent. All private binaries,
assets and evidence remain outside Git.

There was no emulator/gameplay retest for byte-identical output. Runtime
receipts remain truthful evidence of their original execution heads; the
conservative source-fingerprint progress classifier may call them stale after
this source-only refactor. They were not rewritten to claim fresh execution.
The fresh evidence here is exact compiled identity, not new runtime counts,
RAM measurements or fidelity claims. Independent source/hash review and merge
remain separate.
