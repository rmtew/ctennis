# Version 1.1 test candidate

The requested displayed release number is **1.1**, following the repository's
single `major.minor` source, `amiga/VERSION`. Version commit
`0556b8cc6810a3bb6b268c6975486ac5ebfae9a3` changes only that file. This is the
reviewed PR55 exploration runtime with new title metadata, not a merged release.

Development SHA256: `929bdbc163e610f13685a6cdb31ab15e9434016036c9788e06ffa32e4bd2f0a9`.
Stripped release SHA256: `7206a438475bc3057fa2451bc03d66efb889e027d5f1f052023c944c1e4f7d95`.
Standalone ADF SHA256: `90466f45cf3d6ec14d24259583636b00e4c46acd960f30dde65c96dceb129ddc`.
The ADF is 901,120 bytes. The standalone filename is `tutorial-1.1-0556b8c.adf`.

Package campaign `87f6a9bb8c0148daa43ef7c37d693bee` attempt1 passes two clean,
byte-identical builds and embedded executable verification. Both focused PAL and
NTSC cold boots verify all five actual relocated release hunks, title lifecycle,
and independent native title/menu rasters displaying `PAL/NTSC 0556b8c 1.1`.
Each checks 38,912 logo and 59,392 menu/identity pixels. No gameplay input or
callback/timing regime is injected, and no broad gameplay campaign is repeated.

Compared with the preserved 1e3dbb3 candidate, all loaded hunk sizes and layout are
identical. CODE bytes are identical after replacing only the declared BUILD
identity string. All 88 DATA byte differences occur in the 512-byte generated
title-identity rasters. The sole product-source change is `amiga/VERSION`;
compiled nongenerated source files are unchanged. Prior PR55 gameplay results
are explicitly reused on that basis, rather than relabelled as fresh runs.

Initial boot observations correctly displayed 1.1, but their reports mistakenly
included the provisional report itself in artifact hashes. Both invalid binding
receipts remain preserved. Observer commit 1c59f84 excludes that output, and fresh
focused boots provide clean receipts. This correction changes no product bytes.

Exact private receipt paths/checksums and independent review are indexed in
[version-1.1-summary.json](evidence/tutorial-exploration/version-1.1-summary.json).
No large archive, ROM publication or broad resource collector was generated.
Tracked metrics retain incomplete eight-profile coverage and current product
identity. Existing merge and full-release holds remain.

## Conditional GitHub tag

Existing tags were checked before the change: the repository has `1.0.0` at
`2251cc0a6b17f3c8ca9d9af7adf4772acd1eb8d0`; no `1.1.0` tag exists. Accordingly,
the requested conventional tag is **1.1.0**. PR55 is still draft and unmerged,
so no tag has been created or moved.

After merge, verify actual `merged=true`, resolve the real merged commit, verify
its `amiga/VERSION` is 1.1 and recheck tag absence. Tag that actual merged commit
as `1.1.0` if tagging is available. An unmerged PR's tentative `merge_commit_sha`
is insufficient evidence. Do not tag the draft branch or overwrite any tag.
