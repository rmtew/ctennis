# Direct HUD validation

The finite native gate passed at `21b4be65a151258cbc43bdd30beec16e64fe8ebe` with the head unchanged throughout all 37 commands. Command: `RUST_LOG=info python scripts/native_acceptance.py`. Completed: 2026-10-03T10:58:35.944509+00:00.

Gate receipt SHA256: `b317d442f234e4508955fe846e05d8cd3bcfc37f274f6d4b4a13c36bf317c811`. The private raw receipt is `build/acceptance/report.json`; its product hashes are retained in [direct-hud-comparison.json](direct-hud-comparison.json).

Coverage includes host/assets/package, cold menu, physical input, PAL/NTSC clock and DMA, scoreboard and compiled fault controls, scoring/status/audio, all celebration orientations, the independently frozen 10,958-tick demo, physical takeover, repeated attract cycles, ordinary one/two-player matches, early release/repress and audio, setup/raw deadlines and resource completion. Existing deadline and native publication assertions remain unchanged. Pixel expectations and the frozen native recording were not regenerated.

| Supporting check | Private receipt | SHA256 |
| --- | --- | --- |
| PAL DMA | `build/tests/native-sprite-dma-pal-report.json` | `f445c0bcf38d93be4095a2b30a7f1de446703f13aa0c4cecd99dc36413d32ca0` |
| NTSC DMA | `build/tests/native-sprite-dma-ntsc-report.json` | `1a2f6b9da4c2093c2703e6c93e1839de91d6b6ca7fbc6b639ded015ee1182780` |
| Scoreboard | `build/tests/native-scoreboard/report.json` | `b9ba964e780c7a26c4b90f4d05e7b14dd1b5403ff81fd04b39cbe514cbe89537` |
| Startup | `build/tests/native-square-startup/report.json` | `2744f8edc19d62aeb22a74fbec062853b3786424f618b6403cf7bca60c1c4e7f` |
| Frozen demo | `build/tests/demo-full-repeat/report.json` | `e9e651c34ce8b03ccb6704b9f391fbaa15a5e314022c8cf9b9f0cd95fbf5a25c` |

The startup check was refreshed separately after the gate; it verifies generated tiles/strips and rejects the wrong-advantage-position control. Supplemental common old/new HUD-cost and ISR/handover probes are distinct from accepted baseline workloads and from full-gate acceptance; their exact scope, corrected initial observer attempts and baseline misses are documented in the comparison. Raw captures, ROMs and executables remain outside Git.

Independent code review approved head `21b4be65a151258cbc43bdd30beec16e64fe8ebe`, as relayed by the coordinator. Later additions are measurement/documentation only; the development executable remains byte-identical. Final result review and merge approval are pending. No Shot Doctor implementation is included.
