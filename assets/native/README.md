# Retained native inputs

This directory contains the approved native assets for private rmtew/ctennis.
Converted court, racket, ball, shadow, pose, font and effect inputs remain
Sega-derived. Conversion grants no ownership or public redistribution rights.
The repository contains no cartridge, Kickstart, executable, ADF or raw capture.

`manifest.json` records each input's size and SHA256. It also retains imported
hashes and provenance. Builders reject missing, corrupt or undeclared inputs.
They do not extract or recover assets from original media. Preserve these
versioned bytes when the original authoring inputs are unavailable.

The title, labels, palette and score panels include approved native edits.
Classic human and robot bodies use the retained ImageGen source, fitted to
original pose bounds and seams. Rackets and geometry keep their Sega-derived
provenance. See [artwork contracts](../../docs/sprites/README.md).

The independently arranged [Battle Hymn chorus](audio/battle-hymn/README.md)
uses authored accompaniment, a separate period table and a four-byte square
wave. Other effect data are retained. Font-Mac has separate
[provenance and extraction rules](../interface/font-mac/README.md).

`assets/interface/small-font-additions.json` preserves all 47 authored additions
to the retained small font. Its rows match `title/font.bin`. The independent
native input recording is in `assets/interface/demo-inputs.json`.

Builds generate version text and the recording's assembly table under ignored
`build/native`. Generated outputs do not replace the versioned source assets.
Keep the repository and its retained assets private.
