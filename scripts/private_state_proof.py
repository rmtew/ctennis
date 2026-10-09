"""Differential actual-68000 proof: old live, new live and two private owners.

No gameplay model or intermediate expected-state injection. Each context starts
with the real initializer and thereafter receives only declared logical inputs.
"""
from copy import deepcopy
import hashlib
from build_match_core import load_image
from match_core_cpu import Core
from run_shared_match_core import READONLY


def exercise(before,after,standalone,dispatches=512):
    assert 1<=dispatches<=512
    old_image,old_symbols=load_image(before)
    live_image,live_symbols=load_image(after)
    image,symbols=load_image(standalone)
    sequences=[]
    for mode,seed in ((0,0xace1),(1,0x3037)):
        sequence=[('game_core_init',[]),('game_core_select',[mode,seed,0])]
        for tick in range(dispatches):
            sequence.extend((('game_round_poll',[]),
                ('game_core_sample_pads',[(16 if tick%64>=8 else 0)|(8 if tick%96<48 else 4),
                                         (32 if tick%80>=7 else 0)|(4 if tick%112<56 else 8)]),
                ('game_core_sample_result',[0]*6),('game_tick_dispatch',[])))
        sequence.extend((('game_core_latch_actions',[]),('game_core_clear_inputs',[]),
            ('game_core_return_title',[]),('game_core_sample_result',[0]*6),
            ('game_round_poll',[]),('game_tick_dispatch',[])))
        sequences.append(sequence)
    references=[]
    public_a5_checks=0
    # machine68k owns one active CPU: finish each reference before constructing
    # the next machine. The private machine alone alternates its two owners.
    for context,sequence in enumerate(sequences):
        rows=[]
        with Core(old_image,old_symbols,poison=(0x3c,0x96)[context],readonly=READONLY,
                  state_base_register=None) as cpu:
            for name,args in sequence:
                cpu.clear_events();cpu.call_logical(name,args)
                rows.append((cpu.state(),deepcopy(cpu.events)))
            cpu.audit_reads()
        with Core(live_image,live_symbols,poison=(0xa5,0x69)[context],readonly=READONLY) as cpu:
            for index,(name,args) in enumerate(sequence):
                cpu.clear_events();cpu.call_logical(name,args)
                expected_a5=((cpu.logical_calls-1)*65537+13*0x1010101)^0x965aa569^cpu.context_seed
                assert cpu.cpu.r_reg(13)==expected_a5&0xffffffff
                assert (cpu.state(),cpu.events)==rows[index],('Live differential',context,index,name)
                public_a5_checks+=1
            cpu.audit_reads()
        references.append(rows)
    blocked_checks=0
    with Core(image,symbols,readonly=READONLY) as cpu:
        from history_proof import attach
        cpu.call_logical('game_core_init',[]);attach(cpu);cpu.call('game_history_freeze')
        frozen_state=cpu.state()
        for index,(name,args) in enumerate((sequences[0][0],sequences[0][1],
                sequences[0][2],sequences[0][3],sequences[0][4],sequences[0][5],
                *sequences[0][-6:-3])):
            sentinel=0x695a0000+index
            sr=0x2700|(index&31)
            cpu.cpu.w_sr(sr)
            registers={r:arg for r,arg in enumerate(args)};registers[13]=sentinel
            cpu.call(name,registers)
            assert cpu.state()==frozen_state and cpu.cpu.r_reg(13)==sentinel and cpu.cpu.r_sr()==sr
            blocked_checks+=1
        cpu.audit_reads()
    with Core(image,symbols,poison=0xc3,readonly=READONLY) as private:
        bases=[symbols['game_preview_selected_state'],symbols['game_preview_held_state']]
        size=private.stop-private.start
        for base,poison in zip(bases,(0x5a,0x96)):
            private.mem.w_block(base,bytes([poison])*size)
        canonical=private.state()
        canary_address=symbols['game_preview_edited_state']
        canary=bytes(private.mem.r_block(canary_address,size))
        owner=None
        original_trace=private.trace
        def guard(mode,width,address,value):
            extent=1<<width
            for low,high in [(private.start,private.stop),
                             *[(base,base+size) for base in bases],
                             (canary_address,canary_address+size)]:
                if address<high and address+extent>low:
                    assert owner is not None and bases[owner]<=address and address+extent<=bases[owner]+size, \
                        ('Cross-owner state access',mode,address,owner)
            original_trace(mode,width,address,value)
        private.mem.set_trace_func(guard)
        hashes=[hashlib.sha256(),hashlib.sha256()]
        maximum=[0,0];operations=[0,0];paths=[[],[]]
        for index in range(len(sequences[0])):
            for context in (0,1):
                name,args=sequences[context][index]
                previous=bytes(private.mem.r_block(bases[1-context],size))
                private.clear_events()
                for register in range(15):
                    private.cpu.w_reg(register,(index*65537^register*0x1010101^0x695aa596)&0xffffffff)
                private.cpu.w_sr(0x2700|(index&31))
                owner=context
                registers={r:(private.cpu.r_reg(r)&0xffff0000)|arg for r,arg in enumerate(args)}
                registers[13]=bases[context]
                cycles=private.call(name+'_body',registers)
                maximum[context]=max(maximum[context],cycles)
                assert private.cpu.r_reg(13)==bases[context], 'Body clobbers supplied A5'
                actual=bytes(private.mem.r_block(bases[context],size))
                assert actual==references[context][index][0],('Full state',context,index,name)
                assert private.events==references[context][index][1],('Ordered events',context,index,name)
                assert bytes(private.mem.r_block(bases[1-context],size))==previous
                assert private.state()==canonical and bytes(private.mem.r_block(canary_address,size))==canary
                hashes[context].update(actual)
                if name=='game_tick_dispatch':
                    from preview_proof import point
                    paths[context].append(point(actual,symbols))
                operations[context]+=1
        private.audit_reads()
        return dict(passed=True,operations=operations,state_bytes=size,
            alternating_private_bases=bases,canonical_and_other_owner_untouched=True,
            canary_untouched=True,public_a5_preserved=True,body_a5_preserved=True,
            public_a5_checks=public_a5_checks,blocked_a5_and_ccr_checks=blocked_checks,
            full_state_and_ordered_events_equal=True,
            state_trace_sha256=[h.hexdigest() for h in hashes],
            actual_projection_sha256=[hashlib.sha256(b''.join(p)).hexdigest() for p in paths],
            maximum_private_body_cpu_cycles=maximum,
            artifacts={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (before,after,standalone)},
            scope='Finite actual CPU one/two-player operations, including input edges, RNG, title and independently poisoned alternating private contexts; no Amiga deadline claim')
