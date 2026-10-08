"""Required finite native preview evidence; malformed or partial reports fail."""
import math
import re
import hashlib


CAPS=dict(accepted_request_generations=7,playing_dispatches=512,
    ordinary_operations=2049,title_callbacks=256,paused_callbacks=2048,
    video_fields=4096,seconds=70,worker_calls_per_job=8192,
    samples_per_path=256,raw_bytes=268435456)
PRESERVATION=('selected_canonical','history_metadata','frozen_store','live_backup',
    'caller_frame','input_globals','publication_irq_only','audio_cpu_configuration')
BYTE_CAP_SCOPE='stored-artifact-bytes; rpc-and-event-transcripts-gzip; uncompressed-transcripts-measured-separately'
CPU9_SHA='b5b57f313123c2cf457b924bcc64c6b261375a12c41ac9679d817cf1079c401f'
CPU9_RECEIPTS=('build/tests/preview-cpu/report.json',
    'build/acceptance/campaigns/00b055e774894e9c9127e470d17e7823/attempts/preview-cpu/000009/receipt.json')
BODY_ARITIES=dict(game_core_init=0,game_core_select=3,game_core_sample_pads=2,
    game_core_sample_result=6,game_core_clear_inputs=0,game_core_return_title=0,
    game_round_poll=0,game_tick_dispatch=0,game_core_latch_actions=0)


def body_observation(block,api_rows,hunks):
    """Every actual body entry, including unmarked calls, has a matched return."""
    if (not isinstance(block,dict)
            or block.get('protocol')!='read-only-emitted-body-pc-and-matched-stack-return'
            or type(block.get('unpaired_frames')) is not int or block['unpaired_frames']!=0
            or type(block.get('maximum_nesting')) is not int or block['maximum_nesting']!=9
            or type(block.get('maximum_entries_per_api')) is not int or block['maximum_entries_per_api']!=8192
            or not integer(block.get('stack_bottom'),0,524287)
            or not integer(block.get('stack_top'),4096,524288)
            or block['stack_top']-block['stack_bottom']!=4096):return False
    def loaded(pc,length=2):
        return integer(pc,0,524287) and pc%2==0 and any(h['start']<=pc<pc+length<=h['start']+h['bytes'] for h in hunks)
    if not loaded(block['stack_bottom'],4096):return False
    mapping=block.get('loaded_body_map');frames=block.get('frames');intents=block.get('semantic_intents')
    if (not isinstance(mapping,list) or len(mapping)!=9
            or not isinstance(frames,list) or not frames or not isinstance(intents,list)):return False
    specs={}
    for spec in mapping:
        if (not isinstance(spec,dict) or spec.get('operation') not in BODY_ARITIES
                or type(spec.get('arity')) is not int or spec['arity']!=BODY_ARITIES[spec['operation']]
                or spec.get('label')!=spec['operation']+'_body' or not loaded(spec.get('pc'),4)
                or spec['operation'] in specs or not isinstance(spec.get('entry_bytes'),str)
                or re.fullmatch(r'[0-9a-f]{8}',spec['entry_bytes']) is None):return False
        specs[spec['operation']]=spec
    if len({r['pc'] for r in mapping})!=9:return False
    counts=[0]*len(api_rows);entry_stops=set();return_stops=set();stack=[];outer=[]
    for index,frame in enumerate(frames):
        if (not isinstance(frame,dict) or type(frame.get('entry_index')) is not int or frame['entry_index']!=index
                or not integer(frame.get('api_row_index'),0,len(api_rows)-1)
                or frame.get('operation') not in specs):return False
        spec=specs[frame['operation']];api_index=frame['api_row_index'];api=api_rows[api_index]
        if (type(frame.get('arity')) is not int or frame['arity']!=spec['arity']
                or frame.get('entry_pc')!=spec['pc'] or type(frame.get('entry_pc')) is not int
                or not integer(frame.get('entry_sp'),block['stack_bottom'],block['stack_top']-4)
                or frame['entry_sp']%2 or not loaded(frame.get('return_pc'))
                or frame.get('exit_pc')!=frame['return_pc'] or type(frame.get('exit_pc')) is not int
                or type(frame.get('exit_sp')) is not int or frame['exit_sp']!=frame['entry_sp']+4
                or not integer(frame.get('depth'),1,9)
                or not isinstance(frame.get('events'),list)):return False
        registers=frame.get('entry_registers');owner=frame.get('ownership')
        if (not isinstance(registers,dict) or registers.get('pc')!=frame['entry_pc']
                or type(registers.get('pc')) is not int or not integer(registers.get('sr'),0,65535)
                or registers['sr']&0x700 or type(registers.get('stopped')) is not bool
                or any(not isinstance(registers.get(k),list) or len(registers[k])!=8
                    or any(not integer(v,0,2**32-1) for v in registers[k]) for k in ('d','a'))
                or registers['a'][7]!=frame['entry_sp']
                or frame.get('arguments')!=[v&65535 for v in registers['d'][:spec['arity']]]
                or any(type(v) is not int for v in frame['arguments'])
                or not isinstance(owner,dict) or not integer(owner.get('active'),0,2)
                or not integer(owner.get('status'),0,7) or not integer(owner.get('variant'),0,1)
                or not integer(owner.get('seek_active'),0,1) or not integer(owner.get('seek_status'),0,3)
                or not integer(owner.get('seek_generation'),0,2**32-1)
                or not integer(owner.get('seek_cursor'),0,2**64-1)
                or owner['seek_active'] and owner['active']):return False
        try:states=[bytes.fromhex(frame[k]) for k in ('before','after')]
        except (KeyError,TypeError,ValueError):return False
        if any(len(s)!=318 for s in states) or frame.get('state')!=frame['after']:return False
        for key in ('start','end'):
            pos=frame.get(key)
            if (not isinstance(pos,dict) or not integer(pos.get('cck'),api['begin']['cck'],api['end']['cck'])
                    or not integer(pos.get('frame'),api['begin']['frame'],api['end']['frame'])
                    or not number(pos.get('seconds'),api['begin']['seconds'],api['end']['seconds'])
                    or not integer(pos.get('vpos'),0,1023) or not integer(pos.get('hpos'),0,511)):return False
        if (not integer(frame.get('elapsed_cck'),1)
                or frame['elapsed_cck']!=frame['end']['cck']-frame['start']['cck']):return False
        if index and (api_index<frames[index-1]['api_row_index']
                or frame['start']['cck']<frames[index-1]['start']['cck']):return False
        while stack and (stack[-1]['api_row_index']!=api_index or stack[-1]['end']['cck']<=frame['start']['cck']):stack.pop()
        if frame['depth']!=len(stack)+1:return False
        if stack:
            parent=stack[-1]
            if (frame['end']['cck']>parent['end']['cck']
                    or not (frame['entry_sp']<parent['entry_sp'] or
                        (frame['entry_sp']==parent['entry_sp'] and frame['return_pc']==parent['return_pc']))):return False
        else:outer.append(frame)
        stack.append(frame);counts[api_index]+=1
        entry_stops.add((api_index,frame['entry_pc'],frame['entry_sp'],frame['start']['cck']))
        return_stops.add((api_index,frame['exit_pc'],frame['exit_sp'],frame['end']['cck']))
    if (counts!=[r['bodies'] for r in api_rows] or any(n>8192 for n in counts)
            or type(block.get('actual_body_entries')) is not int or block['actual_body_entries']!=len(frames)
            or type(block.get('outer_logical_calls')) is not int or block['outer_logical_calls']!=len(outer)
            or type(block.get('internal_stops')) is not int or block['internal_stops']!=len(entry_stops|return_stops)
            or type(block.get('entry_return_observations')) is not int
            or block['entry_return_observations']!=len(frames)+len(return_stops)):return False
    expected=[(f['api_row_index'],e) for f in outer for e in f['events']]
    actual=[]
    for intent in intents:
        if (not isinstance(intent,dict) or not integer(intent.get('api_row_index'),0,len(api_rows)-1)
                or not isinstance(intent.get('event'),list) or not intent['event']
                or not isinstance(intent.get('position'),dict)):return False
        api=api_rows[intent['api_row_index']]
        if not integer(intent['position'].get('cck'),api['begin']['cck'],api['end']['cck']):return False
        actual.append((intent['api_row_index'],intent['event']))
    return actual==expected


