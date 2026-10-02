# Current executable size attribution

Committed merged product: development **248,480 B**, release **211,920 B**. Release removes only **36,560 B** of HUNK_SYMBOL metadata. Loaded payload is **202,104 B**, unchanged by stripping.

Development SHA256: `0240658feac160753239ca9bfdbed30858b56049ecf68f0a8647d5158bd26ea9`.
Release SHA256: `783bd53c737cab5497d46752f3e95f3acad0ba791570b2b6d547aa64480939f9`.

Every file byte is counted once below. CODE/DATA are containing views and include assets/tables/reserves; only the instruction row is CPU instructions. Fonts, Battle Hymn scores/periods/waveform, robot poses and every active UI cache are included.

| Exclusive category | Development bytes | Release bytes |
| --- | ---: | ---: |
| audio envelopes | 128 | 128 |
| audio period table | 3,072 | 3,072 |
| audio scores | 1,504 | 1,504 |
| build version text | 14 | 14 |
| celebration period table | 3,072 | 3,072 |
| celebration scores | 2,112 | 2,112 |
| celebration square wave | 4 | 4 |
| court bitplanes | 24,576 | 24,576 |
| cpu instructions | 12,186 | 12,186 |
| font | 1,024 | 1,024 |
| front court and title copper lists | 3,184 | 3,184 |
| hunk header table | 28 | 28 |
| hunk record headers and ends | 24 | 24 |
| initial hardware sprites | 576 | 576 |
| menu font mac | 1,024 | 1,024 |
| mode banks | 3,072 | 3,072 |
| other initialized tables and scalars | 750 | 750 |
| pre rendered demo options | 512 | 512 |
| pre rendered help options | 768 | 768 |
| pre rendered menu options | 1,280 | 1,280 |
| pre rendered title ui pages | 29,696 | 29,696 |
| pre rendered ui pages | 14,848 | 14,848 |
| relocation offsets | 9,740 | 9,740 |
| relocation record framing | 24 | 24 |
| replay packets | 1,110 | 1,110 |
| reserved back copper | 3,048 | 3,048 |
| reserved back sprites | 576 | 576 |
| reserved native stack | 4,096 | 4,096 |
| reserved state and work buffers | 962 | 962 |
| reserved ui overlay | 512 | 512 |
| scene animation table | 36 | 36 |
| scene pose table | 112 | 112 |
| scene robot pose table | 112 | 112 |
| scene sprite variants | 11,264 | 11,264 |
| score game banks | 21,504 | 21,504 |
| score patch pointer tables | 7,972 | 7,972 |
| score point banks | 14,336 | 14,336 |
| separate debug records | 0 | 0 |
| source alignment padding | 14 | 14 |
| status banks | 7,168 | 7,168 |
| symbol name padding | 1,503 | 0 |
| symbol names | 23,889 | 0 |
| symbol record framing | 11,168 | 0 |
| title bitplanes | 24,576 | 24,576 |
| ui text and line pointer tables | 1,304 | 1,304 |
| **Total** | **248,480** | **211,920** |

Hunk CODE 49,564 B; DATA 152,540 B; BSS 0 B. Symbols/relocations/framing are separate file metadata. Reserved dcb storage is file-backed, not BSS. No separate HUNK_DEBUG record is emitted.

Identical embedded asset copies contribute 22,528 bytes beyond first copies. This is informational duplication, not validated aliasing/compression savings.

The supplied original cartridge measured 8,192 bytes (SHA256 `19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1`), not the claimed16KB. It is not a build/metrics dependency. Original compact tile/pattern/color representations differ from expanded Amiga planes, masks, UI caches and two prepared sprite variants; no original per-component ROM allocation is inferred.

Regenerate static attribution with the ordinary native build or `python scripts/native_metrics.py --require-runtime --record`. Unknown gaps, overlaps, listing/asset mismatches fail generation. Current runtime evidence is in current.json/.md. Pre-PR19 size reports are preserved under baselines/; the historical stripping comparison does not certify this merged product.
