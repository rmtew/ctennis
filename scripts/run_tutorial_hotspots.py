"""Bounded unchanged-product instruction/DMA hotspot probe. No build or screenshots."""
import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

from native_evidence import ReportRun, TARGET, atomic_json, digest, inputs_for, snapshot
from native_hunk import loaded_hunks,hunk_layout
from native_tools import ROOT, emulator_config
from run_tutorial_capture import FIELDS
from tutorial_capture import CaptureSession, CallbackObserver, SurfaceObserver
from tutorial_latency import LatencyObserver, instruction_map
from tutorial_hotspots import WorkerTiming, summarize_workers, summarize_profile

PRODUCT_SHA256 = '9bfd85797f8b3a997cff8fa1489be8bfdfca45a0396001935da019c3fc117454'
PROVIDER_CLOCK = 3546895
CLOCKS = {'PAL':3546895, 'NTSC':3579545}
CAPS = dict(physical_seconds=30, callbacks=1024, boundary_stops=4096, profile_frames=64,
            profile_bytes=32*1024*1024, uncompressed_transcript_bytes=64*1024*1024)


class LatencySession(CaptureSession):
    MAX_RAW_BYTES = CAPS['uncompressed_transcript_bytes']


def verified_code_range(executable,hunks):
    code=[row for row in hunk_layout(executable)['hunks'] if row['kind']=='code']
    assert len(code)==1 and code[0]['index']==0,'Expected one native code hunk0'
    loaded=[row for row in hunks if row['hunk']==0]
    assert len(loaded)==1 and loaded[0]['matched'] is True
    assert loaded[0]['bytes']==code[0]['bytes']
    assert isinstance(loaded[0].get('actual_sha256'),str) and re.fullmatch(r'[0-9a-f]{64}',loaded[0]['actual_sha256'])
    assert loaded[0]['actual_sha256']==loaded[0]['expected_sha256']
    assert type(loaded[0]['start']) is int and 0<loaded[0]['start']<=524288-loaded[0]['bytes']
    return dict(base=loaded[0]['start'],size=loaded[0]['bytes'])


