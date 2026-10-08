"""Independent known answers for the actual native and standalone entropy code."""
import hashlib
import json
from pathlib import Path

from build_match_core import load_image
from match_core_cpu import Core
from native_tools import ROOT


# Right-shift Galois polynomial 0xb400, low bit returned before the shift.
# These authored mathematical answers are not captured from either executable.
ANSWERS = (
    (0xe270,1), (0x7138,0), (0x389c,0), (0x1c4e,0),
    (0x0e27,0), (0xb313,1), (0xed89,1), (0xc2c4,1),
    (0x6162,0), (0x30b1,0), (0xac58,1), (0x562c,0),
    (0x2b16,0), (0x158b,0), (0xbec5,1), (0xeb62,1),
)


def check(executable):
    image,symbols = load_image(executable)
    size = symbols['game_core_state_end']-symbols['game_core_state']
    assert size == 318
    observed_cycles = {'modern':{},'legacy':{}}
    def initialized(seed,policy):
        initial = bytearray(size)
        offset = symbols['game_match_seed']-symbols['game_core_state']
        initial[offset:offset+2] = seed.to_bytes(2,'big')
        initial[symbols['game_entropy_policy']-symbols['game_core_state']] = policy
        core = Core(image,symbols,initial=initial)
        core.call('game_core_seed_entropy')
        return core
    def word(core,name):
        return int.from_bytes(core.state()[symbols[name]-core.start:symbols[name]-core.start+2],'big')
    def draw(core,index):
        policy = core.state()[symbols['game_entropy_policy']-core.start]
        low_bit = word(core,'game_entropy_state') & 1
        core.cpu.w_sr(0x2700 | (index & 31))
        core.call('native_entropy_bit',{register:(index*65537 ^ register*0x1010101 ^ 0xa55a965a)
                                       & 0xffffffff for register in range(15)})
        observed_cycles['legacy' if policy else 'modern'][str(low_bit)] = core.last_cycles
        return word(core,'game_entropy_state'),core.cpu.r_reg(0)
    for seed,expected in ((1,(0xb400,1)),(2,(1,0)),(0xace1,ANSWERS[0])):
        with initialized(seed,0) as core:
            assert draw(core,seed) == expected, ('known answer',seed)
            core.audit_reads()
    with initialized(0xace1,0) as core:
        for index,expected in enumerate(ANSWERS):
            assert draw(core,index) == expected, ('sequence',index,expected)
        core.audit_reads()
    with initialized(0xace1,0) as core:
        seen = set()
        for index in range(65535):
            value,bit = draw(core,index)
            assert value and value not in seen, ('period',index,value)
            assert bit in (0,1)
            seen.add(value)
        assert value == 0xace1 and len(seen) == 65535
        core.audit_reads()
    with initialized(0xace1,1) as core:
        for index,expected in enumerate(ANSWERS):
            value,bit = draw(core,index)
            assert (value,bit) == (expected[0],0), ('legacy shadow',index)
            assert word(core,'game_legacy_entropy_state') == 0xace1 >> (index+1)
        modern,legacy = word(core,'game_entropy_state'),word(core,'game_legacy_entropy_state')
        # Pausing playback does not end automatic historical continuation.
        core.call_logical('game_core_sample_result',[0,0,255,0,0,0])
        assert core.state()[symbols['game_entropy_policy']-core.start] == 1
        # A retained PLAYING fixture establishes a logical takeover boundary.
        # This is a separate initial-once fixture, never an intermediate restore.
        initial = bytearray(core.state())
    life = symbols['game_lifecycle']-symbols['game_core_state']
    takeover_cycles = {}
    for lifecycle in (1,3,4,5):
        initial[life:life+2] = lifecycle.to_bytes(2,'big')
        with Core(image,symbols,initial=initial) as core:
            core.call_logical('game_core_sample_result',[0,0,0,0,0,0])
            takeover_cycles[str(lifecycle)] = core.last_cycles
            assert core.state()[symbols['game_entropy_policy']-core.start] == 0
            assert (word(core,'game_entropy_state'),word(core,'game_legacy_entropy_state')) == (modern,legacy)
            expected = (modern >> 1) ^ (0xb400 if modern & 1 else 0)
            assert draw(core,1) == (expected,modern & 1)
            assert word(core,'game_legacy_entropy_state') == legacy
            core.audit_reads()
    # Actual title command clears automatic continuation before metadata.
    with initialized(0xace1,1) as core:
        core.call_logical('game_core_sample_result',[0,0,255,255,0,0])
        core.call_logical('game_core_return_title',[])
        core.clear_events()
        core.call_logical('game_core_sample_result',[0,0,0,0,0,0])
        assert core.state()[symbols['game_entropy_policy']-core.start] == 1
        assert core.events == []
        core.audit_reads()
    with Core(image,symbols) as core:
        core.call_logical('game_core_init',[])
        core.call_logical('game_core_select',[0,0,0])
        selection_cycles = core.last_cycles
        assert word(core,'game_match_seed') == 0xace1
        core.call('game_core_seed_entropy')
        assert (word(core,'game_entropy_state'),word(core,'game_legacy_entropy_state')) == (0xace1,0xace1)
        assert draw(core,0) == ANSWERS[0]
        before = core.state()
        core.call('game_core_select',{0:0,1:123,2:2})
        assert core.state() == before, 'Unsupported policy changes canonical state'
        core.audit_reads()
    return {'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
            'state_bytes':size,'period':65535,'known_answer_draws':len(ANSWERS),
            'legacy_shadow_and_takeover':True,'zero_seed_maps_to':0xace1,
            'isolated_cpu_cycles':{'entropy_by_policy_and_modern_low_bit':observed_cycles,
                'zero_seed_selection':selection_cycles,'logical_takeover_sample':takeover_cycles},
            'cycle_scope':'Finite actual 68000 calls; includes harness return trap; no Amiga bus-contention or worst-bound claim'}


if __name__ == '__main__':
    paths = (ROOT/'build/amiga/interfaces/enhanced/baseline-rally',ROOT/'build/standalone/match-core')
    output = ROOT/'build/tests/core-entropy/report.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'passed':False,'state':'incomplete'})+'\n')
    result = {'passed':True,'algorithm':'galois16-b400-v2',
              'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'images':{str(path.relative_to(ROOT)):check(path) for path in paths}}
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
