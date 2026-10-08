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
from run_preview_native import Native,measurement,json_value,qualify_resolver,verify_incoming_prefix,inherited_endpoints,overlay
from preview_native_observation import BodyFrames
from native_tools import ROOT,ASSEMBLER


class NativePreviewTiming(unittest.TestCase):
    def body_native(self,stops):
        native=object.__new__(Native)
        native.symbols={'preview_native_return':0x900};native.stop={'seconds':0};native.internal_body_stops=0
        frames=BodyFrames({0x400:dict(operation='game_core_sample_pads',arity=2)},0x1000,0x2000,{0x500})
        native.observer=SimpleNamespace(body_frames=frames,active=None,drops=0,problems=[],
            api_rows=[],rows=[],pending={'bodies':0},inside_api=lambda:True,
            number=lambda n,w=2:2 if n=='game_preview_active' else 0,
            state=lambda:native.current_state)
        native.current_state=bytes(318)
        native.block=lambda a,b:native.current_state
        native.read=lambda a,b:(0x500).to_bytes(4,'big')
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
                    pc,sp,cck,_=self.current
                    return dict(pc=pc,cck=cck,seconds=cck/1000000,frame=0,vpos=0,hpos=0)
                if method=='regs.get':
                    return dict(pc=self.current[0],a=[0]*7+[self.current[1]],d=[0xdead0010,0xbeef0000]+[0]*6,sr=0x2300)
                raise AssertionError(method)
        native.session=Session()
        return native

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
            with patch('run_preview_native.CPU9_RECEIPT',saved), \
                    patch('run_preview_native.CPU9_CURRENT',current), \
                    patch('run_preview_native.CPU9_SHA',hashlib.sha256(data).hexdigest()):
                self.assertTrue(inherited_endpoints()['passed'])
                current.write_text(json.dumps({'passed':False,'run':'newer-failed'}))
                with self.assertRaisesRegex(AssertionError,'Latest CPU proof'):
                    inherited_endpoints()
                current.write_text(json.dumps({'passed':True,'run':'unreviewed-newer'}))
                with self.assertRaisesRegex(AssertionError,'Latest CPU proof'):
                    inherited_endpoints()

    def test_private_readback_serialization_does_not_mutate_observation(self):
        source={'selected':bytes([1,2]),'rows':[(3,bytes([4]))]}
        self.assertEqual(json_value(source),{'selected':'0102','rows':[[3,'04']]})
        self.assertEqual(source['selected'],bytes([1,2]))


if __name__=='__main__':unittest.main()
