"""Disassemble and reassemble the identified local cartridge; require exact bytes."""

import argparse
import configparser
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_SIZE = 8192
EXPECTED_SHA256 = "19bb6647f14ef50f976e8d0a06d389f06b2e700d54a54fb1734d3140f9745ad1"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
    if completed.returncode:
        raise RuntimeError(
            f"Command failed ({completed.returncode}): {command[0]}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    return completed


def check_blocks(path: Path) -> dict[str, int]:
    pattern = re.compile(
        r"^\w+: unlabeled start 0x([0-9a-f]{4}) unlabeled end 0x([0-9a-f]{4}) "
        r"type (code|bytedata)$"
    )
    counts = {"code": 0, "bytedata": 0}
    cursor = 0
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith(";"):
            continue
        match = pattern.fullmatch(line)
        if not match:
            raise ValueError(f"Invalid block definition at {path}:{number}")
        start, end = int(match[1], 16), int(match[2], 16)
        if start != cursor or end <= start or end > EXPECTED_SIZE:
            raise ValueError(f"Block gap, overlap, or invalid end at {path}:{number}")
        counts[match[3]] += end - start
        cursor = end
    if cursor != EXPECTED_SIZE:
        raise ValueError(f"Block map stops at {cursor:#06x}; expected {EXPECTED_SIZE:#06x}")
    return counts


def apply_comments(listing: Path, comments: Path) -> int:
    """Insert address-keyed prose into generated assembly without changing bytes."""
    notes: dict[int, list[str]] = {}
    for number, line in enumerate(comments.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t", 1)
        if len(fields) != 2 or not re.fullmatch(r"[0-9A-Fa-f]{4}", fields[0]) or not fields[1].strip():
            raise ValueError(f"Invalid annotation at {comments}:{number}")
        notes.setdefault(int(fields[0], 16), []).append(fields[1].strip())
    source = listing.read_text(encoding="utf-8")
    output: list[str] = []
    found: set[int] = set()
    for line in source.splitlines(keepends=True):
        match = re.search(r";([0-9a-f]{4})\t", line)
        if match:
            address = int(match[1], 16)
            if address in notes:
                for note in notes[address]:
                    output.append(f"; {note}\n")
                found.add(address)
        output.append(line)
    missing = notes.keys() - found
    if missing:
        raise ValueError(f"Annotations lack listing starts: {', '.join(f'{x:04X}' for x in sorted(missing))}")
    listing.write_text("".join(output), encoding="utf-8")
    return sum(map(len, notes.values()))


def restore_literal_operands(listing: Path, literal_file: Path) -> int:
    """Undo z80dasm's address-label substitution for reviewed numeric operands."""
    reviewed: dict[int, tuple[str, str]] = {}
    for number, line in enumerate(literal_file.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([0-9A-Fa-f]{4})\t([A-Za-z_][A-Za-z0-9_]*(?:\+1)?)\t([0-9A-Fa-f]{4})", line)
        old_match = re.fullmatch(r"([0-9A-Fa-f]{4})\t(l[0-9a-f]{4}h)", line)
        if old_match:
            match = old_match
        if not match:
            raise ValueError(f"Invalid literal operand at {literal_file}:{number}")
        address = int(match[1], 16)
        if address in reviewed:
            raise ValueError(f"Duplicate literal operand instruction at {literal_file}:{number}")
        value = match[3].lower() if len(match.groups()) == 3 else match[2][1:5]
        reviewed[address] = (match[2], value)
    lines = listing.read_text(encoding="utf-8").splitlines(keepends=True)
    found: set[int] = set()
    for index, line in enumerate(lines):
        match = re.search(r";([0-9a-f]{4})\t", line)
        if not match:
            continue
        address = int(match[1], 16)
        literal = reviewed.get(address)
        if literal is None:
            continue
        symbol, value = literal
        operation, separator, rest = line.partition(";")
        if operation.count(symbol) != 1:
            raise ValueError(f"Reviewed literal {symbol} is absent or repeated at {address:04X}")
        lines[index] = operation.replace(symbol, f"0{value}h") + separator + rest
        found.add(address)
    if found != reviewed.keys():
        raise ValueError(f"Literal instructions missing from listing: {sorted(reviewed.keys() - found)}")
    for symbol, _ in set(reviewed.values()):
        if not re.fullmatch(r"l[0-9a-f]{4}h", symbol):
            continue
        references = sum(bool(re.search(rf"\b{symbol}\b", line.split(";", 1)[0])) for line in lines)
        if references == 1:
            lines = [line for line in lines if line.strip() != f"{symbol}:"]
    listing.write_text("".join(lines), encoding="utf-8")
    return len(reviewed)


def check_semantic_labels(listing: Path) -> int:
    labels = re.findall(r"^([A-Za-z_][A-Za-z0-9_]*):$", listing.read_text(encoding="utf-8"), re.M)
    automatic = [name for name in labels if re.fullmatch(r"(?:sub_|l)[0-9a-f]{4}h", name)]
    placeholders = [name for name in labels if re.fullmatch(r"(?:helper|loc)_[0-9a-f]{4}", name)]
    if automatic or placeholders:
        raise ValueError(f"Unreviewed labels: {', '.join((automatic + placeholders)[:12])}")
    return len(labels)


def simplify_listing(listing: Path) -> None:
    """Drop disassembler byte dumps and pack adjacent data bytes into rows."""
    output: list[str] = []
    pending: list[str] = []

    def flush() -> None:
        if pending:
            output.append("\tdefb " + ",".join(pending) + "\n")
            pending.clear()

    for line in listing.read_text(encoding="utf-8").splitlines(keepends=True):
        if line.startswith("; z80dasm ") or line.startswith("; command line: "):
            continue
        operation = re.sub(r";[0-9a-f]{4}\t[^\r\n]*", "", line).rstrip()
        data = re.fullmatch(r"defb\s+(0[0-9a-f]{2}h)", operation.strip())
        if data:
            pending.append(data[1])
            if len(pending) == 16:
                flush()
            continue
        flush()
        output.append(operation + "\n")
    flush()
    listing.write_text("".join(output), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--linear", action="store_true", help="Rebuild the original all-instruction listing")
    args = parser.parse_args()
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(ROOT / "config.local.ini", encoding="utf-8"):
        raise FileNotFoundError("config.local.ini")
    cartridge = Path(config["inputs"]["cartridge"])
    original = cartridge.read_bytes()
    if len(original) != EXPECTED_SIZE or sha256(original) != EXPECTED_SHA256:
        raise ValueError("Configured cartridge is not the identified 8 KB G-1009 image")

    output = ROOT / "build" / "analysis"
    output.mkdir(parents=True, exist_ok=True)
    stem = "champion-tennis-linear" if args.linear else "champion-tennis-classified"
    listing = output / f"{stem}.asm"
    rebuilt = output / f"{stem}.bin"
    block_file = ROOT / "analysis" / "rom-blocks.def"
    symbol_file = ROOT / "analysis" / "rom-symbols.def"
    comment_file = ROOT / "analysis" / "rom-comments.tsv"
    literal_file = ROOT / "analysis" / "rom-literal-operands.tsv"
    block_counts = None if args.linear else check_blocks(block_file)
    disassembler = ROOT / "build" / "tools" / "z80dasm.exe"
    assembler = ROOT / "build" / "tools" / "z80asm.exe"
    for tool in (disassembler, assembler):
        if not tool.is_file():
            raise FileNotFoundError(f"Missing {tool}; run the corresponding build script")

    listing.unlink(missing_ok=True)
    rebuilt.unlink(missing_ok=True)
    disasm_command = [str(disassembler), "-g", "0x0000", "-l", "-t"]
    if not args.linear:
        disasm_command += ["-b", str(block_file), "-S", str(symbol_file), "-c"]
    disasm_command += ["-o", str(listing), str(cartridge)]
    disasm_result = run(disasm_command)
    if not listing.is_file():
        raise RuntimeError("Disassembler did not create a listing")
    literal_count = 0 if args.linear else restore_literal_operands(listing, literal_file)
    comment_count = 0 if args.linear else apply_comments(listing, comment_file)
    semantic_label_count = None if args.linear else check_semantic_labels(listing)
    if not args.linear:
        simplify_listing(listing)
    asm_result = run([str(assembler), "-o", str(rebuilt), str(listing)])
    if not rebuilt.is_file():
        raise RuntimeError("Assembler did not create a ROM image")

    actual = rebuilt.read_bytes()
    first_difference = next((i for i, (a, b) in enumerate(zip(original, actual)) if a != b), None)
    if first_difference is None and len(actual) != len(original):
        first_difference = min(len(actual), len(original))
    report = {
        "source_size": len(original),
        "source_sha256": sha256(original),
        "rebuilt_size": len(actual),
        "rebuilt_sha256": sha256(actual),
        "byte_exact": actual == original,
        "first_difference_offset": first_difference,
        "classification": "linear all-instruction" if args.linear else "provisional code/byte-emission",
        "block_counts": block_counts,
        "block_file_sha256": None if args.linear else sha256(block_file.read_bytes()),
        "symbol_file_sha256": None if args.linear else sha256(symbol_file.read_bytes()),
        "comment_file_sha256": None if args.linear else sha256(comment_file.read_bytes()),
        "literal_file_sha256": None if args.linear else sha256(literal_file.read_bytes()),
        "restored_literals": literal_count,
        "applied_comments": comment_count,
        "semantic_address_labels": semantic_label_count,
        "disassembler_version": run([str(disassembler), "-V"]).stdout.splitlines()[0],
        "assembler_version": run([str(assembler), "-V"]).stdout.splitlines()[0],
        "disassembler_exe_sha256": sha256(disassembler.read_bytes()),
        "assembler_exe_sha256": sha256(assembler.read_bytes()),
        "listing_sha256": sha256(listing.read_bytes()),
        "disassembler_stderr": disasm_result.stderr.strip(),
        "assembler_stderr": asm_result.stderr.strip(),
        "listing": str(listing.relative_to(ROOT)),
        "rebuilt_image": str(rebuilt.relative_to(ROOT)),
    }
    report_name = "linear-roundtrip-report.json" if args.linear else "roundtrip-report.json"
    (output / report_name).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["byte_exact"]:
        raise RuntimeError(f"ROM mismatch at offset {first_difference:#06x}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ROM round trip failed: {error}", file=sys.stderr)
        sys.exit(1)
