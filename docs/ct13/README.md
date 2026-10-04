# Match celebration and interface behavior

A match ends after six games. The final court, logical winner and totals remain
visible. After 48 celebration ticks, the loser, ball and shadow disappear.
The winner stands on their own half with a raised racket and a small bounce.
Blue/Red ownership remains correct after an end exchange.

The selected Battle Hymn chorus uses three sequenced voices. It has 2,112 score
bytes, a four-byte square waveform and a separate 3,072-byte period bank.
See [authored format and provenance](../../assets/native/audio/battle-hymn/README.md).
Ordinary sound effects retain their pitch, level and envelope behavior.

Celebration timing uses a bounded two/three-tick pattern. Its average is 2.4
simulation ticks per score unit, or about 40.052 ms. A 384-unit phrase and one-unit
terminal rest take 924 simulation ticks per subsequent loop. The first play adds
two queue ticks. All three final note durations must expire and emitted levels
must reach zero before the phrase is complete.

Human play shows PRESS FIRE TO CONTINUE only after the first complete phrase.
Early presses are discarded. Held controls must release before a fresh action
returns to title. Pause freezes the clock and notes, mutes Paula, and restores
levels on resume. Demo play returns to title after the first phrase, then waits
through the ordinary 30-second attract interval.

The title has four aligned menu entries and native A/B figures. Menus and help
use Font-Mac. The footer and game status use the retained court font. Selection
is inverted; static instructions remain normal. Holding a direction does not
repeat navigation. [Title identity](title-release-identity.md) defines the
PAL/NTSC, product hash and release label.

During demo play, the second footer row shows DEMO - TAKE OVER / EXIT. EXIT is
selected initially. Left selects TAKE OVER and right selects EXIT. Either
player's action button or Enter confirms; Escape exits. Takeover preserves the
world, score, audio and AI state. It consumes the confirmation and masks each
held live control until release. Live controls never alter recorded demo play.

Celebration fixtures cover both winners and end orientations. They initialize
native state once, then use actual scoring, controls, audio and scanout. Ordinary
match tests cover uninterrupted lifecycle and timing separately. The independent
10,958-tick recording remains unchanged. See [native tests](../../tests/README.md).
