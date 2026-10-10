"""Actual-68000 root top-up boundary fixtures; timer/beam ABI sinks explicit.

No native elapsed-time claim: physical acceptance uses run_topup_matched.py.
Complete owner states and output order are compared to actual PR48 public calls.
"""
import hashlib,json
from pathlib import Path
from build_match_core import load_image
from run_coherent_classifier_cpu import seed
from coherent_scheduler_proof import raw_json,cursors
from history_proof import field
from match_core_cpu import Core,cpu_tool_inputs
from run_shared_match_core import READONLY

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/tests/topup-cpu'/__import__('uuid').uuid4().hex;OUT.mkdir(parents=True,exist_ok=False)
paths={'original':ROOT/'build/tests/bounded-topup-pr48/baseline-rally',
       'reference':ROOT/'build/tests/topup-padded-pr48/baseline-rally',
       'candidate':ROOT/'build/amiga/interfaces/enhanced/baseline-rally'}
seeds={name:seed(path) for name,path in paths.items()}

def trial(label,variant,phase,budget,condition,expected,poison):
    image,s,initial,owned,generation=seeds[label]
    readonly=dict(READONLY,keyboard_ack=1,blank_seen=1,simulation_interval=4,
                  simulation_interval_whole=4,simulation_started_updates=2)
    with Core(image,s,initial=initial,poison=poison,readonly=readonly) as c:
        for address,data in owned:c.mem.w_block(address,data)
        for name,size in (('tutorial_state',s['tutorial_state_end']-s['tutorial_state']),
                          ('simulation_phase',4),('last_timer_count',4)):
            c.mutable_regions.append((s[name],s[name]+size))
        c.mem.w_block(s['tutorial_state'],bytes(s['tutorial_state_end']-s['tutorial_state']))
        def write(name,width,value):c.mem.w_block(s[name],value.to_bytes(width,'big'))
        # One declared initial scheduler/preview metadata fixture. No state is
        # fed back after execution starts. Private318 comes from actual APIs.
        for name,width,value in (('tutorial_generation',4,generation),('tutorial_presentation_generation',4,generation),
            ('tutorial_job_variant',2,variant),('tutorial_active_variant',1,variant),
            ('tutorial_job_budget',2,budget),('tutorial_job_cost',4,budget*1000),
            ('tutorial_batch_remaining',2,4-budget),('simulation_interval',4,20000),
            ('simulation_interval_whole',4,20000),('simulation_phase',4,0),
            ('last_timer_count',4,100000),('blank_seen',1,0),('keyboard_ack',1,0),
            ('simulation_started_updates',2,2),('game_preview_status',2,3)):
            if name in s:write(name,width,value)
        c.mem.w_block(s['game_preview_stream_cursors']+variant*8,c.mem.r_block(s['game_history_cursor'],8))
        c.mem.w16(s['game_preview_synthetic_phases']+variant*2,phase)
        c.mem.w_block(s['game_preview_launches'],bytes(2))
        c.mem.w_block(s['game_preview_outcomes'],bytes(4))
        c.mem.w_block(s['game_preview_endpoint_ready'],bytes(2))
        changes={'ack':('keyboard_ack',1,1),'stale-generation':('tutorial_generation',4,generation-1),
            'stale-presentation':('tutorial_presentation_generation',4,generation-1),
            'residual':('tutorial_batch_remaining',2,0),'other-selected':('tutorial_active_variant',1,1-variant),
            'producer':('tutorial_placement_dirty',1,1),'menu':('tutorial_menu',1,1),
            'slack':('simulation_phase',4,17000),'latch':('blank_seen',1,1)}
        if condition in changes and changes[condition][0] in s:write(*changes[condition])
        if condition=='ready':c.mem.w8(s['game_preview_endpoint_ready']+variant,255)
        if condition=='animation':
            write('tutorial_animation_ready',1,1);c.mem.w16(s['tutorial_counts']+variant*2,2)
        def sink(name,action):
            def invoke(opcode,pc):
                action();sp=c.cpu.r_sp();target=c.mem.cpu_r32(sp);c.cpu.w_sp(sp+4);c.cpu.w_pc(target)
            c._trap(s[name],invoke)
        # Only hardware reads are replaced; actual account/admission execute.
        sink('read_sim_timer',lambda:c.cpu.w_reg(0,c.mem.r32(s['last_timer_count'])-100))
        sink('read_presentation_line',lambda:c.cpu.w_reg(0,100))
        frozen={n:bytes(c.mem.r_block(s[n],s[e]-s[n])) for n,e in (
            ('game_core_state','game_core_state_end'),('game_history_state','game_history_state_end'),('game_history_buffer','game_history_buffer_end'))}
        c.clear_events();before=cursors(c,variant);body_rows=[];pending=None
        bodies={s[n]:n for n in ('game_round_poll_body','game_core_sample_pads_body',
            'game_core_sample_result_body','game_preview_dispatch','game_ball_tick')}
        oldtrace=c.trace
        def guard(mode,width,address,value):
            size=1<<width
            if c.mem.r8(s['game_preview_active']) and address<c.stop and address+size>c.start:
                raise AssertionError('Private owner accessed canonical318')
            if mode=='W' and address<s['game_history_buffer_end'] and address+size>s['game_history_buffer']:
                raise AssertionError('Frozen history write')
            oldtrace(mode,width,address,value)
        c.mem.set_trace_func(guard)
        def observe(pc):
            nonlocal pending
            c.instruction(pc)
            if pending and pc==pending['return'] and c.cpu.r_sp()==pending['sp']+4:
                body_rows.append(dict(operation=pending['name'],full=c.working_state().hex(),events=c.preview_events[pending['events']:]))
                pending=None
            if pending is None and pc in bodies:
                pending=dict(name=bodies[pc],sp=c.cpu.r_sp(),events=len(c.preview_events),return_=0)
                pending['return']=c.mem.r32(pending['sp'])
        c.cpu.set_instr_hook_callback(observe)
        regs={0:generation,1:budget if label=='candidate' else expected,2:variant}
        preserved={r:c.cpu.r_reg(r) for r in range(3,8)}|{r:c.cpu.r_reg(r) for r in range(10,15)}
        cycles=c.call('game_preview_step_coherent' if label=='candidate' else 'game_preview_step_variant',regs)
        assert c.cpu.r_reg(0)==1
        assert all(c.cpu.r_reg(r)==v for r,v in preserved.items()),'Worker register changed'
        assert not field(c,'game_preview_active',1) and not field(c,'game_preview_explicit')
        assert all(bytes(c.mem.r_block(s[n],len(data)))==data for n,data in frozen.items())
        c.audit_reads()
        result=dict(owners=[bytes(c.mem.r_block(s[n],318)).hex() for n in ('game_preview_held_state','game_preview_released_state')],
            paths=bytes(c.mem.r_block(s['game_preview_paths'],2*513*8)).hex(),
            counts=bytes(c.mem.r_block(s['game_preview_counts'],4)).hex(),
            outcomes=bytes(c.mem.r_block(s['game_preview_outcomes'],4)).hex(),
            before=before,after=cursors(c,variant),events=c.preview_events,bodies=body_rows,status=field(c,'game_preview_status'))
        return result,dict(cycles_with_hardware_sinks=cycles,stack=c.stack_bytes,
            cumulative_budget=field(c,'tutorial_job_budget'),remaining=field(c,'game_preview_budget'),cost=field(c,'tutorial_job_cost',4))

