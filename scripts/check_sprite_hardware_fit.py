"""Check sampled SG sprite records against eight Amiga channels and pair palettes."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CAPTURES = ROOT / "build" / "mame" / "captures"
TIMING = ROOT / "build" / "reference" / "source-timing"


def snapshots():
    for path in sorted(CAPTURES.glob("*.ram")):
        ram = path.read_bytes()
        if len(ram) != 1024:
            raise ValueError(f"Unexpected RAM size: {path}")
        yield path.name, ram
    with (TIMING / "run_a.tsv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["event"] == "checkpoint":
                yield f"timing-{row['frame']}", bytes.fromhex(row["ram"])


def main():
    counts = Counter()
    colours = Counter()
    slots = Counter()
    pair_colours = Counter()
    maximum_scanline = 0
    total = 0
    for name, ram in snapshots():
        total += 1
        records = [tuple(ram[0x10 + 4 * i:0x14 + 4 * i]) for i in range(10)]
        # The sampled game positions use C2 for hidden Y. Y >= C0 is below
        # the 192-line active picture. This is a bounded snapshot test.
        active = [(i, record) for i, record in enumerate(records)
                  if record[0] < 0xC0 and record[3] & 15]
        counts[len(active)] += 1
        colours.update(record[3] & 15 for _, record in active)
        slots.update(i for i, _ in active)
        if len(active) > 8:
            raise AssertionError(f"More than eight visible sprite records in {name}")
        for offset in range(0, len(active), 2):
            distinct = len({record[3] & 15 for _, record in active[offset:offset + 2]})
            pair_colours[distinct] += 1
            if distinct > 3:
                raise AssertionError(f"Sprite-pair palette overflow in {name}")
        maximum_scanline = max(maximum_scanline, max(
            (sum(y < line <= y + 16 for _, (y, _, _, _) in active)
             for line in range(192)), default=0))

    vram = (TIMING / "sprite-f1310.vram").read_bytes()
    ram = (TIMING / "sprite-f1310.ram").read_bytes()
    if len(vram) != 0x4000 or len(ram) != 0x400:
        raise ValueError("Controlled sprite capture is incomplete")
    if vram[0x3B00:0x3B28] != ram[0x10:0x38]:
        raise AssertionError("Controlled frame sprite attributes differ from RAM")
    if vram[0x1800:0x1820] != bytes((0xC0, 0xC0)) + bytes(30):
        raise AssertionError("Sprite pattern zero is not the observed 2x2 mark")
    report = {
        "sampled_ram_snapshots": total,
        "visible_record_counts": dict(sorted(counts.items())),
        "maximum_visible_records": max(counts),
        "maximum_overlapping_16_line_spans": maximum_scanline,
        "observed_sprite_colours": sorted(colours),
        "maximum_distinct_colours_per_amiga_channel_pair": max(pair_colours),
        "observed_populated_source_slots": sorted(slots),
        "controlled_frame": 1310,
        "controlled_vram_sha256": hashlib.sha256(vram).hexdigest(),
        "attribute_bytes_match_ram": True,
        "pattern_zero_pixels": 4,
    }
    (TIMING / "sprite-fit-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
