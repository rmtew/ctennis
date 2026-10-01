"""Native build tool paths; no original-machine generation or emulation."""
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parent.parent
ASSEMBLER = ROOT / '.tools/vasm/vasmm68k_mot.exe'
def run(command, timeout=120):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{command[0]} failed ({result.returncode}): {result.stdout[-2000:]} {result.stderr[-2000:]}')
    return result.stdout + result.stderr
