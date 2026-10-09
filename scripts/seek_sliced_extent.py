"""Complete focused sliced-seek receipts; no second simulation model."""
import hashlib
import json
import re

INPUT_PATH='build/acceptance/campaigns/e61e095609b8412e95275345f78e9421/attempts/preview-native-pal/000003/actual-prefix-835.json'
INPUT_SHA='c46ef840c63608511f941fdab06b3c3a8586f0dcc79ee039e3532f1138621348'
SLICE_SHA='b99b6c3e2f87f86266d97e4eacabc0ebc12af6a18adb79149593c70f3b3a840a'
CORE_SHA='99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5'
IMAGES={'standalone':('build/standalone/match-core',65536),
    'relocated':('build/standalone/match-core',196608),
    'native':('build/amiga/interfaces/enhanced/baseline-rally',65536)}
ADAPTERS={'game_render_sprites','game_scene_present_fields','game_core_title_requested',
    'game_audio_write_period','game_audio_write_level','game_core_status_present'}
ARITIES=dict(game_core_init=0,game_core_select=3,game_core_sample_pads=2,
    game_core_sample_result=6,game_core_clear_inputs=0,game_core_return_title=0,
    game_round_poll=0,game_tick_dispatch=0,game_core_latch_actions=0)
NEGATIVES={'admission-zero','stale-step','stale-commit','stale-cancel',
    'failed-begin-range','failed-begin-schema','failed-begin-simulation',
    'failed-begin-state','failed-begin-opcode','canceled-commit',
    'cancel-before-commit','supersede-before-commit','newer-selection-preserved',
    'preview-request-overlap','preview-result-overlap','generation-exhaustion'}
PRESERVED=('public_canonical_preserved','public_metadata_preserved',
    'frozen_store_preserved','live_outputs_preserved','replaying_zero','preview_owner_zero')


def integer(value,minimum=0,maximum=None):
    return type(value) is int and value>=minimum and (maximum is None or value<=maximum)


def encoded(value,length):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{'+str(2*length)+'}',value) is not None


def integration_extent(proof):
    preview=proof.get('preview_regression');sync=proof.get('sync_validation');carry=proof.get('carry_validation')
    if (not isinstance(preview,dict) or any(preview.get(k) is not True for k in
            ('accepted_after_commit','one_body_yield_preserved','cancellation_preserved','seek_storage_preserved'))
            or type(preview.get('selection')) is not int or preview['selection']!=569
            or not integer(preview.get('ordinal'),0,127) or not integer(preview.get('end'),0,1)
            or any(not integer(preview.get(k),0,255) for k in ('x','y'))):return False
    if (not isinstance(sync,dict) or sync.get('passed') is not True
            or type(sync.get('older_position')) is not int or sync['older_position']!=570
            or not encoded(sync.get('older_state'),318) or not encoded(sync.get('older_metadata'),72)):return False
    if int.from_bytes(bytes.fromhex(sync['older_metadata'])[34:42],'big')!=570:return False
    negatives=sync.get('negatives');success=sync.get('supersession')
    if not isinstance(negatives,list) or len(negatives)!=6 or not isinstance(success,list) or len(success)!=2:return False
    names=[]
    for row in negatives:
        if (not isinstance(row,dict) or row.get('passed') is not True or row.get('preserved') is not True
                or not integer(row.get('cpu_cycles'),1)
                or row.get('before_state')!=sync['older_state'] or row.get('after_state')!=sync['older_state']
                or row.get('before_metadata')!=sync['older_metadata'] or row.get('after_metadata')!=sync['older_metadata']
                or not encoded(row.get('before_store_sha256'),32)
                or row.get('after_store_sha256')!=row['before_store_sha256']
                or not encoded(row.get('before_job'),734) or row.get('after_job')!=row['before_job']
                or not isinstance(row.get('before_live_outputs'),list)
                or row.get('after_live_outputs')!=row['before_live_outputs']
                or not isinstance(row.get('before_native_intents'),list)
                or row.get('after_native_intents')!=row['before_native_intents']):return False
        names.append(row.get('name'))
    if any(not isinstance(n,str) for n in names) or set(names)!={'range','schema','simulation','state','opcode','select-mode'}:return False
    for row,(kind,target,count) in zip(success,(('zero-operation',512,0),('one-operation',513,1))):
        if (not isinstance(row,dict) or row.get('kind')!=kind
                or any(type(row.get(k)) is not int or row[k]!=v for k,v in
                    dict(target=target,position=target,actual_body_operations=count).items())
                or not encoded(row.get('state'),318) or row.get('reference_state')!=row['state']
                or row.get('generation_retired') is not True or row.get('stale_commit_preserved') is not True
                or not integer(row.get('cpu_cycles'),1)):return False
    return carry_extent(carry)