rows=[]
descriptors=[(0,3,'allow',4),(1,2,'allow',3),(2,1,'allow',2),(3,1,'allow',1),(0,2,'allow',2),(0,4,'allow',4)]
descriptors +=[(0,3,c,3) for c in ('ack','stale-generation','stale-presentation','residual','other-selected','producer','menu','slack','latch','ready','animation')]
try:
    for variant in (0,1):
        for phase,budget,condition,expected in descriptors:
            label=f'v{variant}-p{phase}-b{budget}-{condition}'
            results={};costs={}
            for index,name in enumerate(paths):results[name],costs[name]=trial(name,variant,phase,budget,condition,expected,0xa5 if index==0 else 0x96)
            raw_json(OUT/label,dict(results=results,costs=costs))
            assert results['original']==results['reference']==results['candidate'],label
            rows.append(dict(label=label,passed=True,expected_operations=expected,costs=costs))
    tools,cpu=cpu_tool_inputs()
    report=dict(passed=True,cases=rows,products={n:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for n,p in paths.items()},tools={str(p):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in tools},cpu=cpu,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Declared one-time API fixtures; actual logical bodies/state/cursors/output order and owner isolation. Hardware timer/beam ABI sinks, no native elapsed-time or routing acceptance.')
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))
except BaseException as error:
    (OUT/'failure.json').write_text(json.dumps(dict(error=str(error),completed=rows),indent=2)+'\n');raise
