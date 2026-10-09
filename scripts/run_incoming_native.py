"""Finite incoming/contact/outgoing physical latency and sprite probe.

Runs the current manifest-bound product; initializes no intermediate state.
Normal physical play supplies the opponent launch, then freezes via controls.
"""
import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

from native_evidence import ReportRun, TARGET, atomic_json, digest, inputs_for, snapshot
from native_hunk import loaded_hunks
from native_tools import ROOT, emulator_config
from run_tutorial_capture import FIELDS
from tutorial_capture import CaptureSession, CallbackObserver, SurfaceObserver
from tutorial_latency import LatencyObserver, StackTiming, instruction_map

from native_metrics import memory_summary
from ordinary_cadence import chip_memory
PROVIDER_CLOCK = 3546895
CLOCKS = {'PAL':3546895, 'NTSC':3579545}
CAPS = dict(physical_seconds=30, callbacks=2048, boundary_stops=8192,
            uncompressed_transcript_bytes=512*1024*1024)


class LatencySession(CaptureSession):
    MAX_RAW_BYTES = CAPS['uncompressed_transcript_bytes']


def run(standard='PAL', baseline=None):
    assert standard in CLOCKS
    directory = ROOT/'build/tests'/('incoming-flight-native-'+standard.lower())
    directory.mkdir(parents=True, exist_ok=True)
    output = directory/'report.json'
    transaction = ReportRun([output], 'native-feedback', 'maintained-native',
                            'Current native product; fixed incoming, physical edit/publication and looping normal sprites')
    try:
        baseline = Path(baseline) if baseline else ROOT/'build/amiga/interfaces/enhanced'
        executable, listing_path, manifest_path = [baseline/n for n in (
            'baseline-rally','native.lst','baseline-rally.compile.json')]
        product_sha256 = digest(executable)
        manifest = json.loads(manifest_path.read_text())
        assert manifest['executable_sha256'] == product_sha256
        listing_hashes=[sha for name,sha in manifest['files'].items() if name.endswith('/native.lst')]
        assert listing_hashes==[digest(listing_path)], 'Retained listing is not manifest-bound'
        paths, tools = inputs_for('native-feedback','scripts/run_incoming_native.py')
        transaction.meta.update(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                                native_product_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                                files=snapshot(set(paths)|{executable,listing_path,manifest_path}),
                                tools=tools, runner='scripts/run_incoming_native.py',
                                actual_target=dict(TARGET, video=standard),
                                target_role='legacy-validator-reference',
                                target_scope='evidence.target is a PAL compatibility reference; report.target and actual_target bind executed region')
        listing = listing_path.read_text()
        config = emulator_config()
        boundaries, actions, endpoints = [], [], []
        frozen = None
        with LatencySession(directory) as session:
            session.inspect('session_launch', dict(binary=config['tools']['copperline'],
                run=str(executable), args=['--chipset','OCS','--video',standard,
                    '--cpu','68000','--chip','512K','--slow','0','--fast','0',
                    '--noaudio',config['inputs']['amiga_rom']]))
            stop = session.inspect('run_until',dict(seconds=30))
            assert stop['reason'] == 'loadseg'
            segments = session.inspect('segments.list')['current']
            symbols = {n:segments[int(h)]['start']+int(o,16) for n,h,o in re.findall(
                r'^([A-Za-z_]\w*)\s+(\d\d):([\da-fA-F]{8})\s*$',listing,re.M)}
            def read(a,n):
                return bytes.fromhex(session.inspect('mem_read',dict(addr=a,len=n))['data'])
            def block(n,width):return read(symbols[n],width)
            def number(n,width=None):
                return int.from_bytes(block(n,FIELDS.get(n,2) if width is None else width),'big')
            loaded = loaded_hunks(executable,segments,read)
            calls, returns = instruction_map(listing,segments,read)
            simulation_calls=[pc for pc,c in calls.items() if c['callee']=='simulation_update']
            assert len(simulation_calls)==1
            probe_symbols=dict(title_copper=symbols['title_copper'],simulation_update_call_pc=simulation_calls[0],simulation_update=symbols['simulation_update'])
            callbacks = CallbackObserver(0,symbols)
            fields = dict(FIELDS,last_timer_count=4,simulation_phase=4,simulation_interval=4,game_title_display=1)
            callbacks.surfaces = SurfaceObserver(symbols,read,
                last_line=311 if standard=='PAL' else 261, verify_sprites=True)
            timing = StackTiming(calls,returns,symbols['game_stack_bottom'],symbols['game_stack_top'])
            session.observer = LatencyObserver(callbacks,timing)
            watches = callbacks.watches(fields,read)+callbacks.surfaces.watches()+[
                dict(addr=symbols['game_stack_bottom'],
                     len=symbols['game_stack_top']-symbols['game_stack_bottom'],access=access) for access in ('read','write')]+[
                dict(addr=a,len=1,access='read') for a in (0xbfd400,0xbfd500,0xbfd600,0xbfd700)]
            subscribed = session.inspect('events.subscribe',dict(events=['mmio','frame'],mmio=watches))
            assert subscribed.get('dropped_notifications',0)==0
            session.inspect('break_add',dict(kind='pc',addr=symbols['simulation_update']))
            origin = stop['cck']
            def position():
                return dict(cck=stop['cck'], frame=stop['frame'],
                    provider_seconds=stop['seconds'],
                    physical_seconds=(stop['cck']-origin)/CLOCKS[standard])
            def advance(seconds):
                nonlocal stop,frozen
                goal = stop['cck']+math.ceil(seconds*CLOCKS[standard])
                assert (goal-origin)/CLOCKS[standard] <= CAPS['physical_seconds']
                for _ in range(CAPS['boundary_stops']):
                    stop=session.inspect('run_until',dict(seconds=goal/PROVIDER_CLOCK))
                    if stop.get('pc')==symbols['simulation_update']:
                        assert callbacks.pending is None
                        assert callbacks.completed <= CAPS['callbacks']
                        states=tuple(block(n,w) for n,w in (
                            ('game_core_state',318),('game_history_state',72),
                            ('tutorial_interrupted_state',318)))
                        fields={n:number(n) for n in FIELDS}
                        if fields['tutorial_active']:
                            if frozen is None:frozen=states
                            assert states==frozen, 'Frozen selected318/history72/livebackup changed'
                        boundaries.append(dict(position=position(), fields=fields,
                            state=states[0].hex(),history=states[1].hex(),backup=states[2].hex()))
                    if stop.get('reason')=='target' or stop['cck']>=goal:break
                else:raise AssertionError('Latency complete-boundary stop cap')
            def key(code,held,seconds=.06):
                actions.append(dict(rawkey=code,held=held,position=position()))
                session.inspect('input_key',dict(rawkey=code,action='press' if held else 'release'))
                advance(seconds)
            def endpoint(label, previous_generation=None, request=None):
                request=position() if request is None else request
                for _ in range(300):
                    advance(.05)
                    generation=number('tutorial_generation',4)
                    published=[p for p in callbacks.surfaces.publications
                        if p['position']['cck']>=request['cck']
                        and p['tutorial_fields'].get('tutorial_generation')==generation
                        and p['tutorial_fields'].get('tutorial_marker_generation')==generation
                        and p['tutorial_fields'].get('tutorial_marker_ready')
                        and p['tutorial_fields'].get('tutorial_placement_ready')
                        and not p['tutorial_fields'].get('tutorial_placement_dirty')
                        and p['tutorial_fields'].get('tutorial_active_variant')==0
                        and p['tutorial_fields'].get('tutorial_ball_mode') in (1,2)
                        and p['tutorial_fields'].get('tutorial_available_outcomes',0)>>16]
                    if published and (previous_generation is None or generation!=previous_generation):
                        scene=published[0] # actual COPJMP, not a later animation/wait match
                        assert scene.get('native_sprite_check'), 'Endpoint sprite bank lacks actual check'
                        row=dict(label=label, request=request, observed=position(),
                            first_actual_publication=dict(scene),generation=generation,
                            latency_cck=scene['position']['cck']-request['cck'],
                            incoming_cursor=block('game_preview_incoming',8).hex(),
                            incoming_state_sha256=hashlib.sha256(block('game_preview_incoming_state',318)).hexdigest(),
                            counts=[int.from_bytes(block('game_preview_counts',4)[i:i+2],'big') for i in (0,2)],
                            outcomes=[int.from_bytes(block('game_preview_outcomes',4)[i:i+2],'big') for i in (0,2)],
                            incoming_dispatches=[int.from_bytes(block('game_preview_dispatches',4)[i:i+2],'big') for i in (0,2)],
                            outgoing_phases=[int.from_bytes(block('game_preview_flight_phases',4)[i:i+2],'big') for i in (0,2)])
                        # Negative latency means a stale already-published endpoint.
                        assert row['latency_cck']>=0
                        row['physical_latency_seconds']=row['latency_cck']/CLOCKS[standard]
                        endpoints.append(row)
                        return generation
                raise AssertionError('No actual fresh held endpoint within declared latency cap')
            advance(.3)
            for _ in range(100):
                if session.observer.title_ready:
                    break
                advance(.05)
            else:raise AssertionError('No actual native title publication before input')
            title_ready=dict(session.observer.title_ready)
            key(0x01,True);key(0x01,False)
            for _ in range(100):
                if number('game_lifecycle',2)==1 and not (number('game_mode',1)&0x80):
                    break
                advance(.05)
            else:raise AssertionError('One-player physical selection did not enter PLAYING')
            # Ordinary physical serve, then detect the actual receiving flight.
            key(0x23,True,.04);key(0x23,False,.02)
            for _ in range(200):
                if (number('game_contact',1)&0x40 and
                        number('game_flight',1)&0x40 and
                        not number('game_contact',1)&0x8d):
                    break
                advance(.02)
            else:raise AssertionError('No genuine opponent incoming launch under physical play')
            incoming_live=dict(position=position(),state=block('game_core_state',318).hex())
            key(0x24,True,.02);key(0x24,False,.02)
            key(0x24,True,.02);key(0x24,False,.02)
            assert number('tutorial_active')
            assert number('game_preview_ordinal',2)==0xfffe
            assert number('game_preview_kind',2)==0
            held_start=position()
            key(0x23,True) # F held; actual held alternative, not a supplied expected path.
            generation=endpoint('initial-held',request=held_start)
            previous_xy=(number('tutorial_x'),number('tutorial_y'))
            edit_start=position()
            key(0x22,True,.02);key(0x22,False,.001)
            assert (number('tutorial_x'),number('tutorial_y'))!=previous_xy
            endpoint('fresh-D-edit',generation,request=edit_start)
            endpoints[-1]['physical_input_request']=edit_start
            endpoints[-1]['input_to_publication_cck']=(
                endpoints[-1]['first_actual_publication']['position']['cck']-edit_start['cck'])
            endpoints[-1]['physical_input_latency_seconds']=(
                endpoints[-1]['input_to_publication_cck']/CLOCKS[standard])
            assert endpoints[0]['incoming_state_sha256']==endpoints[1]['incoming_state_sha256']
            assert endpoints[0]['incoming_cursor']==endpoints[1]['incoming_cursor']
            before_loop=len(callbacks.surfaces.publications)
            for _ in range(100):
                advance(.05)
                frames=callbacks.surfaces.publications[before_loop:]
                indices=[p.get('tutorial_fields',{}).get('tutorial_animation_index') for p in frames
                         if p.get('tutorial_fields',{}).get('tutorial_generation')==number('tutorial_generation',4)]
                if any(a is not None and b is not None and a>b for a,b in zip(indices,indices[1:])):
                    break
            else:raise AssertionError('Normal ball sequence did not repeat after terminal dwell')
            loop_frames=frames
            # Stop before the next real callback body, not inside an API.
            stop=session.inspect('run_until',dict(seconds=(stop['cck']+CLOCKS[standard]*.02)/PROVIDER_CLOCK))
            assert stop.get('pc')==symbols['simulation_update'] and callbacks.pending is None
            actual_video=[number('presentation_last_line',2),number('simulation_interval_whole',4),
                          number('simulation_interval_fraction',2)]
            assert actual_video == (
                        [311,11838,14906] if standard=='PAL' else [261,11947,13180]), 'Actual video selectors mismatch'
            interval=number('simulation_interval_whole',4)*65536+number('simulation_interval_fraction',2)
            callback_result=callbacks.result(interval)
            stack_result=timing.result()
            open_calls=stack_result['open_enclosing_calls']
            assert len(open_calls)==1 and open_calls[0]['callee']=='simulation_update'
            assert open_calls[0]['depth']==0 and open_calls[0]['caller'] is None
            assert open_calls[0]['entry_pc']==simulation_calls[0], 'Incomplete API/IRQ call at final boundary'
            assert open_calls[0]['entry_store_complete']['cck']<=stop['cck']
            final_stop=dict(stop)
            memory=memory_summary(chip_memory(read))
            assert any(r['category']=='public-preview' for r in stack_result['calls'])
            assert any(r['category']=='core-body' for r in stack_result['calls'])
            raw=dict(records=session.records,uncompressed_bytes=session.raw_bytes,
                     cap_uncompressed_bytes=session.MAX_RAW_BYTES)
        capture=directory/'latency.json'
        atomic_json(capture,dict(boundaries=boundaries,actions=actions,endpoints=endpoints,
            timing=callback_result,stack_timing=stack_result, loaded_hunks=loaded,title_ready=title_ready,probe_symbols=probe_symbols,final_stop=final_stop,
            call_map=calls, return_pcs=sorted(returns),literal_rpc=raw,
            timer_reads=session.observer.timer_reads,
            incoming_live=incoming_live, loop_frames=loop_frames, native_memory=memory,
            timer_scope='Read-only literal cascaded CIA counter reads with actual saved phase/interval/epoch; '
                        'admission declines require emitted control-flow interpretation, not inferred host decisions.'))
        report=dict(passed=True,subject='maintained-native',target=dict(TARGET,video=standard),
            executable_sha256=product_sha256, incoming_flight=True, endpoints=endpoints, native_memory=memory,
            repeated_sequence=True, loop_publications=len(loop_frames),
            capture=str(capture.relative_to(ROOT)),declared_caps=CAPS,
            timing=callback_result, full318_history72_backup_guard=True,
            frozen_boundaries=sum(bool(r['fields']['tutorial_active']) for r in boundaries),
            stack_protocol=stack_result['protocol'], dropped_notifications=callbacks.dropped,
            actual_video=actual_video,title_ready=title_ready,
            physical_clock_hz=CLOCKS[standard], provider_seconds_clock_hz=PROVIDER_CLOCK,
            scope='Current native physical incoming trial, changed placement, actual normal-sprite samples and repeat; '
                  'complete frozen318/history72/livebackup and finite timing. Full release/cold ADF acceptance remains pending.')
        atomic_json(directory/'results-unvalidated.json',report)
        artifacts=[p for p in directory.iterdir() if p.is_file() and p!=output]
        transaction.finalize(output,report,[manifest],artifacts)
    except BaseException as error:
        transaction.abort(error)
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--ntsc',action='store_true')
    parser.add_argument('--baseline',type=Path)
    args=parser.parse_args()
    run('NTSC' if args.ntsc else 'PAL',args.baseline)
