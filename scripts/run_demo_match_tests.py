from native_tools import emulator_config
"""Finite seeded full-native-match replay and live takeover; no RAM writes."""
import argparse,hashlib,json,re
from build_native_game import build
from native_observation import code_symbols
from copperline_test_session import NativeControlSession
from native_evidence import ROOT,atomic_json,tracked_call
from native_observation import target_log

def load_trajectory(recording_path):
 fixture=ROOT/'tests/fixtures/native-demo'
 manifest=json.loads((fixture/'manifest.json').read_text())
 payload=(fixture/'trajectory.sha256').read_bytes()
 assert manifest['schema']==1 and manifest['encoding']=='one lowercase SHA256 hexadecimal digest per line'
 assert len(payload)==manifest['payload_bytes']==manifest['frames']*65
 assert hashlib.sha256(payload).hexdigest()==manifest['payload_sha256'],'Canonical trajectory fixture checksum mismatch'
 assert hashlib.sha256(recording_path.read_bytes()).hexdigest()==manifest['recording_sha256'],'Recording does not match canonical trajectory'
 expected=payload.decode('ascii').splitlines()
 assert len(expected)==manifest['frames'] and all(re.fullmatch('[0-9a-f]{64}',value) for value in expected)
 assert hashlib.sha256(b''.join(bytes.fromhex(value) for value in expected)).hexdigest()==manifest['normalized_raw_digest_sha256']
 return expected,manifest

