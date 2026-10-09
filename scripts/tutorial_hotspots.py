"""Bounded profile reduction; flat PCs and observed call spans are distinct."""
import collections
import json
import re
import struct
from pathlib import Path
from tutorial_latency import StackTiming


class WorkerTiming(StackTiming):
    def __init__(self, *args):
        super().__init__(*args)
        self.active = False
        self.state = None
        self.roots = {pc for pc, call in self.calls.items() if call['callee']=='game_preview_step'}
        assert len(self.roots)==1

    def observe(self, row):
        if not self.active:
            return
        if not self.stack and not (row['access']=='write' and row['size']==4 and row['pc'] in self.roots):
            return
        super().observe(row)
        if row['access']=='write' and row['size']==4 and row['pc'] in self.roots:
            assert self.state is not None
            self.stack[-1]['generation']=self.state['tutorial_generation']
            self.stack[-1]['preview_status']=self.state['game_preview_status']
        assert len(self.rows)<=20000, 'Bounded worker call-row cap'


def union(spans):
    total = 0
    end = -1
    for a,b in sorted(spans):
        assert a<=b
        total += max(0,b-max(a,end))
        end=max(end,b)
    return total


def summarize_workers(rows, start, stop, generation):
    roots=[r for r in rows if r['depth']==0 and r['generation']==generation and start<=r['entry']['cck']<=r['exit']['cck']<=stop]
    assert roots and all(r['callee']=='game_preview_step' for r in roots)
    selected=[r for r in rows if any(p['entry']['cck']<=r['entry']['cck']<=r['exit']['cck']<=p['exit']['cck'] for p in roots)]
    functions={}
    categories=collections.Counter()
    for r in selected:
        f=functions.setdefault(r['callee'],dict(calls=0,inclusive_bus_cck=0,exclusive_bus_cck=0,maximum_bus_cck=0))
        f['calls']+=1;f['inclusive_bus_cck']+=r['elapsed_bus_cck']
        f['exclusive_bus_cck']+=r['exclusive_bus_cck'];f['maximum_bus_cck']=max(f['maximum_bus_cck'],r['elapsed_bus_cck'])
        categories[r['category']]+=r['exclusive_bus_cck']
    inclusive=sum(r['elapsed_bus_cck'] for r in roots)
    assert sum(categories.values())==inclusive
    return dict(protocol='Actual emitted call stack stores and matched RTS reads, rooted only at game_preview_step',
        scope='Wholly contained workers in physical fresh-edit to first actual held endpoint; IRQ/contention included; instruction pre-store/post-read tails excluded',
        start_cck=start,stop_cck=stop,generation=generation,worker_calls=len(roots),worker_inclusive_bus_cck=inclusive,
        core_body_subtree_union_cck=union([(r['entry']['cck'],r['exit']['cck']) for r in selected if r['category']=='core-body']),
        exclusive_categories=dict(categories),functions=functions,
        root_spans=[dict(entry=r['entry'],exit=r['exit'],preview_status=r['preview_status'],elapsed_bus_cck=r['elapsed_bus_cck']) for r in roots])


def decode_frame(stream, metadata):
    assert metadata[:4]==b'CLSM' and len(metadata)>=12
    version,count=struct.unpack_from('<II',metadata,4)
    assert version==1 and len(metadata)==12+20*count and len(stream)==8*count
    for i in range(count):
        pc,cost=struct.unpack_from('<II',stream,8*i)
        total,instruction,wait,level,vector=struct.unpack_from('<IIIII',metadata,12+20*i)
        assert 0<total<65535, 'Scope rejects legal max-chunk/split samples rather than miscounting instructions'
        assert cost==0xffffffff-total and instruction+wait==total
        irq=level!=0xffffffff
        assert (pc==0x7fffffff)==irq and (vector!=0xffffffff)==irq
        yield pc,total,instruction,wait,irq


