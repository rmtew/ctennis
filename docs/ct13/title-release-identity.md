# Title release identity

No existing human release numbering was found; the old corner contained only the
product Git hash. `amiga/VERSION` now starts at1.0 and is deliberately incremented
for releases, not automatically on builds. The README documents this single source.
The existing product-hash rules already include all of `amiga`, so a version
change changes product identity. Evidence tracking also includes the version file.

The corner renders `PAL <hash> 1.0` or `NTSC <hash> 1.0` using the standard already
selected at startup. The existing Font-Mac, palette index6 (`$555`), native y180
and eight-pixel right inset remain. Its left edge is248 minus the complete text
width, so NTSC and multi-digit release versions align to the same right edge.
Builds reject malformed or overlong versions instead of clipping. Credits retain
the existing full BUILD identity, including the local-change marker when needed.

Two256-byte monochrome rows are generated; title rendering copies the selected
row into planes1/2 after the existing menu/figure cache. Other planes remain
blank in this row. There is no new mutable state or versioning framework.

## Focused validation

Product7379b1a, pinned vasm1.9d/Copperline1.0.0-rc.1 and external Kickstart1.3:

- 67 host tests passed. The title-cache test covers both standards, both player
  roles and all three selections using multi-digit version12.34, comparing the
  complete raster with the independent text/colour specification. An interim
  indentation error in this test was corrected before the passing run.
- Exact-release ADF cold boots:4/4 PAL/NTSC × zero/512KB slow RAM passed. Full title
  raster comparison includes the standard/hash/1.0 label; physical Start still
  produces the correct court and hardware/software Copper pointer.
- Real Copperline screenshots were inspected for PAL and NTSC at
  `build/tests/startup-publication/{pal,ntsc}-slow0/title.png`. Both show the
  actual standard,7379b1a and1.0 with the same right edge and muted grey.
- Strict native cadence:239 completed callbacks on each standard passed.
- `git diff --check` passed. No WinUAE/hardware execution or full-game gate claim.

Loaded code43,836 (+44), chip data112,700 (+512), BSS9,424 (unchanged), total165,960.
`native_metrics.py --require-runtime --record` exits1 and honestly records
incomplete full-game runtime resource coverage; old runtime measurements are not
claimed as fresh or reused. Only the focused results above are claimed.

Private artifact SHA256s:

- ADF: `de72b659b14335c8f6753b696cddf4b8e1e8b8429fafca857cf62147509c0f71`.
- release: `addc43cb9c7ade0e7eb6d4ac88618cfa7310f43eb1ff4ac08c56491d9026d800`.
- PAL screenshot: `8cd4cc7bd3c5e1c348993e3b1c61eeb6ed2fed738bd61a7eeebdf5390af2c6a5`.
- NTSC screenshot: `1ae62864530d30523464d39b3914c7451865f9c623f14055ab583e61ea64ec20`.
- cold-start receipt: `3549dcb9f4363f0946a342f2dbcdd54d177e0dbdc0bab28238830b5a0674be38`.
- cadence receipt: `6b4af48d35192fc6ad0c6e82525f287746ff450a19660858574a1999c79239b3`.

Independent review precedes merge. No Library replacement is included.
