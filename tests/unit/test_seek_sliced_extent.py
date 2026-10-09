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
    older=bytearray(metadata);older[34:42]=(570).to_bytes(8,'big')
    proof['preview_regression']=dict(accepted_after_commit=True,one_body_yield_preserved=True,
        cancellation_preserved=True,seek_storage_preserved=True,ordinal=0,selection=569,end=0,x=1,y=1)
    proof['sync_validation']=dict(passed=True,older_position=570,older_state='00'*318,older_metadata=older.hex(),
        negatives=[dict(name=n,passed=True,preserved=True,cpu_cycles=1,
            before_state='00'*318,after_state='00'*318,before_metadata=older.hex(),after_metadata=older.hex(),
            before_store_sha256='03'*32,after_store_sha256='03'*32,before_job='00'*734,after_job='00'*734,
            before_live_outputs=[],after_live_outputs=[],before_native_intents=[],after_native_intents=[])
            for n in ('range','schema','simulation','state','opcode','select-mode')],
        supersession=[dict(kind=k,target=t,position=t,actual_body_operations=c,state='00'*318,
            reference_state='00'*318,generation_retired=True,stale_commit_preserved=True,cpu_cycles=1)
            for k,t,c in (('zero-operation',512,0),('one-operation',513,1))])
    origin=2**32-64;latest=origin+97;carry=[]
    for target in (origin,2**32-1,2**32,2**32+1,2**32+17,latest):
        checkpoint=target//64*64
        carry.append(dict(target=target,origin=checkpoint,body_operations=target-checkpoint,
            position=target,sync_state='00'*318,sliced_state='00'*318,sync_events=[],sliced_events=[],
            begin_cpu_cycles=1,sync_cpu_cycles=1,commit_cpu_cycles=1,
            working_rows=[dict(cursor=c,state='00'*318,reference_state='00'*318,actual_body_operations=1,cpu_cycles=1)
                for c in range(checkpoint+1,target+1)]))
    proof['carry_validation']=dict(passed=True,initial_origin=origin,operations=97,final_cursor=latest,
        low_longword_carry_observed=True,maximum_stack_bytes=100,initialization_scope='Synthetic shapes only',rows=carry,
        range_negatives=[dict(api=a,target=t,preserved=True,cpu_cycles=1)
            for a in ('game_history_seek','game_history_seek_begin') for t in (origin-1,latest+1)])
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

    def test_shared_validator_and_all_ledgers_remain_bound(self):
        proof,sha=receipt()
        for block,key,value in [('sync_validation','older_metadata','00'*72),
                ('preview_regression','seek_storage_preserved',False)]:
            changed=copy.deepcopy(proof);changed[block][key]=value
            with self.subTest(key=key):self.assertFalse(proof_extent(changed,sha))
        proof['sync_validation']['negatives'][0]['after_native_intents']=[['title']]
        self.assertFalse(proof_extent(proof,sha))

    def test_carry_checkpoint_and_one_body_edges_are_required(self):
        proof,sha=receipt();proof['carry_validation']['rows'].pop(2)
        self.assertFalse(proof_extent(proof,sha))
        proof,sha=receipt();proof['carry_validation']['rows'][3]['working_rows'][0]['cursor']-=1
        self.assertFalse(proof_extent(proof,sha))
        proof,sha=receipt();proof['carry_validation']['range_negatives'][0]['api']=[]
        self.assertFalse(proof_extent(proof,sha))

    def test_top_level_binds_source_core_and_three_actual_images(self):
        proof,sha=receipt();proofs={}
        compiled={IMAGES['standalone'][0]:'01'*32,IMAGES['native'][0]:'02'*32}
        for role,(path,base) in IMAGES.items():
            item=copy.deepcopy(proof);item.update(image_role=role,base=base,
                executable_path=path,image_sha256=compiled[path]);proofs[role]=item
        proofs['native'].update(restored_adapter_words={n:'40e7' for n in ADAPTERS},
            **{k:True for k in ('adapters_restored_before_freeze','adapter_words_preserved',
                'full_bus_nonstate_guard','frozen_history_write_guard','semantic_observer_read_only',
                'setup_traps_outside_evidence')})
        report=dict(passed=True,execution='actual-68000-cpu-only',
            evidence=dict(actual_execution='actual-68000-cpu-only',target_role='legacy-validator-reference',
                files={INPUT_PATH:INPUT_SHA},compiled_executables=compiled),
            seek_sliced_validation=dict(passed=True,schema=1,canonical_bytes=318,
                history_metadata_bytes=72,seek_storage_bytes=734,proofs=proofs,
                input_stream=dict(path=INPUT_PATH,sha256=INPUT_SHA,operations=835,target_probe=569),
                normalized_shared_core=dict(matched=True,bytes=17606,relocations=7,
                    sink_branches=14,sha256=CORE_SHA)))
        with patch('seek_sliced_extent.SLICE_SHA',sha):
            self.assertTrue(required_seek_sliced_extent(report))
            for path,value in [(('input_stream','sha256'),'ff'*32),
                    (('normalized_shared_core','sha256'),'ff'*32),
                    (('proofs','relocated','base'),65536),
                    (('proofs','native','image_sha256'),'01'*32),
                    (('proofs','native','image_role'),'standalone'),
                    (('proofs','native','restored_adapter_words'),{}),
                    (('proofs','native','restored_adapter_words'),{n:'4e71' for n in ADAPTERS}),
                    (('proofs','native','adapter_words_preserved'),False)]:
                changed=copy.deepcopy(report);node=changed['seek_sliced_validation']
                for key in path[:-1]:node=node[key]
                node[path[-1]]=value
                with self.subTest(path=path):self.assertFalse(required_seek_sliced_extent(changed))
            report['seek_sliced_validation']['proofs']['native']=copy.deepcopy(proofs['standalone'])
            self.assertFalse(required_seek_sliced_extent(report))


if __name__=='__main__':unittest.main()
