"""Offline native full-match input recorder; ships no world snapshots or capture machinery."""
import sys,re,json,hashlib,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_native_game import build
from native_tools import ASSEMBLER,run
from native_observation import code_symbols
from copperline_test_session import NativeControlSession
from native_evidence import ROOT,atomic_json

def record():
 config,ordinary=build(flavor='enhanced');directory=ROOT/'build/tests/demo-full-recording';directory.mkdir(parents=True,exist_ok=True)
 exe=directory/'native-recording';listing=directory/'native.lst'
 # Offline-only build selects the same seeded entropy provider. UI demo stays off;
 # normal physical input and normal title/start are exercised without playback.
 run([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-DENHANCED_INTERFACE=1','-DDEMO_RECORDING=1','-L',str(listing),'-o',str(exe),'amiga/gameplay_integration_probe.s'])
 symbols=code_symbols(listing.read_text());rows=[];digests=[];awards=[];lastgames=[0,0];lastmask=None
 with NativeControlSession(directory) as s:
  s.inspect('session_launch',{'binary':config['tools']['copperline'],'run':str(exe),'args':['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
  stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg',stop
  base=int(re.search(r'first hunk \$([0-9a-fA-F]+)',stop['detail'])[1],16);time=stop['seconds']
  def advance(t):
   nonlocal time
   time+=t; s.inspect('run_until',{'seconds':time})
  def mem(n,k=1):return bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols[n],'len':k})['data'])
  advance(2);s.inspect('input_key',{'rawkey':1,'action':'press'});advance(.1);s.inspect('input_key',{'rawkey':1,'action':'release'})
  s.inspect('input_set_port',{'port':2,'device':'joystick'})
  started=None
  for tick in range(30000):
   stop=s.inspect('run_until',{'pc':base+symbols['game_source_tick']});time=stop['seconds']
   life=int.from_bytes(mem('game_lifecycle',2),'big')
   if life in (6,7,8):break
   if life!=1:
    s.inspect('step',{'count':1});continue
   stop=s.inspect('run_until',{'pc':base+symbols['game_assignment_done']});time=stop['seconds']
   if started is None:started=time
   world=mem('game_play_state',60);score=mem('game_score_state',28)
   packet=mem('game_input_bits')[0]
   if rows and rows[-1][1]==packet:rows[-1][0]+=1
   else:rows.append([1,packet])
   digests.append(hashlib.sha256(world+score+mem('ui_entropy_state',2)).hexdigest())
   games=list(mem('game_games_a',2))
   if games!=lastgames:
    awards.append({'input_tick':len(digests)-1,'games':games,'seconds':time-started});lastgames=games
    s.inspect('capture_screenshot',{'path':str(directory/f'award-{sum(games)}.png')})
    print('award',awards[-1],flush=True)
   # Read-only physical performer: move toward the incoming ball's native target,
   # return to centre between shots, serve with brief action pulses. No RAM writes.
   if tick%8==0:
    flipped=bool(mem('game_mode')[0]&16);off=10 if flipped else 0;phase,y,x=world[off],world[off+2],world[off+3]
    receiving=bool(world[24]&64)==(not flipped)
    tx=max(68 if flipped else 44,min(172 if flipped else 196,world[36]-8)) if receiving and world[23] else 120
    ty=max(10 if flipped else 100,min(58 if flipped else 150,world[35]-(35 if flipped else 27))) if receiving and world[23] else (30 if flipped else 128)
    # Occasional delayed positioning is intentional: a finite human-like performance,
    # not an unbeatable second AI. It still demonstrates movement and auto returns.
    if tick%600>=520:tx=120;ty=30 if flipped else 128
    mask=(1 if x<tx-4 else 4 if x>tx+4 else 0)|(8 if y<ty-3 else 2 if y>ty+3 else 0)
    if phase&64 and tick%32<8:mask|=16
    if tick%480<8 and not phase&64:mask|=32
    if mask!=lastmask:
     s.inspect('input_joy',{'port':2,'right':bool(mask&1),'up':bool(mask&2),'left':bool(mask&4),'down':bool(mask&8),'red':bool(mask&16),'blue':bool(mask&32)});lastmask=mask
   s.inspect('step',{'count':1})
  else:raise AssertionError('No complete native match inside30000 active input ticks')
  finalgames=list(mem('game_games_a',2));assert max(finalgames)==6,(life,finalgames)
  s.inspect('capture_screenshot',{'path':str(directory/'match-award.png')})
 recording={'schema':2,'game_version':'native-rules-v1','input_clock':'input_update invocations; active callbacks only','entropy_version':'galois16-b400-v1','seed':44257,'initial_game_random':0,'origin':'ordinary native boot/title/one-player start, actual sampled physical port2 inputs; read-only performer; no world writes','target':'PAL A500 68000 OCS 512KB chip no expansion Kickstart1.3','frames':len(digests),'seconds':time-started,'packets':rows,'final_games':finalgames,'awards':awards,'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()}
 atomic_json(directory/'recording.json',recording);atomic_json(directory/'digests.json',digests)
 (ROOT/'assets/interface/demo-inputs.json').write_text(json.dumps(recording,indent=2)+'\n')
 print(json.dumps({'frames':len(digests),'runs':len(rows),'table_bytes':4*len(rows)+2,'seconds':time-started,'games':finalgames}),flush=True)
if __name__=='__main__':record()
