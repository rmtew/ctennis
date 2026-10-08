"""Synthetic receipt shapes; no gameplay oracle or native acceptance claim."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from seek_sliced_extent import NEGATIVES,PRESERVED,proof_extent


def receipt():
    metadata=bytearray(72);metadata[4]=2;metadata[34:42]=(835).to_bytes(8,'big')
    committed=bytearray(metadata);committed[34:42]=(569).to_bytes(8,'big')
    rows=[]
    for boundary in range(513,570):
        state=(boundary.to_bytes(2,'big')*159).hex()
        rows.append(dict(boundary=boundary,working_cursor=boundary,public_position=835,
            actual_body_operations=1,operation='game_round_poll',arguments=[],
            working_state=state,reference_state=state,events=[],reference_events=[],
            public_state='00'*318,public_metadata=metadata.hex(),cpu_cycles=boundary,
            **{k:True for k in PRESERVED}))
    proof=dict(passed=True,checkpoint=512,target=569,body_operations=57,boundaries=57,
        selected_position=835,selected_state='00'*318,selected_metadata=metadata.hex(),
        rows=rows,committed_state=rows[-1]['working_state'],committed_position=569,
        committed_metadata=committed.hex(),negatives=[dict(name=n,passed=True,preserved=True) for n in sorted(NEGATIVES)],
        costs=dict(begin_cpu_cycles=1,step_cpu_cycles=[r['cpu_cycles'] for r in rows],
            commit_cpu_cycles=1,cancel_cpu_cycles=1,maximum_stack_bytes=100))
    sha=hashlib.sha256(json.dumps([[r['operation'],r['arguments']] for r in rows],separators=(',',':')).encode()).hexdigest()
    return proof,sha


class SeekSlicedExtent(unittest.TestCase):
    def test_complete_synthetic_shape(self):
        proof,sha=receipt();self.assertTrue(proof_extent(proof,sha))

    def test_incomplete_or_unbound_boundary_is_rejected(self):
        proof,sha=receipt()
        for key,value in [('boundary',514),('working_cursor',512),('actual_body_operations',2),
                ('working_state','00'*318),('reference_events',[['title']]),
                ('public_state','11'*318),('public_metadata','00'*72),
                ('public_position',569),('arguments',[0]),('cpu_cycles',True),
                ('live_outputs_preserved',False),('replaying_zero',False)]:
            changed=copy.deepcopy(proof);changed['rows'][0][key]=value
            with self.subTest(key=key):self.assertFalse(proof_extent(changed,sha))
        proof['rows'].pop();self.assertFalse(proof_extent(proof,sha))

    def test_commit_cannot_modify_unrelated_metadata(self):
        proof,sha=receipt();changed=bytearray.fromhex(proof['committed_metadata']);changed[8]^=1
        proof['committed_metadata']=changed.hex();self.assertFalse(proof_extent(proof,sha))

    def test_operations_and_costs_remain_bound(self):
        proof,sha=receipt();proof['rows'][0]['operation']='game_core_clear_inputs'
        self.assertFalse(proof_extent(proof,sha))
        proof,sha=receipt();proof['costs']['step_cpu_cycles'][0]+=1
        self.assertFalse(proof_extent(proof,sha))

    def test_missing_or_duplicate_negative_is_rejected(self):
        proof,sha=receipt();proof['negatives'][0]=dict(proof['negatives'][1])
        self.assertFalse(proof_extent(proof,sha))
        proof,sha=receipt();proof['negatives'].pop();self.assertFalse(proof_extent(proof,sha))


if __name__=='__main__':unittest.main()
