# Champion Tennis G-1009: whole-ROM static review

This is a source-level reading of the identified 8,192-byte image, at Z80 origin `$0000`. No emulator was run for this review. Earlier runtime captures remain historical evidence; the classifications and inferences below come from ROM control flow, immediate operands, pointer construction, table consumers, and the byte-exact reconstructed listing. The rebuild proves preservation of bytes, not the correctness of these meanings.

The current [block partition](rom-blocks.def) covers `$0000-$1FFF`: 5,765 instruction bytes and 2,427 bytes emitted as data. [Direct data evidence](rom-data-evidence.tsv) covers 2,413 unique emitted bytes. The other 14 bytes are explicit unknowns, described below. Instruction continuations formerly emitted as bytes were restored where branch targets, fallthrough, and local state use support them. This is a whole-image structural annotation, not a claim that every instruction has a settled gameplay meaning.

| ROM span | Static interpretation and principal consumers |
| --- | --- |
| `$0000-$01C2` | Reset, IM 1 interrupt dispatch, VDP/PSG initialization, title/menu loop, color-run expansion, startup graphics copies. Vector gaps contain padding. IRQ callback is installed through RAM, so the callback body must be read separately. |
| `$01C3-$01D2` | Fifteen encoded color runs and terminator, expanded by `$009A-$00AC`. |
| `$01D3-$02DB` | VDP setup, sprite termination, RAM initialization, ROM-to-VRAM copier `$029D`. |
| `$02DC-$02E3` | Eight initial VDP register bytes. |
| `$02E4-$0375` | VDP byte writer and title name-table construction. |
| `$0376-$0406` | Packed title masks and direct title tile strings; `$05DA` expands masks. |
| `$0407-$0479` | Clears and builds court/title name-table rows; `$046F` uploads RAM sprite attributes. |
| `$047A-$055E` | Setup template, fixed-width VRAM rows, and tile data. |
| `$055F-$0644` | Alternating sprite-pattern copy, title/court transition, screen setup and draw operations. |
| `$0645-$0668` | Court-layout bytes; `$060C-$062B` reads all 36 bytes as 18 two-byte rows, repeating each byte six times in VRAM. |
| `$0669-$0724` | IRQ callback and counters. `$0699` calls sprite upload `$046F`, scoreboard `$06EB`, input `$0832`, scoring gate `$094E`, lower and upper player handlers `$0B29/$0E54`, ball flight `$11A0`, and movement/sprites `$13B9`, in that order. `$06B1` advances counters and services audio. |
| `$0725-$0831` | Scoreboard/mode/tally/point display logic interleaved with fixed-width tile records: seven 3-byte status records, three 5-byte mode strings, seven 12-byte game-tally records, seven 4-byte point records. |
| `$0832-$095D` | SG controller and SC keyboard reads, input selection and normalization, scoring gate. `$0242` derives control flags from mode state `$C03D`; the two input paths populate per-player direction/action state. |
| `$095E-$0B72` | Score selection and tennis-point state transitions, then lower-player serve/hit dispatcher and trajectory setup. `$0B73-$0B79` is a 7-byte trajectory vector copied by `$1760`. |
| `$0B7A-$0E38` | Lower-player contact, launch, and trajectory selection. Shared contact helper `$1770` requires small court-plane separation; additional height test compares `$C034` with `$C04D`. |
| `$0E39-$0E53` | Three 9-byte trajectory threshold/output records. |
| `$0E54-$10D6` | Upper-player serve/hit dispatcher, contact and trajectory selection, plus related AI/return paths. `$0EA0-$0EA6` is its 7-byte serve vector. |
| `$10D7-$10E8` | Two further 9-byte trajectory records. |
| `$10E9-$11A0` | Player sprite-record builder using fourteen 5-byte descriptors at `$115A-$119F`. |
| `$11A0-$144C` | Ball flight, boundary/contact flags, trajectory advance, player movement and sprite state. `$12CE` advances trajectory; `$1298` marks court contact, `$120E` marks out-of-area, `$1383` checks the net vicinity. |
| `$144D-$148B` | Movement update with two 4-by-4 boundary tables at `$144D` and `$147C`. |
| `$148C-$1541` | Animation selection and table at `$14FA-$151D` (four 9-byte records). The selector masks three low bits, but audited ROM writers produce indices 0-3, including the upper serve's `$F3`. Indices 4-7 require an out-of-model RAM value or missed alias. |
| `$1542-$17B8` | Arithmetic, directional AI and ball-intercept calculations, shared hit geometry `$1770`, pseudo-random update `$1754`, audio record initialization `$1787`. `$162D` synthesizes a direction nibble in `$C053`; `$167C` predicts/intercepts from ball position/trajectory. |
| `$17B9-$19BB` | Twelve-byte audio-record template, three-channel sound engine, eight-entry command jump table `$185B`, twelve-word pitch table `$18DA`, PSG output and stream advancement. `$17C5` iterates three 14-byte channel records. `$1754` computes an 8-bit recurrence equivalent to `seed = seed * 5 + 1`. |
| `$19BC-$1FFF` | Audio envelopes, sprite/background graphics, and embedded sound streams. `$19CC-$1DCB` is a 1 KB sprite source; `$1C4C-$1F93` is also used as background patterns, so those bytes have overlapping graphics roles. Sound streams occupy `$1F05-$1F52`, `$1F53-$1F96`, `$1F97-$1FB7`, `$1FB8-$1FDC`, `$1FDD-$1FF2`, and `$1FF3-$1FFA`; their lengths follow the setup immediates and `$19AB-$19B8` stream index/fetch logic. |

