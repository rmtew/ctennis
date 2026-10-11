# Independent ball-query proof review

The report and three proof programs were independently reviewed against product
commit `5623420afbbcb347b823c09b0f8e94d601516e34`. Review outcome: **approved**
for a separate proof branch, with no mathematical or harness blocker.

Reviewed files:

| File | SHA256 at review |
|---|---|
| `docs/ball-query-math-proof.md` | `c07a6dc7c9f766c476101b203b59a6255b6864367124331a6f47d8185de4a974` |
| `scripts/prove_ball_queries.py` | `ac8e059decbf2f03923d0895dad6a2ca0c153190a13bc2d2a06122f1c6eb5705` |
| `scripts/prove_ball_query_forms.py` | `c36eb45c16b1518fe1c892f2c9aee28414b4edd41cf0f2e46590e2cfa13f6a34` |
| `scripts/prove_ball_query_seed.py` | `639474f11c37c96d59dfdc0bba2e957461c25668b949d95539fae858d3875b4f` |

After review, only the report's administrative status changed from local draft
to reviewed proof branch, and this receipt was added. No equations, guard claims,
counts, evidence hashes or proof programs changed.

The reviewer inspected the emitted routines, mathematical derivations, harness
and completed local receipts. Receipt hashes and their source, input and tool
bindings matched. The reviewer independently reran both compact-form and
rolling-seed proof programs, intercepting their output writes to preserve the
original completed receipt bytes:

- Compact forms: all 65,536 word products and all 65,536 byte factor pairs passed.
  The landing checks reproduced 23,309 accepted flights, 615,969 uninterrupted
  emitted ball calls, maximum six candidates, and the same PAL/NTSC guard audits.
- Rolling-seed form: all 65,536 word products, all 65,536 factor pairs and
  5,521,679 ordinary signed landing triples passed.

Compact-form results matched the completed receipt except for host duration.
The earlier 16,777,216-input general division proof was inspected and its
completed bindings verified; that full primitive run was not repeated during
independent review.

The six-candidate claim covers only the explicitly guarded uninterrupted fixed
flight. Wrap, clamp, bounds and special-net preemption are conservatively
excluded; no intervening player contact remains an explicit domain assumption.
The report includes guard rejection counts, finite reachable coverage and
fallback rules, and makes no full-match tick-skipping or native timing claim.
Existing incomplete resource coverage does not block this mathematical proof.
Production implementation, caller-visible effects, native code bytes/cycles and
whole-match acceleration remain separate work requiring their own review.
