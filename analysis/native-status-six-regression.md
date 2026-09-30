# Two-player status 6 lifecycle

`p1-status-6-lifecycle` extends the actual native capture to the independently
retained two-player parent and both physical Amiga joystick ports. It initializes
once from source callback20921, then carries state through the point event,
status appearance20925 and expiry20956. It never supplies expected input-reader
returns, pending messages, selectors or intermediate game states.

All37 consecutive status requests and three completed original/native status
raster crops match. Both source readers return16 throughout this interval; that
is validated against the original recording, not assumed from the input recipe.
The native run sets both ports to joystick and holds both physical fire buttons.
The source parent, phase, actual inputs and display generations are retained in
hashed evidence. The completed raster at target20958 can represent generation
20957; the comparison follows that actual visible generation.

The case is **known red** for state parity. Consecutive native post-tail snapshots
find the first divergence at callback20922: normalized button/control byteC056
is17 in the original and1 in the native run. The original combines both held
button groups; the live native `sample_second_input_group` still returns zero.
Every one of the37 observed callbacks has this same sole meaningful RAM
difference. Matching status output does not establish correct two-player input
or whole-game parity. This is the existing P3 omission exposed in a later context,
not a new independent defect.

Both compiled renderer mutations are detected despite that earlier state failure:

- Retaining status text after expiry changes its requested selector at20956,
  from expected0 to actual6, and corrupts the cleared raster.
- Clearing one callback early changes its requested selector at20955,
  from expected6 to actual0. Its later cleared raster still matches.

Mutation detection compares actual native selections against the normal native
capture, while still checking against the original expected value. The ordinary
first-difference report continues to show the earlier input failure. Separate
`mutation_first_difference` records identify the newly introduced defect; an
existing known red cannot hide a broken negative control.

Baseline acceptance is stricter than matching the first failure alone: all37
post-tail snapshots must contain exactly the declared C056 mismatch, and every
status request and raster check must still pass. A later pixel/state regression,
missing callback or partial change to the known failure is rejected. Both actual
compiled mutations must classify as `unexpected-red`, even though their first
overall difference remains the earlier known input failure.

An initial callback20923 start exposed a capture prerequisite: the first requested
blank screenshot could precede any completed native display generation. Moving
the source-derived start to20921 provides three native updates before that raster
target, preserving the same point/status interval. The original state is still
inactive before the point request. No expected display state is injected to fix
the prerequisite. Invalid missing-generation evidence is explicitly rejected.

Run `python scripts/run_status_tests.py --case p1-status-6-lifecycle --self-test`.
Its expected exit1 represents the exact product/input failure. The aggregate
baseline mode accepts only the registered signature; tool/capture errors and
changed signatures cannot be accepted as this known failure.

All six status messages now have local game-driven appearance/expiry comparisons:
status1 in the first-game prefix, statuses2/3/4/5 in the four one-player lifecycles,
and status6 here. Stop equivalent status-window expansion. This does not close
full P1, continuous transitions, ordinary unpaused input/timing, P2 audio or the
remaining F2/F4/F5 tests. Next protect game-driven point/mode transitions and the
remaining round/result/restart scenes, preserving known upstream failures.

Full aggregate baseline/self-test:88 cases,52 green,36 exact known red, no
unexplained/tool failures. After tightening the known-failure policy, reran this
case with both actual compiled mutants and reclassified all88 actual aggregate
reports with the current policy; classifications are unchanged. Capture,
executable, private-wrapper and screenshot hashes verified. Four remaining
requirement groups still prevent completion.
