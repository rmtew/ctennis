"""Guard full write extents and precise IRQ values without an emulator."""
import sys
import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from preview_native_observation import Observer, BodyFrames
from native_longword_observer import LongwordObserver


class NativePreviewGuards(unittest.TestCase):
    def observer(self):
        observer=object.__new__(Observer)
        observer.symbols={n:a for n,a in [('game_core_state',0x1000),
            ('game_history_state',0x2000),('game_history_buffer',0x3000),
            ('game_preview_storage',0x20000),('game_history_seek_storage',0x27000),('preview_native_mailbox',0x22000),
            ('core_trace_arguments',0x23000),('core_trace_marker',0x23010),
            ('game_stack_bottom',0x24000),('game_stack_top',0x25000)]}
        observer.storage_bytes=10974
        observer.frozen=True;observer.pending=None;observer.problems=[]
        observer.rules={};observer.irq_writes=[];observer.irq_inside=0
        observer.irq_entry_pc=0x400;observer.irq_exit_pc=0x420;observer.audio_writes=[]
        observer.publication={};observer.stack_min=0x25000
        observer.body_frames=SimpleNamespace(stack=[])
        return observer

    def event(self,address,size=2,pc=0x400,value=0):
        return dict(addr=address,size=size,pc=pc,value=value,position={'cck':1})

    def test_seek_private_writes_require_owned_seek_api_and_complete_extent(self):
        observer=self.observer()
        observer._guard(self.event(0x27000))
        self.assertIn('External caller writes frozen seek',observer.problems[-1])
        observer.pending={'name':'game_preview_step','begin':{'cck':0},'end':None}
        observer._guard(self.event(0x27000))
        self.assertIn('Non-seek API',observer.problems[-1])
        observer.pending['name']='game_history_seek_step';observer.problems.clear()
        observer._guard(self.event(0x27000))
        self.assertEqual(observer.problems,[])
        observer._guard(self.event(0x27000+732,4))
        self.assertIn('Forbidden native API',observer.problems[-1])

    def test_frozen_cross_boundary_and_external_call_writes(self):
        observer=self.observer()
        observer._guard(self.event(0x2ffe,4))
        self.assertIn('frozen history',observer.problems[-1])
        observer._guard(self.event(0x1000))
        self.assertIn('External native caller',observer.problems[-1])

    def test_owned_canonical_extent_does_not_permit_adjacent_bytes(self):
        observer=self.observer();observer.pending={'name':'game_preview_step','begin':{'cck':0},'end':None}
        observer._guard(self.event(0x1000+318-2,4))
        self.assertIn('Forbidden native API',observer.problems[-1])
        observer._guard(self.event(0xdead00))
        self.assertEqual(len(observer.problems),2)

    def test_audio_write_cannot_use_presentation_pc_allowance(self):
        observer=self.observer();observer.pending={'name':'game_preview_step','begin':{'cck':0},'end':None}
        observer.rules[0x400]=dict(address=0xdff09c,bytes=2,operation='move',
            source='#$0010',destination='$dff09c')
        observer._guard(self.event(0xdff0a8,value=64))
        self.assertIn('Forbidden native API',observer.problems[-1])

    def test_continuous_audio_guard_allows_pause_only_before_freeze(self):
        observer=self.observer()
        observer._guard(self.event(0xdff0a8,value=0))
        self.assertIn('frozen audio/config',observer.problems[-1])
        observer.frozen=False;observer.problems.clear()
        observer._guard(self.event(0xdff0a8,value=0))
        self.assertEqual(observer.problems,[])
        observer.frozen=True
        observer._guard(self.event(0xdff09e,value=0x8000))
        self.assertIn('frozen audio/config',observer.problems[-1])
        observer._guard(self.event(0xdff096,value=0x8200))
        self.assertIn('DMA configuration',observer.problems[-1])

    def test_outside_dma_permission_cannot_be_borrowed_by_adjacent_store(self):
        observer=self.observer()
        observer.rules[0x400]=dict(address=0xdff096,bytes=2,operation='move',
            source='#$8020',destination='$dff096')
        observer._guard(self.event(0xdff096,value=0x8020))
        self.assertEqual(observer.problems,[])
        observer._guard(self.event(0xdff095,value=0x8020))
        self.assertIn('DMA configuration',observer.problems[-1])
        observer._guard(self.event(0xdff097,value=0x8020))
        self.assertIn('DMA configuration',observer.problems[-1])

    def test_external_ui_publication_requires_exact_instruction_and_value(self):
        observer=self.observer()
        observer.symbols.update(ready_copper=0x26000,spare_copper=0x26004,
            ready_completed=0x26008,discard_ready_scene=0x600)
        observer.publication=dict(ready_copper=bytearray.fromhex('00012340'),
            spare_copper=bytearray(4),ready_completed=bytearray(1))
        observer.source_shadow={};observer.producer_bank=None
        observer.outside_publication_writes=[]
        observer.outside_publication_rules={0x500:dict(address=0x26004,bytes=4,
            destination='spare_copper',operation='move',source='ready_copper')}
        observer._guard(self.event(0x26004,4,pc=0x500,value=0x12340))
        self.assertEqual(observer.problems,[])
        self.assertEqual(len(observer.outside_publication_writes),1)
        observer._guard(self.event(0x26004,4,pc=0x500,value=0x12344))
        self.assertIn('producer write value',observer.problems[-1])
        observer._guard(self.event(0x26006,4,pc=0x500,value=0))
        self.assertIn('Unattributed',observer.problems[-1])

    def test_expanded_preview_extent_keeps_far_end_and_crossing_writes_guarded(self):
        observer=self.observer();base=observer.symbols['game_preview_storage']
        observer._guard(self.event(base+9000))
        self.assertIn('External caller writes frozen preview context',observer.problems)
        observer=self.observer();observer.pending={'name':'game_preview_step'}
        observer._guard(self.event(base+9984,4))
        self.assertTrue(observer.problems, 'A write crossing the complete scratch extent was permitted')

    def test_external_preview_scratch_cannot_change_between_calls(self):
        observer=self.observer()
        observer._guard(self.event(observer.symbols['game_preview_storage']))
        self.assertIn('frozen preview context',observer.problems[-1])

    def input_observer(self):
        observer=self.observer()
        names=('game_keyboard_matrix','ui_joystick_bits','ui_joystick_previous',
            'ui_joystick_pressed','keyboard_ack_timer','ui_saved_volumes')
        observer.symbols.update({name:0x30000+index*0x100 for index,name in enumerate(names)})
        observer.input_shadow={name:bytearray(128 if name=='game_keyboard_matrix' else 6) for name in names}
        observer.current_callback=dict(callback=1,fresh_input=False)
        observer.physical_edges=[];observer.joystick_pressed_observations=[]
        observer.expected_joystick_pressed=[0,0]
        return observer

    def test_ack_timers_and_audio_shadows_are_not_physical_edges(self):
        observer=self.input_observer()
        for name in ('keyboard_ack_timer','ui_saved_volumes'):
            observer.input_write(name,observer.symbols[name],bytes([1]),{'cck':1})
        self.assertFalse(observer.current_callback['fresh_input'])
        self.assertEqual(observer.physical_edges,[])

    def test_actual_physical_press_and_release_observations(self):
        observer=self.input_observer();position={'cck':1}
        def write(name,value):observer.input_write(name,observer.symbols[name],bytes([value]),position)
        write('ui_joystick_bits',4);write('ui_joystick_previous',4);write('ui_joystick_pressed',4)
        write('ui_joystick_bits',0);write('ui_joystick_previous',0);write('ui_joystick_pressed',0)
        write('game_keyboard_matrix',1);write('game_keyboard_matrix',0)
        self.assertTrue(observer.current_callback['fresh_input'])
        self.assertEqual([(r['pressed_bits'],r['released_bits']) for r in observer.physical_edges],
            [(4,0),(0,4),(1,0),(0,1)])
        self.assertEqual(len(observer.joystick_pressed_observations),2)
        with self.assertRaisesRegex(AssertionError,'pressed mask differs'):
            write('ui_joystick_pressed',4)

    def test_pre_and_post_api_irq_frames_do_not_change_return_bracket(self):
        observer=self.observer();observer.slot=0x28fd6
        observer.symbols.update(preview_native_call=0x2bfb4,preview_native_after=0x2bfb6)
        observer.rts_pcs={0x25a70};observer.restore_dummy_pcs=set()
        observer.return_store=LongwordObserver();observer.return_reads=LongwordObserver()
        observer.pending=dict(name='game_preview_request',begin=None,end=None)
        irq=self.event(0x28fd8,2,0x2bfa8,0xbfac)
        observer.return_slot_write(irq)
        observer.return_read(irq) # RTE reads the exception frame before JSR.
        self.assertIsNone(observer.pending['begin'])
        self.assertEqual(observer.return_store.seen,set())
        self.assertEqual(observer.return_reads.seen,set())
        # Frozen selected state remains protected even while a mailbox is pending.
        observer._guard(self.event(0x1000,2,0x2bfa8,0))
        self.assertIn('External native caller',observer.problems[-1])
        jsr=self.event(0x28fd6,4,0x2bfb4,0x2bfb6)
        observer.return_slot_write(jsr)
        self.assertEqual(observer.pending['begin'],jsr['position'])
        with self.assertRaisesRegex(AssertionError,'return slot overwritten'):
            observer.return_slot_write(irq)
        observer.return_read(self.event(0x28fd6,4,0x25a70,0x2bfb6))
        completed=dict(observer.pending['end'])
        observer.return_slot_write(irq);observer.return_read(irq)
        self.assertEqual(observer.pending['end'],completed)
        self.assertEqual(observer.return_store.seen,set())
        self.assertEqual(observer.return_reads.seen,set())

    def test_movem_dummy_read_does_not_complete_or_seed_the_rts(self):
        observer=self.observer();observer.slot=0x28fd6
        observer.symbols['preview_native_after']=0x2bfb6
        observer.rts_pcs={0x25a70};observer.restore_dummy_pcs={0x25a6a}
        observer.return_reads=LongwordObserver();observer.pending={'begin':{'cck':1},'end':None}
        def read(pc,address,size,value):
            event=self.event(address,size,pc,value);event['position']={'cck':17}
            observer.return_read(event)
        read(0x25a6a,0x28fd6,2,2)
        self.assertIsNone(observer.pending['end'])
        self.assertEqual(observer.return_reads.seen,set())
        self.assertEqual(len(observer.pending['restore_dummy_reads']),1)
        for pc,address,size,value in ((0x25a68,0x28fd6,2,2),
                (0x25a6a,0x28fd8,2,2),(0x25a6a,0x28fd6,4,0x2bfb6),
                (0x25a6a,0x28fd6,2,3)):
            with self.assertRaisesRegex(AssertionError,'exact emitted MOVEM'):
                read(pc,address,size,value)
        read(0x25a70,0x28fd8,2,0xbfb6)
        self.assertIsNone(observer.pending['end']) # Dummy high word was ignored.
        read(0x25a70,0x28fd6,2,2)
        self.assertEqual(observer.pending['end'],{'cck':17})
        observer.pending['end']=None
        with self.assertRaisesRegex(AssertionError,'another address'):
            read(0x25a70,0x28fd6,4,0x2bfb8)
        self.assertIsNone(observer.pending['end'])

    def test_irq_ack_value_and_actual_api_interval(self):
        observer=self.observer()
        observer.pending=dict(name='game_preview_step',begin=None,end=None,irq=0,irq_acknowledgements=0)
        observer.rules[0x400]=dict(address=0xdff09c,bytes=2,operation='move',
            source='#$0010',destination='$dff09c')
        observer._guard(self.event(0xdff09c,value=16))
        self.assertEqual(observer.irq_inside,0)
        observer.pending['begin']={'cck':0}
        observer._guard(self.event(0xdff09c,value=16))
        self.assertEqual(observer.irq_inside,1)
        observer.rules[0x420]=dict(observer.rules[0x400])
        observer._guard(self.event(0xdff09c,value=16,pc=0x420))
        self.assertEqual(observer.irq_inside,1)
        self.assertEqual(observer.pending['irq_acknowledgements'],2)
        observer.pending['end']={'cck':2}
        observer._guard(self.event(0xdff09c,value=16))
        self.assertEqual(observer.irq_inside,1)
        observer._guard(self.event(0xdff09c,value=32))
        self.assertIn('Incorrect actual presentation IRQ',observer.problems[-1])

    def test_owned_sink_ledger_does_not_depend_on_wrapper_markers(self):
        observer=self.observer();observer.pending=dict(begin={'cck':0},end=None,bodies=1)
        observer.operations={3:('game_core_sample_pads',2)};observer.active=None
        observer.argbytes=bytearray(12);observer.argwritten=set();observer.outside_events=[]
        observer.api_rows=[];observer.body_sink_events=[]
        observer.body_frames=BodyFrames({0x400:dict(operation='game_core_sample_pads',arity=2)},
            0x1000,0x2000,{0x500})
        observer.body_frames.entry(0x400,dict(pc=0x400,a=[0]*7+[0x1800],d=[0]*8),
            0x500,bytes(318),{'cck':1},{'active':2},0)
        observer._marker(3,{'cck':1}) # Recorded wrapper header does not duplicate the actual body.
        observer.argbytes[:4]=bytes.fromhex('00000007');observer.argwritten=set(range(4))
        observer._marker(0x106,{'cck':2})
        observer._marker(0,{'cck':3})
        self.assertIsNone(observer.active)
        self.assertEqual(observer.pending['bodies'],1)
        self.assertEqual(observer.body_frames.stack[0]['events'],[['level',0,7]])
        self.assertEqual(observer.body_sink_events,[dict(event=['level',0,7],position={'cck':2},api_row_index=0)])
        observer.body_frames.exit(0x500,0x1804,bytes(318),{'cck':4})
        observer.argwritten=set(range(4))
        with self.assertRaisesRegex(AssertionError,'outside an observed'):
            observer._marker(0x106,{'cck':5})


