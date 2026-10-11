"""Native report timing retains every real callback and deadline failure."""
import sys
import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from run_preview_native import Native,measurement,json_value,qualify_resolver,verify_incoming_prefix,inherited_endpoints,overlay,verify_admission,worker_guard_closure,verify_preview_retirement,fresh_seek_receipt,native_report,preserve_pre_status_receipt,native_receipt_artifacts,native_saved_bytes
from preview_native_observation import BodyFrames
from native_tools import ROOT,ASSEMBLER


class NativePreviewTiming(unittest.TestCase):
    def body_native(self,stops,base=0x3000):
        native=object.__new__(Native)
        native.symbols={'preview_native_return':0x900,'game_core_state':0,
            'game_preview_held_state':0x3000,'game_preview_released_state':0x4000}
        native.stop={'seconds':0};native.internal_body_stops=0
        frames=BodyFrames({0x400:dict(operation='game_core_sample_pads',arity=2)},0x1000,0x2000,{0x500})
        native.observer=SimpleNamespace(body_frames=frames,active=None,drops=0,problems=[],
            api_rows=[],rows=[],pending={'bodies':0},inside_api=lambda:True,
            irq_writes=[],irq_entry_pc=0x600,irq_exit_pc=0x602,
            number=lambda n,w=2:2 if n=='game_preview_active' else 0,
            state=lambda:native.current_state)
        native.current_state=bytes(318)
        native.observer.start=0;native.observer.shadow=bytearray(318)
        native.observer.contexts={base:bytearray(318)} if base else {}
        native.block=lambda a,b:bytes(318) if base else native.current_state
        native.observer.state=lambda:native.block(None,None)
        native.read=lambda a,b:native.current_state if b==318 else (0x500).to_bytes(4,'big')
        native.check_caps=lambda:None
        class Session:
            def __init__(self):self.calls=[];self.identifier=0;self.stops=iter(stops);self.current=None
            def inspect(self,method,args=None):
                self.calls.append((method,args))
                if method=='break_add':self.identifier+=1;return {'id':self.identifier}
                if method=='break_remove':return {}
                if method=='run_until':
                    self.current=next(self.stops)
                    native.current_state=bytes([self.current[3]])*318
                    if base:native.observer.contexts[base][:]=native.current_state
                    else:native.observer.shadow[:]=native.current_state
                    pc,sp,cck,_=self.current
                    return dict(pc=pc,cck=cck,seconds=cck/1000000,frame=0,vpos=0,hpos=0)
                if method=='regs.get':
                    return dict(pc=self.current[0],a=[0]*5+[base,0,self.current[1]],d=[0xdead0010,0xbeef0000]+[0]*6,sr=0x2300)
                raise AssertionError(method)
        native.session=Session()
        return native

    def test_private_body_reads_supplied_context_and_keeps_canonical_frozen(self):
        native=self.body_native([(0x400,0x1800,1,0),(0x500,0x1804,9,1),(0x900,0x1900,10,1)],0x3000)
        native.run_owned_api('game_preview_step',1)
        self.assertEqual(native.observer.rows[0]['after'],'01'*318)
        self.assertEqual(native.block(None,None),bytes(318))

    def test_known_wrong_variant_context_is_rejected(self):
        native=self.body_native([(0x400,0x1800,1,0)],0x4000)
        with self.assertRaisesRegex(AssertionError,'actual owner role'):
            native.run_owned_api('game_preview_step',1)

    def test_direct_unmarked_body_is_paired_and_counted_read_only(self):
        native=self.body_native([(0x400,0x1800,1,0),(0x500,0x1804,9,1),(0x900,0x1900,10,1)])
        stop=native.run_owned_api('game_preview_step',1)
        self.assertEqual(stop['pc'],0x900)
        self.assertEqual(native.observer.pending['bodies'],1)
        self.assertEqual(native.observer.rows[0]['arguments'],[16,0])
        self.assertEqual(native.observer.rows[0]['before'],'00'*318)
        self.assertEqual(native.observer.rows[0]['after'],'01'*318)
        self.assertEqual(native.internal_body_stops,2)
        methods=[m for m,_ in native.session.calls]
        self.assertNotIn('regs.set',methods);self.assertNotIn('mem.write',methods)
        returns=[a for m,a in native.session.calls if m=='break_add' and 'cond' in a]
        self.assertEqual(returns,[dict(kind='pc',addr=0x500,cond=dict(lhs='sp',op='eq',rhs=0x1804))])

    def test_body_protocol_rejects_stalled_resume_unpaired_and_budget_excess(self):
        for stops,error in (
                ([(0x400,0x1800,1,0)]*2,'without progress'),
                ([(0x400,0x1800,1,0),(0x900,0x1900,2,0)],'precedes actual body'),
                ([(0x400,0x1800,1,0),(0x500,0x1804,2,0),(0x400,0x1800,3,0)],'exceed requested')):
            native=self.body_native(stops)
            with self.assertRaisesRegex(AssertionError,error):native.run_owned_api('game_preview_step',1)
            added=[a for m,a in native.session.calls if m=='break_add']
            removed=[a for m,a in native.session.calls if m=='break_remove']
            self.assertEqual(len(added),len(removed),'Failed observation leaks debugger traps')

    def test_seek_counts_one_outer_call_and_retains_nested_body_frames(self):
        native=self.body_native([(0x400,0x1800,1,0),(0x420,0x1700,2,0),
            (0x520,0x1704,3,1),(0x500,0x1804,4,2),(0x900,0x1900,5,2)],0)
        frames=native.observer.body_frames
        frames.body_map[0x420]=dict(operation='game_round_poll',arity=0)
        frames.return_pcs.add(0x520)
        native.read=lambda a,b:native.current_state if b==318 else (0x520 if a==0x1700 else 0x500).to_bytes(4,'big')
        native.run_owned_api('game_history_seek_step',1)
        self.assertEqual(native.observer.pending['bodies'],2)
        self.assertEqual([r['depth'] for r in frames.records],[2,1])
        self.assertEqual(len(native.observer.rows),1)

    def test_genuine_tail_frames_share_one_return_breakpoint(self):
        native=self.body_native([(0x400,0x1800,1,0),(0x420,0x1800,2,0),
            (0x500,0x1804,3,1),(0x900,0x1900,4,1)],0)
        native.observer.body_frames.body_map[0x420]=dict(operation='game_round_poll',arity=0)
        native.run_owned_api('game_history_seek_step',1)
        self.assertEqual([r['depth'] for r in native.observer.body_frames.records],[2,1])
        additions=[a for m,a in native.session.calls if m=='break_add' and 'cond' in a]
        self.assertEqual(len(additions),1)
        removed=[a['id'] for m,a in native.session.calls if m=='break_remove']
        self.assertEqual(len(removed),len(set(removed)))

    def test_irq_resume_keeps_one_body_and_original_elapsed_time(self):
        native=self.body_native([(0x400,0x1800,1,0),(0x400,0x1800,4,0),
            (0x500,0x1804,9,1),(0x900,0x1900,10,1)])
        original=native.session.inspect
        def inspect(method,args=None):
            result=original(method,args)
            if method=='run_until' and result['cck']==4:
                native.observer.irq_writes.extend([dict(pc=pc,position=dict(cck=n))
                    for pc,n in ((0x600,2),(0x602,3))])
            return result
        native.session.inspect=inspect
        native.run_owned_api('game_preview_step',1)
        frame=native.observer.rows[0]
        from preview_native_extent import irq_resumptions_valid
        self.assertTrue(irq_resumptions_valid(frame))
        from copy import deepcopy
        bad=deepcopy(frame);bad['irq_resumptions'][0]['state']='ff'*318
        self.assertFalse(irq_resumptions_valid(bad))
        bad=deepcopy(frame);bad['irq_resumptions'][0]['acknowledgements'][1]['position']['cck']=1
        self.assertFalse(irq_resumptions_valid(bad))
        self.assertEqual(frame['elapsed_cck'],8)
        self.assertEqual(len(frame['irq_resumptions']),1)
        self.assertEqual(native.observer.pending['bodies'],1)
        self.assertEqual(native.internal_body_stops,2)
        self.assertEqual(len([a for m,a in native.session.calls if m=='break_add' and 'cond' in a]),1)

    def test_repeated_entry_fails_closed_without_irq_or_after_mutation(self):
        for change in ('no-irq','partial-irq','out-of-order','state','owner','registers','sr','a5','return','intent'):
            native=self.body_native([(0x400,0x1800,1,0),(0x400,0x1800,4,1 if change=='state' else 0)])
            original=native.session.inspect
            def inspect(method,args=None):
                result=original(method,args)
                if method=='run_until' and result['cck']==4:
                    if change!='no-irq':
                        native.observer.irq_writes.extend([dict(pc=pc,position=dict(cck=n))
                            for pc,n in ((0x600,2),) if change=='partial-irq'] or
                            [dict(pc=pc,position=dict(cck=n)) for pc,n in ((0x600,2),(0x602,3))])
                    if change=='out-of-order':native.observer.irq_writes[-1]['position']['cck']=1
                    if change=='owner':native.observer.number=lambda n,w=2:2 if n=='game_preview_active' else 1 if n=='game_preview_status' else 0
                    if change=='return':native.read=lambda a,b:native.current_state if b==318 else (0x502).to_bytes(4,'big')
                    if change=='intent':native.observer.body_frames.stack[-1]['events'].append({'unexpected':True})
                if method=='regs.get' and native.session.current[2]==4:
                    if change=='registers':result['d'][0]+=1
                    if change=='sr':result['sr']+=1
                    if change=='a5':result['a'][5]=0x4000
                return result
            native.session.inspect=inspect
            with self.assertRaisesRegex(AssertionError,'Repeated body entry|unknown supplied context'):
                native.run_owned_api('game_preview_step',1)

    def test_guard_removed_source_must_equal_reviewed_preview_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'amiga/game';path.mkdir(parents=True)
            from run_preview_native import SEEK_GUARD
            original=b'first\nsecond\nthird\n'
            source=SEEK_GUARD.encode()+b'first\n'+SEEK_GUARD.encode()+b'second\n'+SEEK_GUARD.encode()+b'third\n'
            (path/'preview.s').write_bytes(source)
            inherited={'evidence':{'files':{'amiga/game/preview.s':hashlib.sha256(original).hexdigest()}}}
            with patch('run_preview_native.ROOT',Path(directory)):
                self.assertTrue(worker_guard_closure(inherited)['passed'])
                (path/'preview.s').write_bytes(source+b'extra operation\n')
                with self.assertRaisesRegex(AssertionError,'beyond scoped seek guards'):worker_guard_closure(inherited)

    def test_overlay_dispatches_to_tool_helper_without_campaign_recursion(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            with patch('run_preview_native.run_command') as tool, \
                    patch('run_preview_native.compile_manifest',return_value={'files':{}}):
                executable,listing,manifest,identity=overlay(Path(directory))
            tool.assert_called_once()
            command=tool.call_args.args[0]
            self.assertEqual(command[0],str(ASSEMBLER))
            self.assertIn('-DCORE_TRACE=1',command)
            self.assertIn('-DDEMO_RECORDING=1',command)
            self.assertEqual(command[-1],str((Path(directory)/'main-preview-observer.s').relative_to(ROOT)))
            self.assertIn('        jsr     preview_native_hook',
                (Path(directory)/'main-preview-observer.s').read_text())
            self.assertEqual(executable.name,'preview-native')
            self.assertEqual(listing.name,'preview-native.lst')
            self.assertIn('scripts/preview_native_fixture.s',identity['original_sources'])

    def test_transition_callback_miss_and_fresh_input_are_not_excluded(self):
        rows=[dict(callback=1,entry={'cck':0},completion={'cck':40},fresh_input=False),
              dict(callback=2,entry={'cck':50},completion={'cck':111},fresh_input=True)]
        observer=SimpleNamespace(timer_start=0,timer_origin=65535,callback_rows=rows,
            api_rows=[dict(name='game_preview_step',elapsed_cck=30)],stack_min=100)
        native=SimpleNamespace(observer=observer,symbols={'game_stack_top':200})
        result=measurement(native,dict(simulation_interval_whole=10,simulation_interval_fraction=0))
        self.assertEqual(result['callback_distribution']['samples'],2)
        self.assertEqual(result['fresh_input_callback_distribution']['max_cck'],61)
        self.assertEqual(result['minimum_callback_headroom_cck'],-11)
        self.assertEqual(result['worker_distribution']['max_cck'],30)
        self.assertEqual(result['stack_bytes'],100)

    def test_replacement_resolution_can_cross_prime_without_spinning(self):
        class Resolver:
            def __init__(self):self.status=1;self.calls=[];self.cache=1;self.generation=9
            def number(self,name,width=2):return {
                'game_preview_status':self.status,'game_preview_cache_valid':self.cache,
                'game_preview_generation':self.generation}[name]
            def step(self,generation,budget):
                self.calls.append((generation,budget))
                if len(self.calls)==3:self.status=3 # resolver + primers in same bounded call
        native=Resolver();qualify_resolver(native,9)
        self.assertEqual(native.status,3)
        self.assertEqual(native.calls,[(9,4)]*3)
        native.cache=0
        with self.assertRaisesRegex(AssertionError,'no prepared context'):
            qualify_resolver(native,9)
        native.cache=1;native.status=6
        with self.assertRaisesRegex(AssertionError,'became unavailable'):
            qualify_resolver(native,9)
        native.generation=10
        with self.assertRaisesRegex(AssertionError,'generation retired'):
            qualify_resolver(native,9)

    def test_native_prefix_is_derived_from_recorded_dispatches(self):
        names=('game_court_x','game_court_y','game_ball_x','game_ball_y',
            'game_contact','game_flight','game_ball_colour','game_shadow_colour','game_tick')
        symbols={name:0x1000+n for n,name in enumerate(names)};symbols['game_core_state']=0x1000
        state1=bytes(range(9))+bytes(309);state2=bytes(range(1,10))+bytes(309)
        native=SimpleNamespace(cpu=None,symbols=symbols,states={2:state1,4:state2},
            normal=[('game_round_poll',[]),('game_tick_dispatch',[]),
                ('game_core_sample_pads',[0,0]),('game_tick_dispatch',[])],
            launches=[dict(end=1,origin=1)])
        from preview_proof import point
        expected=point(state1,symbols)+point(state2,symbols)
        result=dict(incoming=1,prefix=2,paths=[expected+bytes(8),expected+bytes(8)])
        with patch('run_preview_native.attempts',return_value=[(4,2,0)]):
            proof=verify_incoming_prefix(native,0,4,result)
            self.assertEqual(proof['operation_cursors'],[1,3])
            self.assertEqual(proof['expected_bytes'],expected.hex())
            # The two product paths agree, but neither agrees with actual history.
            result['paths']=[bytes(24),bytes(24)]
            with self.assertRaisesRegex(AssertionError,'actual retained flight'):
                verify_incoming_prefix(native,0,4,result)

    def test_immutable_cpu_pass_cannot_override_latest_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            saved=Path(directory)/'saved.json';current=Path(directory)/'current.json'
            data=json.dumps({'passed':True,'run':'reviewed'}).encode()
            saved.write_bytes(data);current.write_bytes(data)
            from acceptance_campaign import canonical
            (Path(directory)/'started.json').write_text(json.dumps(dict(id='preview-cpu',dependencies={},dependency_key=canonical({}))))
            with patch('run_preview_native.CPU9_RECEIPT',saved), \
                    patch('run_preview_native.CPU9_CURRENT',current), \
                    patch('run_preview_native.CPU9_SHA',hashlib.sha256(data).hexdigest()), \
                    patch('run_preview_native.CPU9_START',Path(directory)/'started.json'), \
                    patch('acceptance_campaign.execution_blocker',return_value=None), \
                    patch('run_preview_native.CPU9_KEY',None):
                self.assertTrue(inherited_endpoints()['passed'])
                current.write_text(json.dumps({'passed':False,'run':'newer-failed'}))
                with self.assertRaisesRegex(AssertionError,'Latest CPU proof'):
                    inherited_endpoints()
                current.write_text(json.dumps({'passed':True,'run':'unreviewed-newer'}))
                with self.assertRaisesRegex(AssertionError,'Latest CPU proof'):
                    inherited_endpoints()

    def test_preview_retirement_requires_actual_canceled_status(self):
        before=dict(generation=5,status=4,cache_valid=1)
        retired=dict(generation=6,status=7,cache_valid=0)
        verify_preview_retirement(before,retired)
        self.assertRegex((ROOT/'amiga/game/preview.s').read_text(),r'PREVIEW_CANCELED equ 7')
        for change in ({'status':0},{'status':4},{'cache_valid':1},{'generation':5}):
            with self.assertRaises(AssertionError):verify_preview_retirement(before,dict(retired,**change))

    def test_guest_admission_threshold_underflow_and_wrap_are_checked(self):
        def row(last,current,phase,interval):
            remaining=interval-phase-((last-current)&0xffffffff)
            return dict(last=last,current=current,phase=phase,interval=interval,
                remaining=max(0,remaining),reserve=10000,admitted=int(remaining>=10000),requested_work=1)
        for args,admitted in (((100,90,0,10010),1),((100,90,0,10009),0),
                ((100,90,12000,11838),0),((5,0xfffffff5,0,10016),1)):
            value=row(*args);self.assertEqual(verify_admission(value),admitted)
            value['admitted']=1-admitted
            with self.assertRaises(AssertionError):verify_admission(value)
        declined=row(100,90,0,10010);declined.update(requested_work=0,admitted=0)
        self.assertEqual(verify_admission(declined),0)
        declined['admitted']=1
        with self.assertRaises(AssertionError):verify_admission(declined)
        bad=row(100,90,0,10010);bad['remaining']+=1
        with self.assertRaises(AssertionError):verify_admission(bad)

    def test_fresh_seek_inheritance_rejects_consumed_input_or_tool_drift(self):
        receipt={'passed':True}
        with patch('run_preview_native.reviewed_execution',return_value=receipt), \
                patch('run_preview_native.status',return_value={'status':'passed'}) as verify:
            self.assertIs(fresh_seek_receipt(),receipt)
            from run_preview_native import SEEK_CURRENT
            verify.assert_called_once_with(SEEK_CURRENT)
        for reason in ('Changed consumed input','Changed tool','Changed compiled executable'):
            with patch('run_preview_native.reviewed_execution',return_value=receipt), \
                    patch('run_preview_native.status',return_value={'status':'failed','reason':reason}):
                with self.assertRaisesRegex(AssertionError,'inputs/tools/products drifted'):fresh_seek_receipt()

    def test_endpoint_inheritance_rejects_later_interrupted_execution(self):
        with patch('run_preview_native.digest',return_value='x'), \
                patch('run_preview_native.CPU9_SHA','x'), \
                patch('pathlib.Path.read_text',side_effect=[json.dumps({'passed':True}),
                    json.dumps(dict(id='preview-cpu',dependencies={},dependency_key=hashlib.sha256(b'{}').hexdigest()))]), \
                patch('run_preview_native.CPU9_KEY',None), \
                patch('acceptance_campaign.execution_blocker',return_value='Latest execution interrupted'):
            with self.assertRaisesRegex(AssertionError,'interrupted'):inherited_endpoints()

    def test_native_report_binds_fixture_executable_and_preserves_finalized_failure_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            executable=Path(directory)/'fixture';executable.write_bytes(b'actual emitted fixture bytes')
            report=native_report(executable,{'video':'PAL'},{'presentation_last_line':311},{'passed':True})
            self.assertEqual(report['executable_sha256'],hashlib.sha256(executable.read_bytes()).hexdigest())
            report['evidence']={'compiled_executables':{'fixture':report['executable_sha256']},
                'files':{'source':'bound-source-hash'},'artifacts':{'events':'bound-events-hash'}}
            path=Path(directory)/'report.json';path.write_text(json.dumps(report))
            diagnostic=Path(directory)/'receipt-unvalidated.json'
            preserve_pre_status_receipt(path,diagnostic)
            preserved=json.loads(diagnostic.read_text())
            self.assertFalse(preserved.pop('receipt_validated'))
            self.assertEqual(preserved,report)
            self.assertEqual(json.loads(path.read_text()),report)

    def test_native_artifacts_count_fresh_results_and_exclude_retry_diagnostic_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);path=folder/'report.json';diagnostic=folder/'receipt-unvalidated.json'
            # Fresh NTSC output: the newly written unvalidated result is bound.
            artifacts=native_receipt_artifacts(folder,path,{'passed':True},[])
            results=folder/'native-results-unvalidated.json'
            self.assertIn(results,artifacts)
            self.assertEqual(native_saved_bytes(folder,[]),results.stat().st_size)
            # Retry: a previous diagnostic must not be hashed then overwritten.
            diagnostic.write_bytes(b'previous receipt audit');path.write_bytes(b'failed canonical receipt')
            artifacts=native_receipt_artifacts(folder,path,{'passed':True},[])
            self.assertNotIn(diagnostic,artifacts);self.assertNotIn(path,artifacts)
            self.assertIn(results,artifacts)
            self.assertEqual(native_saved_bytes(folder,[]),sum(p.stat().st_size for p in folder.iterdir()))
            diagnostic.write_bytes(b'a longer newly finalized receipt audit copy')
            self.assertEqual(native_saved_bytes(folder,[]),sum(p.stat().st_size for p in folder.iterdir()))

    def test_private_readback_serialization_does_not_mutate_observation(self):
        source={'selected':bytes([1,2]),'rows':[(3,bytes([4]))]}
        self.assertEqual(json_value(source),{'selected':'0102','rows':[[3,'04']]})
        self.assertEqual(source['selected'],bytes([1,2]))


if __name__=='__main__':unittest.main()
