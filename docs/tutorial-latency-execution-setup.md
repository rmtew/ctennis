# Latency investigation execution prerequisites

Supported setup completed on 2026-10-10 in `/workspace/ctennis`, following
[tool setup](tool-setup.md) and the hash-pinned
[CPU proof requirements](../tests/match-core-proof-requirements.txt).
This is tool readiness, not native runtime validation. No game build, emulator
session, CPU proof or native campaign was started.

| Prerequisite | Verification |
|---|---|
| Python 3.12.14 | Current interpreter matches tools.lock.json |
| vasm 1.9d | Built source685a87e with Debian gcc14.2.0-19; executable SHA256 matches locked0332feeb…61e39 |
| Copperline 1.0.0-rc.1 | Official AppImage matches e69e732f…89ce5; extracted lowercase usr/bin/copperline matches26d655f0…23e8; --version passes |
| Copperline libraries | ldd resolves all dependencies, including bundled libudev; portable.txt created beside executable |
| Pillow 12.3.0 | Existing installed package matches tools.lock.json |
| amitools 0.8.1 | Installed at ignored .tools/python; metadata version checked |
| machine68k 0.4.1 | Source installed at ignored .tools/proof-python with --require-hashes --no-binary=machine68k; import/version pass |
| External Kickstart attachment | 524,288 bytes; exact SHA256 matches both retained native receipts |
| Local emulator configuration | Ignored config.local.ini points directly to verified Copperline ELF and supplied external ROM; repository emulator_config passes |

The verified assembler is `.tools/vasm/vasmm68k_mot.exe`. Direct Copperline
execution works without a custom launcher or additional LD_LIBRARY_PATH.
Use `RUST_LOG=info` for eventual native commands. CPU scripts can use the
documented `PYTHONPATH=.tools/proof-python` with the pinned current interpreter;
record the actual environment in their receipts. Native capture scripts retain
their separately declared environment. No old Python path identity is inferred
from a current import/version check.

The private ignored `.tools/tutorial-latency-setup-receipt.json` binds installed
executables, archive, bundled library, proof requirements, compiled CPU module,
package metadata, local configuration, external ROM and setup logs. Logs remain
under `/tmp/ctennis-*-setup.log` (plus assembler/extraction logs). Neither tools
nor ROM bytes are committed or uploaded. An initial executable hash command
used uppercase Copperline instead of the actual lowercase filename and failed
before execution; the corrected command verifies the documented ELF hash.

Preserved baseline development executable, listing, compile manifest, complete
machine anchor and original raw traces are still absent here. The current
emulator can answer --version; no launch/debugger/state-save capability has been
tested. Do not equate setup with readiness of the incomplete matched observer
adapter or with transfer of old campaign custody. Any later matched experiment
must qualify its baseline, adapter, absolute input schedule, full-machine replay,
fixed cutoff/tail and physical publication extent before treatment.

Read-only preflight
`RUST_LOG=info PYTHONPATH=.tools/proof-python python scripts/native_acceptance.py --plan --case coherent-contact-pal --case coherent-contact-ntsc`
exits0 and resolves both case commands and dependency closures. Both report
missing local latest receipts, so neither is reusable from this container.
The printed plan identity is not a started campaign; no case was executed.
The closed original campaign and its preserved receipts remain unchanged.

Independent source review additionally identifies dependency-qualified unchanged
presentation qualification and safely larger useful prefixes as hypotheses to
interpret the requested reductions. Public prefixes already amortize validation,
register saves and72-byte history retirement across budget1..4. Each actual
envelope must preserve ordered shared-body checks, cursor progress and sample
append boundaries. Counts alone cannot suppress qualification: endpoint-ready,
launch, outcomes, variant, generation, placement and animation state also matter.
No measured saving or correction decision follows from this source inspection.

The coordinating parent has requested all six compact read-only reductions in
[next analysis](tutorial-latency-next-analysis.md). Runtime remains unchanged
pending those results. All existing appearance/resource/deadline/physical-resume/
cold-release/full-release holds remain; no merge or release is authorized.
