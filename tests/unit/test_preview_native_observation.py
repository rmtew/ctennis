"""Guard full write extents and precise IRQ values without an emulator."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from preview_native_observation import Observer


class NativePreviewGuards(unittest.TestCase):
    def observer(self):
        observer=object.__new__(Observer)
        observer.symbols={n:a for n,a in [('game_core_state',0x1000),
            ('game_history_state',0x2000),('game_history_buffer',0x3000),
            ('game_preview_storage',0x20000),('preview_native_mailbox',0x22000),
            ('core_trace_arguments',0x23000),('core_trace_marker',0x23010),
            ('game_stack_bottom',0x24000),('game_stack_top',0x25000)]}
        observer.frozen=True;observer.pending=None;observer.problems=[]
        observer.rules={};observer.irq_writes=[];observer.irq_inside=0
        observer.irq_entry_pc=0x400;observer.irq_exit_pc=0x420;observer.audio_writes=[]
        observer.publication={};observer.stack_min=0x25000
        return observer

    def event(self,address,size=2,pc=0x400,value=0):
        return dict(addr=address,size=size,pc=pc,value=value,position={'cck':1})

    def test_frozen_cross_boundary_and_external_call_writes(self):
        observer=self.observer()
        observer._guard(self.event(0x2ffe,4))
        self.assertIn('frozen history',observer.problems[-1])
        observer._guard(self.event(0x1000))
        self.assertIn('External native caller',observer.problems[-1])

    def test_owned_canonical_extent_does_not_permit_adjacent_bytes(self):
        observer=self.observer();observer.pending={'name':'game_preview_step'}
        observer._guard(self.event(0x1000+318-2,4))
        self.assertIn('Forbidden native API',observer.problems[-1])
        observer._guard(self.event(0xdead00))
        self.assertEqual(len(observer.problems),2)

    def test_audio_write_cannot_use_presentation_pc_allowance(self):
        observer=self.observer();observer.pending={'name':'game_preview_step'}
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

    def test_external_preview_scratch_cannot_change_between_calls(self):
        observer=self.observer()
        observer._guard(self.event(observer.symbols['game_preview_storage']))
        self.assertIn('frozen preview context',observer.problems[-1])

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


if __name__=='__main__':unittest.main()
