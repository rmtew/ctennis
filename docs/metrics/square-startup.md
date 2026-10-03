# Square LED and HUD startup observation

All six 32-byte generated LED tiles and the 16-byte retained-font WIN mask match independent expectations; all three 3,072-byte HUD strips match their court source rows before field stamping. The compiled wrong advantage-position control is rejected. Construction takes **13.033371ms** of emulated elapsed time before the simulation timer starts, including active OS display DMA. This bounded ordinary-startup observation is not an isolated cold-ADF constructor timing.

Exact executable, contract, target/tools, measurement inputs and receipt hashes are in [square-startup.json](square-startup.json). Recheck constructor/product changes with `RUST_LOG=info python scripts/run_native_square_startup.py --self-test`. The [current resource report](current.md) measures the broader cold-loading path.
