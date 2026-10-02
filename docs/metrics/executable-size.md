# Current executable size attribution

Committed merged product: development **235,180 B**, release **197,812 B**. Release removes only **37,368 B** of HUNK_SYMBOL metadata. Loaded payload is **202,248 B**, unchanged by stripping.

Development SHA256: `045bf76b5553886b9463aa161346c11508ff6437b6b422fd88ffe27dbb6216a8`.
Release SHA256: `0b6932d08ddbf012a0a2a793a3039cbbea4e0f2ce46f3efb9b1d02ad627f4303`.

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
| cpu instructions | 12,442 | 12,442 |
| font | 1,024 | 1,024 |
| front court and title copper lists | 3,200 | 3,200 |
| hunk header table | 32 | 32 |
| hunk payload alignment padding | 2 | 2 |
| hunk record headers and ends | 36 | 36 |
| initial hardware sprites | 576 | 576 |
| menu font mac | 1,024 | 1,024 |
| mode banks | 3,072 | 3,072 |
| other initialized tables and scalars | 790 | 790 |
| pre rendered demo options | 512 | 512 |
| pre rendered help options | 768 | 768 |
| pre rendered menu options | 1,024 | 1,024 |
| pre rendered title ui pages | 29,696 | 29,696 |
| pre rendered ui pages | 14,848 | 14,848 |
| relocation offsets | 9,800 | 9,800 |
| relocation record framing | 32 | 32 |
| replay packets | 1,110 | 1,110 |
| reserved back copper | 3,064 | 3,064 |
| reserved back sprites | 576 | 576 |
| reserved native stack | 4,096 | 4,096 |
| reserved state and work buffers | 962 | 962 |
| reserved ui overlay | 512 | 512 |
| scene animation table | 36 | 36 |
| scene pose table | 112 | 112 |
| scene robot pose table | 112 | 112 |
| scene sprite variants | 11,264 | 11,264 |
| score game banks | 21,504 | 21,504 |
| score patch pointer tables | 8,008 | 8,008 |
| separate debug records | 0 | 0 |
| source alignment padding | 13 | 13 |
| square led construction definitions | 48 | 48 |
| status banks | 7,168 | 7,168 |
| symbol name padding | 1,530 | 0 |
| symbol names | 24,438 | 0 |
| symbol record framing | 11,400 | 0 |
| title bitplanes | 24,576 | 24,576 |
| ui text and line pointer tables | 1,291 | 1,291 |
| **Total** | **235,180** | **197,812** |

Hunk CODE 49,932 B; DATA 137,980 B; BSS 14,336 B. Symbols/relocations/framing are separate file metadata. Reserved dcb storage is file-backed. Startup-generated point banks occupy 14,336 B of chip BSS across28 banks; they contribute no file payload bytes. No separate HUNK_DEBUG record is emitted.

Identical embedded asset copies contribute 2,048 bytes beyond first copies. This is informational duplication, not validated aliasing/compression savings.

The supplied original cartridge measured 8,192 bytes (SHA256 `19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1`), not the claimed16KB. It is not a build/metrics dependency. Original compact tile/pattern/color representations differ from expanded Amiga planes, masks, UI caches and two prepared sprite variants; no original per-component ROM allocation is inferred.

Regenerate static attribution with the ordinary native build or `python scripts/native_metrics.py --require-runtime --record`. Unknown gaps, overlaps, listing/asset mismatches fail generation. Current runtime evidence is in current.json/.md. Pre-PR19 size reports are preserved under baselines/; the historical stripping comparison does not certify this merged product.