def integer(value,low=0,high=None):
    return type(value) is int and value>=low and (high is None or value<=high)


def number(value,low=0,high=None):
    if type(value) not in (int,float):return False
    try:return math.isfinite(value) and value>=low and (high is None or value<=high)
    except OverflowError:return False


def exact_mapping(actual,expected):
    return (isinstance(actual,dict) and actual==expected
        and all(type(actual[k]) is type(value) for k,value in expected.items()))


def sha256(value):
    return isinstance(value,str) and re.fullmatch(r'[0-9a-f]{64}',value) is not None


def hashes(value):
    return isinstance(value,dict) and bool(value) and all(isinstance(k,str) and sha256(v) for k,v in value.items())


def distribution(row,budget,values=None):
    if (not isinstance(row,dict) or not integer(row.get('samples'),1)
            or any(not number(row.get(k)) for k in ('typical_median_cck','p95_cck','max_cck','budget_cck'))
            or not number(row.get('minimum_headroom_cck'))
            or not row['typical_median_cck']<=row['p95_cck']<=row['max_cck']
            or not math.isclose(row['budget_cck'],budget,abs_tol=1e-6,rel_tol=0)
            or not math.isclose(row['minimum_headroom_cck'],budget-row['max_cck'],abs_tol=1e-6,rel_tol=0)):return False
    if values is not None:
        if not values:return False
        values=sorted(values);median=(values[(len(values)-1)//2]+values[len(values)//2])/2
        return (row['samples']==len(values) and row['typical_median_cck']==median
            and row['p95_cck']==values[math.ceil(.95*len(values))-1] and row['max_cck']==values[-1])
    return True


def api_row(row):
    names=('game_history_freeze','game_history_seek_begin','game_history_seek_step',
        'game_history_seek_commit','game_history_seek_cancel','game_preview_request',
        'game_preview_step','game_preview_result','game_preview_cancel','game_history_resume_latest')
    if (not isinstance(row,dict) or row.get('name') not in names
            or not integer(row.get('bodies'),0,
                4 if row['name']=='game_preview_step' else 8192 if row['name']=='game_history_seek_step' else 0)
            or not integer(row.get('irq'),0)
            or not integer(row.get('irq_acknowledgements'),0)
            or row['irq_acknowledgements']!=2*row['irq']
            or not integer(row.get('elapsed_cck'),1)):return False
    begin=row.get('begin');end=row.get('end')
    for position in (begin,end):
        if (not isinstance(position,dict) or not integer(position.get('cck'),0)
                or not integer(position.get('frame'),0)
                or not number(position.get('seconds'))
                or not integer(position.get('vpos'),0,1023)
                or not integer(position.get('hpos'),0,511)):return False
    return (end['cck']-begin['cck']==row['elapsed_cck']
        and end['seconds']>=begin['seconds'] and end['frame']>=begin['frame'])



SEEK_CPU_SHA='1a0a8cc933c5c9f42507ca8b2f1cc7c260db769fffbd0a50570b35beb712995c'
SEEK_CPU_RECEIPTS=('build/tests/seek-sliced-cpu/report.json',
    'build/acceptance/campaigns/69cd1780198c4e55a7f8d6c25484c239/attempts/seek-sliced-cpu/000004/receipt.json')


def complete_bytes(value,length):
    try:return isinstance(value,str) and len(bytes.fromhex(value))==length
    except ValueError:return False


def seek_validation(block,api_rows,frames,files,interval_whole):
    """Private progress, timer admission and retirement bind actual API readbacks."""
    if (not isinstance(block,dict) or block.get('passed') is not True
            or block.get('cpu_receipt_sha256')!=SEEK_CPU_SHA
            or any(files.get(path)!=SEEK_CPU_SHA for path in SEEK_CPU_RECEIPTS)
            or any(block.get(k) is not True for k in ('one_body_per_slice',
                'selected_pending_preserved','actual_guest_timer_admission'))
            or type(block.get('reserve_eclock_ticks')) is not int
            or block['reserve_eclock_ticks']!=10000
            or not isinstance(block.get('reserve_scope'),str)
            or 'estimate' not in block['reserve_scope'].lower()):return False
    rows=block.get('rows');jobs=block.get('jobs')
    if not isinstance(rows,list) or not rows or not isinstance(jobs,list) or not jobs:return False
    if any(not isinstance(j,dict) or not integer(j.get('commit_api_row_index'),0,len(api_rows)-1) for j in jobs):return False
    commits={j['commit_api_row_index'] for j in jobs};seen=set();by_index={};steps=set()
    names={'game_history_seek_begin','game_history_seek_step','game_history_seek_commit','game_history_seek_cancel'}
    for row in rows:
        if (not isinstance(row,dict) or not integer(row.get('api_row_index'),0,len(api_rows)-1)
                or row['api_row_index'] in seen or row.get('name') not in names
                or not integer(row.get('generation'),0,2**32-1)
                or not integer(row.get('body_operations'),0,8192)
                or not integer(row.get('logical_body_operations'),0,1)
                or not integer(row.get('working_cursor'),0,2**64-1)
                or not complete_bytes(row.get('working_state'),318)
                or row['working_state']!=row.get('reference_working_state')
                or not complete_bytes(row.get('selected_state'),318)
                or not complete_bytes(row.get('selected_metadata'),72)
                or not complete_bytes(row.get('public_state'),318)
                or not complete_bytes(row.get('public_metadata'),72)
                or not isinstance(row.get('events'),list) or row['events']!=row.get('reference_events')
                or row.get('actual_core_equal') is not True
                or row.get('frozen_store_preserved') is not True):return False
        index=row['api_row_index'];api=api_rows[index];seen.add(index);by_index[index]=row
        outer=[f for f in frames if f['api_row_index']==index and f['depth']==1]
        if (api['name']!=row['name'] or api['bodies']!=row['body_operations']
                or len(outer)!=row['logical_body_operations']
                or [e for f in outer for e in f['events']]!=row['events']):return False
        if index not in commits and (row['public_state']!=row['selected_state']
                or row['public_metadata']!=row['selected_metadata']):return False
        metadata=bytes.fromhex(row['public_metadata'])
        if metadata[4]!=2 or metadata[71]!=0:return False
        if row['name']!='game_history_seek_step':
            if row.get('admission') is not None or row['body_operations'] or row['events']:return False
            continue
        steps.add(index);admission=row.get('admission')
        keys={'current','last','phase','interval','remaining','reserve','admitted','requested_work'}
        if (not isinstance(admission,dict) or set(admission)!=keys
                or any(not integer(admission[k],0,2**32-1) for k in keys)
                or admission['reserve']!=block['reserve_eclock_ticks']
                or admission['interval'] not in (interval_whole,interval_whole+1)
                or admission['admitted'] not in (0,1) or admission['requested_work'] not in (0,1)):return False
        elapsed=(admission['last']-admission['current'])&0xffffffff
        available=admission['interval']-admission['phase']-elapsed
        if (admission['remaining']!=max(0,available)
                or admission['admitted']!=int(admission['requested_work']==1 and available>=admission['reserve'])
                or row['logical_body_operations']!=admission['admitted']):return False
        if not admission['admitted'] and (row['body_operations'] or row['events']):return False
        if outer and (outer[-1]['after']!=row['working_state']
                or any(f['ownership'].get('seek_active')!=1 or f['ownership']['active']!=0
                    or f['ownership'].get('seek_generation')!=row['generation']
                    or f['ownership'].get('seek_cursor')!=row['working_cursor']-1 for f in outer)):return False
    if seen!={i for i,r in enumerate(api_rows) if r['name'] in names}:return False
    used=set();retained=False
    for job in jobs:
        if (not integer(job.get('generation'),1,2**32-1)
                or not integer(job.get('target'),0,2**64-1)
                or not integer(job.get('checkpoint'),0,job['target'])
                or job['checkpoint']!=job['target']//64*64
                or not integer(job.get('selected_position'),0,2**64-1)
                or not complete_bytes(job.get('selected_state'),318)
                or not complete_bytes(job.get('selected_metadata'),72)
                or not complete_bytes(job.get('final_state'),318)
                or not complete_bytes(job.get('final_metadata'),72)
                or type(job.get('final_position')) is not int or job['final_position']!=job['target']
                or any(job.get(k) is not True for k in ('admission_zero_identity_preserved',
                    'canceled_commit_preserved','superseded_commit_preserved'))):return False
        if int.from_bytes(bytes.fromhex(job['selected_metadata'])[34:42],'big')!=job['selected_position']:return False
        def api(index,name):
            return integer(index,0,len(api_rows)-1) and index in by_index and api_rows[index]['name']==name
        def sequence(begin,indices,generation,zero=None):
            if (not api(begin,'game_history_seek_begin') or not isinstance(indices,list)
                    or not indices or any(not api(i,'game_history_seek_step') or i<=begin for i in indices)
                    or sorted(set(indices))!=indices
                    or used.intersection(indices)):return False
            cursor=job['checkpoint'];previous=by_index[begin]['working_state']
            for index in indices:
                row=by_index[index];cursor+=row['logical_body_operations']
                if (row['generation']!=generation or row['working_cursor']!=cursor
                        or row['selected_state']!=job['selected_state']
                        or row['selected_metadata']!=job['selected_metadata']):return False
                if row['logical_body_operations']==0 and row['working_state']!=previous:return False
                previous=row['working_state']
            used.update(indices)
            return cursor==job['target']
        zero=job.get('admission_zero_api_row_index');canceled=job.get('canceled_job');superseded=job.get('superseded_job')
        if (not api(zero,'game_history_seek_step') or by_index[zero]['admission']['requested_work']!=0
                or by_index[zero]['logical_body_operations'] or zero in used
                or not isinstance(canceled,dict) or not isinstance(superseded,dict)
                or canceled.get('ready_before_cancel') is not True or superseded.get('ready_before_supersession') is not True):return False
        used.add(zero)
        cb=canceled.get('begin_api_row_index');cancel=canceled.get('cancel_api_row_index');oldcommit=canceled.get('canceled_commit_api_row_index')
        sb=superseded.get('begin_api_row_index');stale=superseded.get('stale_commit_api_row_index');begin=job.get('begin_api_row_index');commit=job['commit_api_row_index']
        if (job.get('initial_begin_api_row_index')!=cb
                or not integer(canceled.get('generation'),1,2**32-1)
                or not integer(superseded.get('generation'),canceled['generation']+1,2**32-1)
                or job['generation']<=superseded['generation']
                or not sequence(cb,canceled.get('step_api_row_indices'),canceled['generation'])
                or not sequence(sb,superseded.get('step_api_row_indices'),superseded['generation'])
                or not sequence(begin,job.get('step_api_row_indices'),job['generation'])
                or not api(cancel,'game_history_seek_cancel') or not api(oldcommit,'game_history_seek_commit')
                or not api(stale,'game_history_seek_commit') or not api(commit,'game_history_seek_commit')
                or not cb<zero<canceled['step_api_row_indices'][0]<=canceled['step_api_row_indices'][-1]<cancel<oldcommit<sb
                or not sb<superseded['step_api_row_indices'][0]<=superseded['step_api_row_indices'][-1]<begin<stale<job['step_api_row_indices'][0]
                or not job['step_api_row_indices'][-1]<commit
                or superseded.get('superseding_begin_api_row_index')!=begin
                or by_index[cancel]['generation']!=canceled['generation']
                or by_index[oldcommit]['generation']!=canceled['generation']
                or by_index[stale]['generation']!=superseded['generation']
                or by_index[commit]['generation']!=job['generation']):return False
        expected=bytearray.fromhex(job['selected_metadata']);expected[34:42]=job['target'].to_bytes(8,'big')
        if (job['final_state']!=by_index[job['step_api_row_indices'][-1]]['working_state']
                or job['final_state']!=by_index[commit]['public_state']
                or bytes.fromhex(job['final_metadata'])!=expected
                or job['final_metadata']!=by_index[commit]['public_metadata']):return False
        transition=job.get('preview_transition')
        if not isinstance(transition,dict) or transition.get('retired') is not True:return False
        before=transition.get('before');after=transition.get('after')
        if (not isinstance(before,dict) or not isinstance(after,dict)
                or not integer(before.get('generation'),0,2**32-2)
                or not integer(after.get('generation'),before['generation']+1,2**32-1)
                or type(after.get('status')) is not int or after['status']!=7
                or type(after.get('cache_valid')) is not int or after['cache_valid']!=0):return False
        for key,name in (('result_rejection_api_row_index','game_preview_result'),
                         ('request_rejection_api_row_index','game_preview_request')):
            index=transition.get(key)
            if not integer(index,zero+1,canceled['step_api_row_indices'][0]-1) or api_rows[index]['name']!=name or api_rows[index]['bodies']:return False
        retained|=job['target']==569 and job['checkpoint']==512 and job['selected_position']==835
    return used==steps and retained


def completed_job(row):
    if (not isinstance(row,dict) or row.get('case_id') not in
            ('current-human-serve','cold-incoming','warm-position-edit')
            or any(row.get(k) is not True for k in ('passed',
                'native_jsr_rts_preserved','continuous_state_path_output_equal',
                'independent_continuation_policy_equal','live_history_output_preserved',
                'edited_only_position_changed'))
            or type(row.get('seed')) is not int or row['seed']!=44257
            or not integer(row.get('selection'),1,2**64-1)
            or not integer(row.get('end'),0,1)
            or not integer(row.get('prefix_samples'),0,255)
            or type(row.get('coincident')) is not bool):return False
    ordinal=row.get('ordinal')
    if not integer(ordinal,0,65535) or (ordinal>127 and ordinal!=65535):return False
    if (row['case_id']=='current-human-serve')!=(ordinal==65535):return False
    if row.get('classification_scope')!='native-preview-outcome-labels; endpoint-qualification-inherited-reviewed-cpu9':return False
    if any(not integer(row.get(k),0,2**64-1) for k in ('incoming_origin','action_boundary')):return False
    bounds=row.get('bounds')
    if (not isinstance(bounds,dict)
            or any(not integer(bounds.get(k),0,255) for k in ('left','right','top','bottom'))
            or not integer(row.get('x'),bounds['left'],bounds['right']-1)
            or not integer(row.get('y'),bounds['top'],bounds['bottom']-1)):return False
    if not isinstance(row.get('final_states'),list) or not isinstance(row.get('paths'),list):return False
    try:
        selected=bytes.fromhex(row['selected_state']);edited=bytes.fromhex(row['edited_state'])
        finals=[bytes.fromhex(s) for s in row['final_states']]
        paths=[bytes.fromhex(p) for p in row['paths']]
    except (KeyError,TypeError,ValueError):return False
    player=10*row['end']
    if (len(selected)!=318 or len(edited)!=318 or len(finals)!=2
            or any(len(s)!=318 for s in finals)
            or any(a!=b for n,(a,b) in enumerate(zip(selected,edited)) if n not in (player+2,player+3))
            or edited[player+2]!=row['y'] or edited[player+3]!=row['x']
            or len(paths)!=2 or any(not 8<=len(p)<=2048 or len(p)%8 for p in paths)
            or row.get('path_counts')!=[len(p)//8 for p in paths]
            or any(type(n) is not int for n in row['path_counts'])
            or any(row['prefix_samples']>len(p)//8 for p in paths)
            or paths[0][:row['prefix_samples']*8]!=paths[1][:row['prefix_samples']*8]
            or not isinstance(row.get('ordered_outputs'),list) or len(row['ordered_outputs'])!=2
            or any(not isinstance(outputs,list) for outputs in row['ordered_outputs'])):return False
    prefix=row.get('incoming_prefix_validation')
    if (not isinstance(prefix,dict) or prefix.get('passed') is not True
            or prefix.get('source')!='actual-native-retained-dispatch-boundaries'
            or not integer(prefix.get('expected_samples'),0,255)
            or prefix['expected_samples']!=row['prefix_samples']
            or not isinstance(prefix.get('operation_cursors'),list)
            or len(prefix['operation_cursors'])!=prefix['expected_samples']
            or any(not integer(i,row['incoming_origin'],row['selection']-1) for i in prefix['operation_cursors'])
            or sorted(set(prefix['operation_cursors']))!=prefix['operation_cursors']):return False
    try:expected_prefix=bytes.fromhex(prefix['expected_bytes'])
    except (KeyError,TypeError,ValueError):return False
    if (len(expected_prefix)!=8*row['prefix_samples']
            or any(p[:len(expected_prefix)]!=expected_prefix for p in paths)
            or prefix.get('expected_sha256')!=hashlib.sha256(expected_prefix).hexdigest()
            or ordinal==65535 and prefix['expected_samples']!=0):return False
    classes=row.get('classes')
    if (not isinstance(classes,list) or len(classes)!=2 or any(c not in
            ('landing','net','out','interception','no-contact','lifecycle','limit') for c in classes)):return False
    costs=row.get('costs')
    if (not isinstance(costs,dict) or not integer(costs.get('generation'),1,2**32-1)
            or type(costs.get('cache_hit')) is not bool
            or not integer(costs.get('resolver_operations'),0,4096)
            or not integer(costs.get('worker_calls'),1,8192)
            or not isinstance(costs.get('worker_body_counts'),list)
            or len(costs['worker_body_counts'])!=costs['worker_calls']
            or any(not integer(n,0,4) for n in costs['worker_body_counts'])
            or not integer(costs.get('maximum_worker_operations'),1,4)
            or costs['maximum_worker_operations']!=max(costs['worker_body_counts'])
            or not integer(costs.get('worker_elapsed_cck'),1)
            or not integer(costs.get('maximum_worker_elapsed_cck'),1,costs['worker_elapsed_cck'])
            or not integer(costs.get('fields_to_result'),0,4096)
            or not number(costs.get('seconds_to_result'),0,70)
            or costs['seconds_to_result']==0
            or not integer(costs.get('request_api_row_index'),0)
            or not integer(costs.get('result_api_row_index'),costs['request_api_row_index']+1)
            or not isinstance(costs.get('worker_api_row_indices'),list)
            or len(costs['worker_api_row_indices'])!=costs['worker_calls']
            or any(not integer(i,costs['request_api_row_index']+1,costs['result_api_row_index']-1)
                   for i in costs['worker_api_row_indices'])
            or sorted(set(costs['worker_api_row_indices']))!=costs['worker_api_row_indices']):return False
    if row['case_id']=='warm-position-edit':
        return costs['cache_hit'] is True and costs['resolver_operations']==0
    if row['case_id']=='cold-incoming':
        return costs['cache_hit'] is False and costs['resolver_operations']>0
    return costs['cache_hit'] is False


def replacement_case(row):
    if (not isinstance(row,dict) or row.get('case_id') not in
            ('replacement-resolve','replacement-held')
            or any(row.get(k) is not True for k in ('passed','cold_replacement',
                'edited_only_position_changed','old_result_rejected',
                'canceled_result_rejected','selected_history_output_preserved'))
            or not integer(row.get('partial_body_operations'),1,4*8192)
            or not integer(row.get('old_generation'),1,2**32-2)
            or not integer(row.get('new_generation'),row['old_generation']+1,2**32-1)
            or not integer(row.get('replacement_resolver_operations'),1,4096)):return False
    if row.get('partial_phase')!=row['case_id'].removeprefix('replacement-'):return False
    old=row.get('old_position');new=row.get('new_position')
    return (isinstance(old,list) and isinstance(new,list) and len(old)==len(new)==2
        and all(integer(n,0,255) for n in old+new) and old[0]!=new[0] and old[1]==new[1])


def required_preview_native_extent(case_id,report):
    if not isinstance(report,dict):return False
    ntsc=case_id=='preview-native-ntsc'
    if case_id not in ('preview-native-pal','preview-native-ntsc'):return False
    target=dict(video='NTSC' if ntsc else 'PAL',cpu='68000',chipset='OCS',
        chip_kib=512,slow_kib=0,fast_kib=0)
    video=dict(presentation_last_line=261 if ntsc else 311,
        simulation_interval_whole=11947 if ntsc else 11838,
        simulation_interval_fraction=13180 if ntsc else 14906)
    evidence=report.get('evidence') or {}
    stage=report.get('preview_native_validation')
    if (report.get('passed') is not True
            or report.get('execution')!='actual-native-paused-preview'
            or not exact_mapping(report.get('target'),target)
            or not exact_mapping(report.get('native_video'),video)
            or not isinstance(evidence,dict)
            or evidence.get('target_role')!='legacy-validator-reference'
            or not exact_mapping(evidence.get('actual_target'),target)
            or not isinstance(stage,dict) or stage.get('passed') is not True
            or any(type(stage.get(key)) is not int or stage[key]!=value for key,value in dict(canonical_bytes=318,
                history_metadata_bytes=72,preview_storage_bytes=5550,
                preview_metadata_bytes=110,seek_storage_bytes=734).items())):return False
    acquisition=stage.get('acquisition')
    if (not isinstance(acquisition,dict) or type(acquisition.get('seed')) is not int
            or acquisition['seed']!=44257
            or acquisition.get('seed_policy')!='DEMO_RECORDING-selection-only'
            or not integer(acquisition.get('ordinary_operations'),1,2049)
            or not integer(acquisition.get('playing_dispatches'),1,512)
            or not integer(acquisition.get('title_callbacks'),0,256)
            or not integer(acquisition.get('completed_index_kind'),1,2)
            or not integer(acquisition.get('ordinal'),0,127)
            or not integer(acquisition.get('end'),0,1)
            or any(not integer(acquisition.get(k),0,2**64-1) for k in
                   ('incoming_origin','probe_origin','selected_cursor'))
            or not acquisition['incoming_origin']<=acquisition['selected_cursor']<=acquisition['probe_origin']):return False
    preservation=stage.get('preservation')
    if (not isinstance(preservation,dict) or any(preservation.get(k) is not True for k in PRESERVATION)
            or preservation.get('publication_scope')!='worker-api-irq-only; outside-api-native-ui-attributed'
            or preservation.get('input_scope')!='worker-api-only; native-physical-sampling-before-hook'):return False
    interrupts=stage.get('interrupts')
    if (not isinstance(interrupts,dict)
            or not integer(interrupts.get('inside_worker_entries'),1)
            or not integer(interrupts.get('inside_api_entries'),interrupts['inside_worker_entries'])
            or interrupts.get('entry_exit_ack_pairs') is not True
            or type(interrupts.get('keyboard_irq_allowances')) is not int
            or interrupts['keyboard_irq_allowances']!=0
            or not isinstance(interrupts.get('exact_pc_address_width_value_rules'),list)
            or not interrupts['exact_pc_address_width_value_rules']):return False
    rules=interrupts['exact_pc_address_width_value_rules']
    for rule in rules:
        if (not isinstance(rule,dict) or not integer(rule.get('pc'),0,0xffffff)
                or not integer(rule.get('address'),0,0xffffff)
                or type(rule.get('bytes')) is not int or rule['bytes'] not in (1,2,4)
                or rule.get('operation') not in ('move','clr','addq','subq')
                or not isinstance(rule.get('destination'),str)
                or not isinstance(rule.get('instruction'),str)):return False
    if (len({r['pc'] for r in rules})!=len(rules)
            or sum(r['address']==0xdff09c and r['bytes']==2 and r.get('source')=='#$0010'
                   and r['operation']=='move' for r in rules)!=2):return False
    physical=stage.get('physical_inputs')
    if (not isinstance(physical,dict) or physical.get('pause_resume_observed') is not True
            or any(not integer(physical.get(k),1) for k in ('joystick_press_edges',
                'joystick_release_edges','keyboard_presses','keyboard_releases','fresh_input_callbacks'))):return False
    edges=physical.get('observed_edges');pressed=physical.get('joystick_pressed_observations')
    if not isinstance(edges,list) or not edges or not isinstance(pressed,list) or not pressed:return False
    counts=dict(joystick_press_edges=0,joystick_release_edges=0,keyboard_presses=0,keyboard_releases=0)
    frozen_counts=dict(counts)
    for edge in edges:
        if (not isinstance(edge,dict) or edge.get('name') not in ('ui_joystick_bits','game_keyboard_matrix')
                or not integer(edge.get('index'),0,1 if edge['name']=='ui_joystick_bits' else 127)
                or any(not integer(edge.get(k),0,255) for k in ('old','new','pressed_bits','released_bits'))
                or edge['old']==edge['new'] or type(edge.get('frozen')) is not bool
                or edge['pressed_bits']!=edge['new']&~edge['old']
                or edge['released_bits']!=edge['old']&~edge['new']
                or not isinstance(edge.get('position'),dict) or not integer(edge['position'].get('cck'),0)):return False
        if edge['name']=='ui_joystick_bits':
            additions=dict(joystick_press_edges=edge['pressed_bits'].bit_count(),joystick_release_edges=edge['released_bits'].bit_count())
        else:
            if edge['old'] not in (0,1) or edge['new'] not in (0,1):return False
            additions=dict(keyboard_presses=int(bool(edge['pressed_bits'])),keyboard_releases=int(bool(edge['released_bits'])))
        for key,value in additions.items():
            counts[key]+=value
            if edge['frozen']:frozen_counts[key]+=value
    if any(physical[k]!=v or not frozen_counts[k] for k,v in counts.items()):return False
    for observation in pressed:
        if (not isinstance(observation,dict) or not integer(observation.get('index'),0,1)
                or not integer(observation.get('value'),0,255)
                or type(observation.get('expected')) is not int
                or observation['expected']!=observation['value']):return False
    telemetry=stage.get('telemetry')
    if (not isinstance(telemetry,dict) or not integer(telemetry.get('notifications'),1)
            or not integer(telemetry.get('public_boundary_drain_checks'),1)
            or any(type(telemetry.get(k)) is not int or telemetry[k]!=0
                   for k in ('dropped_notifications','dropped_accesses'))):return False
    observed=stage.get('observed_caps')
    if (not exact_mapping(stage.get('caps'),CAPS) or not isinstance(observed,dict)
            or stage.get('byte_cap_scope')!=BYTE_CAP_SCOPE):return False
    for key,limit in CAPS.items():
        if key=='seconds':
            if not number(observed.get(key),0,limit) or observed[key]==0:return False
        elif not integer(observed.get(key),0 if key=='title_callbacks' else 1,limit):return False
    if (observed['accepted_request_generations']!=7
            or observed['ordinary_operations']!=acquisition['ordinary_operations']
            or observed['playing_dispatches']!=acquisition['playing_dispatches']
            or observed['title_callbacks']!=acquisition['title_callbacks']):return False
    jobs=stage.get('completed_jobs');replacements=stage.get('replacement_cancel_cases')
    if (not isinstance(jobs,list) or len(jobs)!=3 or not all(completed_job(r) for r in jobs)
            or {r['case_id'] for r in jobs}!={'current-human-serve','cold-incoming','warm-position-edit'}
            or not isinstance(replacements,list) or len(replacements)!=2
            or not all(replacement_case(r) for r in replacements)
            or {r['case_id'] for r in replacements}!={'replacement-resolve','replacement-held'}):return False
    cold=next(r for r in jobs if r['case_id']=='cold-incoming')
    warm=next(r for r in jobs if r['case_id']=='warm-position-edit')
    if (any(cold[k]!=acquisition[a] for k,a in (('selection','selected_cursor'),
            ('ordinal','ordinal'),('end','end'),('incoming_origin','incoming_origin')))
            or any(cold[k]!=warm[k] for k in ('selected_state','selection','ordinal','end',
            'incoming_origin','action_boundary','prefix_samples'))
            or any(bytes.fromhex(cold['paths'][v])[:cold['prefix_samples']*8]
                   !=bytes.fromhex(warm['paths'][v])[:warm['prefix_samples']*8] for v in (0,1))
            or (cold['x'],cold['y'])==(warm['x'],warm['y'])):return False
    if (observed['worker_calls_per_job']<max(r['costs']['worker_calls'] for r in jobs)
            or observed['samples_per_path']<max(n for r in jobs for n in r['path_counts'])
            or any(r['costs']['fields_to_result']>observed['video_fields']
                   or r['costs']['seconds_to_result']>observed['seconds'] for r in jobs)):return False
    costs=stage.get('costs')
    if (not isinstance(costs,dict) or not isinstance(costs.get('api_rows'),list)
            or not costs['api_rows'] or not all(api_row(r) for r in costs['api_rows'])
            or not number(costs.get('minimum_callback_headroom_cck'))
            or not integer(costs.get('stack_bytes'),1,4095)):return False
    rows=costs['api_rows'];workers=[r for r in rows if r['name']=='game_preview_step']
    if any(a['end']['cck']>b['begin']['cck'] for a,b in zip(rows,rows[1:])):return False
    used=set();intervals=[]
    for job in jobs:
        c=job['costs'];indices=[c['request_api_row_index'],*c['worker_api_row_indices'],c['result_api_row_index']]
        if max(indices)>=len(rows) or used.intersection(indices):return False
        used.update(indices)
        intervals.append((indices[0],indices[-1]))
        middle=range(indices[0]+1,indices[-1])
        if (c['worker_api_row_indices']!=[i for i in middle if rows[i]['name']=='game_preview_step']
                or any(rows[i]['name'] not in ('game_preview_step','game_preview_result') for i in middle)):return False
        request=rows[indices[0]];result=rows[indices[-1]];steps=[rows[i] for i in c['worker_api_row_indices']]
        if (request['name']!='game_preview_request' or result['name']!='game_preview_result'
                or any(r['name']!='game_preview_step' for r in steps)
                or c['worker_body_counts']!=[r['bodies'] for r in steps]
                or c['worker_elapsed_cck']!=sum(r['elapsed_cck'] for r in steps)
                or c['maximum_worker_elapsed_cck']!=max(r['elapsed_cck'] for r in steps)
                or c['fields_to_result']!=result['end']['frame']-request['begin']['frame']
                or not math.isclose(c['seconds_to_result'],result['end']['seconds']-request['begin']['seconds'],
                                    abs_tol=1e-9,rel_tol=0)):return False
    intervals.sort()
    if any(a[1]>=b[0] for a,b in zip(intervals,intervals[1:])):return False
    if ({r['name'] for r in rows}!={'game_history_freeze','game_history_seek_begin',
            'game_history_seek_step','game_history_seek_commit','game_history_seek_cancel',
            'game_preview_request','game_preview_step','game_preview_result',
            'game_preview_cancel','game_history_resume_latest'}
            or sum(r['name']=='game_preview_request' for r in rows)<7
            or len(workers)<sum(r['costs']['worker_calls'] for r in jobs)+4
            or sum(r['bodies'] for r in workers)<sum(sum(r['costs']['worker_body_counts']) for r in jobs)
                +sum(r['partial_body_operations']+r['replacement_resolver_operations'] for r in replacements)
            or telemetry['public_boundary_drain_checks']<len(rows)
            or sum(r['irq'] for r in workers)!=interrupts['inside_worker_entries']
            or sum(r['irq'] for r in rows)!=interrupts['inside_api_entries']):return False
    budget=(video['simulation_interval_whole']+video['simulation_interval_fraction']/65536)*5
    if (not distribution(costs.get('worker_distribution'),budget,[r['elapsed_cck'] for r in workers])
            or not distribution(costs.get('callback_distribution'),budget)
            or not distribution(costs.get('fresh_input_callback_distribution'),budget)
            or costs['fresh_input_callback_distribution']['samples']!=physical['fresh_input_callbacks']):return False
    resources=stage.get('resources');identity=stage.get('compiled_identity')
    if (not isinstance(resources,dict)
            or not integer(resources.get('fixture_chip_free_bytes'),1,512*1024)
            or not integer(resources.get('fixture_loaded_bytes'),1,512*1024)
            or type(resources.get('product_static_loaded_bytes')) is not int
            or resources['product_static_loaded_bytes']!=259456
            or resources['fixture_chip_free_bytes']+resources['fixture_loaded_bytes']>512*1024
            or not isinstance(identity,dict)):return False
    core=identity.get('normalized_shared_core')
    if (not isinstance(core,dict) or core.get('matched') is not True
            or any(type(core.get(k)) is not int or core[k]!=v for k,v in
                dict(bytes=18020,relocations=257,sink_branches=14).items())
            or core.get('sha256')!='9a457929bc223b843132bb53af7d604ed574441e32c4651eb69897aa0b48689d'):return False
    hunks=identity.get('loaded_hunks');worker=identity.get('worker_bytes');overlay=identity.get('overlay')
    if (not isinstance(hunks,list) or not hunks or not isinstance(worker,dict)
            or not isinstance(overlay,dict)):return False
    spans=[]
    for h in hunks:
        if (not isinstance(h,dict) or h.get('matched') is not True
                or not integer(h.get('hunk'),0) or not integer(h.get('start'),0,512*1024-1)
                or not integer(h.get('bytes'),1,512*1024-h['start'])
                or not sha256(h.get('expected_sha256'))
                or h.get('actual_sha256')!=h['expected_sha256']):return False
        spans.append((h['start'],h['start']+h['bytes']))
    if (len({h['hunk'] for h in hunks})!=len(hunks)
            or sum(h['bytes'] for h in hunks)!=resources['fixture_loaded_bytes']):return False
    spans.sort()
    if any(a[1]>b[0] for a,b in zip(spans,spans[1:])):return False
    if not body_observation(stage.get('body_observation'),rows,hunks):return False
    if not seek_validation(stage.get('seek_validation'),rows,stage['body_observation']['frames'],evidence.get('files') or {},video['simulation_interval_whole']):return False
    frames=stage['body_observation']['frames']
    if any(f['ownership']['seek_active'] for f in frames if rows[f['api_row_index']]['name']=='game_preview_step'):return False
    seek_storage=identity.get('seek_storage')
    if (not isinstance(seek_storage,dict) or type(seek_storage.get('bytes')) is not int
            or seek_storage['bytes']!=734
            or not integer(seek_storage.get('loaded_start'),0,512*1024-734)
            or type(seek_storage.get('loaded_end')) is not int
            or seek_storage['loaded_end']!=seek_storage['loaded_start']+734
            or not any(a<=seek_storage['loaded_start']<seek_storage['loaded_end']<=b for a,b in spans)
            or seek_storage.get('fixture_executable_sha256')!=worker.get('fixture_executable_sha256')):return False
    for job in jobs:
        actual=[f for f in frames if f['depth']==1 and f['api_row_index'] in job['costs']['worker_api_row_indices']]
        if sum(f['ownership']['active']==1 for f in actual)!=job['costs']['resolver_operations']:return False
        for variant in (0,1):
            branch=[f for f in actual if f['ownership']['active']==2 and f['ownership']['variant']==variant]
            if (not branch or branch[0]['before']!=job['edited_state']
                    or branch[-1]['after']!=job['final_states'][variant]
                    or [e for f in branch for e in f['events']]!=job['ordered_outputs'][variant]):return False
    if (any(not sha256(worker.get(k)) for k in
            ('source_sha256','loaded_sha256','fixture_executable_sha256'))
            or not integer(worker.get('bytes'),1)
            or not integer(worker.get('loaded_start'),0,512*1024-1)
            or not integer(worker.get('loaded_end'),worker['loaded_start']+1,512*1024)
            or worker['loaded_end']-worker['loaded_start']!=worker['bytes']
            or not any(a<=worker['loaded_start']<worker['loaded_end']<=b for a,b in spans)
            or not hashes(overlay.get('original_sources')) or not hashes(overlay.get('generated_sources'))
            or overlay.get('seed_policy')!='DEMO_RECORDING-selection-only'
            or not isinstance(overlay.get('insertion_anchor'),str) or not overlay['insertion_anchor']
            or not isinstance(overlay.get('scope'),str) or not overlay['scope']
            or not sha256(identity.get('fixture_manifest_sha256'))
            or not sha256(identity.get('product_manifest_sha256'))):return False
    files=evidence.get('files');compiled=evidence.get('compiled_executables')
    if (not isinstance(files,dict) or not isinstance(compiled,dict)
            or worker['source_sha256']!=files.get('amiga/game/preview.s')
            or worker['fixture_executable_sha256'] not in compiled.values()
            or identity['fixture_manifest_sha256'] not in files.values()
            or identity['product_manifest_sha256'] not in files.values()
            or any(files.get(k)!=v for mapping in
                   (overlay['original_sources'],overlay['generated_sources']) for k,v in mapping.items())
            or 'amiga/main.s' not in overlay['original_sources']
            or 'scripts/preview_native_fixture.s' not in files):return False
    rpc=stage.get('rpc_transcript');inherited=stage.get('inherited_endpoint_validation')
    if (not isinstance(rpc,dict) or rpc.get('encoding')!='gzip-jsonl'
            or not isinstance(rpc.get('path'),str) or not sha256(rpc.get('sha256'))
            or files.get(rpc['path'])!=rpc['sha256']
            or not integer(rpc.get('compressed_bytes'),1,observed['raw_bytes'])
            or not integer(rpc.get('uncompressed_bytes'),rpc['compressed_bytes'])
            or not integer(rpc.get('calls'),1) or type(rpc.get('records')) is not int
            or rpc['records']!=2*rpc['calls']
            or not isinstance(inherited,dict) or inherited.get('scope')!='CPU9-independent-endpoints; native-labels-only'
            or inherited.get('cpu_receipt_sha256')!=CPU9_SHA
            or any(files.get(path)!=CPU9_SHA for path in CPU9_RECEIPTS)):return False
    closure=inherited.get('worker_guard_closure')
    if (inherited.get('current_ownership_cpu_receipt_sha256')!=SEEK_CPU_SHA
            or not isinstance(closure,dict) or closure.get('passed') is not True
            or type(closure.get('removed_entry_guards')) is not int or closure['removed_entry_guards']!=3
            or closure.get('current_source_sha256')!=files.get('amiga/game/preview.s')
            or closure.get('guard_removed_source_sha256')!='40c07983067fb211d75e655fd7affbcec572272d98e310728f976e9568c6ee5d'
            or not isinstance(closure.get('scope'),str) or not closure['scope']):return False
    event=stage.get('event_transcript')
    if (not isinstance(event,dict) or event.get('encoding')!='gzip-jsonl'
            or not isinstance(event.get('path'),str) or not sha256(event.get('sha256'))
            or files.get(event['path'])!=event['sha256'] or event['path']==rpc['path']
            or not integer(event.get('compressed_bytes'),1,observed['raw_bytes'])
            or event['compressed_bytes']+rpc['compressed_bytes']>observed['raw_bytes']
            or not integer(event.get('uncompressed_bytes'),event['compressed_bytes'])
            or type(event.get('notifications')) is not int
            or event['notifications']!=telemetry['notifications']):return False
    outside=stage.get('outside_publication')
    if (not isinstance(outside,dict) or not isinstance(outside.get('rules'),list)
            or not outside['rules'] or not isinstance(outside.get('writes'),list)
            or not integer(outside.get('count'),1) or outside['count']!=len(outside['writes'])):return False
    outside_rules={}
    for rule in outside['rules']:
        if (not isinstance(rule,dict) or not integer(rule.get('pc'),0,0xffffff)
                or rule['pc'] in outside_rules or not integer(rule.get('address'),0,0xffffff)
                or type(rule.get('bytes')) is not int or rule['bytes'] not in (1,2,4)
                or rule.get('operation') not in ('move','clr','addq','subq','st')
                or not isinstance(rule.get('destination'),str)
                or not isinstance(rule.get('instruction'),str)):return False
        outside_rules[rule['pc']]=rule
    for write in outside['writes']:
        if (not isinstance(write,dict) or not integer(write.get('pc'),0,0xffffff)
                or not integer(write.get('address'),0,0xffffff)
                or type(write.get('size')) is not int or write['size'] not in (1,2,4)
                or not integer(write.get('value'),0,2**(8*write['size'])-1)
                or not isinstance(write.get('position'),dict)
                or not integer(write['position'].get('cck'),0)):return False
        rule=outside_rules.get(write['pc'])
        if (not rule or not rule['address']<=write['address']<write['address']+write['size']<=rule['address']+rule['bytes']):return False
    return stage.get('continuous_actual_core_equal') is True
