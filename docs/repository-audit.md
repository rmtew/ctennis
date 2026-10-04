# Repository audit

Baseline: `dd97c573df8044ba090facaedf31d549b83e12cf` (master, PR #29).
The baseline has 283 tracked files and 4,315,618 bytes of file content.
Git metadata and filesystem allocation are excluded.

[The index](repository-audit.tsv) gives every file's baseline size, type,
purpose, consumer, decision and evidence. It includes removed paths and the
three new audit files. Stage file additions and removals, then run:

```sh
python scripts/check_repository_audit.py
```

The check compares the complete baseline Git tree with the current Git index.
It rejects missing, duplicate and incomplete rows. It checks baseline sizes and
keep/update/remove/add decisions against actual file contents. It does not
replace review of the evidence. Keep the baseline commit available in shallow
checkouts. Git history is the recovery source for tracked removals.

## Decisions

The audit keeps 193 baseline files, updates 37 and removes 53. It adds this
report, the index and the coverage check. The resulting tree has 233 files.

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

Validation commands and outcomes are recorded below after the clean-checkout run.

## Product identity and limits

All native asset bytes, assembly, tool locks, independent contracts and frozen
trajectory bytes are unchanged. Retained Python support logic is unchanged after
excluding module prose strings. Four descriptions now occur before imports so
that Python and command help can use them as module documentation.

The build selects its revision from all of `assets`, as well as assembly and
selected build scripts. Asset README edits and removal of the optional font proof
therefore advance the displayed BUILD revision. A normal new build is expected
to differ in its title identity. The PAL/NTSC selection and PR #29 label layout
remain unchanged. No binary-equivalence claim is made without the assembler.

This environment has Python 3.12.14 and Pillow 12.3.0. It lacks the locked vasm
executable (`.tools/vasm/vasmm68k_mot.exe`, SHA256
`0332feebc562e06bf245c1d60bef3fd7598c464a4be8162429be5e3e3a061e39`),
Copperline 1.0.0-rc.1 and amitools 0.8.1. The repository supplies no recipe that
reproduces the locked vasm executable. Build/package and native execution need
these external tools. No tool lock was weakened to bypass this requirement.

The supplied Kickstart and cartridge files are outside the checkout. They were
not changed, copied into Git or packaged. Initially the checkout had no untracked
or ignored files. Validation creates only ignored build outputs and Python
caches. Other workspace attachments and tools remain untouched. No Library file
was uploaded or replaced.

The baseline `docs/metrics/current.json` is already `incomplete`; all eight
profiles are unmeasured. Its bytes and required previous reports are retained.
`native_metrics.py --check` cannot certify it. This inherited limitation is
separate from this cleanup and is not a fresh native test failure.
