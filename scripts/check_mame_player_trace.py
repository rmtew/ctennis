"""Validate the controlled SC-3000 left-movement trace, not just its screenshot."""

import csv
from collections import Counter
from pathlib import Path


trace = Path(__file__).resolve().parent.parent / "build/mame/player-left-trace.tsv"
with trace.open(newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))

frames = [row for row in rows if row["event"] == "frame"]
writes = [row for row in rows if row["event"] == "write"]
assert [int(row["frame"]) for row in frames] == list(range(1280, 1501))
by_address = Counter(row["address"] for row in writes)
assert by_address == {"C04E": 440, "C035": 440, "C021": 220, "C04A": 43, "C06B": 220}
assert Counter(int(row["frame"]) for row in writes if row["address"] not in {"C04A", "C06B"}) == {
    frame: 5 for frame in range(1280, 1500)
}
assert Counter(int(row["frame"]) for row in writes if row["address"] == "C06B") == {
    frame: 1 for frame in range(1280, 1500)
}
assert {row["pc"] for row in writes if row["address"] == "C06B"} == {"06B5"}
assert {row["pc"] for row in writes if row["address"] == "C04A"} == {"143B"}
assert int(frames[0]["c04a"], 16) == 0xC0
assert int(frames[-1]["c04a"], 16) == 0x80
assert int(frames[-1]["c021"], 16) == 0x94
assert all(row["joy"] == "3B" for row in frames if 1301 <= int(row["frame"]) <= 1450)
assert all(row["joy"] == "3F" for row in frames if int(row["frame"]) >= 1451)

print({"sampled_frames": len(frames), "writes": len(writes),
       "base_x_writes": by_address["C04A"], "base_x_first": "C0",
       "base_x_last": "80", "attached_ball_x_last": "94",
       "ball_x_write_frames": 220, "counter_write_frames": 220})
