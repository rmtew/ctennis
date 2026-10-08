# Current limits

- Retained converted graphics, fonts, poses, music and effects remain Sega-derived.
  Private retention is approved. Public redistribution rights are not asserted.
- RAM telemetry starts with initialized Exec chip pools. Earlier bootstrap use
  remains unmeasured. Executable size is not a whole-machine RAM measurement.
- Tests do not establish whole-game original pixel, waveform, filter, phase or
  stereo parity. Do not replace missing historical media with expected results
  generated from the implementation. Native assets and independent contracts
  provide the maintained protection.
- Copperline checks cover fixed region pointers, fetched words, row restoration,
  three-bank ownership and PAL/NTSC publication. They do not establish a fresh
  WinUAE or physical-hardware pass. Earlier WinUAE feedback with 512 KB slow RAM
  is separate from the unexpanded target.
- The current resource report has incomplete runtime coverage. Older complete
  reports are historical evidence. See [resource reporting](metrics/README.md).
- The shared deterministic production core and bounded rolling history/seek are
  implemented. The focused history evidence is described in
  [bounded history](bounded-history.md). Isolated previews and bounded native seek scheduling are implemented with
  independently reviewed selective CPU/PAL/NTSC evidence; see
  [isolated previews](isolated-shot-previews.md). The tutorial court UI is the
  active [roadmap](tutorial-mode-design.md) increment. Branching, persistent saves
  and the full target/release gate remain later work. Finite observed callback
  headroom does not establish a universal timing bound. Reboot remains intentional after play.
