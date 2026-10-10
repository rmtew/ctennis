"""Read retained next-operation captures; exhaustive integer-CCK accounting."""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
from build_match_core import load_image
from tutorial_latency_accounting import CATEGORIES,NAMES,partition,collapsed_breakdown,union_duration
NAMES['preview_envelopes_state_support'].add('game_preview_step_coherent')
HZ={'PAL':3546895,'NTSC':3579545}
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def reduce(report_path, executable):
    report=json.loads(Path(report_path).read_text());assert report['passed']
    assert digest(executable)==report['executable_sha256'], 'Reducer requires the exact retained candidate executable'
    directory=Path(report['attempt']);raw=directory/'literal-rpc.jsonl.gz';symbols=None;passes=[];active=None
    for line in gzip.open(raw,'rt'):
        x=json.loads(line)
        if x.get('type')=='reply' and x.get('method')=='segments.list':
            addresses=[h['start'] for h in x['result']['current']]
            symbols=load_image(executable,hunk_addresses=addresses)[1]
        if x.get('type')=='request' and x.get('method')=='events.unsubscribe':active=None
        if x.get('type')=='request' and x.get('method')=='events.subscribe':active={'inputs':[],'clears':[],'ready_stores':[]};passes.append(active)
        if active is None:continue
        if x.get('type')=='request' and x.get('method')=='input.key' and 'at_seconds' in x['arguments']:
            active['inputs'].append(x['arguments'])
        if x.get('type')=='notification':
            row=x['value'].get('params',{})
            if row.get('access')=='write' and row.get('addr')==symbols['game_preview_endpoint_ready']:
                if row['value']==0:active['clears'].append(row)
                elif row['size']==1 and row['value']==255:active['ready_stores'].append(row)
    assert len(passes)==len(report['passes'])==3
    rows=[];hz=HZ[report['standard']]
    for p,data in zip(report['passes'],passes):
        start=round(data['inputs'][0]['at_seconds']*3546895);end=start+p['latency_cck']
        stores=[r for r in data['ready_stores'] if start<r['position']['cck']<end]
        assert stores and any(start<r['position']['cck']<stores[0]['position']['cck'] for r in data['clears'])
        known=stores[0]['position']['cck']
        enclosing=[r for r in p['stack_rows'] if r['callee']=='game_preview_endpoint_step' and r['entry']['cck']<=known<=r['exit']['cck']]
        assert len(enclosing)==1
        intervals=[]
        for r in p['stack_rows']:
            for i,c in enumerate(CATEGORIES):
                if r['callee'] in NAMES.get(c,set()):intervals.append((i,r['entry']['cck'],r['exit']['cck']));break
        totals=partition(start,end,intervals);suffix=partition(known,end,intervals)
        collapsed=collapsed_breakdown(totals,suffix,hz)
        collapsed['partition_cck']['endpoint_ready_store_to_qualifying_copjmp']=collapsed['partition_cck'].pop('known_upper_bound_to_qualifying_copjmp')
        collapsed['partition_ms']['endpoint_ready_store_to_qualifying_copjmp']=collapsed['partition_ms'].pop('known_upper_bound_to_qualifying_copjmp')
        ui=[(r['entry']['cck'],r['exit']['cck']) for r in p['stack_rows'] if r['callee']=='ui_sample']
        relevant=[r for r in p['stack_rows'] if start<=r['entry']['cck']<known]
        grants=[r for r in relevant if r['callee'] in ('game_preview_step_variant','game_preview_step_coherent')]
        topups=[r for r in relevant if r['callee']=='tutorial_preview_topup']
        accepted=sum(any(r['callee']=='game_preview_dispatch' and t['exit']['cck']<=r['entry']['cck']<g['exit']['cck'] for r in relevant) for t in topups for g in grants if g['entry']['cck']<=t['entry']['cck']<g['exit']['cck'])
        grouping=dict(grants=len(grants),topup_attempts=len(topups),accepted_topups=accepted,refused_topups=len(topups)-accepted,topup_observed_ms=sum(r['elapsed_bus_cck'] for r in topups)*1000/hz,operations=sum(r['callee'] in ('game_preview_continue_one','game_preview_prime_one','game_preview_resolve_one') for r in relevant),dispatches=sum(r['callee']=='game_preview_dispatch' for r in relevant))
        queries=[r for r in relevant if r['callee']=='game_preview_endpoint_pending']
        grouping.update(endpoint_checks=len(queries),endpoint_check_inclusive_ms=sum(r['elapsed_bus_cck'] for r in queries)*1000/hz,
            endpoint_check_exclusive_ms=sum(r['exclusive_bus_cck'] for r in queries)*1000/hz)
        rows.append(dict(grouping=grouping,label=p['label'],physical_input_cck=start,endpoint_ready_store_cck=known,endpoint_step_return_cck=enclosing[0]['exit']['cck'],copjmp_cck=end,latency_ms=p['latency_ms'],accounting=collapsed,primary_cck=totals,suffix_cck=suffix,ui_sample_before_known_cck=union_duration(start,known,ui),ui_sample_before_known_ms=union_duration(start,known,ui)*1000/hz,ui_sample_full_window_ms=union_duration(start,p['fixed_end_cck'],ui)*1000/hz,inputs=data['inputs'],ready_store_pc=stores[0]['pc']))
    return dict(standard=report['standard'],native_run_id=report['evidence']['run_id'],native_commit=report['evidence']['commit'],native_product_sha256=report['executable_sha256'],symbol_executable_path=str(executable),symbol_executable_sha256=digest(executable),report_path=str(report_path),report_sha256=digest(report_path),raw_path=str(raw),raw_sha256=digest(raw),binary=report['evidence']['compiled_executables'],anchor_sha256=digest(directory/'anchor.state'),accepted_requests=report['accepted_requests'],baseline_replay_equal=report['baseline_replay_equal'],passes=rows,scope='Observed emitted-call spans include IRQ; instruction tails/gaps stay unclassified. Endpoint-ready is actual held-ready store after new-request clear; point/outcome stores precede it in unchanged source. This is not WCET or first scanout.')
p=argparse.ArgumentParser();p.add_argument('reports',nargs='+');p.add_argument('--output',required=True);p.add_argument('--executable',required=True);args=p.parse_args()
result=dict(schema=1,reducer_sha256=digest(__file__),regions=[reduce(p,args.executable) for p in args.reports]);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({r['standard']:[(p['label'],p['latency_ms'],p['accounting']['partition_ms']) for p in r['passes']] for r in result['regions']}))
