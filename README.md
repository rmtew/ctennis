# Baseline Rally for Amiga

The maintained enhanced game runs on PAL A500/68000/OCS with512KB chip RAM and
no expansion. It includes native controls, gameplay/scoring, graphics/audio,
menu/help/pause and a complete native attract recording with takeover. The old
comparison build and original-platform tooling are retired; Git history retains
tracked rollback. CT12 gives the native game its Baseline Rally title, Blue/Red player identity
and expanded gameplay labels. CT13 adds selected Battle Hymn chiptune and a full-match winner celebration;
Classic sprites preserve logical A/B ownership with human/robot roles. Recording extensions remain later scope. See [CT13](docs/ct13/README.md).

This private repository includes the approved retained Amiga-native assets.
They remain Sega-derived; retention/conversion grants no new ownership or public
redistribution permission. See [asset provenance](assets/native/README.md).
Cartridge/source captures are unnecessary for builds or tests. Kickstart is an
external emulator-test input only and is never packaged.

Install the exact tools declared in [tools.lock.json](tools.lock.json):

- Python3.12.14.
- Validated vasm1.9d executable at `.tools/vasm/vasmm68k_mot.exe`, with the locked
  SHA256. Use the existing validated native tool cache or reproduce its build;
  do not substitute an unpinned assembler.
- `python -m pip install --target .tools/python amitools==0.8.1` for ADF packaging.
- Copperline1.0.0-rc.1 for target tests, plus Pillow12.3.0 for raster checks.
  `python -m pip install Pillow==12.3.0` installs the pinned image reader.

Build and package directly from a fresh checkout:

```sh
RUST_LOG=info python scripts/build_native_game.py
RUST_LOG=info python scripts/build_native_adf.py --self-test
```

Outputs remain ignored/private under `build/amiga/interfaces/enhanced/`.
The disk label, executable and startup command are `baseline-rally`; the package
is `baseline-rally.adf`. The disk never contains Kickstart.
Asset validation rejects missing/corrupt/undeclared inputs. Only version text and
the committed native input recording's assembly table are generated at build time.
No cartridge extraction, source emulation or translation fallback exists.

Copy [config.example.ini](config.example.ini) to ignored `config.local.ini` and
configure legitimate Kickstart1.3 and the pinned Copperline executable for tests.
See [native acceptance](tests/README.md), [current risks](docs/ct11/risks.md) and
[CT11 cutover evidence](docs/ct11/README.md). The canonical native fixture remains
independent of replay; do not regenerate its expected hashes to fix a failure.

The title corner shows the detected PAL/NTSC standard, product Git hash, and
release version. `amiga/VERSION` is the single `major.minor` release number,
starting at `1.0`; increment it deliberately for releases, never for rebuilds.
The label keeps its existing grey and eight-pixel right inset, aligning from its
full text width. Overlong labels fail the build instead of clipping.
