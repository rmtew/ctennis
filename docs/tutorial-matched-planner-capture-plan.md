# Matched selected-planner capture proposal

This is a tooling proposal for the latency experiment after PR47. It does not
approve a planner change or claim a speedup. The ad4 runtime and existing PR47
observers remain untouched. `scripts/matched_planner_capture.py` accepts one
already owned native session; it cannot build or boot an emulator. The candidate
control-word ABI and conditional deferral cohort are still under review.

Use one candidate executable with the experiment disabled/enabled by a declared
word configured once after restoration and before measured input. A separate
actual CPU comparison must first qualify ad4 versus disabled candidate behavior.
Different executables or independently played input sequences are not a matched
native treatment comparison.

The controller may establish contact placement through physical controls before
saving the anchor. Save full machine state while paused at actual `main_loop`
with SP at `game_stack_top`, no private helper, keyboard ACK retired, D up, menu
closed, and controller/render/footer/producer work settled. The helper retains
complete canonical318, public history72, records/checkpoints, preview, seek and
tutorial owner regions and registers. The saved machine also owns CIA/keyboard,
CPU, beam and DMA state; a gameplay packet alone is not an anchor. Never inject
expected intermediate state. Cancellation and resume have separate physical
extents; neither belongs to the measured fresh-D window.

For each region, restore that same anchor for disabled baseline1, disabled
baseline2, then enabled. Each restore drops scheduled input; unsubscribe and
clear debugger hooks, create fresh observers and install identical hooks and
watches. Do not assume debugger state was serialized. Audit the one-time word
write against all512 KiB of chip RAM; no other byte may change. Prequeue exactly
one raw D press and release at identical absolute CCK positions before running.
`input.key.at_seconds` uses provider time CCK/3546895, including NTSC; physical
window limits use the region's physical clock. No adaptive key input, setup
writes, endpoint-driven stop, or runtime mutation is allowed in the measured
window. Pump events at most1 physical ms between drains; retain loss notices and
fail on loss. Baseline-to-baseline complete emulated observations must match
before the enabled pass is permitted.

The observer adapter must combine existing actual stack, callback, input ACK,
coherent publication/native sprite/bank detectors and full owner-state reads.
It must retain complete canonical/history isolation at callbacks, all owner
states/cursors, ordered output events, endpoint points/reasons, generation/epoch
cancellation, actual COPJMP timing and ACK latency. Match full states/events and
positions for the repeated baseline; hashes or launch counters alone do not
qualify replay. The helper rejects missing adapter extent, active final owners,
notification loss, absent native bank proof and resume in the measured window.

A fixed end CCK may intersect a native helper. The current helper fails closed
on an open owner. Before native execution, reviewers must either accept a
separately bounded completion tail after that fixed end (reported separately and
excluded from the measured-window latency) or define an equally rigorous finite
cutoff contract. Do not adapt the measured end to whichever endpoint finishes
first. Matching baseline replay is a prerequisite, not proof of every state-file
component or universal deterministic replay.

The execution controller still needs to supply the observer adapter, approved
control symbol/values, physical anchor setup and approved absolute input/window
extent. The harness does not select a deferral threshold or implement a physics
model. Native experiments must wait until accounting readers are idle and the
root explicitly grants the one-emulator/controller ownership.

Proposed catalog IDs are `matched-planner-pal` and `matched-planner-ntsc` under a
new targeted latency extent. Do not alter PR47's existing case IDs, validators,
receipts or captures. Register these IDs only after adapter/cutoff review and a
clean frozen build. Their validator should bind candidate executable/listing,
control declaration, pinned CPU/emulator/ROM, anchor and raw hashes; recheck the
baseline replay gate, identical schedule, full actual output correctness, fixed
extent, and conditional cohort. The output is a finite treatment observation,
not a whole-target gate or normative deadline safety pass.

Use a fresh `/tmp` artifact directory while workspace free space is13 MiB.
There is108 MiB free in `/tmp` at planning time; those are observations, not
storage guarantees. Begin with explicit aggregate caps of32 MiB compressed raw
and64 MiB uncompressed raw plus8 MiB anchor/receipt budget, fail closed and report
actual bytes. These caps may be insufficient at the prior stack-trace rate;
review measured size before requesting an explicit increase or second region.
Never overwrite or delete unique historical evidence. No screenshots or asset
uploads are needed. The controller must use `ReportRun` and retain failed raw
and anchor artifacts before any retry.
