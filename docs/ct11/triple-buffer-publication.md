# Three-bank publication

The renderer has three complete Copper, sprite and HUD banks. `front_copper`
is displayed. `ready_copper` is the latest completed scene. Both are immutable.
`back_copper` is writable. The third bank is either ready or spare.

When rendering finishes, it records the scene generation and title/court choice
before publishing readiness. A newer completed scene can replace the ready scene.
The superseded ready bank then becomes writable. The displayed bank is released
only after a safe display handover.

Both title and court Copper lists request COPER at line 253. The level 3 handler
saves working registers, acknowledges COPER and calls the guarded presenter.
Main-loop polling can call the same presenter. The whole beam/latch/strobe
transaction masks interrupts. Gameplay and bank preparation remain outside it.

The bottom publication window starts after the footer at line 251 and sprite
terminators at line 252. Startup selects conservative PAL/NTSC field bounds from
Kickstart; see [standard selection](field-measurement.md). The window closes four
lines before the last line. Full nine-bit beam reads use high/low/high sampling.
A changed high bit forces a retry.

At most one COPJMP strobe occurs per physical field. The presenter installs a
completed frozen generation even when the next update is active. If no scene is
ready, or the safe window is missed, it retains the front bank. It never recycles
a displayed bank merely because the beam is distant from a changed region.

Each bank owns a 3,072-byte HUD strip set. Point planes 0/2/3 cover y48..63;
WIN plane 1 covers y72..119. Status composition repairs the overlapping WIN rows.
Six point masks occupy 192 bytes; the WIN mask occupies 16 bytes. The native
startup constructs masks and initializes all three banks before the CIA clock
starts. Per-bank caches suppress unchanged field writes.

DMA tests bind all eight sprite channels to the installed bank and generation.
They check pointer completion before header DMA, image and terminator addresses,
whole frozen banks, and every fetched HUD word. CPU writes may touch only the
building strip. Tests cover PAL/NTSC phases, paused scenes, delayed completion,
and duplicate-publication controls. See [native tests](../../tests/README.md).

PAL uses 11838 + 14906/65536 E-clock ticks per simulation update. NTSC uses
11947 + 13180/65536. Both are about 59.923 updates per second. Display frequency
is a separate quantity. Copperline reports PAL-derived host seconds, so NTSC
clock tests use actual CCK and the documented NTSC E-clock frequency. This does
not establish audio pacing or physical-hardware behavior.
