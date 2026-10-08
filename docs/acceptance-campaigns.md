# Acceptance campaigns

Use the campaign controller for native acceptance and focused native checks.
It serializes the shared build/test output directory, prints why each stable case
will run or reuse evidence, and keeps completed attempts when a session ends.
The catalog retains the existing 41 finite gate commands and adds nine actual
shared-core proof cases. A selected subset is reported as a subset pass; only
complete compatible mandatory coverage establishes acceptance.

```sh
# Read-only preflight; no build or emulator launch.
RUST_LOG=info python scripts/native_acceptance.py --plan
RUST_LOG=info python scripts/native_acceptance.py --plan --case dma-pal

# Run a focused case in a detached controller and monitor its final result.
RUST_LOG=info python scripts/native_acceptance.py --case dma-pal

# Start without waiting. Save the printed campaign ID.
RUST_LOG=info python scripts/native_acceptance.py --start --case dma-pal

# Reconnect: monitor live work, or resume a stopped campaign between cases.
RUST_LOG=info python scripts/native_acceptance.py --campaign CAMPAIGN_ID
RUST_LOG=info python scripts/native_acceptance.py --resume --campaign CAMPAIGN_ID

# Complete finite native/core gate, with compatible evidence reuse.
RUST_LOG=info python scripts/native_acceptance.py
```

Case IDs and exact commands are in `scripts/acceptance_cases.py` and
`scripts/campaign_core_evidence.py`. Repeat `--case` to select several. Resume
restores the saved selection automatically. Unknown IDs fail before execution.
An existing owner is reported as already running; reconnect observes that
controller rather than opening a second emulator connection. Interrupting the
foreground monitor leaves the detached controller running.

Receipts bind actual consumed executable bytes, observer/imported helpers,
compiled source and asset manifests, independent fixtures, tools, ROM and local
configuration hashes, complete arguments and effective environment. Defaults
and finite extent remain bound by observer source and explicit receipt checks,
including PAL/NTSC and required negative controls. Dependencies without a
verified compiled manifest use a conservative source/asset fallback. Commit
provenance is retained but a new documentation commit alone is not a rerun key.
An unrelated host test edit does not invalidate declared native observers.

Only compatible, complete passing evidence can be reused. Execution history is
shared across campaigns in the same resolved build directory, for each exact
case/dependency key. A failed or interrupted execution blocks older passes even
when a new campaign is started and the child left the canonical report untouched.
A successful reuse does not clear that block; a compatible successful execution
does. The latest canonical receipt also remains authoritative. Preflight explains
failure, interruption, missing provenance and changed artifacts.

Imported native receipts must explicitly record the compatible Python provider
environment, including `PYTHONPATH`; missing metadata is unverified, rather than
an assumed unset value. Execution through this controller binds fresh results to
the actual environment without rewriting their original report format. This
also supplies the missing uniform provenance for older startup and video-selector
observers. Historical unverified receipts require execution before reuse.

The resource collector's freshness includes the runtime/build receipts and
artifacts it consumes. Source equality alone cannot reuse a prior collector pass
after a consumed resource receipt becomes failed or incomplete.

Each campaign lives under ignored `build/acceptance/campaigns/ID/`. Its immutable
numbered attempts retain start/child identity, logs, exact receipt copies and
atomic completion files. Content-addressed copies preserve build evidence when
a later case overwrites canonical output. The final report checks compatible
coverage again, rather than treating exit codes alone as acceptance. Logs and
private evidence stay outside Git.

The single lock belongs to the resolved physical build directory, so symlinked
worktrees sharing outputs also share ownership. Linux host, boot ID and process
start time establish process identity; PID or a stale heartbeat alone cannot
authorize reclaim. Live or ambiguous descendants block another controller.
The reconnect caller's verified ancestor identities are excluded after checking
owned group membership; unrelated live permission denials still block reclaim.
Use this entry point consistently; a manually launched builder or observer does
not acquire the controller lock and must not overlap a campaign.

The detached controller owns the running Python observer and emulator socket
state. It survives loss of the foreground monitor where the executor permits
background processes. Destruction of the executor may kill all work. If storage
survives, reconnect validates completed cases and reruns an interrupted case from
its beginning after ownership is proved dead. This is resume **between tests**;
emulator memory and pending observer assertions are not restored mid-test.
Loss of the output storage loses that campaign's resume evidence.

Shared-core cases use pinned `machine68k` 0.4.1 and the same actual native and
standalone 68000 images. They never launch an Amiga emulator or assemble a new
product. Use the pinned Python environment that provides this module, retaining
the same `PYTHONPATH` on resume if it is required by that installation. Entropy
known answers and the emitted-byte comparison execute directly; recorded PAL,
NTSC and five scoring streams replay complete state and ordered output with
poisoned working state and full relocation. PAL also repeats every recorded
lifecycle poll and executes forbidden-access/initialization controls. Native
capture provenance must remain compatible before these CPU proofs can run;
stale capture inputs require explicit review or recapture, never an automatic
fresh-native claim.

Validation of this runner uses cheap temporary fake children for interruption,
failure, duplicate ownership, stale locks, cache invalidation and artifact
corruption. Existing native evidence is reused only where compatible. Changing
the runner does not justify repeating a completed full gameplay campaign.

The first integration preflight found that retained PAL/NTSC core captures name
an older `run_demo_match_tests.py` dependency. Their original successful core
results remain recorded in PR34; the new stricter adapter rejects their reuse
until that provenance difference is resolved. This draft does not claim a fresh
complete campaign or hide that blocker. History/seek implementation remains a
separate reviewed increment.