The point transition at `$09CE-$0A78` is more specific than the earlier branch-coverage plan implied. Each side has a point code in `$C03E/$C03F`. The selected side advances through codes 0, 1, and 2; when an opponent is at code 3, a score from code 2 sets both sides to code 5 (deuce). A score at code 3 or 4 awards a game. Scoring from code 5 sets the selected side to code 4 and the other to code 6; scoring against that advantage returns both to 5. The seven four-byte display records at `$0816` include matching pairs for 40/advantage display states. Tennis labels are inferred from transition logic and records, not verified text decoding. Game tallies at `$C040/$C041` index the seven 12-byte records at `$07B1`; the award path increments one and sets `$C03D` bit 6 at six.

For ball resolution, `$1770` requires absolute Y separation below 4 and X separation below 17; both player hit paths then require court-plane height difference from sprite Y in the range 0-28. Flight processing records court contact and out-of-area in `$C039`; `$094E/$0989` use those flags to enter scoring. This explains the static route from input and contact through the point transition without proving every physical interpretation of the flag bits or every reachable trajectory.

The audio high-nibble dispatch table at `$185B` has eight two-byte targets: `$186B`, `$1883`, `$18F2`, `$1905`, `$1911`, `$192C`, `$1934`, `$193C`. Their bodies implement note/rest emission, alternate note handling, pitch shift, attenuation, envelope selection, scaling, duration and tick setup respectively. Record processing uses `$C085`, `$C093`, `$C0A1`, with stream buffers at `$C0AF`, `$C0CF`, `$C0EF`. This is a static command-family annotation; exact timing against sound output still needs later confirmation.

The 14 bytes without direct data-consumer evidence are `$000E-$000F`, `$0016-$0017`, `$0027`, `$002E-$002F`, `$0036-$0037` (nine inter-vector padding bytes) and `$1FFB-$1FFF` (five image-tail bytes, `00 FF FF FF FF`). They stay byte-emitted and unresolved. The corrected court-layout reader and animation index audit supersede the earlier 27-byte/0-2-index notes. A later emulator pass should confirm exact mode/AI and presentation timing and compare the eventual Amiga implementation against the SG/SC reference. Those checks are deferred; no emulator was used in this static review.
