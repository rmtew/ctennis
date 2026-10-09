"""Bounded read-only original/candidate native live-ball cost probe."""
import argparse
import os
import statistics
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

PRODUCTS = {'baseline':'9bfd85797f8b3a997cff8fa1489be8bfdfca45a0396001935da019c3fc117454',
            'candidate':'158f25910598de48ca266b9af459eda779cc3ccee3fac861e0690fb920e0698d'}
PROVIDER_CLOCK = 3546895
CLOCKS = {'PAL':3546895, 'NTSC':3579545}
CAPS = dict(physical_seconds=30, callbacks=2048, boundary_stops=8192,
            uncompressed_transcript_bytes=512*1024*1024)


class LatencySession(CaptureSession):
    MAX_RAW_BYTES = CAPS['uncompressed_transcript_bytes']


def run(standard='PAL', variant='candidate'):
    PRODUCT_SHA256 = PRODUCTS[variant]
    product_root = Path(os.environ['CTENNIS_RATIO32_BASELINE_ROOT']).resolve() if variant=='baseline' else ROOT
    assert standard in CLOCKS
    directory = ROOT/'build/tests'/('ratio32-live-'+variant+'-'+standard.lower())
    directory.mkdir(parents=True, exist_ok=True)
    output = directory/'report.json'
    transaction = ReportRun([output], 'native-feedback', 'maintained-native',
                            'Physical two-second live ball workload; original/candidate native product')
    try:
        baseline = product_root/'build/tests/tutorial-court-pal'
        executable, listing_path, manifest_path = [baseline/n for n in (
            'baseline-rally','native.lst','baseline-rally.compile.json')]
        assert digest(executable) == PRODUCT_SHA256, 'Latency probe requires reviewed unchanged product'
        manifest = json.loads(manifest_path.read_text())
        assert manifest['executable_sha256'] == PRODUCT_SHA256
        manifest['files'] = {str(product_root/name) if not Path(name).is_absolute() else name:sha for name,sha in manifest['files'].items()}
        manifest['executable'] = str(product_root/manifest['executable'])
        listing_hashes=[sha for name,sha in manifest['files'].items() if name.endswith('/native.lst')]
        assert listing_hashes==[digest(listing_path)], 'Retained listing is not manifest-bound'
        paths, tools = inputs_for('native-feedback','scripts/run_ratio32_native.py')
        transaction.meta.update(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                                native_product_commit=('5623420afbbcb347b823c09b0f8e94d601516e34' if variant=='baseline' else 'd6146ff696696aba5e7a466169ea01f1defcd75f'),
                                files=snapshot(set(paths)|{executable,listing_path,manifest_path}),
                                tools=tools, runner='scripts/run_ratio32_native.py',
                                actual_target=dict(TARGET, video=standard),
                                target_role='legacy-validator-reference',
                                target_scope='evidence.target is a PAL compatibility reference; report.target and actual_target bind executed region')
        transaction.meta['environment'].update(PYTHONPATH=os.environ.get('PYTHONPATH'), CTENNIS_RATIO32_BASELINE_ROOT=os.environ.get('CTENNIS_RATIO32_BASELINE_ROOT'))
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
            fields = dict(FIELDS,last_timer_count=4,simulation_phase=4,simulation_interval=4,game_title_display=1,game_lifecycle=2,game_flight=1,game_step=1)
            callbacks.surfaces = SurfaceObserver(symbols,read,
                last_line=311 if standard=='PAL' else 261, verify_sprites=True)
            timing = StackTiming(calls,returns,symbols['game_stack_bottom'],symbols['game_stack_top'])
            session.observer = LatencyObserver(callbacks,timing)
            watches = callbacks.watches(fields,read)+callbacks.surfaces.watches()+[
                dict(addr=symbols['game_stack_bottom'],
                     len=symbols['game_stack_top']-symbols['game_stack_bottom'],access='read')]+[
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
                        current_fields={n:number(n,width) for n,width in fields.items()}
                        if current_fields['tutorial_active']:
                            if frozen is None:frozen=states
                            assert states==frozen, 'Frozen selected318/history72/livebackup changed'
                        boundaries.append(dict(position=position(), fields=current_fields,
                            state=states[0].hex(),history=states[1].hex(),backup=states[2].hex()))
                    if stop.get('reason')=='target' or stop['cck']>=goal:break
                else:raise AssertionError('Latency complete-boundary stop cap')
            def key(code,held,seconds=.06):
                actions.append(dict(rawkey=code,held=held,position=position()))
                session.inspect('input_key',dict(rawkey=code,action='press' if held else 'release'))
                advance(seconds)
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
            rally_start=position()
            key(0x23,True,.5)
            key(0x23,False,1.5)
            rally_stop=position()
            assert any(row['fields']['game_flight']&64 for row in boundaries
                if rally_start['cck']<=row['position']['cck']<=rally_stop['cck']), 'Physical F never launched an active ball'
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
            entry='game_ratio' if variant=='baseline' else 'game_ratio32'
            ratio_calls=[r for r in stack_result['calls'] if r['callee']==entry and r['caller'] in ('game_displacement','game_advance_ball') and rally_start['cck']<=r['entry']['cck']<=r['exit']['cck']<=rally_stop['cck']]
            assert len(ratio_calls)>=3, 'No applicable live-ball ratio calls'
            live_callbacks=[r for r in callback_result['callbacks'] if rally_start['cck']<=r['entry']['cck']<=r['completion']['cck']<=rally_stop['cck'] and r['state'].get('game_lifecycle')==1]
            assert len(live_callbacks)>=30
            def summary(values):
                values=sorted(values)
                return dict(samples=len(values),minimum=min(values),median=statistics.median(values),p95=values[math.ceil(.95*len(values))-1],maximum=max(values))
            ratio_summary=summary([r['inclusive_bus_cck'] for r in ratio_calls])
            callback_summary=summary([r['work_cck'] for r in live_callbacks])
            raw=dict(records=session.records,uncompressed_bytes=session.raw_bytes,
                     cap_uncompressed_bytes=session.MAX_RAW_BYTES)
        capture=directory/'live.json'
        atomic_json(capture,dict(boundaries=boundaries,actions=actions,endpoints=endpoints,
            timing=callback_result,stack_timing=stack_result, loaded_hunks=loaded,title_ready=title_ready,probe_symbols=probe_symbols,final_stop=final_stop,
            call_map=calls, return_pcs=sorted(returns),literal_rpc=raw,rally_start=rally_start,rally_stop=rally_stop,ratio_calls=ratio_calls,
            timer_reads=session.observer.timer_reads,
            timer_scope='Read-only literal cascaded CIA counter reads with actual saved phase/interval/epoch; '
                        'admission declines require emitted control-flow interpretation, not inferred host decisions.'))
        report=dict(passed=True,subject='maintained-native',target=dict(TARGET,video=standard),
            executable_sha256=PRODUCT_SHA256, variant=variant, live_ball=True, rally_start=rally_start,rally_stop=rally_stop, ratio_summary_cck=ratio_summary,live_callback_summary_cck=callback_summary,
            capture=str(capture.relative_to(ROOT)),declared_caps=CAPS,
            timing=callback_result, full318_history72_backup_guard=True,
            frozen_boundaries=sum(bool(r['fields']['tutorial_active']) for r in boundaries),
            stack_protocol=stack_result['protocol'], dropped_notifications=callbacks.dropped,
            actual_video=actual_video,title_ready=title_ready,
            physical_clock_hz=CLOCKS[standard], provider_seconds_clock_hz=PROVIDER_CLOCK,
            scope='Bounded physical live ball; actual emitted call/RTS bus spans and complete callbacks. No screenshots, gameplay oracle, paired RNG or full release claim.')
        atomic_json(directory/'results-unvalidated.json',report)
        artifacts=[p for p in directory.iterdir() if p.is_file() and p!=output]
        transaction.finalize(output,report,[manifest],artifacts)
    except BaseException as error:
        transaction.abort(error)
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--ntsc',action='store_true')
    parser.add_argument('--variant',choices=tuple(PRODUCTS),default='candidate')
    args=parser.parse_args()
    run('NTSC' if args.ntsc else 'PAL',args.variant)
