"""Compare finite original match/result/title/restart scenes on native hardware."""
import argparse,json
from pathlib import Path
from presentation_reference import ROOT
from phase_reference import build_phase,validate_phase
from regime_reference import validate_extension,load_reference
from run_round_presentation_tests import check,mutation
from capture_native_presentation import capture
from run_presentation_tests import digest
from maintained_state_contract import MAINTAINED_STATE_CONTRACT, MAINTAINED_SCRATCH_OFFSETS
CASES=('p1-one-player-result-restart-scenes','p1-two-player-result-restart-scenes')

def reference(case):
    phase_path=ROOT/case['initial_phase_reference'];phase_case=json.loads((ROOT/'tests/cases'/phase_path.name).read_text())
    phase=build_phase(phase_case);proof=validate_phase(phase,phase_case);phase_path.write_text(json.dumps(phase,indent=2)+'\n')
    parent_path=ROOT/phase['parent_reference'];parent=json.loads(parent_path.read_text())
    base_name=case['source_case'].replace('-restart-complete','-match');base,_=load_reference(base_name)
    proof['extension']=validate_extension(parent,{'continuous_parent':base_name});m=base['milestones']
    award,selected=m['match_award']['update'],m['restart_selection']['update']
    events=[e for e in parent['timeline'] if e['kind']=='M' and e.get('pc') in (0x580,0x109) and award<=e.get('after_callback',0)<=selected]
    if [e['pc'] for e in events]!=[0x580,0x109]:raise ValueError('Result/title source boundaries missing')
    targets=[award+4,events[0]['after_callback']+2,events[1]['after_callback']+5,selected+3,m['restart_gameplay']['update']+2,m['restart_serve_flight']['update']+3]
    schedule=[]
    for event in parent['timeline']:
        if event['kind']!='control' or event['frame']<parent['updates'][award-2]['end_frame'] or event['frame']>parent['updates'][targets[-1]-1]['end_frame']:continue
        value=bool(event['value']);control=event['control']
        if control=='select':
            row=next(r for r in parent['updates'] if r['begin_frame']>=event['frame'])
            args={'rawkey':0x46 if base_name=='one-player-match' else 0x42,'action':'press' if value else 'release'}
        elif control in ('fire','p2-button1'):
            row=next(r for r in parent['updates'] if any(read['frame']>=event['frame'] and bool(read['value']&16)==value for read in r['inputs']))
            args={'port':2 if control=='fire' else 1,'red':value}
        else:raise ValueError('Unexpected physical control in result interval')
        schedule.append({'after_callback':row['ordinal']-1,'source_control':event,'arguments':args})
    inputs=[{'port':2,'red':True}] if base_name=='one-player-match' else [{'port':1,'red':True},{'port':2,'red':True}]
    if (case['source_case']!=Path(phase['parent_reference']).stem or case['initial_source_update']!=phase['initial_source_update'] or case['completed_callbacks']!=targets or case['native_input_schedule']!=schedule or case['inputs']!=inputs):
        raise ValueError('Result recipe differs from validated original events')
    proof.update(parent_sha256=digest(parent_path),phase_sha256=digest(phase_path),physical_schedule=schedule)
    return parent,proof

def late_mutation(kind,case,captured):
    # Result sprites are hidden. Use the existing visible returned-court and
    # restarted-serve checkpoints; do not perturb the title-transition window.
    index={'sprite':3,'field':4,'entropy':5}[kind]
    target=case['completed_callbacks'][index]
    generation=captured['observations'][index]['completed_raster']['generation']['prepared_after_callback']
    if kind=='sprite':
        return mutation(kind,{**case,'completed_callbacks':[case['completed_callbacks'][0],target]},generation)
    # A field bank must be poisoned before the displayed generation is built;
    # the two-player capture can present one bank behind the normal run.
    threshold=generation-2 if kind=='field' else target-1
    def alter(text):
        old='game_observe_pre_tail:\n        rts'
        if text.count(old)!=1:raise ValueError('Shared result observation hook no longer unique')
        body=('        move.b  #1,field_values+1\n        bsr     patch_score_pointers' if kind=='field' else
              '        movem.l d0-d1/a0,-(sp)\n        bsr     read_refresh_adapter\n        movem.l (sp)+,d0-d1/a0')
        return text.replace(old,f'game_observe_pre_tail:\n        cmpi.w  #{threshold},simulation_updates\n        bcs.s   result_mutation_done\n'+body+'\nresult_mutation_done:\n        rts')
    return alter


