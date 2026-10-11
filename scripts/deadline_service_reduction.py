"""Read-only exact-callsite reduction of completed native root service spans.

Original receipts retain their recognizable adjacent-call subset metric. This
supplement measures all complete main-loop sequences including intervening IRQs.
"""
import gzip
import json
from native_evidence import ReportRun,atomic_json,digest,inputs_for,snapshot
from native_tools import ROOT

NAMES=['account_sim_timer','game_poll_keyboard','poll_presentation','account_sim_timer']


def reduce_capture(captured):
    mapping=sorted((int(pc),v) for pc,v in captured['call_map'].items())
    choices=[]
    for i in range(len(mapping)-3):
        group=mapping[i:i+4]
        if [v['callee'] for _,v in group]==NAMES and all(group[j][1]['return_pc']==group[j+1][0] for j in range(3)):
            choices.append([pc for pc,_ in group])
    assert len(choices)==1,choices
    pcs=choices[0];calls=sorted(captured['stack_timing']['calls'],key=lambda v:v['entry']['cck'])
    root=[v for v in calls if v['depth']==0 and v.get('caller') is None]
    selected=[(i,v) for i,v in enumerate(root) if v['entry_pc'] in pcs]
    assert len(selected)%4==0,'Incomplete exact main-loop service sequence'
    spans=[]
    for i in range(0,len(selected),4):
        seq=selected[i:i+4];assert [v['entry_pc'] for _,v in seq]==pcs
        first,last=seq[0][1],seq[-1][1]
        extra=[v['callee'] for v in root[seq[0][0]:seq[-1][0]+1] if v['entry_pc'] not in pcs]
        spans.append(dict(entry=first['entry'],exit=last['exit'],elapsed_cck=last['exit']['cck']-first['entry']['cck'],intervening_root_calls=extra))
    maximum=max(v['elapsed_cck'] for v in spans)
    return dict(passed=maximum<=2500,service_hypothesis_cck=2500,maximum_service_cck=maximum,
        exact_main_loop_callsites=pcs,complete_sequences=len(spans),
        sequences_with_intervening_root_calls=sum(bool(v['intervening_root_calls']) for v in spans),spans=spans,
        scope='Complete first account entry-store through second account return-stack read, including intervening IRQ elapsed time. CPU pre-store/post-return, full IRQ entry/RTE tails and WCET remain unresolved.')


def main():
    directory=ROOT/'build/tests/deadline-service-audit';output=directory/'report.json'
    paths,tools=inputs_for('build','scripts/deadline_service_reduction.py')
    consumed={ROOT/('build/tests/deadline-native-'+v+'/'+name) for v in ('pal','ntsc') for name in ('report.json','latency.json.gz')}
    transaction=ReportRun([output],'offline-native-reduction','maintained-native','Exact emitted main-loop service calls; no fresh emulator execution')
    transaction.meta.update(files=snapshot(paths|consumed),tools=tools,runner='scripts/deadline_service_reduction.py')
    try:
        results={};artifacts=[]
        for standard in ('pal','ntsc'):
            source=ROOT/('build/tests/deadline-native-'+standard)
            native=json.loads((source/'report.json').read_text());assert native['passed'] and native['deadline']['prototype_only']
            with gzip.open(source/'latency.json.gz','rt') as handle:captured=json.load(handle)
            result=reduce_capture(captured)
            raw=directory/(standard+'-service-spans.json.gz')
            with gzip.open(raw,'wt') as handle:json.dump(result,handle,separators=(',',':'))
            artifacts.append(raw)
            results[standard]={k:v for k,v in result.items() if k!='spans'}
            results[standard].update(native_receipt_sha256=digest(source/'report.json'),native_capture_sha256=digest(source/'latency.json.gz'),native_run_id=native['evidence']['run_id'],executable_sha256=native['executable_sha256'])
        assert all(v['passed'] for v in results.values()),results
        transaction.finalize(output,dict(passed=True,execution='offline-retained-native-capture-reduction',standards=results,normative_deadline_safety=False),artifacts=artifacts)
        print(json.dumps(dict(report=str(output),sha256=digest(output),standards=results)),flush=True)
    except BaseException as error:transaction.abort(error);raise


if __name__=='__main__':main()