def run(takeover=False):
 config,exe=build(flavor='enhanced'); config = emulator_config();compiled_modules=json.loads((exe.parent/'build-report.json').read_text())['native_modules'];symbols=code_symbols((exe.parent/'native.lst').read_text())
 recording_path=ROOT/'assets/interface/demo-inputs.json'
 recording=json.loads(recording_path.read_text());expected,fixture_manifest=load_trajectory(recording_path)
 assert recording['schema']==2 and len(expected)==recording['frames']
 assert recording['entropy_version']=='galois16-b400-v1' and 0<recording['seed']<65536 and recording['initial_game_random']==0
 directory=ROOT/('build/tests/demo-mid-takeover' if takeover else 'build/tests/demo-full-repeat');checks=[];awards=[];seen_games=[0,0];index=0;contacts=0;previous_side=None
 def check(label,actual,expected_value):
  checks.append({'label':label,'actual':actual,'expected':expected_value})
  if actual!=expected_value:raise AssertionError(checks[-1])
 with NativeControlSession(directory) as s:
  s.inspect('session_launch',{'binary':config['tools']['copperline'],'run':str(exe),'args':['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
  stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg',stop
  base=int(re.search(r'first hunk \$([0-9a-fA-F]+)',stop['detail'])[1],16);time=stop['seconds']
  def until(args):
   nonlocal time
   stop=s.inspect('run_until',args);time=stop['seconds'];return stop
  def mem(n,k=1):return bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols[n],'len':k})['data'])
  def num(n,k=1):return int.from_bytes(mem(n,k),'big')
  def frozen():return mem('game_play_state',60)+mem('game_score_state',28)+mem('game_audio_voices',96)+mem('game_audio_wait')+mem('game_action_clock')+mem('game_status_clock')+mem('game_aux_clock')+mem('ui_entropy_state',2)
  until({'pc':base+symbols['ui_seed_entropy']});check('ordinary title idle starts seeded demo',num('ui_demo'),255)
  s.inspect('step',{'count':1});check('actual initialized seed matches metadata',num('ui_entropy_state',2),recording['seed'])
  for callback in range(30000):
   until({'pc':base+symbols['game_tick_dispatch']});life=num('game_lifecycle',2)
   if life in (6,7,8):break
   if life!=1:
    s.inspect('step',{'count':1});continue
   until({'pc':base+symbols['game_assignment_done']})
   world=mem('game_play_state',60);score=mem('game_score_state',28)
   digest=hashlib.sha256(world+score+mem('ui_entropy_state',2)).hexdigest()
   assert index<len(expected),(index,len(expected))
   if digest!=expected[index]:raise AssertionError(('seeded trajectory differs',index,digest,expected[index]))
   games=list(mem('game_games_a',2))
   if games!=seen_games:
    awards.append({'input_tick':index,'games':games});seen_games=games
    print('replay award',awards[-1],flush=True)
   side=bool(world[24]&64)
   if previous_side is not None and side!=previous_side and world[23]:contacts+=1
   previous_side=side
   if index in (len(expected)//4,len(expected)//2,3*len(expected)//4):
    s.inspect('capture_screenshot',{'path':str(directory/f'rally-{index}.png')})
   if takeover and index==len(expected)//2:
    s.inspect('input_key',{'rawkey':0x4f,'action':'press'})
    for attempt in range(12):
     until({'pc':base+symbols['ui_sample']});until({'pc':base+symbols['ui_input_draw']})
     if num('ui_demo_choice')==1:break
    check('left selects takeover',num('ui_demo_choice'),1)
    s.inspect('input_key',{'rawkey':0x44,'action':'press'})
    for attempt in range(12):
     until({'pc':base+symbols['ui_sample']});before=frozen()
     until({'pc':base+symbols['ui_input_draw']})
     if not num('ui_demo'):
      check('mid-match takeover preserves world score audio clocks entropy',frozen().hex(),before.hex());break
    else:raise AssertionError('Mid-match selected Enter never took over')
    until({'pc':base+symbols['native_input_done']});check('takeover held direction and confirmation consumed',num('game_input_bits',2),0)
    state=mem('ui_entropy_state',2);before=mem('game_play_state',60)
    until({'seconds':time+1});check('live entropy stops advancing demo generator',mem('ui_entropy_state',2).hex(),state.hex())
    check('AI remains assigned after takeover',num('game_score_flags')&3,2 if num('game_mode')&16 else 1)
    check('ordinary world continues after takeover',mem('game_play_state',60)!=before,True)
    s.inspect('input_key',{'rawkey':0x44,'action':'release'})
    s.inspect('input_key',{'rawkey':0x4f,'action':'release'})
    s.inspect('capture_screenshot',{'path':str(directory/'taken-over.png')});index+=1;break
   if not takeover and index in (100,200,300,400):
    s.inspect('input_key',{'rawkey':(0x4f,0x4e,0x4c,0x4d)[index//100-1],'action':'press'})
   if not takeover and index in (150,250,350,450):
    s.inspect('input_key',{'rawkey':(0x4f,0x4e,0x4c,0x4d)[(index-50)//100-1],'action':'release'})
   index+=1;s.inspect('step',{'count':1})
  else:raise AssertionError('Full playback did not end within finite bound')
  if not takeover:
   check('all recorded input ticks reproduce native trajectory',index,len(expected))
   check('complete match award reproduced',list(mem('game_games_a',2)),recording['final_games'])
   check('normal match result lifecycle',life,6)
   s.inspect('capture_screenshot',{'path':str(directory/'complete-match.png')})
  if not takeover:
   # After the independently frozen full match, retain every actual Copper
   # publication through first-play, returned-title idle and next attract entry.
   segments=s.inspect('segments.list')['current']
   located={n:(int(h),int(o,16)) for n,h,o in re.findall(r'^([A-Za-z_][\w]*)\s+(\d\d):([0-9A-Fa-f]{8})\s*$',(exe.parent/'native.lst').read_text(),re.M)}
   h,offset=located['title_copper'];title_pointer=segments[h]['start']+offset
   regs=s.inspect('custom_dump')['regs']
   end_state=dict(life=6,demo=255,idle=0,started=num('simulation_started_updates',2),completed=num('simulation_updates',2),
                  first_play=None,returned=None,title_published=False,next_demo=None,next_seed=False,maximum_loops=0,
                  pointer=bytearray(((regs['COP1LCH']<<16)|regs['COP1LCL']).to_bytes(4,'big')))
   publications=[];tail_events=[];tail_checks=[]
   def event(message):
    if message.get('method')!='event.mmio':return
    row=message['params'];addr=row['addr'];value=row['value'];size=row['size'];position=row['position']
    assert not row.get('dropped_events',0) and not row.get('dropped_notifications',0),'Demo-end telemetry dropped'
    if addr==base+symbols['simulation_started_updates']:end_state['started']=value
    if addr==base+symbols['simulation_updates']:
     end_state['completed']=value
     if end_state['returned'] and value-end_state['returned']['callback'] in (4,600,1200,1790):
      s.send_async('capture.screenshot',{'path':str(directory/f'title-idle-{value-end_state["returned"]["callback"]}.png')})
    if addr==base+symbols['ui_idle']:end_state['idle']=value
    if addr==base+symbols['game_celebration_loops']:end_state['maximum_loops']=max(end_state['maximum_loops'],value)
    if addr==base+symbols['game_celebration_first_play'] and value:
     end_state['first_play']=dict(callback=end_state['started'],position=position)
    if addr==base+symbols['game_lifecycle']:
     end_state['life']=value
     if value==2 and end_state['returned'] is None:
      assert end_state['first_play'],'Unattended demo returned before actual full phrase completion'
      end_state['returned']=dict(callback=end_state['completed'],position=position)
    if addr==base+symbols['ui_demo']:
     end_state['demo']=value
     if value and end_state['returned']:
      assert end_state['idle']>=1800,'Next attract entered before bounded title idle'
      end_state['next_demo']=dict(callback=end_state['started'],position=position,idle=end_state['idle'])
    if addr==base+symbols['ui_entropy_state'] and value==recording['seed'] and end_state['next_demo']:end_state['next_seed']=True
    if 0xdff080<=addr and addr+size<=0xdff084:end_state['pointer'][addr-0xdff080:addr-0xdff080+size]=value.to_bytes(size,'big')
    if addr==0xdff088:
     pointer=int.from_bytes(end_state['pointer'],'big')
     assert end_state['started']==end_state['completed'],'Demo-end publication of incomplete callback'
     assert position['vpos']<25 or position['vpos']>=252,'Demo-end publication outside retained blank window'
     if end_state['returned'] and not end_state['next_demo']:
      assert pointer==title_pointer,{'label':'actual Copper returns to court during title idle','pointer':pointer,'title':title_pointer,'position':position}
      end_state['title_published']=True
     publications.append(dict(pointer=pointer,position=position,lifecycle=end_state['life'],demo=end_state['demo']))
    tail_events.append(row)
   watches=[{'addr':base+symbols[n],'len':length,'access':'write'} for n,length in
            [('game_lifecycle',2),('ui_demo',1),('ui_idle',2),('ui_entropy_state',2),('simulation_started_updates',2),('simulation_updates',2),('game_celebration_first_play',1),('game_celebration_loops',2)]]
   watches += [{'addr':0xdff080,'len':4,'access':'write'},{'addr':0xdff088,'len':2,'access':'write'}]
   s.notification_handler=event;s.inspect('events.subscribe',{'events':['mmio'],'mmio':watches})
   s.inspect('step',{'count':1});until({'seconds':time+54});s.inspect('events.unsubscribe');s.notification_handler=None
   check('demo automatically returned after actual first complete tune',bool(end_state['returned'] and end_state['first_play']),True)
   check('only one completed tune before automatic demo return',end_state['maximum_loops'],1)
   check('actual title bank published throughout bounded idle',end_state['title_published'],True)
   check('next demo starts without physical input',bool(end_state['next_demo'] and end_state['next_seed']),True)
   check('next demo is ordinary active attract',num('ui_demo'),255)
   check('next demo resets game totals',list(mem('game_games_a',2)),[0,0])
   check('next demo resets default selector EXIT',num('ui_demo_choice'),0)
   from native_identity_raster import assert_menu_selection_raster
   for offset in (4,600,1200,1790):assert_menu_selection_raster(directory/f'title-idle-{offset}.png',0,1)
   s.inspect('capture_screenshot',{'path':str(directory/'next-attract.png')})
   from native_identity_raster import assert_mode_raster,assert_footer_raster
   assert_mode_raster(directory/'next-attract.png',1)
   assert_footer_raster(directory/'next-attract.png',{0:'',2:'A WINS GAME',3:'B WINS GAME',4:'YOUR SERVE'}[num('ui_overlay_kind')],'DEMO - TAKE OVER / EXIT','EXIT')
   atomic_json(directory/'demo-end-publications.json',publications);atomic_json(directory/'demo-end-events.json',tail_events)
   end_state['pointer']=end_state['pointer'].hex();atomic_json(directory/'demo-end-state.json',end_state)
  deadlines=num('missed_presentation_deadlines',2)
 target_log(directory)
 report={'passed':True,'takeover':takeover,'verified_input_ticks':index,'checks':checks,'awards':awards,'observed_flight_side_changes':contacts,'missed_publications':deadlines,'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'native_modules':compiled_modules,'recording_sha256':hashlib.sha256(recording_path.read_bytes()).hexdigest(),'trajectory_fixture_sha256':fixture_manifest['payload_sha256'],'scope':'Local seeded native recording/replay equality, ordinary boot and physical input; no original-reference parity claim'}
 atomic_json(directory/'report.json',report);print(json.dumps({'passed':True,'takeover':takeover,'input_ticks':index,'flight_side_changes':contacts,'missed_publications':deadlines}))
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--takeover', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'build/tests' / ('demo-mid-takeover' if args.takeover else 'demo-full-repeat') / 'report.json'
    tracked_call([path], 'native-demo', 'maintained-native', 'ordinary title',
                 'scripts/run_demo_match_tests.py', None, lambda: run(args.takeover),
                 lambda path, report: [ROOT / 'build/amiga/interfaces/enhanced/baseline-rally'])
