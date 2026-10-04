# Native elapsed-time and UI checks

The native clock uses CIA-B timer A as the low word and timer B as the underflow
high word. Stable 32-bit reads preserve elapsed time across long UI updates.
The simulation epoch and fractional phase remain continuous.

Static menu and help pages are generated from authored text and committed fonts.
Native construction copies cached planes and samples the clock and physical
keyboard between bounded copies. Dynamic selections use the existing overlay.
Only a completed display can become ready for publication.

Run `RUST_LOG=info python scripts/run_native_setup_tests.py --self-test` for the
focused check. It covers menu, Help, Controls, Credits, repeated navigation,
idle, start, pause, return and restart. Every raw callback keeps its deadline.
There is no setup exemption or observer epoch reset.

The compiled lost-wrap control must lose exactly 327,680 CCK and fail accounting.
A separate delayed construction must fail the raw deadline while the 32-bit
clock still accounts for the full interval. Both controls restore the ordinary
executable. Actual scanout is checked against committed font and layout data.

CT11 exposed the old 16-bit timer-wrap loss and slow synchronous page drawing.
Those failed receipts and proposed phase exemptions remain historical evidence
in Git. The proposals were never adopted as acceptance rules. Current results
must come from receipts for the exact product under test.
