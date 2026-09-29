"""Verify RAM-backed 40-byte sprite-attribute uploads in the long reset trace."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WRITE = re.compile(r"DATA WRITE VRAM\[\$([0-9A-F]{4})\] <- \$([0-9A-F]{2})")


def main():
    trace = json.loads((ROOT / "build/smoke/hardware-trace-reset-400.json").read_text())
    final_vram = (ROOT / "build/smoke/vram-reset-400.bin").read_bytes()
    vint = 0
    attr = []
    for index, line in enumerate(trace["lines"]):
        if "VINT FLAG" in line:
            vint += 1
        match = WRITE.search(line)
        if match and 0x3B00 <= int(match[1], 16) < 0x3B80:
            attr.append((int(match[1], 16), int(match[2], 16), vint, index))
    assert [(address, value) for address, value, _, _ in attr[:3]] == [
        (0x3B00, 0xD0), (0x3B28, 0xD0), (0x3B00, 0xD0)]
    uploads = attr[3:]
    assert len(uploads) % 40 == 0
    groups = [uploads[i:i + 40] for i in range(0, len(uploads), 40)]
    assert len(groups) == 38
    for group in groups:
        assert [address for address, _, _, _ in group] == list(range(0x3B00, 0x3B28))
    assert bytes(value for _, value, _, _ in groups[-1]) == final_vram[0x3B00:0x3B28]
    report = {
        "trace_count": trace["count"],
        "complete_40_byte_uploads": len(groups),
        "first_upload_vint": groups[0][0][2],
        "last_upload_vint": groups[-1][0][2],
        "first_upload": bytes(value for _, value, _, _ in groups[0]).hex(),
        "last_upload": bytes(value for _, value, _, _ in groups[-1]).hex(),
        "last_ten_records": [final_vram[0x3B00 + i:0x3B04 + i].hex()
                             for i in range(0, 40, 4)],
    }
    out = ROOT / "build/analysis/sprite-attribute-report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
