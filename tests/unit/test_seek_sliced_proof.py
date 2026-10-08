"""Focused input provenance and observation-owner negatives; no host tennis model."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from match_core_cpu import Core
from run_seek_sliced_proof import input_stream,proof_inputs,INPUT,INPUT_SHA
from native_tools import ROOT


class SeekObservationOwner(unittest.TestCase):
    def cpu(self,preview=0,seek=0):
        cpu=object.__new__(Core)
        cpu.symbols={'game_preview_active':1,'game_history_seek_active':2,'game_preview_variant':3}
        cpu.mem=SimpleNamespace(r8=lambda address:{1:preview,2:seek,3:1}[address])
        cpu.cpu=SimpleNamespace(r_reg=lambda reg:0xdead0007 if reg==7 else 0xbeef002a)
        cpu.events=[['interrupted-existing-intent']];cpu.preview_events=[];cpu.seek_events=[]
        cpu.preview_event_groups={}
        return cpu

    def test_seek_intents_are_separate_without_replacing_live_ledger(self):
        cpu=self.cpu(seek=1);live=cpu.events
        cpu.observe_adapter('game_audio_write_level')
        self.assertIs(cpu.events,live)
        self.assertEqual(cpu.events,[['interrupted-existing-intent']])
        self.assertEqual(cpu.seek_events,[['level',7,42]])
        self.assertEqual(cpu.preview_events,[])

    def test_ordinary_and_preview_routes_remain_distinct(self):
        cpu=self.cpu();cpu.observe_adapter('game_audio_write_level')
        self.assertEqual(cpu.events[-1],['level',7,42]);self.assertEqual(cpu.seek_events,[])
        cpu=self.cpu(preview=2);cpu.observe_adapter('game_audio_write_level')
        self.assertEqual(cpu.preview_event_groups,{(2,1):[['level',7,42]]})
        self.assertEqual(cpu.events,[['interrupted-existing-intent']]);self.assertEqual(cpu.seek_events,[])

    def test_overlapping_seek_and_preview_owner_is_rejected(self):
        cpu=self.cpu(preview=1,seek=1)
        with self.assertRaisesRegex(AssertionError,'cannot own one actual body'):
            cpu.observe_adapter('game_audio_write_level')
        self.assertEqual(cpu.events,[['interrupted-existing-intent']])
        self.assertEqual(cpu.preview_events,[]);self.assertEqual(cpu.seek_events,[])


class ActualPrefixContract(unittest.TestCase):
    def test_provenance_call_arity_and_build_tools_are_preserved(self):
        with patch('run_seek_sliced_proof.inputs_for',return_value=({ROOT/'amiga/main.s'},
                {'assembler':{'sha256':'assembler-pin'},'copperline':{'sha256':'emulator-pin'}})) as declared, \
                patch('run_seek_sliced_proof.cpu_tool_inputs',return_value=({ROOT/'cpu-provider'}, {'version':'cpu-pin'})):
            paths,tools=proof_inputs({'source_files':{'raw-source':'hash'}})
        declared.assert_called_once_with('build','scripts/run_seek_sliced_proof.py')
        self.assertEqual(paths,{ROOT/'amiga/main.s',ROOT/'cpu-provider',ROOT/'raw-source',INPUT})
        self.assertEqual(tools,{'assembler':{'sha256':'assembler-pin'},'copperline':{'sha256':'emulator-pin'},
            'machine68k':{'version':'cpu-pin'}})

    def document(self):
        return dict(initialization=dict(operation='game_core_init',arguments=[]),
            source_files={'retained-source':'source-sha'},
            rows=[dict(cursor=index,operation='game_round_poll',arguments=[]) for index in range(1,836)])

    def read(self,document,prefix_hash=INPUT_SHA,source_hash='source-sha'):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'prefix.json';path.write_text(json.dumps(document))
            with patch('run_seek_sliced_proof.INPUT',path), \
                    patch('run_seek_sliced_proof.digest',side_effect=lambda p:prefix_hash if p==path else source_hash):
                return input_stream()

    def test_exact_recorded_prefix_and_source_hashes_are_required(self):
        document=self.document();saved,stream=self.read(document)
        self.assertEqual(saved,document);self.assertEqual(len(stream),835)
        with self.assertRaisesRegex(AssertionError,'Pinned actual native input'):
            self.read(document,prefix_hash='changed')
        with self.assertRaisesRegex(AssertionError,'Original native input evidence'):
            self.read(document,source_hash='changed')

    def test_missing_reordered_or_wrong_initialization_rejects(self):
        for change in ('missing','reordered','initialization'):
            document=self.document()
            if change=='missing':document['rows'].pop()
            elif change=='reordered':document['rows'][0]['cursor']=2
            else:document['initialization']['arguments']=[1]
            with self.assertRaises(AssertionError):self.read(document)


if __name__=='__main__':unittest.main()
