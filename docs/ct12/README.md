# CT12: Baseline Rally identity and readable native labels

Implementation base is merged master43e1118d878453809a68c257deef20a937697e15.
CT11 cleanup and focused UI timing retain their product logic. Repository name
remains rmtew/ctennis. This is a private native milestone, not a public release;
retained Sega-derived assets confer no new ownership or redistribution rights.
See [initial finite plan/checkpoint](checkpoint.md).

## Intentional visual changes

- Native title now reads BASELINE RALLY in enlarged existing native font glyphs.
  The menu remains four entries and a short navigation hint. Help/Controls/Credits
  retain their page structure; credits identify Sega-derived private-port origins.
- Sega's logo is removed from the native court and title planes. No source
  cartridge or captures were read. Background changes are confined to logo and
  retired mode cells plus player-linked score indicators.
- Pink becomes Red ($e33) in dynamic sprite palettes, static pair defaults and
  index13's logical B label. The old index13 audit found82 pixels, all within
  B's header x227..237/y19..31. Court colours $f77 and $dc5 stay intact. All14
  player pose descriptors, animation sequences and8192-byte sprite atlas stay
  unchanged; dynamic palette selection colours every pose and both ends.
- Player-linked heart indicators now use Blue/Red instead of shared coral.
  Red's point banks add high planes around the identical original digit and
  graphical advantage masks. No advantage text or rules change is introduced.
  Logical scores/tallies/controls/win prompts follow their players across ends.
- Status variants retain IN/OUT/NET/ACE; FLT is FAULT and actual DBF is DOUBLE
  FAULT. Status moves from x112/y96 (24x8 over the net) to x80/y0 (96x8 above
  the players). All four full-row planes restore at native y8. Blank status
  restores all glyph pixels. The clock and status event logic are unchanged.
- Mode retains DEMO; 1PLAY and 2PLAY become 1 PLAYER and 2 PLAYERS. Existing
  five-pixel native glyphs use six-pixel cells, fitting the widened56x8 field at
  x200/y32 between the B header and point field. Its row is clear of court, B header and point score. Full-row pointers switch at Copper76 and restore at84, with
  B point high-plane banks supplying planes0/3 at that boundary. Original point
  and tally WAIT/fetch positions remain intact, including tally slots4b/ab and
  offsets2/26. Field descriptors increase224→242; footer still ends at251 and
  court publication keeps the before25 or blank>=252 window.
- Native executable, disk label, startup command and ADF are baseline-rally.
  Attract/takeover input recording and canonical10958-tick trajectory are unchanged.

Before images are actual unchanged-baseline Copperline scanout, not cartridge
captures. After images are actual native scanout and are added after focused
verification. No expected images are regenerated from runtime rendering.
The independently authored field tests spell each label from committed font
bits and check full-row clearing; native raster observers check completed bank
association and actual scanout. Intentional asset hashes retain imported hashes.

| View | Before | After |
|---|---|---|
| Menu | [before](screenshots/before-menu.png) | [after](screenshots/after-menu.png) |
| Play | [before](screenshots/before-play.png) | [after](screenshots/after-play.png) |
| Controls | [before](screenshots/before-controls.png) | [after](screenshots/after-controls.png) |
| Credits | [before](screenshots/before-credits.png) | [after](screenshots/after-credits.png) |
| FAULT | [before](screenshots/before-fault.png) | [after](screenshots/after-fault.png) |
| DOUBLE FAULT | previously abbreviated DBF | [after](screenshots/after-double-fault.png) |

Final commands, exact hashes, verification extent and remaining limits are
recorded in verification.md after the finite gate. No master merge is performed.
