"""Bounded read-only HUD cost probe, same one-time native initialization on both products."""
import os, sys, re, json, hashlib
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'scripts'));os.chdir(root)
from native_tools import ROOT, ASSEMBLER, emulator_config, run
from native_evidence import compile_manifest, atomic_json
from native_observation import code_symbols, target_log
from native_hunk import loaded_hunks
from native_metrics_observation import MetricsObserver
from fractions import Fraction
from copperline_test_session import NativeControlSession
for standard in ('PAL','NTSC'):
 for exchanged in (False,True):
  directory=ROOT/'build/tests/hud-cost'/f'{standard.lower()}-{int(exchanged)}';directory.mkdir(parents=True,exist_ok=True)
  source=(ROOT/'amiga/main.s').read_text();marker='        bsr     game_begin_title'
  assert source.count(marker)==1
  init='        moveq #0,d0\n        bsr game_new_match\n        bsr game_begin_active\n'
  for name,value in [('game_mode',16 if exchanged else 0),('game_score_flags',64|(2 if exchanged else 1)),('game_point_a',4),('game_point_b',3),('game_games_a',5),('game_games_b',2),('game_display',0xa6),('game_status_clock',224)]:init+=f'        move.b #{value},{name}\n'
  init+='        bsr game_scene_build_players\n';source=source.replace(marker,init)
  fixture=directory/'fixture.s';fixture.write_text(source);exe=directory/'native-fixture';listing=directory/'native.lst'
  run([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-DENHANCED_INTERFACE=1','-L',str(listing),'-o',str(exe),str(fixture)])
  compile_manifest(exe,listing);text=listing.read_text();symbols=code_symbols(text);cfg=emulator_config()
  with NativeControlSession(directory) as s:
   s.inspect('session_launch',{'binary':cfg['tools']['copperline'],'run':str(exe),'args':['--chipset','OCS','--video',standard,'--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',cfg['inputs']['amiga_rom']]})
   stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg';segments=s.inspect('segments.list')['current'];base=segments[0]['start']
   def raw(a,n):return bytes.fromhex(s.inspect('mem_read',{'addr':a,'len':n})['data'])
   loaded=loaded_hunks(exe,segments,raw);assert loaded and all(x['matched'] for x in loaded)
   metrics=MetricsObserver(base,symbols,text);cachebase=base+symbols['score_pointer_cache'];cache=bytearray(raw(cachebase,18));masks={};state={'callback':0}
   def observe(message):
    metrics.observe(message)
    if message.get('method')!='event.mmio':return
    r=message['params'];a=r['addr'];size=r['size']
    if a==base+symbols['simulation_started_updates']:state['callback']=r['value']
    if cachebase<=a and a+size<=cachebase+18 and r['access']=='write':
     for i,value in enumerate(r['value'].to_bytes(size,'big')):
      off=a-cachebase+i
      if value!=cache[off]:masks[state['callback']]=masks.get(state['callback'],0)|(1<<(off%6))
      cache[off]=value
   s.notification_handler=observe
   s.inspect('events.subscribe',{'events':['mmio'],'mmio':metrics.watches()+[{'addr':cachebase,'len':18,'access':'write'}]})
   s.inspect('run_until',{'seconds':stop['seconds']+1.0})
   s.inspect('events.unsubscribe');s.notification_handler=None
   assert metrics.dropped==0 and metrics.rows and metrics.timer_start and metrics.timer_origin is not None
   interval=Fraction((int.from_bytes(raw(base+symbols['simulation_interval_whole'],4),'big')*65536+int.from_bytes(raw(base+symbols['simulation_interval_fraction'],2),'big'))*5,65536)
   origin=metrics.timer_start['cck']+(65535-metrics.timer_origin)*5
   rows=[dict(callback=r['callback'],changed_fields_mask=masks.get(r['callback'],0),work_cck=r['completion']['cck']-r['entry']['cck'],entry_lateness_cck=float(r['entry']['cck']-(origin+(r['callback']-1)*interval)),deadline_headroom_cck=float(origin+r['callback']*interval-r['completion']['cck'])) for r in metrics.rows]
   groups={}
   for mask in sorted({r['changed_fields_mask'] for r in rows}):
    group=[r for r in rows if r['changed_fields_mask']==mask]
    groups[str(mask)]={'samples':len(group),'max_work_cck':max(r['work_cck'] for r in group),'max_entry_lateness_cck':max(r['entry_lateness_cck'] for r in group),'minimum_deadline_headroom_cck':min(r['deadline_headroom_cck'] for r in group)}
   deadline_passed=all(r['deadline_headroom_cck']>=-11 for r in rows)
   report={'measurement_complete':True,'deadline_passed':deadline_passed,'standard':standard,'exchanged':exchanged,'chip_bytes':524288,'slow_bytes':0,'fast_bytes':0,'rows':rows,'groups':groups,'loaded_hunks':loaded,'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'one-time serve initialization with points4/3, games5/2, status6; no later state injection; callback entry/completion counter bus writes; changed masks derived from cache bytes, bits pointA/pointB/WINA/WINB/status/mode; observed extrema, not bounds','cck_hz':3546895 if standard=='PAL' else 3579545,'simulation_interval_cck':float(interval)}
  target_log(directory,standard=standard);atomic_json(directory/'report.json',report);print(standard,exchanged,groups,flush=True)
