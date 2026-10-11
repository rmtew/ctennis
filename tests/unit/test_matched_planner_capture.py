import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import matched_planner_capture as m


class Session:
    def __init__(self):
        self.memory=bytearray(524288);self.calls=[];self.cck=10
        self.symbols={}
        for index,(_,start,end) in enumerate(m.REGIONS):
            self.symbols[start]=0x100+index*0x400
            self.symbols[end]=self.symbols[start]+(318 if index==0 else 72 if index==1 else 32)
        for index,name in enumerate(('tutorial_active','tutorial_menu','game_preview_active','game_preview_explicit','game_history_seek_active','keyboard_ack','ready_completed','display_ready','ready_copper','tutorial_pending','tutorial_work_pending','tutorial_render_phase','tutorial_placement_dirty','tutorial_footer_ready','tutorial_footer_dirty','game_keyboard_matrix')):
            self.symbols[name]=0x3000+index*0x100
        self.memory[self.symbols['tutorial_active']]=255
        self.symbols.update(main_loop=0x5000,game_stack_top=0x6000,experiment_word=0x7000)
    def inspect(self,method,args=None):
        args=args or {};self.calls.append((method,args))
        if method=='status':return dict(state='paused',cck=self.cck)
        if method=='regs.get':return dict(pc=self.symbols['main_loop'],a=[0]*7+[self.symbols['game_stack_top']])
        if method=='mem.read':return dict(data=bytes(self.memory[args['addr']:args['addr']+args['len']]).hex())
        if method=='mem.write':self.memory[args['addr']:args['addr']+2]=bytes.fromhex(args['data']);return {}
        if method=='state.save':Path(args['path']).write_bytes(b'fixture-only');return {}
        return {}


class MatchedPlannerTests(unittest.TestCase):
    def test_anchor_rejects_owner_ack_pending_and_held_d(self):
        for name in ('game_preview_active','game_preview_explicit','keyboard_ack','ready_completed','tutorial_footer_ready'):
            s=Session();s.memory[s.symbols[name]]=1
            with self.assertRaisesRegex(AssertionError,'active owner'):m.require_anchor(s,s.symbols)
        s=Session();s.memory[s.symbols['game_keyboard_matrix']+0x22]=1
        with self.assertRaisesRegex(AssertionError,'D already held'):m.require_anchor(s,s.symbols)

    def test_full_snapshot_and_declared_word_only(self):
        s=Session();a=m.require_anchor(s,s.symbols)
        self.assertEqual(len(bytes.fromhex(a['regions']['canonical'])),318)
        self.assertEqual(m.configure_once(s,s.symbols,'experiment_word',1)['after'],'0001')
        self.assertEqual(sum(s.memory),256)

    def test_readonly_observer_cannot_adapt_run_input_or_memory(self):
        s=Session();readonly=m.ReadOnlyControl(s)
        for method in ('input.key','mem.write','run_until','state.load','regs.set'):
            with self.assertRaisesRegex(AssertionError,'mutation'):readonly.inspect(method)
        self.assertEqual(s.calls,[])

    def test_fixed_future_raw_d_window(self):
        w=m.Window('NTSC',100,200,300,'experiment_word')
        self.assertEqual(w.validate(10),[dict(rawkey=0x22,action='press',cck=100),dict(rawkey=0x22,action='release',cck=200)])
        with self.assertRaises(AssertionError):m.Window('PAL',10,200,300,'experiment_word').validate(10)

    def test_baseline_mismatch_forbids_enabled_trial(self):
        s=Session();w=m.Window('PAL',100,200,300,'experiment_word')
        with tempfile.TemporaryDirectory() as d,patch.object(m,'capture_pass',side_effect=[dict(label='baseline-1',state='one'),dict(label='baseline-2',state='two')]) as capture:
            with self.assertRaisesRegex(AssertionError,'enabled trial forbidden'):m.matched_capture(s,s.symbols,Path(d)/'anchor.clstate',w,None)
            self.assertEqual(capture.call_count,2)

    def test_matched_baseline_gates_same_candidate_enabled_pass(self):
        s=Session();w=m.Window('PAL',100,200,300,'experiment_word')
        with tempfile.TemporaryDirectory() as d,patch.object(m,'capture_pass',side_effect=[dict(label='baseline-1',state='same'),dict(label='baseline-2',state='same'),dict(label='enabled',state='candidate')]) as capture:
            result=m.matched_capture(s,s.symbols,Path(d)/'anchor.clstate',w,None)
            self.assertTrue(result['baseline_replay_equal']);self.assertEqual(capture.call_count,3)
            self.assertEqual([call.args[5] for call in capture.call_args_list],[0,0,1])

    def test_missing_native_extent_fails(self):
        with self.assertRaisesRegex(AssertionError,'omitted'):m.validate_observation({})