def run(standard='PAL', baseline=None):
    assert standard in CLOCKS
    directory = ROOT/'build/tests'/('tutorial-hotspots-'+standard.lower())
    directory.mkdir(parents=True, exist_ok=True)
    output = directory/'report.json'
    transaction = ReportRun([output], 'native-feedback', 'maintained-native',
                            'Unchanged native product; physical fresh-edit landing latency only')
    try:
        baseline = Path(baseline) if baseline else ROOT/'build/tests/tutorial-court-pal'
        executable, listing_path, manifest_path = [baseline/n for n in (
            'baseline-rally','native.lst','baseline-rally.compile.json')]
        assert digest(executable) == PRODUCT_SHA256, 'Latency probe requires reviewed unchanged product'
        manifest = json.loads(manifest_path.read_text())
        assert manifest['executable_sha256'] == PRODUCT_SHA256
        listing_hashes=[sha for name,sha in manifest['files'].items() if name.endswith('/native.lst')]
        assert listing_hashes==[digest(listing_path)], 'Retained listing is not manifest-bound'
        paths, tools = inputs_for('native-feedback','scripts/run_tutorial_hotspots.py')
        transaction.meta.update(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                                native_product_commit='b1eb145c8417a54045b80f585b475f4f1f3665e3',
                                files=snapshot(set(paths)|{executable,listing_path,manifest_path}),
                                tools=tools, runner='scripts/run_tutorial_hotspots.py',
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
            code_range=verified_code_range(executable,loaded)
            calls, returns = instruction_map(listing,segments,read)
            simulation_calls=[pc for pc,c in calls.items() if c['callee']=='simulation_update']
            assert len(simulation_calls)==1
            probe_symbols=dict(title_copper=symbols['title_copper'],simulation_update_call_pc=simulation_calls[0],simulation_update=symbols['simulation_update'])
            callbacks = CallbackObserver(0,symbols)
            fields = dict(FIELDS,last_timer_count=4,simulation_phase=4,simulation_interval=4,game_title_display=1)
            callbacks.surfaces = SurfaceObserver(symbols,read,
                last_line=311 if standard=='PAL' else 261, verify_sprites=True)
            timing = WorkerTiming(calls,returns,symbols['game_stack_bottom'],symbols['game_stack_top'])
            timing.state=callbacks.state
            session.observer = LatencyObserver(callbacks,timing)
            all_watches = callbacks.watches(fields,read)+callbacks.surfaces.watches()
            watches = [w for w in all_watches if w['addr']!=symbols['game_stack_bottom']]
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
                assert sum(p.stat().st_size for p in directory.rglob('*') if p.is_file() and p.parent.name=='profile') <= CAPS['profile_bytes']
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
                for _ in range(40):
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
                        and p['tutorial_fields'].get('tutorial_ball_mode')==1]
                    if published and (previous_generation is None or generation!=previous_generation):
                        scene=published[0] # actual COPJMP, not a later animation/wait match
                        assert scene.get('native_sprite_check'), 'Endpoint sprite bank lacks actual check'
                        row=dict(label=label, request=request, observed=position(),
                            first_actual_publication=dict(scene),generation=generation,
                            latency_cck=scene['position']['cck']-request['cck'])
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
            advance(.1)
            key(0x24,True);key(0x24,False)
            key(0x24,True);key(0x24,False)
            assert number('tutorial_active')
            held_start=position()
            key(0x23,True) # F held; actual held alternative, not a supplied expected path.
            generation=endpoint('initial-held',request=held_start)
            previous_xy=(number('tutorial_x'),number('tutorial_y'))
            edit_start=position()
            subscribed=session.inspect('events.subscribe',dict(events=['mmio','frame'],mmio=all_watches+[
                # tutorial_tick preserves 15 registers (60 B) before the worker.
                # Exclude shallower busy-loop returns; every root slot is checked.
                dict(addr=symbols['game_stack_bottom'],len=timing.read_top-symbols['game_stack_bottom'],access='read')]))
            assert subscribed.get('dropped_notifications',0)==0
            profile_path=directory/'profile'
            profile_start=session.inspect('profile.start',dict(path=str(profile_path),
                frames=CAPS['profile_frames'],samples=True,registers=False,
                slots=False,memory=False,screenshots='none',
                relocation_bases=[s['start'] for s in segments],
                code_ranges=[code_range]))
            timing.active=True
            key(0x22,True,.02);key(0x22,False,.001)
            assert (number('tutorial_x'),number('tutorial_y'))!=previous_xy
            endpoint('fresh-D-edit',generation,request=edit_start)
            endpoints[-1]['physical_input_request']=edit_start
            endpoints[-1]['input_to_publication_cck']=(
                endpoints[-1]['first_actual_publication']['position']['cck']-edit_start['cck'])
            endpoints[-1]['physical_input_latency_seconds']=(
                endpoints[-1]['input_to_publication_cck']/CLOCKS[standard])
            advance(.08) # Commit at least two fields beyond the endpoint; stop discards pending tail.
            profile_stop=session.inspect('profile.stop')
            assert sum(p.stat().st_size for p in profile_path.iterdir() if p.is_file()) <= CAPS['profile_bytes']
            # Stop before the next real callback body, not inside an API.
            stop=session.inspect('run_until',dict(seconds=(stop['cck']+CLOCKS[standard]*.02)/PROVIDER_CLOCK))
            assert stop.get('pc')==symbols['simulation_update'] and callbacks.pending is None
            actual_video=[number('presentation_last_line',2),number('simulation_interval_whole',4),
                          number('simulation_interval_fraction',2)]
            assert actual_video == (
                        [311,11838,14906] if standard=='PAL' else [261,11947,13180]), 'Actual video selectors mismatch'
            interval=number('simulation_interval_whole',4)*65536+number('simulation_interval_fraction',2)
            callback_result=callbacks.result(interval)
            assert not timing.stack, 'Partial public worker at complete final boundary'
            stack_result=summarize_workers(timing.rows, endpoints[-1]['request']['cck'],
                endpoints[-1]['first_actual_publication']['position']['cck'],endpoints[-1]['generation'])
            final_stop=dict(stop)
            profile_result=summarize_profile(profile_path,listing,segments,code_range)
            assert profile_result['started']['seconds']<=edit_start['provider_seconds']
            assert profile_result['last_committed_frame']>=endpoints[-1]['first_actual_publication']['position']['frame']+2
            assert profile_result['frames']<CAPS['profile_frames'], 'Profile self-stop truncated the job'
            raw=dict(records=session.records,uncompressed_bytes=session.raw_bytes,
                     cap_uncompressed_bytes=session.MAX_RAW_BYTES)
        capture=directory/'hotspots.json'
        atomic_json(capture,dict(boundaries=boundaries,actions=actions,endpoints=endpoints,
            timing=callback_result,worker_timing=stack_result, profile=profile_result,profile_start=profile_start,profile_stop=profile_stop,loaded_hunks=loaded,code_range=code_range,title_ready=title_ready,probe_symbols=probe_symbols,final_stop=final_stop,
            call_map=calls, return_pcs=sorted(returns),literal_rpc=raw,
            admission_scope='No new CIA return-value ledger; current-product admission/wait costs use flat PC samples and complete callback spans.'))
        report=dict(passed=True,subject='maintained-native',target=dict(TARGET,video=standard),
            executable_sha256=PRODUCT_SHA256, landing_latency=True, endpoints=endpoints,
            capture=str(capture.relative_to(ROOT)),declared_caps=CAPS,
            timing=callback_result, full318_history72_backup_guard=True,
            frozen_boundaries=sum(bool(r['fields']['tutorial_active']) for r in boundaries),
            stack_protocol=stack_result['protocol'],profiling=True,profile_summary=profile_result, dropped_notifications=callbacks.dropped,
            stack_scope='Stack accesses observed only during fresh-edit profiling; startup stack usage unmeasured',
            actual_video=actual_video,title_ready=title_ready,
            physical_clock_hz=CLOCKS[standard], provider_seconds_clock_hz=PROVIDER_CLOCK,
            scope='Unchanged native executable; bounded fresh-edit instruction/DMA/worker profiling. '
                  'No screenshots, new trajectories, gameplay oracle or full tutorial acceptance.')
        atomic_json(directory/'results-unvalidated.json',report)
        artifacts=[p for p in directory.rglob('*') if p.is_file() and p!=output]
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
