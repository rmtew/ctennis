# Upper-return action timing regression

This is a finite F2 behaviour set. The existing continuous rally did not vary
an action across the same accepted contact. An implementation that samples the
action too early/late, or always applies/ignores its trajectory choice, can pass
that replay while changing gameplay. Three fixed four-frame action pulses now
protect this boundary. No additional equivalent onset variants are required.

Each case selects two-player mode from reset and preserves the frozen natural
rally prefix until its first changed input. Original upper contact is accepted
at source callback707/frame2006 in every case. The original input sampler records
the pulse; an action held before or at contact changes the launch, whereas an
action first sampled afterward leaves that existing launch unchanged. Contact
acceptance itself is geometric and must not be inferred from the action pulse.

| Case | Action onset frame | Unchanged prefix callbacks | Sampled action callbacks | Captured launch choice |
|---|---:|---:|---|---|
| contact-upper-action-before | 2005 | 705 | 706..709 | Action trajectory |
| contact-upper-action-at | 2006 | 706 | 707..710 | Same action trajectory |
| contact-upper-action-after | 2007 | 707 | 708..711 | Normal trajectory |

Each source recording is independently repeated twice and retained through
callback722/frame2021, after release and subsequent flight. No source RAM/CPU
writes or game-result model are used. Validation requires the exact original
prefix, accepted-return marker, launched phase, consumed four-frame pulse and
before/at equality versus the distinct late launch. It rejects a missing contact,
wrong sampled action and shortened post-release capture in all three cases.

Actual shared assembled gameplay routines compare green for every case: all
254 observed state bytes at entry/pre-tail/return across722 consecutive callbacks
and151 ordered PSG writes. At contact the source sound writes are C5/0D/DF/D0
in all three cases; the trajectory distinction remains independently observable.

A temporary mutation inverts the native upper-contact action gate only at the
captured contact geometry, preserving the original CCR and stack elsewhere.
Each case first diverges at callback707/frame2006, pre-tail ball motion flags:
before/at expected66 actual64; after expected64 actual66. The runner requires
this exact target callback rather than accepting a mutation caught earlier in
the shared prefix. Temporary mutation source/executables are removed. Production
source is unchanged. This demonstrates detection of the specific regression
these tests are intended to prevent.

Reproduce (expand one case ID per invocation):

```
python scripts/capture_test_reference.py --case contact-upper-action-before
python scripts/capture_test_reference.py --case contact-upper-action-at
python scripts/capture_test_reference.py --case contact-upper-action-after
python scripts/contact_reference.py
python scripts/run_regression_tests.py --case <case-id> --self-test
python scripts/run_test_suite.py --baseline-check --self-test
```

Private source fixtures remain in tests/reference; raw captures are in
build/tests/<case-id>-capture and native reports in build/tests/<case-id>-report.json.
The aggregate validates the three-case relationship and includes it in the report.

| Case suffix | Fixture SHA256 |
|---|---|
| before | `04c4b7fe8dbf07c7ff305fcff7a87b27163a2f0e034a3fdae223f1a3bd713765` |
| at | `72f5f6c8b5149253aaf8f01571cd264d6feff2a52c3883ad84cb0beb352274e2` |
| after | `1998b25f5c85cbdf9b86be295920f1cd5e8ce6017daf05914312b85aca50226b` |

This boundary is complete. Broader F2 serve/lower-return/geometric distinctions,
later round/result regimes and native P1/P2/P3 remain open. Next prioritize
missing complete round/reset/resume and result/restart comparison intervals;
these three cases do not establish full hardware input sampling acceptance.
