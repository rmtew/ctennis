#!/usr/bin/env python3
"""Actual old/new 68000 font and footer comparison; never builds or boots.

CPU cycles include harness return-trap overhead. They are measured instruction
costs, not Amiga elapsed-time or DMA bounds. Oracle is an independent retained
pre-staging native executable, not a Python renderer or rebuilt old source.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from build_match_core import load_image
from match_core_cpu import Core, cpu_tool_inputs, STACK_TOP
from native_evidence import ReportRun, snapshot, digest, atomic_json, python_inputs, ROOT

FROZEN_SHA = '0999288675e9d201f3dda8add25732b326995d0ae59692fa58c68bb53b564dfa'
FIXTURE = 0x180000


def machine(path, poison=0xa5):
    image, symbols = load_image(path)
    core = Core(image + [(FIXTURE, bytes(65536))], symbols,
                initial=bytes(symbols['game_core_state_end']-symbols['game_core_state']),poison=poison)
    core.mutable_regions += [(symbols['tutorial_state'], symbols['tutorial_state_end']),
                             (FIXTURE, FIXTURE+65536)]
    core.mem.w_block(symbols['tutorial_state'], bytes(symbols['tutorial_state_end']-symbols['tutorial_state']))
    core.mem.w_block(symbols['game_preview_storage'], bytes(symbols['game_preview_storage_end']-symbols['game_preview_storage']))
    core.mem.w_block(symbols['tutorial_footer_scratch'],bytes([poison])*512)
    return core


def put(core, fields):
    for name, (width, value) in fields.items():
        core.mem.w_block(core.symbols[name], value.to_bytes(width, 'big'))


def data(core, name, size):
    return bytes(core.mem.r_block(core.symbols[name], size))


def audit_footer_writes(core):
    s=core.symbols
    allowed=set(range(s['tutorial_footer_scratch'],s['tutorial_footer_scratch']+512))
    allowed.update(range(s['tutorial_footer_first'],s['tutorial_footer_second']+4))
    allowed.update(range(s['tutorial_footer_ready'],s['tutorial_footer_ready']+2))
    allowed.update(range(s['tutorial_footer_stage'],s['tutorial_footer_scratch']))
    assert core.writes <= allowed, 'Footer wrote outside scratch and ownership metadata'


def run_steps(core):
    cycles, steps = [], []
    live = data(core, 'ui_overlay_plane', 512)
    core_before = data(core, 'game_core_state', core.stop-core.start)
    for _ in range(80):
        glyph = core.symbols['ui_text_character']; before = core.visits.get(glyph, 0)
        preserved = {i: core.cpu.r_reg(i) for i in range(1, 15)}
        stage = int.from_bytes(data(core, 'tutorial_footer_stage', 2), 'big')
        core.writes.clear();core.stack_low=STACK_TOP
        cycles.append(core.call('tutorial_footer_step'))
        audit_footer_writes(core)
        assert all(core.cpu.r_reg(i) == value for i, value in preserved.items()), 'Step changed caller registers'
        assert core.visits.get(glyph, 0)-before <= 2, 'Step exceeded two actual glyph calls'
        assert data(core, 'ui_overlay_plane', 512) == live, 'Partial renderer changed live overlay'
        assert data(core, 'game_core_state', core.stop-core.start) == core_before, 'Renderer changed simulation'
        assert data(core, 'tutorial_footer_ready', 2) == bytes(2), 'Renderer marked partial ready'
        complete = core.cpu.r_reg(0)
        assert complete in (0, 1)
        steps.append(dict(stage_before=stage,cycles=cycles[-1],complete=complete,written_bytes=len(core.writes),stack_bytes=STACK_TOP-core.stack_low))
        if complete:
            assert data(core, 'tutorial_footer_stage', 2) == bytes(2)
            return steps
        assert data(core, 'tutorial_footer_first', 8) == bytes(8), 'Partial cache claims completion'
    raise AssertionError('Footer failed finite completion extent')


def proof(original, current):
    assert hashlib.sha256(original.read_bytes()).hexdigest() == FROZEN_SHA, 'Independent oracle bytes changed'
    cpu_tool_inputs()
    rows = []
    # Entire printable ASCII alphabet, empty/exact-32/overlong and both font modes.
    strings = [b'', b'A', b'X'*28, b'X'*32, b'X'*33]
    strings += [bytes(range(start, min(start+32,127))) for start in range(32,127,32)]
    for lifecycle in (0, 2):
        for entry in ('ui_footer_text','ui_footer_selected','ui_text','ui_selected_text'):
            for index, text in enumerate(strings):
                outputs=[]
                for path in (original,current):
                    core=machine(path)
                    put(core,dict(game_lifecycle=(2,lifecycle)))
                    core.mem.w_block(FIXTURE,text+b'\0')
                    core.mem.w_block(FIXTURE+256,bytes([0x5a])*24576)
                    core.call(entry,{8:FIXTURE,10:FIXTURE+256,4:0 if 'footer' in entry else 1})
                    outputs.append(bytes(core.mem.r_block(FIXTURE+256,24576)))
                    cycles=core.last_cycles
                assert outputs[0] == outputs[1], f'Actual font mismatch {entry}/{index}/{lifecycle}'
                rows.append(dict(kind='font',entry=entry,length=len(text),lifecycle=lifecycle,cycles=cycles,original_sha256=hashlib.sha256(outputs[0]).hexdigest(),current_sha256=hashlib.sha256(outputs[1]).hexdigest()))
    cases = [dict(tutorial_menu=(1,1),tutorial_menu_selection=(1,i)) for i in range(3)]
    cases += [dict(tutorial_status=(2,5)),dict(tutorial_waiting_ready=(1,255)),{}]
    for source in (0,1):
        for variant in (0,1):
            for outcome in range(8):
                fields = dict(tutorial_placement_ready=(1,255),tutorial_input_source=(1,source),tutorial_active_variant=(1,variant),tutorial_available_outcomes=(4,0x10001),tutorial_outcomes=(4,outcome << (16 if variant==0 else 0)))
                cases.append(fields)
    # Actual released serve-wait selector path, both player ends.
    for end in (0,1):
        cases.append(dict(tutorial_placement_ready=(1,255),tutorial_active_variant=(1,1),tutorial_available_outcomes=(4,0x10001),tutorial_outcomes=(4,1),tutorial_end=(1,end),game_preview_ordinal=(2,65535),game_preview_status=(2,3),game_preview_primed_mask=(2,2),game_preview_dispatches=(4,1),game_preview_released_state=(1,0)))
    for index, fields in enumerate(cases):
        outputs=[]
        for path in (original,current):
            core=machine(path,poison=0x5a if path==original else 0xa5)
            # Named fixture initialization only; actual selector determines output.
            put(core,fields)
            if 'game_preview_ordinal' in fields:
                phase='game_upper_phase' if fields['tutorial_end'][1] else 'game_lower_phase'
                core.mem.w8(core.symbols['game_preview_released_state']+core.symbols[phase]-core.start,0x40)
            if path==original:
                core.call('tutorial_footer');old_stack=STACK_TOP-core.stack_low;old_cycles=core.last_cycles
            else:steps=run_steps(core)
            outputs.append(data(core,'tutorial_footer_scratch',512))
        assert outputs[0]==outputs[1], f'Caption mismatch {index}'
        # Fresh synchronous invocation must agree, including its saved ABI.
        synchronous=machine(current,poison=0x33);put(synchronous,fields)
        if 'game_preview_ordinal' in fields:
            phase='game_upper_phase' if fields['tutorial_end'][1] else 'game_lower_phase'
            synchronous.mem.w8(synchronous.symbols['game_preview_released_state']+synchronous.symbols[phase]-synchronous.start,0x40)
        synchronous.writes.clear();synchronous.call('tutorial_footer');audit_footer_writes(synchronous)
        assert data(synchronous,'tutorial_footer_scratch',512)==outputs[0],'Synchronous staged ABI mismatch'
        rows.append(dict(kind='caption',case=index,steps=steps,original_bytes=outputs[0].hex(),current_bytes=outputs[1].hex(),old_sync_cycles=old_cycles,old_sync_stack_bytes=old_stack,sync_cycles=synchronous.last_cycles,sync_stack_bytes=STACK_TOP-synchronous.stack_low,sha256=hashlib.sha256(outputs[1]).hexdigest()))
    for change in ('caption','generation','cancel','mixed','completed-caption','completed-generation'):
        new=machine(current);new.call('tutorial_footer_step');new.call('tutorial_footer_step')
        assert new.cpu.r_reg(0)==0
        if change.startswith('completed-'):run_steps(new)
        fields = dict(tutorial_menu=(1,1),tutorial_menu_selection=(1,2)) if 'caption' in change else dict(tutorial_generation=(4,1)) if 'generation' in change else {}
        put(new,fields)
        if change=='cancel':new.call('tutorial_footer_invalidate')
        if change=='mixed':
            new.writes.clear();new.call('tutorial_footer');audit_footer_writes(new)
            actual=data(new,'tutorial_footer_scratch',512)
            old=machine(original);old.call('tutorial_footer')
            assert actual==data(old,'tutorial_footer_scratch',512),'Mixed synchronous/cooperative caption mismatch'
            rows.append(dict(kind='mixed'));continue
        new.call('tutorial_footer_step')
        assert new.cpu.r_reg(0)==0 and data(new,'tutorial_footer_scratch',512)==bytes(512), 'Stale partial stage not restarted'
        steps=run_steps(new)
        actual=data(new,'tutorial_footer_scratch',512)
        old=machine(original);put(old,fields);old.call('tutorial_footer')
        assert actual==data(old,'tutorial_footer_scratch',512), 'Restart differs from actual old renderer'
        rows.append(dict(kind='restart',change=change,steps=steps))
    maximum=max(step['cycles'] for row in rows for step in row.get('steps',[]))
    return dict(passed=True,execution='actual-native-68000-cpu',oracle_sha256=FROZEN_SHA,current_sha256=hashlib.sha256(current.read_bytes()).hexdigest(),maximum_step_cpu_cycles=maximum,ownership_metadata_bytes=22,write_audit='Only private512 payload, completed caption pointers, ready flag and22 ownership bytes; stack audited separately',rows=rows,scope='Finite fixtures and CPU cycles; no Amiga wall-clock, IRQ, beam, DMA or worst-case bound')


def main():
    p=argparse.ArgumentParser();p.add_argument('--original',type=Path,required=True);p.add_argument('--current',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    transaction=ReportRun([a.output],'native-footer-cpu','coherent-footer','Actual retained old/new native code; CPU only')
    try:
        cpu_paths,cpu_info=cpu_tool_inputs()
        manifests=[]
        bound=set(cpu_paths)|python_inputs(Path(__file__))
        for executable in (a.original,a.current):
            manifest_path=Path(str(executable)+'.compile.json');listing=executable.parent/'native.lst'
            manifest=json.loads(manifest_path.read_text())
            assert manifest['executable_sha256']==digest(executable),'Executable differs from compiled manifest'
            assert digest(listing) in [sha for name,sha in manifest['files'].items() if name.endswith('/native.lst')],'Listing differs from compiled manifest'
            bound.update((executable,manifest_path,listing))
            if executable==a.current:manifests.append(manifest)
        transaction.meta.update(files=snapshot(bound),tools=dict(machine68k=cpu_info),
            commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            execution_scope='CPU only; no hardware beam/DMA execution')
        result=proof(a.original,a.current)
        result['executable_sha256']=result['current_sha256']
        raw=a.output.parent/'actual-font-comparison.json';atomic_json(raw,result.pop('rows'))
        result['capture']=str(raw.absolute());result['capture_sha256']=digest(raw)
        transaction.finalize(a.output,result,compiled=manifests,artifacts=[raw])
        print(json.dumps(result))
    except BaseException as error:
        transaction.abort(error);raise

if __name__=='__main__':main()
