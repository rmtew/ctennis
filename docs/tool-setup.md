# Tool setup

Run build commands from the repository root. Use Python 3.12.14 and the versions
in [tools.lock.json](../tools.lock.json). Tools and local configuration stay
ignored. A fresh clone does not contain the tool cache or a Kickstart ROM.

## Linux x86_64 recovery

This vasm procedure was verified on Debian 13 x86_64 with
`gcc (Debian 14.2.0-19) 14.2.0`. A fresh source checkout produced the exact
executable SHA256 in `tools.lock.json`. Other compilers and operating systems
may produce different bytes. Keep the hash check.
The unmodified Makefile uses `-std=c90 -O2 -pedantic -Wno-long-long -DUNIX`,
generated output-format defines and `-lm`. Do not add stripping or custom flags.

Install Git, GNU Make and a C compiler through the host's normal package process.
Then build the pinned vasm source in the ignored tool directory:

```sh
set -eu
mkdir -p .tools
git init .tools/vasm-source
git -C .tools/vasm-source fetch --depth=1 https://github.com/Leffmann/vasm.git 685a87e5ed14285350ccdb6581c9771bc8df6c7d
git -C .tools/vasm-source checkout --detach FETCH_HEAD
make -C .tools/vasm-source CPU=m68k SYNTAX=mot
printf '%s  %s\n' \
  0332feebc562e06bf245c1d60bef3fd7598c464a4be8162429be5e3e3a061e39 \
  .tools/vasm-source/vasmm68k_mot | sha256sum --check
install -Dm755 .tools/vasm-source/vasmm68k_mot .tools/vasm/vasmm68k_mot.exe
```

The `.exe` suffix is the repository's fixed path. It does not require a Windows
binary on Linux. The verified output is a Linux ELF. If the hash differs,
stop and compare the build environment with the validated cache. The current build checks the executable bytes.

Install the Python packages with the pinned Python interpreter:

```sh
python -m pip install --target .tools/python amitools==0.8.1
python -m pip install Pillow==12.3.0
```

ADF packaging reads amitools from `.tools/python`. A global install alone does
not satisfy the packaging check. Host raster tests import Pillow normally.

## Copperline and test configuration

Use the official Copperline 1.0.0-rc.1 x86_64
[AppImage](https://github.com/CopperlineHQ/Copperline/releases/download/v1.0.0-rc.1/Copperline-1.0.0-rc.1-x86_64.AppImage). Its archive SHA256 is:

`e69e732fc027d35f74874ea6720cc39f2f194006997d7000dc94b870ae989ce5`

The extracted Copperline ELF SHA256 is:

`26d655f07484412d00ad20eb5f0b363498eccb83d2261526c0cbb21ad8c723e8`

The source tag `v1.0.0-rc.1` resolves to
`e65a9584ccd0c86e678661ed5d2c18622da63fd4`. Fresh extraction, ELF hash and
`--version` checks verified the published package. This does not establish
reproducible compilation of Copperline from source.

Enable portable mode to keep `--run` staging in writable tool storage. Otherwise
it can fail when home/Documents is read-only. Put an empty `portable.txt` beside
the extracted ELF. For an extraction under `.tools/copperline`, run:

```sh
touch .tools/copperline/squashfs-root/usr/bin/portable.txt
```

Use AppImage extraction if FUSE is unavailable. The selected archive supports
`--appimage-extract`; run it inside the intended `.tools/copperline` directory.
Verify the archive hash before executing it and the ELF hash after extraction.
The full runtime library installation and launcher setup are not specified here.
Use the validated extracted tool environment; do not assume the ELF runs without
its bundled libraries or substitute a launcher that bypasses evidence checks.

Copy `config.example.ini` to `config.local.ini`. Set `tools.copperline` to the
validated executable or launcher. Set `inputs.amiga_rom` to the legitimate
external Kickstart 1.3 file. Keep the ROM outside Git. Run the configured
Copperline with `--version`; it must report 1.0.0-rc.1.

Use `RUST_LOG=info` for native commands. The evidence checker records this value
and requires the native target log. See [test instructions](../tests/README.md).
No Windows or macOS provisioning recipe is verified here.
