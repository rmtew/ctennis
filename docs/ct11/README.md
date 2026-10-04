# Native build independence

The maintained game uses explicit versioned native inputs and pinned tools.
Builds and packaging do not need a source cartridge, captured state or emulator.
Tests use the actual native dispatcher, controls, rendering and audio.
The independent 10,958-tick demo fixture remains a test input.

CT11 removed the original comparison build, extraction tools and translation
adapters. Its file ledger and intermediate reports remain in Git history.
Asset import hashes and Sega-derived provenance remain in
[the native manifest and README](../../assets/native/README.md).

Current guidance is in [tests](../../tests/README.md), [limits](risks.md),
[timing](verification-issues.md), [publication](triple-buffer-publication.md),
and [startup standard selection](field-measurement.md).
