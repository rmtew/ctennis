"""Small native listing and target validators, independent of historical runners."""
import re


def code_symbols(listing):
    return {name: int(offset, 16) for name, offset in
            re.findall(r'^([A-Za-z_][\w]*)\s+00:([0-9A-Fa-f]{8})\s*$', listing, re.M)}


def target_log(directory, standard="PAL"):
    if standard not in ("PAL", "NTSC"):
        raise ValueError("Unsupported native video standard: " + standard)
    log = (directory / 'emulator.log').read_text()
    for marker in ('cpu=M68000', 'chip_ram=512K', 'slow_ram=0K', 'fast_ram=0K',
                   'chipset=Ocs', 'video='+standard.title(), 'Kickstart 1.3'):
        if marker not in log:
            raise ValueError('Missing actual target marker: ' + marker)
    (directory / 'copperline.log').write_text(log)
