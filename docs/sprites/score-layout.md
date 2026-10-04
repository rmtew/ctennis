# Score panel layout

The score panels use fixed tens and units positions. A single zero occupies
the units position used by 30 and 40. Its tens cell is blank. The single A
keeps its selected position. The selected segment pixels are unchanged.

All coordinates below are native pixels. Border coordinates are inclusive.

| Element | A | B |
| --- | --- | --- |
| Role label | y34–41 | y34–41 |
| Point-score cell | x16–31, y48–63 | x224–239, y48–63 |
| Frame sides | x11,36 | x219,244 |
| Top, divider, bottom | y43,68,123 | y43,68,123 |
| WIN cells | x17–31, y72–119 | x225–239, y72–119 |

There are two blank rows between each A/B header and its role label. Each
point-score cell has four blank pixels between the cell and its frame.
Six WIN words use an eight-row pitch. Earned rows use the owner's Blue or Red;
remaining rows use solid dim grey. The frames are white and closed.

`score-layout-contract.json` freezes this geometry. The selected masks stay in
`square-led-contract.json`. The seven point states mean 0, 15, 30, 40, A, 40
and blank. There is no translation table for individual values.

Startup builds point masks and fixed HUD strips. Gameplay writes the building
strip and publishes a completed bank. Current direct HUD DMA uses three banks;
older reports about two banks and stored point strips describe previous code.
See [native acceptance](../../tests/README.md) for current validation commands.
Host tests check fixed digit positions, frame geometry and role-label spacing.
Native scoreboard and status checks compare the visible panels and frame pixels.