def summarize_profile(directory, listing, segments):
    summary=json.loads((directory/'profile.json').read_text())
    assert summary['options']['samples'] and not summary['options']['registers']
    assert not summary['options']['slots'] and not summary['options']['memory']
    assert summary['sampling']['cck_per_cpu_cycle']==0.5
    assert not summary.get('samples_dropped',0)
    instructions={}
    for h,o,encoded,mnemonic,operand in re.findall(r'^(\d\d):([\da-fA-F]{8})[ \t]+([\dA-F]+)[ \t]+[^\n]*?:[ \t]*(\S+)[ \t]*([^\n]*)$',listing,re.M):
        instructions[segments[int(h)]['start']+int(o,16)]=dict(source_mnemonic=mnemonic,operand=operand.strip(),emitted=encoded)
    # Lexical source regions are not an unwind table or a reconstructed call graph.
    root=Path(__file__).resolve().parents[1]
    names=set()
    for path in [root/'amiga/main.s',*(root/'amiga/game').glob('*.s')]:
        names.update(re.findall(r'^([A-Za-z_]\w*):',path.read_text(),re.M))
    labels=sorted((segments[int(h)]['start']+int(o,16),n) for n,h,o in re.findall(r'^([A-Za-z_]\w*)\s+(\d\d):([\da-fA-F]{8})\s*$',listing,re.M) if n in names and int(h)==0)
    import bisect
    addresses=[a for a,n in labels]
    pcs={};functions={};owners=collections.Counter();deniers=collections.Counter()
    total_rows=ordinary=irq_cck=0;frames=[]
    for line in (directory/'profile.jsonl').read_text().splitlines():
        row=json.loads(line)
        assert 'marker' not in row and row['traced']
        data=(directory/row['samples']).read_bytes();meta=(directory/row['samples_meta']).read_bytes()
        local=list(decode_frame(data,meta));assert len(local)==row['sample_count']
        retired=sum(not r[-1] for r in local)
        assert retired==row['retired'], 'Retired instruction/sample completeness mismatch'
        for pc,total,instruction,wait,irq in local:
            total_rows+=1
            if irq:
                irq_cck+=total;continue
            ordinary+=1
            f=pcs.setdefault(pc,dict(pc=pc,count=0,charged_cck=0,chip_wait_cck=0,total_cck=0,minimum_charged_cck=instruction,maximum_charged_cck=instruction))
            f['count']+=1;f['charged_cck']+=instruction;f['chip_wait_cck']+=wait;f['total_cck']+=total
            f['minimum_charged_cck']=min(f['minimum_charged_cck'],instruction);f['maximum_charged_cck']=max(f['maximum_charged_cck'],instruction)
        if not row.get('partial'):
            owners.update(row['owner_cck']);deniers.update(row['cpu']['wait_by'])
        frames.append(dict(frame=row['frame'],seconds=row['seconds'],partial=row.get('partial',False),retired=retired,samples=len(local),sample_cck=sum(r[1] for r in local),cpu_wait=row['cpu']))
    assert total_rows==summary['samples_total'] and irq_cck==summary['irq_cck'] and len(frames)==summary['frames_written']
    for pc,f in pcs.items():
        index=bisect.bisect_right(addresses,pc)-1
        in_code=segments[0]['start']<=pc<segments[0]['start']+56836
        name=labels[index][1] if index>=0 and in_code else 'outside-native-code'
        f.update(region=name,**instructions.get(pc,{}))
        g=functions.setdefault(name,dict(instructions=0,charged_cck=0,chip_wait_cck=0,total_cck=0,entry_visits=0))
        for key,pkey in [('instructions','count'),('charged_cck','charged_cck'),('chip_wait_cck','chip_wait_cck'),('total_cck','total_cck')]:g[key]+=f[pkey]
        if index>=0 and pc==labels[index][0]:g['entry_visits']+=f['count']
    return dict(scope='Flat precise instruction samples for the bounded profile capture, including trailing commit frames; lexical source regions, no invented unwind/call graph; full-frame DMA ownership only',
        started=summary['started'],ended=summary['ended'],last_committed_frame=frames[-1]['frame'],
        frames=len(frames),ordinary_instructions=ordinary,encoded_samples=total_rows,irq_cck=irq_cck,
        charged_cck=sum(f['charged_cck'] for f in pcs.values()),chip_wait_cck=sum(f['chip_wait_cck'] for f in pcs.values()),
        cck_per_cpu_cycle=0.5,complete_frame_bus_owners=dict(owners),complete_frame_cpu_wait_by=dict(deniers),
        lexical_regions=functions,top_pcs=sorted(pcs.values(),key=lambda r:r['total_cck'],reverse=True)[:80],frame_summaries=frames,
        completeness='Every CLSM row paired with exact cost/PC stream; ordinary rows equal every frame retired count; totals equal profile summary; legal max/split chunks rejected as unsupported scope; pinned e65a958 has no explicit sample-drop counter; uncommitted stop tail excluded')


