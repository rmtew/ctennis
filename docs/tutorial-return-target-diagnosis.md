# Original return controls and net outcomes

Returns do not use the serve's frozen absolute-target sampling rule. The
original `amiga/game/gameplay_contact.s` accepts contact on the receiving side
only: court Y must be within less than4 units of the player's contact point,
court X within less than17, and ball height above ground must be0..28. The
contact point is player X+8, player Y+27 (upper adds another8 to Y).
Position therefore changes contact eligibility, timing and the actual height at
contact; a different position can also miss entirely.
An incoming shot that faults before an eligible return is a different case from
an outgoing return hitting the net: the contact routine rejects an already
flagged net ball. Return controls do not repair that incoming fault.

For a human contact less than8 units above ground, the original special branch
sets height12 and target depth104 (lower) or120 (upper), before consulting the
action button. `gameplay_ball.s` treats that special flight near court Y110 as a
net reflection. B1 therefore cannot change that low-contact formula at the same
contact. This does not establish that all incoming episodes or positions must
produce the same low contact, nor that every net is rescuable.

Regular released contact uses height = actual contact height+24. Its target
depth is224 minus the player's contact Y, clamped to at least64 for the lower
player or at most160 for the upper. A nonzero human action (including B1)
selects a different formula: lower height = contact Y-96, depth = height+16;
upper height =128-contact Y, depth =208-height. These byte arithmetic formulas
are original rules, not a new tutorial aiming system.

`game_return_vector` derives horizontal placement from player location, ball
offset and court perspective. At horizontal offset13 or greater it adds a
0..7 random jitter before doubling the offset. AI choices also consume random
draws. The initial frozen RNG is deterministic, but changing geometry or contact
timing can change which draws occur; it does not independently predetermine every
return outcome. Human regular B1 selection itself is not a random serve target
draw. `game_derive_launch` derives the actual velocity from these values.

The retained actual68000 proof supplies a controlled counterexample, without a
new emulator campaign. For one identical lower-human incoming episode and seed:

| Player XY | B1 held | B1 released |
| --- | --- | --- |
|111,128|Net|Net|
|111,153|Clears net; first ground94,100|Clears net; first ground94,62|
|100,153|Clears net; first ground112,100|Clears net; first ground111,62|
|40,153|No contact|No contact|

The111,128 contact occurs at height7, invoking the fixed low branch. The111,153
contact occurs later, at height13; held selects height84/depth100, while released
selects height37/depth64. Initial318-byte prime states differ only at requested
Y (offset2) or X (offset3) for the compared held cases. All exact/projected preview
paths equal their independently advanced original-dispatcher reference paths.
Both actions at the low position still net; changing only Y changes net to clear.
Changing X and B1 changes placement/depth in the other examples.

Evidence is the reused56-case `build/tests/coherent-scheduler-cpu/report.json`,
actual standalone SHA256
`38c48b8953c495fd86f5ddd4a475ddb27d5a3f881c9397c8f50ed8814e60c390`;
its bound `raw-7fda71d81cb448c98a96b818af32f55c/reference-0-*.json.gz` and
corresponding exact/projected worker captures. The read-only reduction
`build/tests/tutorial-auto-potential-reduction/return-control-original-reference-reduction.json`
checks source/raw hashes and both variants against each worker's actual path.
`scripts/coherent_scheduler_proof.py` records the common incoming source/stream
and changes only requested player XY; `scripts/predictor_proof.py` advances the
actual original bodies independently. This is finite CPU rule/preview evidence,
not a new physical input, native timing, WinUAE or universal rescue result.

The automatic-preview interaction campaign continues separately. No gameplay,
RNG, contact, net or serve rule was changed to obtain this diagnosis.
