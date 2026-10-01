"""Reject incomplete observations or widened scratch exceptions in CT07 receipts."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import progress


class PresentationProof(unittest.TestCase):
    def setUp(self):
        self.recipe = {'name':'p1-moving-prefix','completed_callbacks':[17,63],
                       'fields':['whole_display']}
        self.report = {'subject':'maintained-native',
            'state_contract':progress.MAINTAINED_STATE_CONTRACT,
            'omitted_legacy_scratch_offsets':list(progress.MAINTAINED_SCRATCH_OFFSETS),
            'passed':True,'first_difference':None,'self_test':True,
            'checks':[{'requested_callback':n,'field':'whole_display','first_difference':None,
                       'raster':{'generation':{'prepared_after_callback':n}}} for n in (17,63)],
            'raw_state_differences':[{'update':n,'differences':[{'offset':103}]} for n in (17,63)]}

    def test_compatible_complete_receipt(self):
        self.assertTrue(progress.presentation_proof(self.report,self.recipe))

    def test_late_observation_is_required(self):
        for key in ('checks','raw_state_differences'):
            changed=copy.deepcopy(self.report);changed[key].pop()
            self.assertFalse(progress.presentation_proof(changed,self.recipe))
        changed=copy.deepcopy(self.report);changed['checks'][-1]['first_difference']={'x':1}
        self.assertFalse(progress.presentation_proof(changed,self.recipe))

    def test_no_subject_or_scratch_waiver(self):
        for key,value in (('subject','translated'),('self_test',False),
                          ('omitted_legacy_scratch_offsets',[103,104,105,106,107])):
            changed={**self.report,key:value}
            self.assertFalse(progress.presentation_proof(changed,self.recipe))
        changed=copy.deepcopy(self.report);changed['raw_state_differences'][-1]['differences'][0]['offset']=107
        self.assertFalse(progress.presentation_proof(changed,self.recipe))
