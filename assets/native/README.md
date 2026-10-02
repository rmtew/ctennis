# Retained native build assets

Private-repository retention approved by the user. These96 native Amiga scene,
audio, court/score/sprite and enhanced-title/font inputs are copied unchanged
from the validated transfer archive. They are converted legacy assets, not
clean-room replacement graphics/music. Per-directory conversion metadata remains
intact; the root manifest pins every size/hash and former build path.

Former `build/amiga/<subdirectory>/<file>` maps to
`assets/native/<subdirectory>/<file>`. CT11 owns updates to .i incbin paths and
build preparation; the retained .i files intentionally keep their original paths
in this asset-only commit. No code or current build behavior changes here.
Generate version.bin and demo-inputs.i from revision/committed input metadata
separately. Keep cartridge/Kickstart, source captures, diagnostics and deliverable
executables/ADFs outside Git. Do not publish these assets publicly.
