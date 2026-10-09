# Incoming reconstruction cost and next proof

Scheduling authority: [the scheduling specification](tutorial-deadline-scheduling-design.md) supersedes future scheduling/admission recommendations here. Measurements and implementation facts below remain historical evidence for their named products.

Analysis only of reviewed PR41 head `1e25a197fdf329f17d0d302a2c240e0d058bac91`. No runtime edits, reserve changes, new native captures or release approval. The recommendation is to prove and calibrate the existing four-operation incoming worker before adding a trajectory cache or direct-contact path.

## Evidence and accounting

Reused complete fresh PAL/NTSC incoming receipts from campaign `da9d751502054394adaf4ac0064f125e`, product source `a936ebac16c977cfc6c39a4426de1cbfdf62170e`, development SHA256 `4821dfcb1df4b8febfa82a80d23cc787241f45bbd3efc2f513b4dc9d2925a518`. These are independent live-entropy trials, not paired comparisons or universal bounds. [Existing results](tutorial-incoming-flight-results.md) describe their checked extent and remaining release gates.

Reproduce offline with `python docs/analysis/incoming-costs.py --output /tmp/incoming-costs.json`. The tool validates every dependency in each retained receipt and the current executable. Raw captures remain private. No emulator or core runner is invoked.

| Standard | Receipt SHA256 | Capture SHA256 |
|---|---|---|
| PAL | `a236e403a9966f3f1302254b51f45de887e733a9e8fb5b7b8aba78e31579acea` | `9668371d5d7b3a797dd198d4b96126430acd7232637933738b9e34ee6b5256f7` |
| NTSC | `d7e891a261ca775137053a2a5dcecf4402627dfde586626dad8dedcd70fbed9b` | `ae5fc0df01c23acd7af6f3c340f9c755ab45087fecd02f3a9048e2d7c7345e61` |

The following half-open bus-span categories are clipped at the actual human contact hook, pairwise disjoint and sum exactly to elapsed time. Literal stack calls identify original execution; callback ownership and subtraction identify the remaining categories. IRQ/contention are included: these are not CPU-only instruction costs. Nested callees must not be added to their parents. Unassigned time remains unassigned.

| Request → contact category | PAL CCK | NTSC CCK |
|---|---:|---:|
| Actual original dispatcher (including tail scene work) | 331,005 | 334,894 |
| Other original input/poll/result envelopes | 21,437 | 21,554 |
| Public worker residual outside original calls | 214,447 | 226,527 |
| Callback admission checks | 45,073 | 43,802 |
| Observed named presentation calls | 27,705 | 175 |
| Native input and tutorial controls | 330,555 | 338,014 |
| Progress metadata | 63,759 | 63,041 |
| Other callback time, unassigned | 43,007 | 50,470 |
| Observed polling outside callbacks | 995,321 | 1,021,254 |
| Other outside-callback time, unassigned | 133,894 | 137,296 |
| **Total** | **2,206,203** | **2,237,027** |

Request→hook is 0.622010 s PAL / 0.624947 s NTSC. Original dispatch consumes about 15%; all public workers including original calls consume about 25.7% / 26.1%. Observed outside-callback polling consumes 995,321 / 1,021,254 CCK (about 281 / 285 ms), but this is not an idle-time measurement or a claim that all those cycles are available to preview. Named calls do not capture BRA-tail entries independently; absent `game_scene_finish_tick` spans mean unavailable attribution, not zero cost. The dispatcher already includes that tail.

There are 213 original envelope entries before contact: 52 dispatches (48 named plus four indirect active ticks) and 161 other envelopes, including two PRIME pad samples. The 19 indirect entries are classified from their actual nested calls in these playing captures, not as a general decoder for every lifecycle. All 107 entered workers execute two operations; the last worker crosses contact and includes an outgoing ball operation, hence 214 completed operation slots versus 213 pre-hook entries. These counts do not justify removing original operations.

