"""Offline comparison of retained controlled PAL/NTSC captures; no guest writes."""
import gzip,json
from pathlib import Path
from deadline_service_reduction import reduce_capture
from native_evidence import ReportRun,atomic_json,digest,inputs_for,snapshot
from native_tools import ROOT


def union_span(calls,start,end):
    spans=sorted((max(start,r['entry']['cck']),min(end,r['exit']['cck'])) for r in calls if r['entry']['cck']<end and r['exit']['cck']>start)
    total=0;last=start
    for a,b in spans:
        if b>last:total+=b-max(a,last);last=b
    return total


def summarize(native,capture):
    calls=capture['stack_timing']['calls'];rows=[]
    requests=[r for r in calls if r['callee']=='game_preview_request_projected']
    for endpoint in capture['endpoints']:
        gesture=endpoint['request']['cck'];marker=endpoint['first_actual_publication']['position']['cck']
        relevant=[r for r in requests if gesture<=r['entry']['cck']<=marker]
        # Alignment issues a series of generations; the last request owns the
        # endpoint. First-entry statistic is reported separately by the runner.
        start=relevant[-1]['entry']['cck'] if relevant else requests[0]['entry']['cck']
        APIs=[r for r in calls if r['callee'] in ('game_preview_step','game_preview_endpoint_try')]
        useful=union_span(APIs,start,marker)
        rows.append(dict(label=endpoint['label'],x=endpoint['x'],y=endpoint['y'],end=endpoint['end'],generation=endpoint['generation'],
            public_request_to_marker_cck=marker-start,gesture_to_marker_cck=marker-gesture,
            preview_api_elapsed_cck=useful,outside_preview_api_elapsed_cck=marker-start-useful,
            contact_timing=endpoint['contact_timing'],incoming_sha256=endpoint['incoming_state_sha256'],
            launch_sha256=digest_bytes(endpoint['held_launch_state']),terminal_sha256=digest_bytes(endpoint['held_terminal_state'])))
    service=reduce_capture(capture)
    chunks=capture['deadline']['chunks']
    roots=[r for r in calls if r['callee']=='game_launch_root']
    physics=[c for c in chunks if c['operation']==8]
    background_contacts=sum(any(c['entry']['cck']<=r['entry']['cck']<=r['exit']['cck']<=c['exit']['cck'] for r in roots) for c in physics)
    contact_dispatches=[r for r in calls if r['callee']=='game_preview_dispatch' and any(r['entry']['cck']<=q['entry']['cck']<=q['exit']['cck']<=r['exit']['cck'] for q in roots)]
    return dict(background_physics_owners=len(physics),background_contact_owners=background_contacts,
        maximum_contact_dispatch_cck=max((r['elapsed_bus_cck'] for r in contact_dispatches),default=None),endpoints=rows,classes=native['deadline']['classes'],maximum_by_class_cck=native['deadline']['maximum_by_class_cck'],
        accepted=native['deadline']['background_worker_calls'],declined=native['deadline']['declined_owner_calls'],
        maximum_declined_cck=native['deadline']['maximum_declined_owner_cck'],
        maximum_callback_cck=native['deadline']['maximum_callback_cck'],maximum_entry_lateness_cck=native['deadline']['maximum_entry_lateness_cck'],
        minimum_absolute_callback_headroom_cck=min(r['absolute_headroom_cck'] for r in capture['timing']['callbacks']),
        callback_count=len(capture['timing']['callbacks']),stack=native['timing']['stack_bytes'],
        service={k:v for k,v in service.items() if k!='spans'},
        input={k:v for k,v in native['input_probe'].items() if k not in ('rows','transitions','acknowledgements')},memory=native['native_memory'])


def digest_bytes(h):
    import hashlib
    return hashlib.sha256(bytes.fromhex(h)).hexdigest()


def main():
    directory=ROOT/'build/tests/physics-comparison';output=directory/'report.json';directory.mkdir(parents=True,exist_ok=True)
    consumed={ROOT/('build/tests/'+prefix+region+'/'+name) for prefix in ('physics-native-','physics-control-native-') for region in ('pal','ntsc') for name in ('report.json','latency.json.gz')}
    paths,tools=inputs_for('build','scripts/physics_comparison.py')
    transaction=ReportRun([output],'offline-native-reduction','maintained-native','Controlled scheduling switch and exact root services; no fresh emulator')
    transaction.meta.update(files=snapshot(paths|consumed),tools=tools,runner='scripts/physics_comparison.py')
    try:
        regions={};artifacts=[]
        for region in ('pal','ntsc'):
            natives={};captures={};results={}
            for kind,prefix in (('control','physics-control-native-'),('candidate','physics-native-')):
                source=ROOT/('build/tests/'+prefix+region);native=json.loads((source/'report.json').read_text());assert native['passed']
                with gzip.open(source/'latency.json.gz','rt') as h:captured=json.load(h)
                natives[kind]=native;captures[kind]=captured;results[kind]=summarize(native,captured)
                full=reduce_capture(captured);assert full['passed']
                artifact=directory/(region+'-'+kind+'-service.json.gz')
                with gzip.open(artifact,'wt') as h:json.dump(full,h,separators=(',',':'))
                artifacts.append(artifact)
                results[kind].update(receipt_sha256=digest(source/'report.json'),capture_sha256=digest(source/'latency.json.gz'),run_id=native['evidence']['run_id'],executable_sha256=native['executable_sha256'])
            a,b=captures['control'],captures['candidate']
            paired=dict(cached_origin_equal=a['incoming_live']['origin_cache']==b['incoming_live']['origin_cache'],
                retained_records_equal=a['records']==b['records'],history_end_equal=a['history_end']==b['history_end'])
            assert len(a['endpoints'])==len(b['endpoints'])==3,'Endpoint comparison would omit a trial'
            pairs=[]
            for x,y in zip(a['endpoints'],b['endpoints']):
                pairs.append(dict(label=x['label'],same_label=x['label']==y['label'],same_placement=(x['x'],x['y'],x['end'])==(y['x'],y['y'],y['end']),
                    same_incoming_origin=x['incoming_state']==y['incoming_state'],same_launch_seed=x['held_launch_state']==y['held_launch_state'],same_terminal=x['held_terminal_state']==y['held_terminal_state'],
                    control_physical_seconds=x['physical_latency_seconds'],candidate_physical_seconds=y['physical_latency_seconds']))
            regions[region]=dict(control=results['control'],candidate=results['candidate'],pairing=paired,endpoint_pairs=pairs,
                physical_inputs_scope='Same guided controls; alignment and later actions begin after each independently observed outcome. Absolute physical input timelines differ. Computational pairing requires equal origin/records/placement/launch seed; do not infer paired speedup when any differ.')
        transaction.finalize(output,dict(passed=True,execution='offline-retained-native-capture-reduction',regions=regions,normative_deadline_safety=False,
            work_scope='Observed union of preview step/query API bus spans; remaining elapsed includes nominal waiting, input, presenter, rendering and other work, not CPU-idle time. Request to marker uses last actual request during each gesture; first request reported separately.'),artifacts=artifacts)
        print(json.dumps(dict(report=str(output),sha256=digest(output))),flush=True)
    except BaseException as e:transaction.abort(e);raise


if __name__=='__main__':main()
