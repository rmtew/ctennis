"""Synthetic receipt shapes; no gameplay oracle or native acceptance claim."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from seek_sliced_extent import (NEGATIVES,PRESERVED,proof_extent,required_seek_sliced_extent,
    INPUT_PATH,INPUT_SHA,CORE_SHA,IMAGES,ADAPTERS)


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

    def test_top_level_binds_source_core_and_three_actual_images(self):
        proof,sha=receipt();proofs={}
        compiled={IMAGES['standalone'][0]:'01'*32,IMAGES['native'][0]:'02'*32}
        for role,(path,base) in IMAGES.items():
            item=copy.deepcopy(proof);item.update(image_role=role,base=base,
                executable_path=path,image_sha256=compiled[path]);proofs[role]=item
        proofs['native'].update(restored_adapter_words={n:'4e71' for n in ADAPTERS},
            **{k:True for k in ('adapters_restored_before_freeze','adapter_words_preserved',
                'full_bus_nonstate_guard','frozen_history_write_guard','semantic_observer_read_only',
                'setup_traps_outside_evidence')})
        report=dict(passed=True,execution='actual-68000-cpu-only',
            evidence=dict(actual_execution='actual-68000-cpu-only',target_role='legacy-validator-reference',
                files={INPUT_PATH:INPUT_SHA},compiled_executables=compiled),
            seek_sliced_validation=dict(passed=True,schema=1,canonical_bytes=318,
                history_metadata_bytes=72,seek_storage_bytes=734,proofs=proofs,
                input_stream=dict(path=INPUT_PATH,sha256=INPUT_SHA,operations=835,target_probe=569),
                normalized_shared_core=dict(matched=True,bytes=18020,relocations=257,
                    sink_branches=14,sha256=CORE_SHA)))
        with patch('seek_sliced_extent.SLICE_SHA',sha):
            self.assertTrue(required_seek_sliced_extent(report))
            for path,value in [(('input_stream','sha256'),'ff'*32),
                    (('normalized_shared_core','sha256'),'ff'*32),
                    (('proofs','relocated','base'),65536),
                    (('proofs','native','image_sha256'),'01'*32),
                    (('proofs','native','image_role'),'standalone'),
                    (('proofs','native','restored_adapter_words'),{}),
                    (('proofs','native','adapter_words_preserved'),False)]:
                changed=copy.deepcopy(report);node=changed['seek_sliced_validation']
                for key in path[:-1]:node=node[key]
                node[path[-1]]=value
                with self.subTest(path=path):self.assertFalse(required_seek_sliced_extent(changed))
            report['seek_sliced_validation']['proofs']['native']=copy.deepcopy(proofs['standalone'])
            self.assertFalse(required_seek_sliced_extent(report))


if __name__=='__main__':unittest.main()
