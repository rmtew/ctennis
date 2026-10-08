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

The original capture called its entropy provider `galois16-b400-v1`, but its
MOVEQ instruction cleared the shift carry before the branch: it actually
returned zero and shifted the observer word to zero. The immutable input JSON,
manifest and 10,958 digests retain their original bytes and provenance.
`assets/interface/demo-entropy-compat.json` names this effective historical
policy `legacy-shift16-v1` and binds the exact recording checksum. Production
advances a corrected stream from the same seed during playback, then uses that
stream on logical takeover without reseeding. The 90-byte historical preimage
continues to include `ui_entropy_state`, an alias of the legacy observer word.
New recordings use the corrected `galois16-b400-v2` metadata and modern word;
they cannot replace these expected values to conceal a regression.
