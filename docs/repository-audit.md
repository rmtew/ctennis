# Repository audit

Baseline: `dd97c573df8044ba090facaedf31d549b83e12cf` (master, PR #29).
The baseline has 283 tracked files and 4,315,618 bytes of file content.
Git metadata and filesystem allocation are excluded.

[The index](repository-audit.tsv) gives every file's baseline size, type,
purpose, consumer, decision and evidence. It includes removed paths and the
four new support files. Stage file additions and removals, then run:

```sh
python scripts/check_repository_audit.py
```

The check compares the complete baseline Git tree with the current Git index.
It rejects missing, duplicate and incomplete rows. It checks baseline sizes and
keep/update/remove/add decisions against actual file contents. It does not
replace review of the evidence. Keep the baseline commit available in shallow
checkouts. Git history is the recovery source for tracked removals.

## Decisions

The audit keeps 192 baseline files, updates 38 and removes 53. It adds this
report, the index, the coverage check and current tool setup instructions. The resulting tree has 234 files.

Remove completed branch handoffs, obsolete review images, redundant metric
snapshots, the old WIN authoring script and the old acceptance-resume runner.
The WIN script requires removed point-bank inputs. The resume runner requires
an old executable, private receipts and an obsolete stage list.

Keep all 80 native manifest inputs, all assembly, both native fonts, the source
font image and extraction map, original ImageGen artwork and the frozen demo.
Keep the independent sprite, score-layout and LED contracts. Dynamic filename
construction, test discovery, assembly includes and historical report consumers
were checked. Lack of a text reference was not sufficient grounds for removal.

Keep the historical metric JSON chain: pre-title-score and pre-PR19 reports.
Keep the pre-direct-HUD baseline used by the retained comparison.
Keep the direct HUD comparison and its limits. `native_composite.py` remains
because current metric reporting imports its dependency normalization.
Historical JSON dependencies may name the removed font proof PNG. These are
past input hashes, not current build requirements. Do not rewrite those hashes.

Update first-party reading text with short instructions, consistent terms and
current facts. This is practical controlled English, not STE certification.
Keep source assembly style. PR #24 remains an active, unapproved Shot Doctor
design. Exit-game work remains cancelled; reboot is intentional.

## Workflow and validation

The assembly include graph reaches all 40 `.s` and `.i` files. `amiga/VERSION`
remains `1.0`. The native manifest declares 80 immutable inputs. The build validates
those inputs, generates the demo table and UI caches, and assembles `main.s`.
ADF packaging strips symbols from a copy and checks its embedded release bytes.
The finite native gate adds emulator and physical-input checks. Host tests and
offline authoring checks do not certify the native gate.

The following checks ran in a separate clean clone of cleanup commit `d237b02`.
Commit `65c1422` then added only the audit receipt. Review corrections below
were checked separately.

| Command or check | Result |
| --- | --- |
| `python scripts/check_repository_audit.py` | All 283 baseline and 233 current files covered |
| `python -m unittest discover -s tests/unit -q` | 67 tests passed |
| `python scripts/native_assets.py` | 80 declared inputs validated; demo table generated |
| `python assets/interface/font-mac/extract.py --proof /tmp/ctennis-font-proof.png` | 5,504 source pixels checked; proof generated outside Git |
| `python scripts/author_battle_hymn.py --output /tmp/ctennis-clean-music` | All six outputs equal the committed files |
| `author_title_logo_b.logo()` against retained title planes | All four 256 x 76 header planes match |
| `python -m compileall -q scripts tests assets/interface/font-mac docs/sprites` | Passed |
| `python scripts/progress.py --help` | Documented read-only entrypoint works |
| Retained support script AST comparison | All 14 edited modules have identical logic after removing module prose strings |
| Local Markdown links and removed-path search | No broken links; only historical font-proof hashes remain |
| Retained JSON previous-report chains | All three path/SHA256 links verified |
| `git diff --check` | Passed |
| `RUST_LOG=info python scripts/build_native_game.py` | Blocked: missing pinned vasm |
| `RUST_LOG=info python scripts/build_native_adf.py --self-test` | Blocked: missing pinned vasm |
| `python scripts/native_metrics.py --check` | Rejected inherited incomplete metrics |

The local clean clone had no tracked changes after validation. Its initial
missing-tool results are superseded by the separate worker checks below.
Neither worker ran the full acceptance gate for this cleanup.

## Separate worker validation at `65c1422`

The parent relayed clean-worktree results from the worker with the pinned tools:

- `python scripts/build_native_adf.py --self-test` passed for baseline and candidate.
- All 67 host tests passed.
- Exact-release startup passed all four PAL/NTSC × zero/512 KB slow-RAM cases.
- Normal candidate BUILD `d237b02`, version `1.0`, changed only generated
  `version.bin` and `ui-title-identities.bin` compared with the baseline inputs.
- Controlling only the build hash produced byte-identical development and release
  executables and all 787 symbols. The normal build was restored for emulator tests.
- The metrics check still rejected the inherited incomplete report.

These results establish the checked extent at `65c1422`. Subsequent review fixes
change prose and one generator comment. The comment leaves the generator AST
unchanged but advances the normal displayed build hash under existing rules.
Do not label the predecessor's native receipts as fresh for the later head.

## Review corrections

The current title has three menu entries at x108 and y114/125/136. Its selected
row cache is 768 bytes. The native copy owns ten bytes per row, offsets 11–20.
The host layout test covers both standards, both modes and all three selections.
Corrected documentation now agrees with the generator, native copy loop and
independent raster test. The generator's stale four-row comment was corrected;
its logic is unchanged. The focused title-layout test passed after these edits.

The same source review corrected role-label wording, the Credits identity claim,
the generated-only LOCAL marker and the requirement for one player to win six
games. It also checked scoreboard geometry, mask sizes, music cadence, startup
bounds and fixture counts against current code. These checks do not add native
execution evidence.

## Product identity and limits

All native asset bytes, assembly, tool locks, independent contracts and frozen
trajectory bytes are unchanged. Retained Python support logic is unchanged after
excluding module prose strings. Four descriptions now occur before imports so
that Python and command help can use them as module documentation.

The build selects its revision from all of `assets`, as well as assembly and
selected build scripts. Asset README edits and removal of the optional font proof
therefore advance the displayed BUILD revision. A normal new build is expected
to differ in its title identity. The PAL/NTSC selection and PR #29 label layout
remain unchanged. The controlled-hash equality result above applies to `65c1422`; normal builds
retain their own commit-derived identity.

This environment has Python 3.12.14 and Pillow 12.3.0. It lacks the locked vasm
executable (`.tools/vasm/vasmm68k_mot.exe`, SHA256
`0332feebc562e06bf245c1d60bef3fd7598c464a4be8162429be5e3e3a061e39`),
Copperline 1.0.0-rc.1 and amitools 0.8.1. The first audit missed the Linux
recovery recipe in the removed CT12 checkpoint. Independent review found it.
[Tool setup](tool-setup.md) now preserves its source commit, build command,
hashes and portable-mode workaround. A separate validation worker reproduced
the exact locked vasm on Debian 13 x86_64 with GCC 14.2.0-19. It also confirmed
the portable marker location beside the extracted Copperline ELF. The initial
missing-tool failures above
do not establish that provisioning is impossible. No tool lock was weakened.

The supplied Kickstart and cartridge files are outside the checkout. They were
not changed, copied into Git or packaged. Initially the checkout had no untracked
or ignored files. Validation creates only ignored build outputs and Python
caches. Other workspace attachments and tools remain untouched. No Library file
was uploaded or replaced.

The baseline `docs/metrics/current.json` is already `incomplete`; all eight
profiles are unmeasured. Its bytes and required previous reports are retained.
`native_metrics.py --check` cannot certify it. This inherited limitation is
separate from this cleanup and is not a fresh native test failure.