The other envelopes occupy 75.6% of entered logical slots but consume only 21,437 / 21,554 CCK (about 6 ms). Eliminating their CPU work while charging the same slots cannot explain a large speedup. Removing their scheduling charge would change the pacing contract and needs separate proof. Nested `game_ratio32` is only 13,662 / 13,728 CCK (about 3.85 ms); ballistic arithmetic alone is a weak first target.

## Admission and publication

| Retained incoming observation | PAL | NTSC |
|---|---:|---:|
| Intersecting callback opportunities | 38 | 38 |
| Callbacks with 0 / 1 / 3 / 4 workers | 2 / 1 / 34 / 1 | 2 / 1 / 34 / 1 |
| Dense admission checks | 142 | 141 |
| Admitted two-operation workers | 107 | 107 |
| Refused two-operation workers | 35 | 34 |
| Checks meeting four-operation reserve | 0 | 0 |
| Admitted remaining E-ticks: min / median / max | 7,164 / 9,183 / 9,943 | 7,308 / 9,274 / 9,995 |
| Refused remaining E-ticks: min / median / max | 4,371 / 6,489 / 6,899 | 5,358 / 6,629.5 / 6,948 |

These decisions are reconstructed from literal coherent CIA counter reads and their captured timer parameters, matched to direct dense-slice checks. Observed next-worker branches agree with the 7,000 E-tick threshold. The four-operation threshold is 10,000 E-ticks; it never qualifies here. The four-slice callback ceiling is reached only once; that does not prove it prevented useful fifth-slice work. Raising that ceiling is weakly supported as a first change.

Adjacent complete two-operation workers after the final request, excluding PRIME and the contact-crossing worker, have summed costs: PAL median 10,437, p95 11,300, maximum 11,723 CCK; NTSC median 10,455.5, p95 11,372, maximum 11,379. Each uses 52 pairs. This is a counterfactual estimate, not a measured four-operation bound: ownership overhead, IRQ and contention would differ. Retained same-product native preview diagnostics did exercise budget four, with cold-incoming worker maxima 20,840 / 20,958 CCK, but on a different miss fixture with one worker per callback. Neither dataset approves lowering a shipping reserve.

PAL has one request API call in this interval; NTSC has two. Their individual generation/cancellation effects are not attributed here. The pair model starts after the last request to avoid treating earlier work as steady-state progress. Input admission/restart costs remain in the elapsed table.

| Contact and publication interval | PAL CCK | NTSC CCK |
|---|---:|---:|
| Hook → completed original dispatcher | 4,811 | 4,901 |
| Dispatcher return → first actual COPJMP marker | 259,673 | 204,157 |
| Of return→publication: original sequential ball | 12,613 | 6,732 |
| Of return→publication: bounded landing helper | 3,955 | 3,947 |
| Of return→publication: worker residual | 20,324 | 12,524 |
| Of return→publication: outside polling | 149,365 | 124,118 |

Hook→publication totals about 74.568 / 58.404 ms. This includes completing the dispatcher, outgoing readiness, endpoint work, admission and actual publication opportunities. It is not all render cost. The remaining return→publication categories are reproduced by the tool; they include input, metadata, admission and explicitly unassigned time. Zero observed named presentation spans do not prove zero presentation work. Generation-owned first actual publication is the endpoint, not API readiness or a later readback phase.

## What can be reused safely

The immutable complete actual post-opponent-launch318 origin is already reusable when its selected context matches. Later complete states are not invariant under human position/action edits: `game_ai_track` reads opposite-player X, retargets and changes movement and RNG call timing; scene geometry depends on both players; input held/edges/latches and entropy-policy transitions differ. Restoring a later full318 then patching X/Y is not an equivalent reconstruction.

A narrow incoming ball projection may be invariant before contact only with explicit already-launched flight, fixed receiving end, unchanged playing lifecycle and no serve attachment/reset/transition guards. Actual player contact precedes ball tick; player phase gates it, and scene work can clamp courtY. Contact geometry uses byte-wrapped player coordinates, receiving-end offset, X/Y tolerances and courtY/ball-height checks. Action, low-height and RNG-dependent outgoing decisions still need the actual contact path. A projection can become an advisory candidate filter; it does not replace advancing AI, scene, audio, clocks and ordered outputs in the edited full state.

