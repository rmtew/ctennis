# Canonical native demo trajectory

`trajectory.sha256` contains10958 ordered lowercase SHA256 digests, one per line
(712270bytes). It is a lossless text export of the original native input recorder's
receipt, not expectations produced by replay. Every entry was checked against
the preserved capture. It contains only hashes, no world snapshots, ROMs, audio,
graphics or proprietary original-platform references; nothing here ships in game.

`manifest.json` pins the original capture receipt/metadata/executable hashes,
input recording, target, seed and90-byte native digest preimage. The checker
verifies text and normalized digest-stream checksums before comparing every
native input boundary. This repository fixture replaces the private-build receipt
dependency mentioned in earlier interface documentation.

With normal private native build prerequisites already prepared, run:

```sh
RUST_LOG=info python scripts/run_demo_match_tests.py
RUST_LOG=info python scripts/run_demo_match_tests.py --takeover
```

A fresh checkout does not need `build/tests/demo-full-recording/digests.json`.
The input table and expected hashes must remain bound; do not regenerate expected
values from replay to fix a failure. New recordings require independent native
physical-input capture and review of the corresponding provenance.
