# Native title figures: parent integration handoff

Parent owns the approved title/menu preview. This branch does not change title
rendering, toggle behaviour, physics or the other worker's footer.

Use existing gameplay ready poses, with retained white rackets, at native size:

| Facing / pose index | Human racket / top / bottom byte offsets | Robot racket / top / bottom byte offsets | Racket anchor (dy,dx) |
| --- | --- | --- | --- |
| Upper/back ready0 |1536 /1280 /1408 |1536 /8192 /8320 |(+8,0) |
| Lower/front ready7 |2432 /5376 /5504 |2432 /9728 /9856 |(0,0) |

Each body consists of two16×16 monochrome masks at (X,Y) and (X,Y+16).
The white16×16 racket is a third primitive at (X+dx,Y+dy). Transparent holes
remain transparent. Every atlas slot is128 bytes:16 big-endian (mask,0) pairs,
then16 (0,mask) pairs for the alternate hardware-plane colour arrangement.
Read both orientations directly from `game_scene_poses` /
`game_scene_robot_poses`; never assume a different pose layout or redraw them.

Gameplay role selection lives in `game_scene_actor` in scene.s: human unless
single-player logical B; mode bit7 means both humans, bit4 exchanges court-end
ownership. Demo A is always human. A Blue55e/B Rede33 colours remain logical.
Gameplay objects have8-byte records (Y0,X1,frame2 word,colour4,visible5) and
colour1 is white racket,2 Blue,3 Red. Racket/body anchors and hitboxes are unchanged.

For title figures, select masks directly from the menu toggle and explicit A/B
ownership: A always human; B robot for HUMAN VS AI and human for HUMAN VS HUMAN.
Do not call `game_new_match`, mutate `game_mode`, assign players, step animations,
or refresh gameplay state merely to render a title preview. The existing actor
builder reads global game_mode and is unsuitable as an unmodified pure title
selector; give the title renderer its own presentation records/mask choice.
Native preview A/B labels and no custom title drawings follow the user request.
