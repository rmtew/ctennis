"""Small resource report from compiled hunks and existing native receipts.

Default writes ignored build/metrics. --record explicitly updates the reviewable
tracked summary; no commits, publication or emulator campaign happen implicitly.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from native_tools import ROOT
from native_evidence import atomic_json, digest, snapshot, status, changed
from native_hunk import hunk_layout
from native_metrics_observation import PROFILES

EXE=ROOT/'build/amiga/interfaces/enhanced/baseline-rally'
TRACKED=ROOT/'docs/metrics/current.json'
CASES={
    'cold-one':'build/tests/ct10-adf-one-cadence-enhanced-report.json',
    'two':'build/tests/ct09-ordinary-two-cadence-enhanced-report.json',
    'setup':'build/tests/native-setup/report.json',
    'demo':'build/tests/demo-full-repeat/report.json',
}
COMMANDS=[['scripts/run_ordinary_round_tests.py','--mode=one','--match','--cadence','--adf'],
          ['scripts/run_ordinary_round_tests.py','--mode=two','--match','--cadence'],
          ['scripts/run_native_setup_tests.py'],['scripts/run_demo_match_tests.py']]


def identity(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def static_metrics(exe=EXE):
    manifest=json.loads(Path(str(exe)+'.compile.json').read_text())
    if digest(exe)!=manifest['executable_sha256'] or changed(manifest['files']):
        raise ValueError('Compile manifest is stale; rebuild the native game')
    sources={p:sha for p,sha in manifest['files'].items()
             if not p.startswith('build/') and p!=str(exe)}
    assets=[]
    for p,sha in manifest['files'].items():
        if p.startswith('assets/native/') and p.endswith('.bin'):
            assets.append({'path':p,'bytes':(ROOT/p).stat().st_size,'sha256':sha,
                           'group':'audio' if '/audio/' in p else 'graphics'})
    listing=exe.parent/'native.lst'
    symbols={n:(int(h),int(o,16)) for n,h,o in re.findall(r'^([A-Za-z_][\w]*)\s+(\d\d):([0-9A-Fa-f]{8})\s*$',listing.read_text(),re.M)}
    replay=None
    if 'ui_demo_packets' in symbols and 'build/native/demo-inputs.i' in manifest['files']:
        table=(ROOT/'build/native/demo-inputs.i').read_text()
        replay=2*sum(len(line.split('dc.w',1)[1].strip().split(',')) for line in table.splitlines() if 'dc.w' in line)
    if 'ui_demo_inputs' in symbols and 'ui_demo_inputs_end' in symbols:
        begin,end=symbols['ui_demo_inputs'],symbols['ui_demo_inputs_end']
        if begin[0]!=end[0] or end[1]<begin[1]:raise ValueError('Replay symbol bounds invalid')
        replay=end[1]-begin[1]
    groups={group:sum(a['bytes'] for a in assets if a['group']==group) for group in ('graphics','audio')}
    groups['replay_loaded_bytes']=replay
    return {'executable_sha256':digest(exe),'layout':hunk_layout(exe),
            'assets':{'active_incbin_bytes':groups,'files':assets,
                      'generated_ui_pages_bytes':(ROOT/'build/native/ui-pages.bin').stat().st_size,
                      'recording_json_bytes':(ROOT/'assets/interface/demo-inputs.json').stat().st_size,
                      'note':'Active retained incbin payloads only; totals overlap loaded hunks. Generated pages and assembled replay are separate. Recording JSON is source storage, not runtime allocation.'},
            'product_inputs':sources,'generated_inputs':{p:sha for p,sha in manifest['files'].items() if p.startswith('build/native/')},
            'build_receipt_sha256':digest(exe.parent/'build-report.json')}


def memory_summary(memory):
    regions=memory['regions'];free=sum(r['free'] for r in regions)
    return {'chip_used_bytes':memory['used_chip_bytes'],'chip_free_bytes':free,
            'largest_chip_free_block_bytes':max((c['bytes'] for r in regions for c in r['chunks']),default=0),
            'other_pool_bytes':sum(r['upper']-r['lower'] for r in regions if not r['attributes']&2),
            'scope':'Whole initialized machine pool, including OS/application/stack and non-pool reservations; not exclusive application ownership.'}


def cold_timing(capture, report):
    metrics=report['resource_metrics'];points=capture.get('cold_timing_points',{})
    points=dict(points, executable_entry=capture.get('entry_stop'),
                assets_ready=metrics.get('assets_ready_and_controls_initialized'),
                first_complete_title_frame=metrics.get('first_complete_title_frame'),
                input_responsive=capture.get('checkpoints',{}).get('first_selection',{}).get('position'))
    ordered=['reset','boot_script_begins','loadseg_begin','loadseg_complete','executable_entry',
             'assets_ready','first_complete_title_frame','input_responsive']
    stages=[];previous=None
    for name in ordered:
        p=points.get(name)
        cck=p.get('cck') if isinstance(p,dict) else None
        stages.append({'stage':name,'cck':cck,'seconds':cck/3546895 if cck is not None else None,
                       'from_previous_listed_milestone_cck':cck-previous if cck is not None and previous is not None else None})
        if cck is not None:previous=cck
    reset=points.get('reset',{}).get('cck');end=points.get('input_responsive',{}).get('cck')
    displayed=(points.get('first_complete_title_frame') or {}).get('cck')
    complete=max(end,displayed) if end is not None and displayed is not None else None
    def interval(begin,end):
        a=(points.get(begin) or {}).get('cck');b=(points.get(end) or {}).get('cck')
        return b-a if a is not None and b is not None else None
    return {'stages':stages,'total_reset_to_input_cck':end-reset if end is not None and reset is not None else None,
            'total_reset_to_display_and_input_cck':complete-reset if complete is not None and reset is not None else None,
            'measured_intervals_cck':{'os_boot_plus_loader':interval('reset','loadseg_complete'),
                                      'entry_to_assets_controls_ready':interval('executable_entry','assets_ready'),
                                      'assets_ready_to_complete_display':interval('assets_ready','first_complete_title_frame')},
            'configuration':{'floppy_speed_percent':100,'cold_reset':True,'read_only_adf':True,
                             'adf_sha256':report.get('adf_sha256'),'calibration':'Separate pre-measurement boot locates Exec headers; cold reset starts measured run.'},
            'disk_reads':None,'disk_seeks':None,'disk_count_reason':'Pinned control API does not expose cumulative drive read/seek counters; DMA words are not file reads or seeks.',
            'host_emulator_launch_seconds':None,
            'scope':'Emulated CCK only. LoadSeg catch is completion/entry, not start; file reads/relocation not independently separated. First complete title frame is a frame boundary after a full title-selected frame. Input-responsive point is successful normal selection after the existing first-callback input request; includes that workflow wait. Milestones may overlap: input can respond before a complete title frame. Listed-milestone differences are signed offsets, not invented sequential phase durations; boot complete requires both displayed title and successful input.'}


def measurement_status(path):
    classification=status(path,subject='maintained-native',interface_flavor='enhanced')
    # Build's static-report hook broadens the Python closure into this reporter.
    # Reporter-only edits do not change the measured executable/observer. Keep
    # every actual observer, product, tool, config and raw-artifact hash strict.
    if classification.get('changed_dependencies')==['scripts/native_metrics.py']:
        report=json.loads(path.read_text());meta=report.get('evidence',{})
        if (report.get('passed') is True and report.get('first_difference') is None
                and meta.get('state')=='complete' and meta.get('subject')=='maintained-native'
                and report.get('subject')=='maintained-native'
                and meta.get('interface_flavor')==report.get('interface_flavor')=='enhanced'):
            return {'status':'passed','freshness':'reused','reason':'Reporter-only change; exact executable and all observation/config/tool/raw-artifact inputs unchanged'}
    return classification


def read_case(name,relative,sha):
    path=ROOT/relative;classification=measurement_status(path)
    result={'receipt':relative,'classification':classification}
    if not path.is_file():return result
    report=json.loads(path.read_text());meta=report.get('evidence',{})
    result['receipt_sha256']=digest(path)
    if classification['status']!='passed':return result
    if report.get('executable_sha256')!=sha:
        result['classification']={'status':'stale','reason':'Different measured executable'};return result
    metrics=report.get('resource_metrics')
    if not metrics or metrics['extent']['dropped_events'] or not metrics['extent']['completed_callbacks']:
        result['classification']={'status':'incomplete','reason':'Resource phase extent absent/dropped'};return result
    result.update(metrics=metrics, provenance={'command':meta['command'],'commit':meta.get('commit'),
                  'target':meta['target'],'tools':meta['tools'], 'dependencies':{p:sha for p,sha in meta['files'].items() if not p.startswith(('build/','.tools/','/')) and p!='scripts/native_metrics.py'},
                  'external_inputs_sha256':identity({p:sha for p,sha in meta['files'].items() if p.startswith('/') or p.startswith('.tools/')}),
                  'tool_sha256':{tool:digest(ROOT/info['path']) for tool,info in meta['tools'].items() if info.get('path') and (ROOT/info['path']).is_file()},
                  'kickstart_sha256':next((sha for p,sha in meta['files'].items() if p.endswith('.rom')),None),
                  'compiled_executables':meta['compiled_executables'],'state':meta['state']})
    if name in ('cold-one','two'):
        capture=json.loads((ROOT/report['capture']).read_text())
        result['memory']={'at_loadseg':memory_summary(capture['memory_initial']),
                          'runtime_final':memory_summary(capture['memory_final']),
                          'cold_boot_samples':[{'position':sample['position'],'memory':memory_summary(sample['memory'])} for sample in capture.get('boot_samples',[])],
                          **report['memory'],
                          'pre_exec_bootstrap':'unmeasured','allocation_failures':None,
                          'allocation_failure_scope':'No allocator-result observer; product performs no runtime AllocMem calls.'}
        result['deadlines']={'missed_native_callbacks':report.get('resource_missed_deadlines'),
                             'missed_publications_counter':report.get('missed_publications'),
                             'publication_failures':sum('publication' in d['field'] or 'presentation' in d['field'] or 'Copper' in d['field'] for d in report.get('differences',[]))}
        if name=='cold-one':result['cold_loading']=cold_timing(capture,report)
    if name in ('setup','demo'):
        result['deadlines']={'missed_publications_counter':report.get('missed_publications'),
                             'missed_native_callbacks':sum(p['missed_deadlines'] or 0 for p in metrics['profiles'].values())}
    return result


def summarize(report):
    static=report.get('static',{});layout=static.get('layout',{})
    lines=['# Native resource and loading metrics','',f"Completion: **{report['state']}**. Acceptance is separate from metric coverage.",
           f"Product SHA256: `{static.get('executable_sha256','unavailable')}`.",
           'Identity excludes generated report files and Git report commits; timestamps are not freshness evidence.','',
           '| Executable | Code | Data | BSS | Loaded payload |','|---:|---:|---:|---:|---:|',
           '| '+' | '.join(str(layout.get(k,'unmeasured')) for k in ('executable_bytes','code_bytes','data_bytes','bss_bytes','loaded_payload_bytes'))+' |','',
           f"Asset bytes: {static.get('assets',{}).get('active_incbin_bytes',{})}. These overlap loaded hunks.",'',
           'Timing uses elapsed emulated colour clocks, including chip-bus waits; host time is unavailable.',
           'PAL display budget: 70,824 CCK (~19.97 ms). Simulation budget: ~59,191.14 CCK (~16.69 ms).',
           'Typical = median; p95 = nearest rank. Frozen/absent phase values remain unmeasured.','',
           '| Case / profile | Samples | Update median / p95 / max ms | Sprite / UI render max ms | Dispatcher max ms | Work / deadline headroom ms |',
           '|---|---:|---:|---:|---:|---:|']
    def ms(cck):return f'{cck*1000/3546895:.3f}' if cck is not None else 'unmeasured'
    for name,case in report.get('runtime',{}).items():
        metrics=case.get('metrics')
        if not metrics:
            lines.append(f"| {name}: {case['classification']['status']} | | | | | |")
            continue
        for profile,data in metrics['profiles'].items():
            update=data['update_including_render']
            if not update:continue
            lines.append(f"| {name} / {profile} | {data['callbacks']} | "+' / '.join(ms(update[k]) for k in ('typical_median_cck','p95_cck','max_cck'))+
                         f" | {ms((data['render'] or {}).get('max_cck'))} / {ms((data['ui_construction_render'] or {}).get('max_cck'))} | {ms((data['dispatcher'] or {}).get('max_cck'))} | {ms(update['minimum_headroom_cck'])} / {ms(data['minimum_deadline_headroom_cck'])} |")
        if 'memory' in case:
            memory=case['memory'];final=memory['runtime_final']
            lines.extend(['',f"{name}: chip used {final['chip_used_bytes']:,} B; free {final['chip_free_bytes']:,} B; largest block {final['largest_chip_free_block_bytes']:,} B; runtime peak {memory['peak_chip_bytes']} B; cold initialized-pool peak {memory['cold_boot_peak']} B.",
                          f"Deadlines/publications: `{case['deadlines']}`. Allocation failures: unmeasured; pre-Exec bootstrap: unmeasured.",''])
        if 'cold_loading' in case:
            cold=case['cold_loading'];lines+=['| Cold loading stage | Emulated seconds | Signed offset from previous listed milestone (ms) |','|---|---:|---:|']
            for stage in cold['stages']:
                seconds=f"{stage['seconds']:.6f}" if stage['seconds'] is not None else 'unmeasured'
                lines.append(f"| {stage['stage']} | {seconds} | {ms(stage['from_previous_listed_milestone_cck'])} |")
            lines.extend(['',f"Total reset to successful input: {ms(cold['total_reset_to_input_cck'])} ms; displayed title and input both ready: {ms(cold['total_reset_to_display_and_input_cck'])} ms. Disk reads/seeks and host launch time: unavailable.",cold['scope'],''])
    lines+=['','Coverage: '+', '.join(f"{p}: {s}" for p,s in report.get('coverage',{}).items()),'',
            'Deltas: '+json.dumps(report.get('deltas',{}),sort_keys=True), '',
            'Refresh hook: after merging new fonts/celebration, run the affected native checks or `RUST_LOG=info python scripts/native_metrics.py --refresh --record`; never copy results from an unfinished branch.','']
    return '\n'.join(lines)


def metric_deltas(previous, report):
    delta={'state':'against previous accepted compatible report','previous_identity':previous['identity'],
        'static_bytes':{k:v-previous['static']['layout'][k] for k,v in report['static']['layout'].items() if isinstance(v,int)},'runtime':{}}
    for name,current in report['runtime'].items():
        old=previous['runtime'].get(name,{})
        compatible=('metrics' in old and 'metrics' in current and old['metrics']['clock']==current['metrics']['clock']
            and old['metrics']['boundaries']==current['metrics']['boundaries']
            and old['provenance']['target']==current['provenance']['target']
            and old['provenance'].get('tool_sha256')==current['provenance'].get('tool_sha256')
            and old['provenance'].get('kickstart_sha256')==current['provenance'].get('kickstart_sha256')
            and {k:v['version'] for k,v in old['provenance']['tools'].items()}=={k:v['version'] for k,v in current['provenance']['tools'].items()})
        if not compatible:
            delta['runtime'][name]={'state':'incompatible or unmeasured'};continue
        profiles={}
        for profile,metrics in current['metrics']['profiles'].items():
            profiles[profile]={}
            for phase in ('update_including_render','render','dispatcher','ui_construction_render'):
                a,b=metrics[phase],old['metrics']['profiles'][profile][phase]
                profiles[profile][phase]={k:a[k]-b[k] for k in ('typical_median_cck','p95_cck','max_cck','minimum_headroom_cck')} if a and b else None
        delta['runtime'][name]={'profiles':profiles}
        if 'memory' in current and 'memory' in old:
            delta['runtime'][name]['runtime_memory_bytes']={k:v-old['memory']['runtime_final'][k] for k,v in current['memory']['runtime_final'].items() if isinstance(v,int)}
        if 'cold_loading' in current and 'cold_loading' in old:
            a=current['cold_loading']['total_reset_to_input_cck'];b=old['cold_loading']['total_reset_to_input_cck']
            delta['runtime'][name]['reset_to_input_cck']=a-b if a is not None and b is not None else None
    return delta


def generate():
    static=static_metrics();runtime={name:read_case(name,path,static['executable_sha256']) for name,path in CASES.items()}
    measurement_inputs={}
    for case in runtime.values():
        if 'provenance' in case:
            dependencies=case['provenance'].pop('dependencies')
            case['provenance']['source_dependency_identity']=identity(dependencies)
            for path,sha in dependencies.items():
                if path in measurement_inputs and measurement_inputs[path]!=sha:raise ValueError('Cases disagree on dependency '+path)
                measurement_inputs[path]=sha
    coverage={p:'measured' if any(c.get('metrics',{}).get('profiles',{}).get(p,{}).get('callbacks',0) for c in runtime.values()) else 'unmeasured' for p in PROFILES}
    coverage['celebration']='unavailable in this product; remeasure when implemented'
    complete=all(c['classification']['status']=='passed' and 'metrics' in c for c in runtime.values()) and all(coverage[p]=='measured' for p in PROFILES if p!='celebration')
    report={'schema':1,'state':'complete' if complete else 'incomplete','static':static,'runtime':runtime,'coverage':coverage,'measurement_inputs':measurement_inputs,
            'identity':identity({'executable':static['executable_sha256'],'inputs':static['product_inputs']}),
            'report_generator_sha256':digest(ROOT/'scripts/native_metrics.py'),
            'deltas':{'state':'no previous accepted compatible report'}}
    accepted=subprocess.run(['git','show','master:docs/metrics/current.json'],cwd=ROOT,capture_output=True,text=True)
    if accepted.returncode==0:
        previous=json.loads(accepted.stdout)
        if previous.get('schema')==1 and previous.get('state')=='complete':
            report['deltas']=metric_deltas(previous,report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record',action='store_true',help='Write tracked JSON/Markdown for explicit review')
    parser.add_argument('--refresh',action='store_true',help='Run only the four existing affected native checks')
    parser.add_argument('--require-runtime',action='store_true',help='Fail if any required case lacks current completed metrics')
    parser.add_argument('--check',action='store_true',help='Verify accepted report product/dependencies and latest receipts without emulation')
    args=parser.parse_args();out=ROOT/'build/metrics/current.json'
    # Incomplete invocation supersedes an earlier pass, even if generation fails.
    atomic_json(out,{'schema':1,'state':'incomplete','command':sys.argv})
    try:
        if args.refresh:
            import os
            for command in COMMANDS:
                subprocess.run([sys.executable,*command],cwd=ROOT,env=dict(os.environ,RUST_LOG='info'),check=True)
        if args.check:
            accepted=json.loads(TRACKED.read_text())
            if accepted.get('state')!='complete':raise ValueError('Accepted metrics are incomplete')
            static=static_metrics()
            if static['executable_sha256']!=accepted['static']['executable_sha256']:raise ValueError('Accepted product differs; regenerate metrics')
            differences=changed(accepted['measurement_inputs'])
            if differences:raise ValueError(f'Measurement dependencies changed/missing: {differences[:8]}')
            for name,case in accepted['runtime'].items():
                differences=[]
                if differences:raise ValueError(f'{name} dependencies changed/missing: {differences[:8]}')
                from native_tools import emulator_config
                config=emulator_config()
                if digest(Path(config['inputs']['amiga_rom']))!=case['provenance']['kickstart_sha256']:
                    raise ValueError(f'{name} Kickstart changed')
                for tool,sha in case['provenance']['tool_sha256'].items():
                    if digest(ROOT/case['provenance']['tools'][tool]['path'])!=sha:raise ValueError(f'{name} tool changed: {tool}')
                latest=ROOT/CASES[name]
                if latest.exists() and digest(latest)!=case['receipt_sha256']:
                    raise ValueError(f'{name} has a later run; regenerate report (later failures supersede pass)')
            accepted=dict(accepted,reuse='proven identical product/config; accepted measurements reused, not a fresh campaign')
            atomic_json(out,accepted)
            print(accepted['reuse']);return 0
        report=generate();atomic_json(out,report)
        (out.parent/'current.md').write_text(summarize(report))
        if args.record:
            # Raw native captures remain ignored; only bounded summary/provenance is tracked.
            atomic_json(TRACKED,report);TRACKED.with_suffix('.md').write_text(summarize(report))
        print(json.dumps({'state':report['state'],'executable_bytes':report['static']['layout']['executable_bytes'],
                          'coverage':report['coverage'],'report':str(TRACKED if args.record else out)}))
        return 1 if args.require_runtime and report['state']!='complete' else 0
    except BaseException as error:
        failure={'schema':1,'state':'interrupted' if isinstance(error,KeyboardInterrupt) else 'failed','error':str(error),'command':sys.argv}
        atomic_json(out,failure)
        if args.record:atomic_json(TRACKED,failure);TRACKED.with_suffix('.md').write_text('Metrics generation '+failure['state']+': '+str(error)+'\n')
        raise


if __name__=='__main__':raise SystemExit(main())