def run(name,self_test=False):
    path=ROOT/f'build/tests/{name}-report.json';case=json.loads((ROOT/f'tests/cases/{name}.json').read_text());parent,proof=reference(case)
    # Use visible, stable original checkpoints for each existing late fault.
    fault_index={'sprite':3,'field':4,'entropy':5}
    def obtain(kind=None):
        result=capture(tuple(case['completed_callbacks']),recorded_entropy=True,track_commits=True,completed_rasters=True,observe_fields=True,observe_state=True,observe_audio=True,initial_source_update=case['initial_source_update'],initial_phase_reference=case['initial_phase_reference'],capture_label=name+('-'+kind if kind else ''),source_mutator=late_mutation(kind,case,captured) if kind else None,source_case=case['source_case'],native_inputs=case['inputs'],strict_source_events=False,presentation_reference_directory=case['presentation_reference_directory'],native_input_schedule=case['native_input_schedule'])
        if [(e['after_callback'],e['arguments']) for e in result['applied_physical_events']]!=[(e['after_callback'],e['arguments']) for e in case['native_input_schedule']]:raise AssertionError('Physical restart schedule incomplete')
        return result
    captured=obtain();checks,baseline=check(case,parent,captured);mutants=[]
    if self_test:
        for kind in ('sprite','field','entropy'):
            changed=obtain(kind);comparison,observed=check(case,parent,changed)
            if observed['states']!=baseline['states'] or observed['pixels'][:7]!=baseline['pixels'][:7] or checks['first_difference'] is not None and comparison['first_difference']!=checks['first_difference']:raise AssertionError('Late mutant changed RAM or early baseline')
            if kind=='entropy':
                target=case['completed_callbacks'][fault_index[kind]]
                original=next((e for e in baseline['source_events'] if e['boundary']=='native-entropy-consumption' and e['update']==target),{'actual':[]})
                extra=next((e for e in observed['source_events'] if e['boundary']=='native-entropy-consumption' and e['update']==target),{'actual':[]})
                if len(extra['actual'])!=len(original['actual'])+1:raise AssertionError('Extra late refresh read escaped')
            else:
                region='viewport' if kind=='sprite' else 'point_b'
                # Result sprites are hidden; target their original returned-court
                # checkpoint rather than declaring an invisible result fault detected.
                visible_target=case['completed_callbacks'][fault_index[kind]]
                if not any(a['actual_sha256']!=b['actual_sha256'] and a['region']==region and a['checkpoint']==visible_target for a,b in zip(observed['pixels'],baseline['pixels'])):raise AssertionError('Late compiled output change escaped')
            from run_test_suite import classify_behavior,failure_check_digest
            policy=({'signature':checks['first_difference'],'complete_checks_sha256':failure_check_digest({'baseline_observations':baseline})} if checks['first_difference'] is not None else None)
            if comparison['first_difference'] is None:raise AssertionError('Actual late fault escaped result acceptance')
            candidate={'passed':False,'first_difference':comparison['first_difference'],'baseline_observations':observed}
            if classify_behavior(candidate,policy)!='unexpected-red':raise AssertionError('Early failure hid later mutant')
            mutants.append({'kind':kind,'detected':True,'classification':'unexpected-red','checks':comparison,'baseline_observations':observed,'capture_report_path':changed['capture_report_path'],'capture_report_sha256':digest(Path(changed['capture_report_path'])),'executable_sha256':changed['executable_sha256']})
    report={'case':name,'subject':'maintained-native','state_contract':MAINTAINED_STATE_CONTRACT,'omitted_legacy_scratch_offsets':list(MAINTAINED_SCRATCH_OFFSETS),'state_bytes_compared_per_callback':250,'raw_state_subject':'maintained-native','raw_state_contract':'original-byte-page-diagnostic-v1','raw_state_bytes_compared_per_callback':254,'raw_state_passed':checks['raw_state_first_difference'] is None,'raw_state_first_difference':checks['raw_state_first_difference'],'passed':checks['first_difference'] is None,'first_difference':checks['first_difference'],'checks':checks,'baseline_observations':baseline,'reference_proof':proof,'case_sha256':digest(ROOT/f'tests/cases/{name}.json'),'capture_report_path':captured['capture_report_path'],'capture_report_sha256':digest(Path(captured['capture_report_path'])),'executable_sha256':captured['executable_sha256'],'self_test':self_test,'hardware_mutations':mutants,'scope':case['contract']}
    path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'case':name,'passed':report['passed'],'first_difference':report['first_difference'],'states':len(checks['states']),'crops':len(checks['pixels']),'mutants':len(mutants)}),flush=True);return report['passed']

def run_cli():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',choices=CASES,required=True);parser.add_argument('--self-test',action='store_true');args=parser.parse_args();return 0 if run(args.case,args.self_test) else 1


def main():
    from evidence import tracked_call
    probe=argparse.ArgumentParser(add_help=False);probe.add_argument('--case')
    selected,_=probe.parse_known_args()
    if selected.case not in CASES:return run_cli()
    path=ROOT/f'build/tests/{selected.case}-report.json'
    return tracked_call([path],'result-scenes','maintained-native','captured result phase',
                        'scripts/run_result_presentation_tests.py',selected.case,run_cli,
                        lambda path,report:[Path(report['capture_report_path']).parent/'native-application'])

if __name__=='__main__':raise SystemExit(main())