Stable-playing round polls may be no-ops under score/restart/S_MODE guards. Pads require unchanged held state, zero edges and unchanged action latches; result requires all stored bytes and falling-edge entropy policy unchanged. Irregular histories need fallback. Any suppression must preserve cursors, phase/count, ordered events and checks after every envelope. Public yields restore history72, not full318, so a full-state-copy bottleneck must not be invented.

## Ranked next work and approval gate

| Rank / alternative | Expected benefit | Size and proof burden |
|---|---|---|
| 1. Calibrate guarded budget-four admission using existing `game_preview_step` | Best evidence for reducing callback count: every observed fresh incoming worker fell back to two operations | Small scheduling change; substantial native worst-case timing proof. Existing API already preserves original envelope order and checks after each operation |
| 2. Reduce public yields or add a guarded multi-envelope packet | May reduce the measured ~60–63 ms worker residual and slot pacing if it remains material after rank 1 | Medium change; preserve irregular prefixes, PRIME, cancellation, every original body/event and immediate contact/terminal checks |
| 3. Use more time between callbacks | Potentially material, but polling attribution is not an available-time budget | Larger ownership/scheduling proof: IRQ, clock, fresh input, cancellation, publication and private-state isolation |
| 4. Cache projected incoming trajectory / candidate contact | May avoid geometry searches; full edited-state execution remains necessary | Medium to large dependency proof, guarded projection and fallback |
| 5. Direct contact or later full-state reuse | Benefit unmeasured; later full-state patching is currently invalid | Highest equivalence burden; defer pending a complete dependency proof |

A conditional arithmetic model of four four-operation jobs per callback would need roughly 14 callbacks for 213 envelopes. This is not a latency bound: fitting those jobs, request/PRIME overhead, input restarts and transition costs are unproven. Do not advertise a measured hundreds-of-milliseconds improvement.

First small proof, after user approval: retain the production state/event algorithm and measure existing four-operation workers in full callback context. Cover contact and miss, both receiving ends, serve handoff, net/out/fault, AI/RNG variations, audio/scoring/lifecycle transitions and fresh physical input/cancellation. Record bus/CPU costs, complete callback headroom including input and publication tail, stack and RAM. Compare complete318, ordered events, history/cursors and actual first publication with the unchanged reference; include poisoned working state and nonstandard envelope prefixes. Only then propose a guarded reserve, with fallback and an independent review. Raising the slice ceiling or introducing a packet ABI is not required for this proof.

The integrator owns any future implementation and evidence reconciliation; the independent reviewer challenges attribution, equivalence, worst cases and acceptance extent before merge. User review is required before a production scheduling/reserve change. This analysis does not authorize that change. PR41 remains draft/unmerged; appearance, broader resource profiles and cold stripped-release validation remain open. No new native campaign was needed for this analysis.

## Analysis checks

The offline analysis completed against both retained receipts, validating all bound file hashes, coherent CIA read patterns, timer parameters, observed admission branches, category containment, pairwise disjointness and exact elapsed sums. An independent integer-set oracle checked interval union, subtraction and clipping over 1,000 deterministic adversarial span pairs, plus owner containment edge cases; all passed. These check the analysis arithmetic, not a new native timing gate.

Documentation resource check: `python scripts/native_metrics.py --check` exited 1 with `ValueError: Accepted metrics are incomplete`. This preserves the existing resource hold; no metrics or production inputs changed. No host suite or native campaign was rerun for these documentation-only changes.

Independent read-only review (`ratio32_review`) cleared the report and analyser after checking the emitted CIA read/reserve calculation, unique admission-to-worker mapping, disjoint attribution, indirect dispatch scope, tail-call limitations and reuse constraints. No runtime build or emulator execution was used for review; no reserve or latency improvement was approved.
