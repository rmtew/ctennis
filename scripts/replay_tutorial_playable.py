"""Read-only reconstruction of retained prototype bus events, including failures.

This does not execute or model gameplay. It reuses the observer on literal
recorded accesses and keeps failed native receipts failed.
"""
import argparse,gzip,hashlib,json
from pathlib import Path
from build_match_core import load_image
from tutorial_capture import CallbackObserver
from coherent_publication import CoherentSurfaceObserver
from run_tutorial_capture import FIELDS

def replay(attempt,standard):
    attempt=Path(attempt);raw=attempt/'literal-rpc.jsonl.gz';cache=bytearray(512*1024);seen=bytearray(len(cache));request=None;symbols=None
    for line in gzip.open(raw,'rt'):
        x=json.loads(line)
        if x.get('type')=='request':
            request=x
            if x.get('method')=='events.subscribe':break
        elif x.get('type')=='reply':
            if x.get('method')=='segments.list':
                symbols=load_image(attempt/'baseline-rally',hunk_addresses=[h['start'] for h in x['result']['current']])[1]
            if request and request.get('method') in ('mem.read','mem_read'):
                a=request['arguments']['addr'];data=bytes.fromhex(x['result']['data']);cache[a:a+len(data)]=data;seen[a:a+len(data)]=b'\1'*len(data)
    assert symbols
    def read(a,n):
        assert all(seen[a:a+n]),('Missing recorded initial bytes',a,n)
        return bytes(cache[a:a+n])
    cb=CallbackObserver(0,symbols);cb.surfaces=CoherentSurfaceObserver(symbols,read,last_line=311 if standard=='PAL' else 261,verify_sprites=True)
    extra=dict(tutorial_job_cost=4,tutorial_job_budget=2,tutorial_job_kind=2,tutorial_job_variant=2,
        game_preview_primed_mask=2,game_preview_synthetic_phases=4,game_preview_flight_phases=4,
        simulation_interval=4,simulation_phase=4,keyboard_ack=1,keyboard_ack_timer=2)
    cb.watches(dict(FIELDS,**extra),read);active=False;last_stop=None;critical=[]
    for line in gzip.open(raw,'rt'):
        x=json.loads(line)
        if x.get('type')=='request':
            request=x
            if x.get('method')=='events.subscribe':active=True
        elif x.get('type')=='reply':
            if x.get('method')=='run_until':last_stop=x['result']
            if active and request and request.get('method') in ('mem.read','mem_read'):
                a=request['arguments']['addr'];n=request['arguments']['len']
                names=[name for name,width in (('game_core_state',318),('game_history_state',72),('tutorial_interrupted_state',318),('game_input_bits',2),('game_input_pressed',2)) if symbols[name]==a and n==width]
                if names:critical.append(dict(name=names[0],data=x['result']['data'],stop=last_stop))
        elif active and x.get('type')=='notification':cb.observe(x['value'])
    mismatches=[]
    for index,p in enumerate(cb.surfaces.publications):
        bank=p.get('tutorial_fields',{});live=p.get('publication_live_fields',{})
        if bank.get('tutorial_active') and not bank.get('tutorial_generation')==bank.get('tutorial_presentation_generation')==live.get('tutorial_generation'):
            mismatches.append(dict(index=index,position=p['position'],surface=p['surface'],bank=bank,live=live,native_sprite_check=p.get('native_sprite_check')))
    return dict(schema=1,standard=standard,raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),executable_sha256=hashlib.sha256((attempt/'baseline-rally').read_bytes()).hexdigest(),symbols={n:symbols[n] for n in ('plane0','tutorial_surface0','tutorial_surface1','tutorial_resume_restored','game_history_state','game_history_mode','game_history_position','game_history_cursor')},publications=cb.surfaces.publications,mismatches=mismatches,callbacks=cb.rows,critical_reads=critical,scope='Offline literal-event reconstruction; native failure remains failed. No new native execution or gameplay oracle.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('attempt');p.add_argument('--ntsc',action='store_true');p.add_argument('--output',required=True);args=p.parse_args()
    result=replay(args.attempt,'NTSC' if args.ntsc else 'PAL');result['reducer_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    Path(args.output).write_bytes(gzip.compress(json.dumps(result,separators=(',',':')).encode(),mtime=0));print(json.dumps(dict(publications=len(result['publications']),mismatches=result['mismatches'],output=args.output)))
