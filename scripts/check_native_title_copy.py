"""Bounded actual-68000 copy/epoch regression; not an Amiga deadline proof."""
import hashlib
import json
from pathlib import Path

from build_match_core import load_image
from native_tools import ROOT


def run():
    import machine68k as m
    path = ROOT / 'build/amiga/interfaces/enhanced/baseline-rally'
    image, symbols = load_image(path)
    machine = m.Machine(m.CPUType.M68000, 2048)
    mem, cpu = machine.mem, machine.cpu
    for address, data in image:
        mem.w_block(address, data)
    cpu.w_sr(0x2700)
    end = machine.create_execute_end('return')
    trap = machine.traps.alloc(lambda opcode, pc: end)
    mem.w16(0x100000, 0xa000 | trap)

    def call(name):
        cpu.w_sp(0x1ffff0)
        mem.w32(0x1ffff0, 0x100000)
        cpu.w_pc(symbols[name])
        result = machine.execute(1000000)
        assert result.result is end, name
        assert cpu.r_sp() == 0x1ffff4, name

    source, destination = 0x180000, 0x190000
    pattern = bytes((index * 37 + index // 256) & 255 for index in range(3712))
    mem.w_block(source, pattern)
    mem.w_block(destination - 4, b'\xa5' * 3720)
    for register in range(15):
        cpu.w_reg(register, 0x12340000 + register)
    cpu.w_reg(8, source)
    cpu.w_reg(9, destination)
    saved = [cpu.r_reg(register) for register in range(15)]
    call('ui_copy_cached_plane')
    assert bytes(mem.r_block(destination, 3712)) == pattern
    assert bytes(mem.r_block(destination - 4, 4)) == b'\xa5' * 4
    assert bytes(mem.r_block(destination + 3712, 4)) == b'\xa5' * 4
    assert cpu.r_reg(8) == source + 3712 and cpu.r_reg(9) == destination + 3712
    assert all(cpu.r_reg(register) == saved[register]
               for register in range(15) if register not in (8, 9))

    # A fresh shortcut may enter play before the deferred title is built.
    # Its flag must retire even across the native16-bit callback counter wrap.
    mem.w16(symbols['game_lifecycle'], 1)
    mem.w16(symbols['ui_overlay_signature'], 0)
    mem.w16(symbols['simulation_started_updates'], 0xffff)
    mem.w16(symbols['ui_title_request_epoch'], 0xffff)
    mem.w8(symbols['ui_title_deferred'], 0xff)
    call('ui_render')
    assert mem.r8(symbols['ui_title_deferred']) == 0xff
    entry = symbols['simulation_update']
    size, instruction = cpu.disassemble(entry)
    assert instruction.startswith('addq.w') and size == 6
    stop_trap = machine.traps.alloc(lambda opcode, pc: end)
    mem.w16(entry + size, 0xa000 | stop_trap)
    cpu.w_pc(entry)
    assert machine.execute(1000).result is end
    assert mem.r16(symbols['simulation_started_updates']) == 0
    call('ui_render')
    assert mem.r8(symbols['ui_title_deferred']) == 0
    return {'passed': True, 'executable_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'copied_bytes': 3712, 'sentinels_and_registers_preserved': True,
            'actual_counter_wrap': '65535->0', 'shortcut_flag_retired': True,
            'scope': 'Actual68000 bytes/registers/epoch; no native deadline or DMA claim'}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