def carry_extent(carry):
    origin=2**32-64;latest=origin+97;targets=(origin,2**32-1,2**32,2**32+1,2**32+17,latest)
    if (not isinstance(carry,dict) or carry.get('passed') is not True
            or carry.get('low_longword_carry_observed') is not True
            or any(type(carry.get(k)) is not int or carry[k]!=v for k,v in
                dict(initial_origin=origin,operations=97,final_cursor=latest).items())
            or not integer(carry.get('maximum_stack_bytes'),1,4095)
            or not isinstance(carry.get('initialization_scope'),str) or not carry['initialization_scope']):return False
    rows=carry.get('rows');negative=carry.get('range_negatives')
    if not isinstance(rows,list) or len(rows)!=6 or not isinstance(negative,list) or len(negative)!=4:return False
    for row,target in zip(rows,targets):
        checkpoint=target//64*64;count=target-checkpoint
        if (not isinstance(row,dict)
                or any(type(row.get(k)) is not int or row[k]!=v for k,v in
                    dict(target=target,position=target,origin=checkpoint,body_operations=count).items())
                or not encoded(row.get('sync_state'),318) or row.get('sliced_state')!=row['sync_state']
                or not isinstance(row.get('sync_events'),list) or row.get('sliced_events')!=row['sync_events']
                or (count==0 and row['sync_events'])
                or any(not integer(row.get(k),1) for k in ('begin_cpu_cycles','sync_cpu_cycles','commit_cpu_cycles'))):return False
        working=row.get('working_rows')
        if not isinstance(working,list) or len(working)!=count:return False
        for boundary,item in enumerate(working,checkpoint+1):
            if (not isinstance(item,dict) or type(item.get('cursor')) is not int or item['cursor']!=boundary
                    or type(item.get('actual_body_operations')) is not int or item['actual_body_operations']!=1
                    or not encoded(item.get('state'),318) or item.get('reference_state')!=item['state']
                    or not integer(item.get('cpu_cycles'),1)):return False
        if count and working[-1]['state']!=row['sync_state']:return False
    pairs=[]
    for row in negative:
        if (not isinstance(row,dict) or row.get('preserved') is not True
                or not integer(row.get('cpu_cycles'),1) or type(row.get('target')) is not int
                or row.get('api') not in ('game_history_seek','game_history_seek_begin')):return False
        pairs.append((row.get('api'),row['target']))
    return set(pairs)=={(api,target) for api in ('game_history_seek','game_history_seek_begin') for target in (origin-1,latest+1)}