class NativeBodyPairs(unittest.TestCase):
    def frames(self):
        return BodyFrames({0x400:dict(operation='game_core_sample_pads',arity=2),
            0x420:dict(operation='game_round_poll',arity=0)},0x1000,0x2000,{0x500,0x520})

    def entry(self,frames,pc=0x400,sp=0x1800,return_pc=0x500):
        registers=dict(pc=pc,a=[0]*7+[sp],d=[0xdead0010,0xbeef0002]+[0x12345678]*6,sr=0x2300)
        return frames.entry(pc,registers,return_pc,bytes(318),{'cck':1},
            {'active':2,'status':3,'variant':0},7)

    def test_declared_arity_and_complete_state_are_actual_capture(self):
        frames=self.frames();row=self.entry(frames)
        self.assertEqual(row['arguments'],[16,2])
        self.assertEqual(row['entry_registers']['d'][2],0x12345678)
        frames.sink(['title'])
        done=frames.exit(0x500,0x1804,bytes([1])*318,{'cck':8})
        self.assertEqual(done[0]['events'],[['title']])
        self.assertEqual(done[0]['after'],'01'*318)
        self.assertEqual(frames.internal_stops,2)

    def test_nested_same_return_pc_requires_exact_innermost_stack(self):
        frames=self.frames();self.entry(frames)
        self.entry(frames,0x420,0x1700,0x500)
        frames.sink(['level',0,7])
        with self.assertRaisesRegex(AssertionError,'innermost'):
            frames.exit(0x500,0x1804,bytes(318),{'cck':3})
        child=frames.exit(0x500,0x1704,bytes(318),{'cck':4})[0]
        parent=frames.exit(0x500,0x1804,bytes(318),{'cck':5})[0]
        self.assertEqual(child['arguments'],[])
        self.assertEqual(parent['events'],child['events'])
        self.assertEqual(parent['depth'],1);self.assertEqual(child['depth'],2)

    def test_tail_frames_drain_at_one_physical_return(self):
        frames=self.frames();self.entry(frames)
        self.entry(frames,0x420,0x1800,0x500)
        completed=frames.exit(0x500,0x1804,bytes(318),{'cck':5})
        self.assertEqual(len(completed),2)
        self.assertEqual(frames.stack,[])
        self.assertEqual(frames.internal_stops,3)

    def test_invalid_stack_return_state_and_missing_entry_reject(self):
        for pc,sp,return_pc in ((0x444,0x1800,0x500),(0x400,0x1801,0x500),
                (0x400,0x2000,0x500),(0x400,0x1800,0x501)):
            with self.assertRaises(AssertionError):self.entry(self.frames(),pc,sp,return_pc)
        frames=self.frames()
        with self.assertRaisesRegex(AssertionError,'without entry'):
            frames.exit(0x500,0x1804,bytes(318),{'cck':5})
        with self.assertRaisesRegex(AssertionError,'outside an observed'):
            frames.sink(['title'])
        self.entry(frames)
        with self.assertRaisesRegex(AssertionError,'complete canonical'):
            frames.exit(0x500,0x1804,bytes(317),{'cck':5})

    def test_nesting_and_non_descending_frames_are_bounded(self):
        frames=self.frames();self.entry(frames)
        with self.assertRaisesRegex(AssertionError,'does not descend'):
            self.entry(frames,0x420,0x1810,0x520)
        for index in range(1,9):self.entry(frames,0x420,0x1800-4*index,0x520)
        with self.assertRaisesRegex(AssertionError,'nine-body'):
            self.entry(frames,0x420,0x1700,0x520)


