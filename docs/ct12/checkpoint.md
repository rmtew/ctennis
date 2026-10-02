# CT12 identity/readability checkpoint

Base: `43e1118d878453809a68c257deef20a937697e15` (merged CT11 cleanup and
focused native UI timing fix). Branch: `ct12/baseline-rally`.
No master merge or repository rename is authorized.

## Finite implementation plan

1. Capture baseline native menu/help/credits, both logical players at both ends,
   status visible/expired and longest mode fields using pinned tools.
2. Replace title with Baseline Rally, remove the Sega logo from the game and
   consistently name executable, disk label, startup and package baseline-rally.
   Retain concise, honest Sega-derived asset provenance without ownership or
   public redistribution claims.
3. Audit shared palette indices against actual pixels; change the actual Pink
   player's poses/sprites and logical-player labels/indicators/scores/tally/prompts
   to Red while preserving unrelated court/background art and Blue/Red identity
   across end exchange.
4. Expand FLT to FAULT, DBF to DOUBLE FAULT, 1PLAY to 1 PLAYER and 2PLAY to
   2 PLAYERS. Widen/reposition native fields and verify clearing/restoration,
   longest text, score/net/tally separation and exact bank/Copper/DMA windows.
   Preserve IN/OUT/NET/ACE/DEMO and the graphical advantage indicator.
5. Review intentional asset/palette/raster expectations against before/after
   actual scanout; preserve canonical 10958 gameplay replay/entropy/input controls.
   Run affected host/native checks, deterministic build/package, status expiry and
   pointer fault controls, both ends/players, menu/help/pause/takeover/cold ADF,
   strict UI/gameplay cadence and memory after UI cache. Reuse only explicitly
   unchanged evidence, with its subject/limits recorded.
6. Record commands, hashes, screenshots and limits; commit private native assets
   only and prepare a draft PR. Never commit ROM, executable, ADF or raw runtime
   reports. Parent independently reviews any merge.

## Initial checkpoint (2026-10-02)

Fresh unchanged-baseline checks:

- `python -m unittest discover -s tests/unit -q`: PASS, 20 tests.
- `python scripts/native_assets.py`: PASS, 92 versioned native inputs.
- `python scripts/build_native_game.py`: FAILED before assembly because
  `.tools/vasm/vasmm68k_mot.exe` is absent.

Python is the locked 3.12.14. No `.tools` directory or `config.local.ini` is
present; neither vasm nor Copperline is on PATH. Required vasm 1.9d SHA256 is
`0332feebc562e06bf245c1d60bef3fd7598c464a4be8162429be5e3e3a061e39`;
Copperline is locked to 1.0.0-rc.1, source commit e65a958. A separately supplied
Kickstart file exists externally but has not been configured or validated here.
No cartridge was opened or used.

Product changes, intentional expectation updates, screenshots, deterministic
package and native target gates are not performed. CT11 and timing code remain
intact. This checkpoint is not CT12 acceptance. Provision the validated tool
cache and native test configuration to continue at step 1.

## Setup recovery and baseline completion

The saved checkout genuinely lacked its prior tool cache. Inventory searched
/workspace, /tmp, /opt, /home, /usr/local, /var/cache, /mnt and /media for vasm,
Copperline and native configuration. /root, /opt/containerd, the private daemon
and some /var/cache subdirectories were unreadable. No permission escalation or
ROM transfer was used; external supplied Kickstart already existed.

Recovered vasm from https://github.com/Leffmann/vasm at parent-supplied commit
685a87e5ed14285350ccdb6581c9771bc8df6c7d. `make CPU=m68k SYNTAX=mot` reproduced
the exact locked SHA256, then copied it to the locked native assembler path.
Downloaded the official Copperline 1.0.0-rc.1 Linux x86_64 AppImage (SHA256
e69e732fc027d35f74874ea6720cc39f2f194006997d7000dc94b870ae989ce5), extracted it
under ignored .tools and used its documented portable.txt mode to put --run
staging in writable .tools rather than read-only home/Documents. No emulator
code or machine settings were modified. Its --version reports 1.0.0-rc.1;
official source checked out at e65a958. Pinned Pillow was already installed;
`python -m pip install --target .tools/python amitools==0.8.1` succeeded.

Unchanged-base build and deterministic package passed. Cold ADF menu passed69
checks and screenshots; native physical inputs passed11; status-5 passed102.
The initial finite gate stopped at native-inputs on Copperline's read-only home
staging error; portable mode fixed it and the affected input check passed fresh.
That incomplete baseline gate is not a full baseline acceptance claim.