def proof_extent(proof,operations_sha=SLICE_SHA):
    if (not isinstance(proof,dict) or proof.get('passed') is not True
            or any(type(proof.get(k)) is not int or proof[k]!=v for k,v in
                dict(checkpoint=512,target=569,body_operations=57,boundaries=57,selected_position=835).items())
            or not encoded(proof.get('selected_state'),318)
            or not encoded(proof.get('selected_metadata'),72)):return False
    rows=proof.get('rows');costs=proof.get('costs');negatives=proof.get('negatives')
    selected_metadata=bytes.fromhex(proof['selected_metadata'])
    expected_metadata=selected_metadata[:34]+(569).to_bytes(8,'big')+selected_metadata[42:]
    if (not isinstance(rows,list) or len(rows)!=57 or not isinstance(costs,dict)
            or not isinstance(negatives,list) or len(negatives)!=len(NEGATIVES)
            or int.from_bytes(selected_metadata[34:42],'big')!=835
            or selected_metadata[4]!=2 or selected_metadata[71]!=0):return False
    names=[];operations=[]
    for row in negatives:
        if (not isinstance(row,dict) or row.get('passed') is not True
                or row.get('preserved') is not True):return False
        names.append(row.get('name'))
    if any(not isinstance(n,str) for n in names) or set(names)!=NEGATIVES:return False
    for boundary,row in enumerate(rows,513):
        if (not isinstance(row,dict)
                or any(type(row.get(k)) is not int or row[k]!=v for k,v in
                    dict(boundary=boundary,working_cursor=boundary,public_position=835,actual_body_operations=1).items())
                or any(row.get(k) is not True for k in PRESERVED)
                or not encoded(row.get('working_state'),318)
                or row.get('reference_state')!=row['working_state']
                or row.get('public_state')!=proof['selected_state']
                or row.get('public_metadata')!=proof['selected_metadata']
                or not isinstance(row.get('events'),list)
                or row.get('reference_events')!=row['events']
                or not integer(row.get('cpu_cycles'),1)):return False
        name=row.get('operation');args=row.get('arguments')
        if (not isinstance(name,str) or name not in ARITIES or not isinstance(args,list)
                or len(args)!=ARITIES[name] or any(not integer(v,0,65535) for v in args)):return False
        operations.append([name,args])
    if hashlib.sha256(json.dumps(operations,separators=(',',':')).encode()).hexdigest()!=operations_sha:return False
    if (costs.get('step_cpu_cycles')!=[r['cpu_cycles'] for r in rows]
            or any(not integer(v,1) for v in costs['step_cpu_cycles'])
            or any(not integer(costs.get(k),1) for k in
                ('begin_cpu_cycles','commit_cpu_cycles','cancel_cpu_cycles'))
            or not integer(costs.get('maximum_stack_bytes'),1,4095)
            or proof.get('committed_state')!=rows[-1]['working_state']
            or proof.get('committed_metadata')!=expected_metadata.hex()
            or proof['committed_state']==proof['selected_state']
            or type(proof.get('committed_position')) is not int or proof['committed_position']!=569):return False
    return integration_extent(proof)


def required_seek_sliced_extent(report):
    stage=report.get('seek_sliced_validation');evidence=report.get('evidence')
    if (report.get('passed') is not True or report.get('execution')!='actual-68000-cpu-only'
            or not isinstance(stage,dict) or not isinstance(evidence,dict)
            or evidence.get('actual_execution')!='actual-68000-cpu-only'
            or evidence.get('target_role')!='legacy-validator-reference'
            or stage.get('passed') is not True
            or any(type(stage.get(k)) is not int or stage[k]!=v for k,v in
                dict(schema=1,canonical_bytes=318,history_metadata_bytes=72,seek_storage_bytes=734).items())):return False
    source=stage.get('input_stream');files=evidence.get('files');core=stage.get('normalized_shared_core')
    if (not isinstance(source,dict) or source.get('path')!=INPUT_PATH or source.get('sha256')!=INPUT_SHA
            or type(source.get('operations')) is not int or source['operations']!=835
            or type(source.get('target_probe')) is not int or source['target_probe']!=569
            or not isinstance(files,dict) or files.get(INPUT_PATH)!=INPUT_SHA
            or not isinstance(core,dict) or core.get('matched') is not True or core.get('sha256')!=CORE_SHA
            or any(type(core.get(k)) is not int or core[k]!=v for k,v in
                dict(bytes=17606,relocations=7,sink_branches=14).items())):return False
    proofs=stage.get('proofs')
    if not isinstance(proofs,dict) or set(proofs)!={'standalone','relocated','native'}:return False
    compiled=evidence.get('compiled_executables')
    if not isinstance(compiled,dict):return False
    for role,(path,base) in IMAGES.items():
        proof=proofs[role];sha=compiled.get(path)
        if (not isinstance(proof,dict) or not encoded(sha,32)
                or proof.get('image_role')!=role or proof.get('executable_path')!=path
                or proof.get('image_sha256')!=sha
                or type(proof.get('base')) is not int or proof['base']!=base):return False
    if compiled[IMAGES['native'][0]]==compiled[IMAGES['standalone'][0]]:return False
    native=proofs['native'];words=native.get('restored_adapter_words')
    if (not isinstance(words,dict) or set(words)!=ADAPTERS
            or any(v!='40e7' for v in words.values())
            or any(native.get(k) is not True for k in ('adapters_restored_before_freeze',
                'adapter_words_preserved','full_bus_nonstate_guard','frozen_history_write_guard',
                'semantic_observer_read_only','setup_traps_outside_evidence'))):return False
    if not all(proof_extent(p,SLICE_SHA) for p in proofs.values()):return False
    comparable=lambda p:[(r['operation'],r['arguments'],r['working_state'],r['events'],r['working_cursor']) for r in p['rows']]
    first=comparable(proofs['standalone'])
    return all(comparable(p)==first for p in proofs.values())