class NativeEventArchive(unittest.TestCase):
    def observer(self,directory):
        observer=object.__new__(Observer)
        observer.raw_path=Path(directory)/'events.jsonl.gz'
        observer.raw=gzip.open(observer.raw_path,'wt',encoding='utf-8',compresslevel=3)
        observer.raw_bytes=observer.raw_uncompressed_bytes=observer.notifications=observer.drops=0
        observer.problems=[]
        return observer

    def test_all_literal_notifications_survive_gzip_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            observer=self.observer(directory)
            records=[dict(method='event.frame',params=dict(index=index,dropped_notifications=0,
                note='literal repeated notification')) for index in range(513)]
            for record in records:observer.observe(record)
            self.assertGreater(observer.raw_bytes,0) # Incremental 512-record flush happened.
            observer.close()
            with gzip.open(observer.raw_path,'rt',encoding='utf-8') as archive:
                self.assertEqual([json.loads(line) for line in archive],records)
            self.assertEqual(observer.notifications,len(records))
            expected=sum(len((json.dumps(r,separators=(',',':'))+'\n').encode()) for r in records)
            self.assertEqual(observer.raw_uncompressed_bytes,expected)
            self.assertEqual(observer.raw_bytes,observer.raw_path.stat().st_size)
            self.assertLess(observer.raw_bytes,observer.raw_uncompressed_bytes)

    def test_saved_cap_counts_other_artifacts_and_does_not_drop_records(self):
        with tempfile.TemporaryDirectory() as directory:
            observer=self.observer(directory)
            (Path(directory)/'other-artifact').write_bytes(bytes(256))
            record=dict(method='event.frame',params=dict(dropped_notifications=0))
            with patch('preview_native_observation.RAW_CAP',128),patch('preview_native_observation.RESERVE',0):
                for _ in range(512):observer.observe(record)
            self.assertIn('Native stored-artifact cap approached',observer.problems)
            observer.close()
            with gzip.open(observer.raw_path,'rt',encoding='utf-8') as archive:
                self.assertEqual(len(list(archive)),512)


if __name__=='__main__':unittest.main()
