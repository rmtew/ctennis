"""Offline recording of physical inputs in ordinary native play; never included in runtime."""
import sys,re,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_native_game import build
from capture_native_presentation import code_symbols
from copperline_test_session import NativeControlSession
config,exe=build(flavor='original');symbols=code_symbols((exe.parent/'native.lst').read_text());directory=exe.parents[3]/'tests/demo-input-recording';rows=[]
with NativeControlSession(directory) as s:
 s.inspect('session_launch',{'binary':config['tools']['copperline'],'run':str(exe),'args':['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
 stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg',stop
 base=int(re.search(r'first hunk \$([0-9a-fA-F]+)',stop['detail'])[1],16);time=stop['seconds']
 def advance(t):
  global time
  time+=t; s.inspect('run_until',{'seconds':time})
 def mem(n,k):return bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols[n],'len':k})['data'])
 advance(2);s.inspect('input_key',{'rawkey':0x46,'action':'press'});advance(1.5);s.inspect('input_key',{'rawkey':0x46,'action':'release'});advance(.1)
 assert int.from_bytes(mem('game_lifecycle',2),'big')==1
 s.inspect('input_set_port',{'port':2,'device':'joystick'})
 # Record actual physical sampled input packets at the ordinary sample boundary.
 # Finite action/direction timeline; normal gameplay and AI run without RAM writes.
 timeline={0:{'red':True},24:{'red':False},50:{'left':True},70:{'left':False},90:{'blue':True},114:{'blue':False},145:{'up':True},160:{'up':False},180:{'right':True},200:{'right':False},215:{'red':True},239:{'red':False}}
 for tick in range(300):
  if tick in timeline:s.inspect('input_joy',{'port':2,**timeline[tick]})
  stop=s.inspect('run_until',{'pc':base+symbols['input_ready']});assert stop['reason']=='target',stop;time=stop['seconds']
  packet=mem('game_input_bits',1)[0]
  if rows and rows[-1][1]==packet:rows[-1][0]+=1
  else:rows.append([1,packet])
  s.inspect('step',{'count':1})
 record={'schema':1,'origin':'Copperline physical port 2 input, ordinary original native title/start/play; read-only sampling at input_ready, no state writes','executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'target':'PAL A500 68000 OCS 512KB chip no expansion Kickstart 1.3','frames':300,'packets':rows,'events':timeline}
 (Path(__file__).resolve().parents[1]/'assets/interface/demo-inputs.json').write_text(json.dumps(record,indent=2)+'\n');print(record)
