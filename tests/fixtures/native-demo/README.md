# Canonical native demo trajectory

`trajectory.sha256` contains 10,958 ordered SHA256 digests. Each line contains
one lowercase digest. The file is 712,270 bytes.

The file is a lossless export of the original native input recording receipt.
Every entry was checked against the preserved capture. Replay did not generate
these expected values. The file contains hashes only and does not ship in the game.

`manifest.json` binds the capture receipt, metadata, executable, input recording,
target and seed. Each digest covers 90 bytes of native state. The checker verifies
the text checksum and the normalized digest-stream checksum. It then checks every
native input boundary against the frozen trajectory.

Install the pinned tools and build from the versioned native assets. Run:

```sh
RUST_LOG=info python scripts/run_demo_match_tests.py
RUST_LOG=info python scripts/run_demo_match_tests.py --takeover
```

A fresh checkout does not need `build/tests/demo-full-recording/digests.json`.
Keep the input table bound to the expected hashes. Do not regenerate expected
values from replay to fix a failure. A new recording needs an independent native
physical-input capture and a review of its provenance.
