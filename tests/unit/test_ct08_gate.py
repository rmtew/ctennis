"""Finite audio receipts must retain hardware fault and extent protection."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import progress

class AudioProof(unittest.TestCase):
    def setUp(self):
        self.rows_patch=patch.object(progress,'audio_expected_rows',return_value=[17]);self.rows_patch.start();self.addCleanup(self.rows_patch.stop)
        self.report={'case':'p2-first-serve-pitch','subject':'maintained-native','passed':True,'first_difference':None,
            'state_contract':progress.MAINTAINED_STATE_CONTRACT,
            'omitted_legacy_scratch_offsets':list(progress.MAINTAINED_SCRATCH_OFFSETS),
            'raw_state_differences':[{'offset':103}], 'self_test':True,
            'native_executable_sha256':'normal','mutation':{'executable_sha256':'fault','detected_difference':{'update':17}},
            'observations':[{'update':17,'criterion_expected':1688,'criterion_actual':1688,'first_difference':None}]}
    def test_native_fault_control_required(self):
        self.assertTrue(progress.audio_proof(self.report,'p2-first-serve-pitch'))
        for key,value in [('subject','translated'),('self_test',False),('first_difference',{'update':17})]:
            r=copy.deepcopy(self.report);r[key]=value
            self.assertFalse(progress.audio_proof(r,'p2-first-serve-pitch'))
        r=copy.deepcopy(self.report);r['observations'][0]['update']=18
        self.assertFalse(progress.audio_proof(r,'p2-first-serve-pitch'))
        r=copy.deepcopy(self.report);r['case']='p2-first-serve-envelope'
        self.assertFalse(progress.audio_proof(r,'p2-first-serve-pitch'))
        r=copy.deepcopy(self.report);r['mutation']['executable_sha256']='normal'
        self.assertFalse(progress.audio_proof(r,'p2-first-serve-pitch'))
    def test_hardware_and_scratch_are_not_waived(self):
        r=copy.deepcopy(self.report);r['observations'][0]['criterion_actual']=1687
        self.assertFalse(progress.audio_proof(r,'p2-first-serve-pitch'))
        r=copy.deepcopy(self.report);r['raw_state_differences'][0]['offset']=0x83
        self.assertFalse(progress.audio_proof(r,'p2-first-serve-pitch'))
    def test_class_extents_and_ordered_output_required(self):
        classes=['intro-a','intro-b','result-a','result-b','ready-cue','strike']
        r=copy.deepcopy(self.report);r.update(case='ct08-effect-classes',initial_source_update=11959,final_source_update=13381,
            observed_callbacks=1422,due_callbacks=890,two_tick_countdowns=530,classes=classes,
            interval_inventory=[{}]*18,emitted_classes=[{'class':c,'expected_signal':c!='silence','actual_signal':c!='silence'} for c in classes+['silence']],
            checks=[{'update':12089,'tone':t,'expected_volume':0,'actual_volume':0,'expected_period':None} for t in range(3)])
        with patch.object(progress,'audio_expected_checks',return_value=[(12089,t) for t in range(3)]):
            self.assertTrue(progress.audio_proof(r,'ct08-effect-classes'))
            for key,value in [('observed_callbacks',1421),('classes',classes[:-1]),('due_callbacks',889)]:
                changed=copy.deepcopy(r);changed[key]=value
                self.assertFalse(progress.audio_proof(changed,'ct08-effect-classes'))
            changed=copy.deepcopy(r);changed['checks'][-1]['tone']=1
            self.assertFalse(progress.audio_proof(changed,'ct08-effect-classes'))
            changed=copy.deepcopy(r);changed['emitted_classes'][-1]['actual_signal']=True
            self.assertFalse(progress.audio_proof(changed,'ct08-effect-classes'))
