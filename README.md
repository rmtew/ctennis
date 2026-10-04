# Baseline Rally for Amiga

Baseline Rally is a native tennis game for the Amiga A500, 68000 and OCS.
It runs with 512 KB chip RAM and no expansion. Startup selects PAL or NTSC.
The game includes menus, help, pause, scoring, sound, an attract demo with
player takeover, and a match celebration. Reboot after play is intentional.

This private repository contains Sega-derived graphics and audio. Retention and
conversion grant no new ownership or public redistribution rights. See
[asset provenance](assets/native/README.md). Builds do not need a cartridge or
source captures. Emulator tests need a legitimate external Kickstart 1.3 ROM.
The ROM is never packaged.

## Tools

Use the exact versions in [tools.lock.json](tools.lock.json):

- Python 3.12.14.
- vasm 1.9d at `.tools/vasm/vasmm68k_mot.exe`, with the locked SHA256.
  Restore the validated tool cache or follow the Linux recovery procedure in
  [tool setup](docs/tool-setup.md). Verify the executable hash before use.
- amitools 0.8.1 for ADF packaging:
  `python -m pip install --target .tools/python amitools==0.8.1`.
- Copperline 1.0.0-rc.1 and Pillow 12.3.0 for emulator and raster tests.
  Install Pillow with `python -m pip install Pillow==12.3.0`.

The repository does not supply vasm, Copperline or Kickstart. A fresh checkout
needs these external tools before the corresponding commands can run. The setup
guide gives the verified Debian vasm recipe, preserves emulator recovery facts
and states the remaining platform limits.

## Build and test

Run from the repository root:

```sh
RUST_LOG=info python scripts/build_native_game.py
RUST_LOG=info python scripts/build_native_adf.py --self-test
python -m unittest discover -s tests/unit -q
python scripts/native_assets.py
```

Outputs stay under ignored `build/amiga/interfaces/enhanced/`. The executable,
disk label and startup command are `baseline-rally`. The disk image is
`baseline-rally.adf`. Missing, corrupt or undeclared native inputs fail the build.
Builds generate version text, UI caches and the native input recording table.
They do not extract cartridge assets or recover files from archives.

Copy [config.example.ini](config.example.ini) to ignored `config.local.ini`.
Set the paths to the pinned Copperline executable and legitimate Kickstart ROM.
See [native tests](tests/README.md) for the finite acceptance command and focused
checks. See [current limits](docs/ct11/risks.md) before interpreting test results.
Do not regenerate the independent demo fixture to fix a test failure.

The title corner shows the selected video standard, product Git hash and release
version. `amiga/VERSION` is the single `major.minor` release number. Change it
only for a release. The label uses grey text and an eight-pixel right inset.
The build rejects labels that do not fit. Documentation outside product-input paths does not change the label.
Documentation inside `assets/` is a product input and can change it.

See [game behavior](docs/ct13/README.md), [publication design](docs/ct11/triple-buffer-publication.md),
[resource reporting](docs/metrics/README.md) and [deferred work](TODO.md).

See [the repository audit](docs/repository-audit.md) for all file decisions and
the repeatable inventory coverage check.