def required_hotspots_extent(report, standard):
    import math
    from native_tools import ROOT
    from native_evidence import digest,TARGET
    evidence=report.get('evidence') or {};files=evidence.get('files') or {}
    if not (report.get('passed') is True and report.get('profiling') is True and report.get('target')==dict(TARGET,video=standard)
            and evidence.get('state')=='complete' and not evidence.get('changed_during_run')
            and evidence.get('actual_target')==report.get('target')
            and evidence.get('native_product_commit')=='6f2828735c273258c0c0abdb577778f1e831a7ae'
            and report.get('executable_sha256')=='c543a695d9493254eb152cf34a093676c3c0c0dcd4df203d0ad105a5b97e3cb8'
            and report.get('full318_history72_backup_guard') and report.get('dropped_notifications')==0):return False
    capture=report.get('capture','')
    if capture!=f'build/tests/tutorial-hotspots-{standard.lower()}/hotspots.json' or files.get(capture)!=digest(ROOT/capture):return False
    data=json.loads((ROOT/capture).read_text());profile=data['profile'];timing=data['worker_timing']
    if not (0<profile['frames']<=64 and profile['ordinary_instructions']>0 and profile['cck_per_cpu_cycle']==0.5
            and report.get('profile_summary')==profile and report.get('timing')==data.get('timing')
            and data.get('final_stop',{}).get('pc')==data.get('probe_symbols',{}).get('simulation_update')
            and data['timing']['pending_callback'] is None and math.isfinite(data['timing']['minimum_absolute_headroom_cck'])
            and data['timing']['minimum_absolute_headroom_cck']>0
            and data['timing']['dropped_notifications']==0 and report.get('endpoints')==data.get('endpoints')
            and 0<data.get('literal_rpc',{}).get('uncompressed_bytes',0)<=64*1024*1024
            and timing['worker_calls']>0 and timing['core_body_subtree_union_cck']>0
            and sum(timing['exclusive_categories'].values())==timing['worker_inclusive_bus_cck']):return False
    caps=report.get('declared_caps') or {}
    if caps!=dict(physical_seconds=30,callbacks=1024,boundary_stops=4096,profile_frames=64,profile_bytes=32*1024*1024,uncompressed_transcript_bytes=64*1024*1024):return False
    if report.get('actual_video')!=([311,11838,14906] if standard=='PAL' else [261,11947,13180]):return False
    endpoints=data.get('endpoints') or []
    if len(endpoints)!=2 or [r['label'] for r in endpoints]!=['initial-held','fresh-D-edit']:return False
    fresh=endpoints[-1];publication=fresh['first_actual_publication'];clock=3546895 if standard=='PAL' else 3579545
    fields=publication.get('tutorial_fields') or {}
    delta=publication['position']['cck']-fresh['request']['cck']
    if not (delta>0 and delta==fresh['latency_cck']==fresh['input_to_publication_cck']
            and fresh['physical_latency_seconds']==fresh['physical_input_latency_seconds']==delta/clock
            and fields.get('tutorial_generation')==fields.get('tutorial_marker_generation')==fields.get('tutorial_presentation_generation')==fresh['generation']
            and fresh['generation']!=endpoints[0]['generation']
            and fields.get('tutorial_active_variant')==0 and fields.get('tutorial_ball_mode')==1
            and fields.get('tutorial_marker_ready') and fields.get('tutorial_placement_ready') and not fields.get('tutorial_placement_dirty')
            and publication['generation']==fields.get('tutorial_published_generation')
            and timing['generation']==fresh['generation']
            and publication.get('native_sprite_check',{}).get('matched') is True
            and profile['started']['seconds']<=fresh['request']['provider_seconds']
            and profile['last_committed_frame']>=publication['position']['frame']+2
            and profile['frames']<caps['profile_frames']):return False
    frozen=[]
    for row in data.get('boundaries',[]):
        if any(len(bytes.fromhex(row[n]))!=size for n,size in [('state',318),('history',72),('backup',318)]):return False
        if row['fields']['tutorial_active']:frozen.append(tuple(row[n] for n in ('state','history','backup')))
    if not frozen or len(frozen)!=report.get('frozen_boundaries') or any(r!=frozen[0] for r in frozen):return False
    directory=(ROOT/capture).parent/'profile'
    artifacts=[p for p in directory.iterdir() if p.is_file()]
    return bool(artifacts) and sum(p.stat().st_size for p in artifacts)<=32*1024*1024 and all(files.get(str(p.relative_to(ROOT)))==digest(p) for p in artifacts)
