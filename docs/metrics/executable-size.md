# Measured executable size attribution

Static attribution only. Executable and assets are unchanged. Local observer changes need affected validation before a new complete runtime report.

Executable SHA256: `e81fe61be19e28cb585f4c0f5808ebc96aa038d77a5f6667780e14f79f30f46c`.

Every file byte is counted exactly once. CODE 40,140 and DATA 114,540 contain these categories; do not add hunk totals again. BSS is 0. Loaded payload is 154,680 bytes and metadata 44,280.

| Exclusive category | Bytes |
| --- | ---: |
| audio envelopes | 128 |
| audio period table | 3,072 |
| audio scores | 2,208 |
| build version text | 14 |
| court bitplanes | 24,576 |
| cpu instructions | 11,118 |
| font | 1,024 |
| front court and title copper lists | 3,256 |
| hunk header table | 28 |
| hunk payload alignment padding | 2 |
| hunk record headers and ends | 24 |
| initial hardware sprites | 576 |
| mode banks | 3,072 |
| other initialized tables and scalars | 738 |
| paula square wave | 4 |
| pre rendered ui pages | 10,240 |
| relocation offsets | 9,120 |
| relocation record framing | 24 |
| replay packets | 1,110 |
| reserved back copper | 3,120 |
| reserved back sprites | 576 |
| reserved native stack | 4,096 |
| reserved state and work buffers | 704 |
| reserved ui overlay | 512 |
| scene animation table | 36 |
| scene pose table | 112 |
| scene sprite variants | 8,192 |
| score game banks | 21,504 |
| score patch pointer tables | 7,604 |
| score point banks | 14,336 |
| separate debug records | 0 |
| source alignment padding | 13 |
| status banks | 7,168 |
| symbol name padding | 1,383 |
| symbol names | 22,989 |
| symbol record framing | 10,712 |
| title bitplanes | 24,576 |
| ui text and line pointer tables | 993 |
| **Total** | **198,960** |

CPU instructions include operand extensions. CODE also embeds assets, tables and reserves. Symbols contain 22,989 name bytes, 1,383 padding and 10,712 framing bytes (1,337 symbols). Relocations contain 9,120 offset bytes and 24 framing bytes (2,280 offsets). No HUNK_DEBUG record is emitted. Reserves are file-backed dcb storage, not BSS. Final CODE padding is a 2-byte NOP (`4e71`); source alignment adds 13 bytes.

Identical embedded copies contribute 26,624 bytes beyond first copies. This is measured duplication, not validated savings; sharing requires separate correctness work. The JSON lists each group.

## Original comparison

The supplied cartridge is **8,192 bytes**, not 16,384; SHA256 `19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1`. It is not a build/metrics dependency. No original component allocation is inferred from its size.

Native storage uses expanded Amiga representations. Each title/court screen uses four 32-byte-wide planes over 192 rows (24,576 bytes). Score/status/mode banks retain prepared masks across values and planes. Four cached UI pages add 10,240 bytes alongside a 1,024-byte font and strings. The 64 scene images retain two prepared 64-byte Amiga sprite variants each (8,192 bytes), versus 2,048 bytes of monochrome pixels for those logical images. That 4:1 representation ratio does not establish an original ROM component allocation.

Original tile/pattern/color representations reconstruct displays; they do not serialize full Amiga bitplanes, working banks, AmigaOS metadata or our UI/audio/replay implementation. Historical generator source at `50ef76227a72e137c37efe29502cf60b1d4590d4` documents the conversions; no historical generator was executed for this measurement.

## Reproduction and limits

`python scripts/native_metrics.py --require-runtime` regenerates attribution in ignored `build/metrics/current.json` and its readable summary. Normal native builds also generate static attribution. Unknown gaps, overlaps, listing-byte mismatches or incbin mismatches fail generation. This snapshot binds executable, listing, manifest, tool lock and reader hashes.

Release-only symbol removal is now implemented: 198,960 → 163,876 bytes, saving 35,084 bytes (17.6%). Development symbols remain available. No deduplication, compression or gameplay change was performed. Current runtime generation correctly remains incomplete after observer edits. Static accounting does not recertify the historical runtime baseline.
