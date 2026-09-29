"""Check the source-derived ball-state path through the first scored point."""

import csv
from pathlib import Path


path = Path(__file__).resolve().parent.parent / "build/mame/ball-point-trace.tsv"
with path.open(newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle, delimiter="\t"))

frames = [row for row in rows if row["event"] == "frame"]
writes = [row for row in rows if row["event"] == "write"]
assert [int(row["frame"]) for row in frames] == list(range(1250, 1501))

def writes_to(address):
    return [(int(row["frame"]), row["pc"], row["value"]) for row in writes
            if row["address"] == address]


assert writes_to("C039") == [
    (1362, "12CD", "02"),  # court-contact flag
    (1368, "0FE2", "40"),  # return/side change
    (1411, "12CD", "42"),  # next court contact
    (1432, "1213", "C2"),  # out-of-area flag
]
assert writes_to("C03F") == [(1433, "0A31", "01")]
assert [(frame, row["c038"], row["c039"], row["c03f"])
        for frame, row in ((int(row["frame"]), row) for row in frames)
        if frame in {1317, 1363, 1369, 1412, 1433, 1434}] == [
    (1317, "40", "00", "00"),
    (1363, "40", "02", "00"),
    (1369, "40", "40", "00"),
    (1412, "40", "42", "00"),
    (1433, "20", "C2", "00"),
    (1434, "00", "C2", "01"),
]
assert all(int(row["c066"], 16) == frame - 1317
           for frame, row in ((int(row["frame"]), row) for row in frames)
           if 1317 <= frame <= 1349)
score_trace = path.with_name("score-point-trace.tsv")
with score_trace.open(newline="", encoding="utf-8") as handle:
    score_rows = list(csv.DictReader(handle, delimiter="\t"))
award = next(row for row in score_rows if row["event"] == "write" and row["address"] == "C03F")
assert (award["frame"], award["c042"], award["c03d"]) == ("1433", "81", "00")
ball_award = next(row for row in writes if row["address"] == "C03F")
assert ball_award["c039"] == "C2"
# At 09CE HL starts at C03E. C042 low bits = 1 keeps HL there;
# C039 bit 6 swaps HL/DE to C03F; C03D bit 4 leaves that selection.
assert int(award["c042"], 16) & 7 == 1
assert int(ball_award["c039"], 16) & 0x40
assert not int(award["c03d"], 16) & 0x10
print({"frames": len(frames), "writes": len(writes), "court_contact_frames": [1362, 1411],
       "return_frame": 1368, "out_frame": 1432, "score_frame": 1433,
       "selected_score_field": "C03F"})
