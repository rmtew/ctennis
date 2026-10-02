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


def emulator_config():
    import configparser
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini', encoding='utf-8')
    for section, option in [('tools', 'copperline'), ('inputs', 'amiga_rom')]:
        if not config.has_option(section, option) or not Path(config[section][option]).is_file():
            raise FileNotFoundError('Configure legitimate native test input: ' + section + '.' + option)
    import json
    lock = json.loads((ROOT / "tools.lock.json").read_text())
    version = run([config["tools"]["copperline"], "--version"])
    if lock["copperline_version"] not in version:
        raise ValueError("Use pinned Copperline " + lock["copperline_version"])
    return config


def verify_build_tools():
    import hashlib, json, sys
    lock = json.loads((ROOT / 'tools.lock.json').read_text())
    if '.'.join(map(str, sys.version_info[:3])) != lock['python_version']:
        raise ValueError('Use pinned Python ' + lock['python_version'])
    if not ASSEMBLER.is_file() or hashlib.sha256(ASSEMBLER.read_bytes()).hexdigest() != lock['vasm_sha256']:
        raise ValueError('Install pinned vasm ' + lock['vasm_version'] + ' at ' + str(ASSEMBLER))
