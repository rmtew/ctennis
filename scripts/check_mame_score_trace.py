"""Validate the controlled first-point score trace against the displayed B:15 state."""

import csv
from pathlib import Path


trace = Path(__file__).resolve().parent.parent / "build/mame/score-point-trace.tsv"
with trace.open(newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))

frames = [row for row in rows if row["event"] == "frame"]
writes = [row for row in rows if row["event"] == "write"]
assert [int(row["frame"]) for row in frames] == list(range(1200, 1801))
score = [row for row in writes if row["address"] in {"C03E", "C03F"}]
assert [(row["frame"], row["pc"], row["address"], row["value"]) for row in score] == [
    ("1433", "0A31", "C03F", "01")
]
assert all(row["c03e"] == "00" and row["c03f"] == "00" for row in frames if int(row["frame"]) <= 1433)
assert all(row["c03e"] == "00" and row["c03f"] == "01" for row in frames if int(row["frame"]) >= 1434)
assert any(row["frame"] == "1433" and row["pc"] == "0A15" and row["address"] == "C03D" and row["value"] == "08" for row in writes)
print({"frames": len(frames), "writes": len(writes), "point_frame": 1433,
       "score_write_pc": "0A31", "score_address": "C03F", "score_value": "01"})
