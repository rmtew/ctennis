# Display timing and publication

## Startup standard

Before taking over the machine, the game reads Kickstart's
`ExecBase.VBlankFrequency` byte at offset `$212`. The field is available on
Kickstart 1.3; see [exec/execbase.i](https://d0.se/include/exec/execbase.i).
A value of 50 selects PAL; 60 selects NTSC. Other values return DOS
`RETURN_FAIL` (20) before takeover and leave timing state unchanged.

| Bound | PAL | NTSC |
| --- | ---: | ---: |
| Simulation interval, E-clock ticks | 11838 + 14906/65536 | 11947 + 13180/65536 |
| Shortest field, lines | 312 | 262 |
| Last line, zero-based | 311 | 261 |
| Last safe publication line | 307 | 257 |

The four-line end guard applies to fixed OCS A500 modes. Startup does not infer
field length from beam movement. A transient beam decrease can look like a field
wrap; the [WinUAE beam-read fix](https://github.com/tonioni/WinUAE/commit/5b2b253dcf27d24e6b183a06d2c4625d5fae0181)
illustrates why the OS standard is used instead.

## Simulation clock and UI construction

Both standards run at about 59.923 simulation updates per second. Display
frequency is separate. Copperline reports PAL-derived host seconds, so NTSC
clock checks use actual CCK and the NTSC E-clock frequency.

CIA-B timer A is the elapsed-time low word. Timer B counts its underflows.
Stable 32-bit reads preserve elapsed time across long UI updates. The simulation
epoch and fractional phase remain continuous.

Static menu and help pages are generated from authored text and committed fonts.
Native construction copies cached planes. It samples the clock and keyboard
between bounded copies. Dynamic selections use overlays. Only a completed
display can become ready for publication. UI construction has no deadline
exemption or observer epoch reset.

## Three-bank publication

The renderer maintains three court Copper, sprite and HUD banks. `front_copper`
names the front court bank. Court display uses its Copper list; title display
uses the shared `title_copper` list with court sprite DMA disabled.
`ready_copper` holds the latest completed scene. Front and ready banks are
immutable; `back_copper` is writable. The third bank is either ready or spare.

Rendering records the scene generation and title/court choice before publishing
readiness. A newer completed scene can replace the ready scene. The superseded
ready bank then becomes writable. The displayed bank is released only after a
safe display handover.

Title and court Copper lists request COPER at line 253. The level 3 handler
saves registers, acknowledges COPER and calls the guarded presenter. Main-loop
polling can call the same presenter. The beam/latch/strobe transaction masks
interrupts. Gameplay and bank preparation remain outside it.

The publication window starts at line 253, after the footer at 251 and sprite
terminators at 252. It closes four lines before the last line. Nine-bit beam
reads use high/low/high sampling; a changed high bit forces a retry.

At most one COPJMP strobe occurs per physical field. The presenter installs a
completed frozen generation even when the next update is active. If no scene is
ready, or the window is missed, it retains the front bank. It does not recycle
a displayed bank because the beam is distant from a changed region.

Each bank owns a 3,072-byte HUD strip set. Point planes 0/2/3 cover y48–63;
WIN plane 1 covers y72–119. Status composition repairs overlapping WIN rows.
Six point masks occupy 192 bytes; the WIN mask occupies 16 bytes. Startup builds
these masks and initializes all banks before the CIA clock starts. Per-bank
caches suppress unchanged field writes.

## Verification

The [native test guide](../tests/README.md) lists setup and commands.
`run_video_standard_tests.py` executes the actual selector for all 256 frequency
byte values. `run_startup_publication_tests.py` checks exact-release cold start
for PAL/NTSC with zero and 512 KB slow RAM. Clock tests check each standard's
bounds and callback deadlines in CCK.

`run_native_setup_tests.py --self-test` checks UI timing and scanout. Its lost-wrap
control must lose exactly 327,680 CCK and fail accounting. Delayed construction
must fail its raw deadline while the normal clock accounts for the full interval.
Both controls restore the ordinary executable.

DMA checks bind all eight sprite channels to the installed bank and generation.
They check pointer completion before header DMA, addresses, frozen bank bytes
and every fetched HUD word. CPU writes may touch only the building strip.
See [current limits](limits.md) before interpreting emulator results.
