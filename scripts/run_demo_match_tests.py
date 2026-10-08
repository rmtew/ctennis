"""Check the frozen native match recording and physical-input takeover."""
from native_tools import emulator_config
import argparse,hashlib,json,re
from build_native_game import build
from native_observation import code_symbols
from copperline_test_session import NativeControlSession
from native_metrics_observation import MetricsObserver
from native_evidence import ROOT,atomic_json,tracked_call
from native_observation import target_log
from native_assets import demo_entropy_policy

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

def run(takeover=False, takeover_tail=False):
 config,exe=build(flavor='enhanced'); config = emulator_config();compiled_modules=json.loads((exe.parent/'build-report.json').read_text())['native_modules'];symbols=code_symbols((exe.parent/'native.lst').read_text())
 recording_path=ROOT/'assets/interface/demo-inputs.json'
 recording=json.loads(recording_path.read_text());expected,fixture_manifest=load_trajectory(recording_path)
 assert recording['schema']==2 and len(expected)==recording['frames']
 assert recording['entropy_version']=='galois16-b400-v1' and 0<recording['seed']<65536 and recording['initial_game_random']==0
 compatibility=json.loads((ROOT/'assets/interface/demo-entropy-compat.json').read_text())
 assert demo_entropy_policy(recording_path.read_bytes(),compatibility)==1
 directory=ROOT/('build/tests/demo-tail-takeover' if takeover_tail else 'build/tests/demo-mid-takeover' if takeover else 'build/tests/demo-full-repeat');checks=[];awards=[];seen_games=[0,0];index=0;contacts=0;previous_side=None
 if not takeover:
  atomic_json(directory/'demo-end-state.json',{'state':'incomplete','passed':False})
  atomic_json(directory/'demo-end-events.json',[]);atomic_json(directory/'demo-end-publications.json',[])
 def check(label,actual,expected_value):
  checks.append({'label':label,'actual':actual,'expected':expected_value})
  if actual!=expected_value:raise AssertionError(checks[-1])
 with NativeControlSession(directory) as s:
  s.inspect('session_launch',{'binary':config['tools']['copperline'],'run':str(exe),'args':['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',config['inputs']['amiga_rom']]})
  stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg',stop
  base=int(re.search(r'first hunk \$([0-9a-fA-F]+)',stop['detail'])[1],16);time=stop['seconds']
  metrics=MetricsObserver(base,symbols,(exe.parent/'native.lst').read_text())
  s.notification_handler=metrics.observe
  s.inspect('events.subscribe',{'events':['mmio','frame'],'mmio':metrics.watches()})
  def until(args):
   nonlocal time
   stop=s.inspect('run_until',args);time=stop['seconds'];return stop
  def mem(n,k=1):return bytes.fromhex(s.inspect('mem_read',{'addr':base+symbols[n],'len':k})['data'])
  def num(n,k=1):return int.from_bytes(mem(n,k),'big')
  def frozen():return mem('game_play_state',60)+mem('game_score_state',28)+mem('game_audio_voices',96)+mem('game_audio_wait')+mem('game_action_clock')+mem('game_status_clock')+mem('game_aux_clock')+mem('ui_entropy_state',2)+mem('game_entropy_state',2)+mem('game_match_seed',2)
  until({'pc':base+symbols['ui_seed_entropy']});check('ordinary title idle starts seeded demo',num('ui_demo'),255)
  # Observe both completed writes at their actual return boundary.
  until({'pc':base+symbols['game_core_seed_entropy_done']});check('actual initialized seed matches metadata',num('ui_entropy_state',2),recording['seed'])
  check('modern shadow starts from same match seed',num('game_entropy_state',2),recording['seed'])
  check('historical playback policy is explicit',num('game_entropy_policy'),1)
  def take_over(tail=False):
   check('takeover begins in historical policy',num('game_entropy_policy'),1)
   check('takeover begins with automatic playback',num('game_auto_continue')!=0,True)
   s.inspect('input_key',{'rawkey':0x4f,'action':'press'})
   for attempt in range(12):
    until({'pc':base+symbols['ui_sample']});until({'pc':base+symbols['ui_input_draw']})
    if num('ui_demo_choice')==1:break
   check('left selects takeover',num('ui_demo_choice'),1)
   s.inspect('input_key',{'rawkey':0x44,'action':'press'})
   for attempt in range(12):
    until({'pc':base+symbols['ui_sample']});before=frozen();confirmation_phase=num('game_lifecycle',2)
    until({'pc':base+symbols['ui_input_draw']})
    if not num('ui_demo'):
     check('mid-match takeover preserves world score audio clocks entropy',frozen().hex(),before.hex());break
   else:raise AssertionError('Mid-match selected Enter never took over')
   if tail:
    check('takeover confirmation is in a natural round tail',confirmation_phase in (4,5),True)
    until({'pc':base+symbols['simulation_menu']})
    check('tail metadata changes only playback policy and controls',frozen().hex(),before.hex())
    check('tail takeover switches policy before the tail dispatch',num('game_entropy_policy'),0)
    check('tail takeover ends automatic playback before the tail dispatch',num('game_auto_continue'),0)
    s.inspect('input_key',{'rawkey':0x44,'action':'release'})
    s.inspect('input_key',{'rawkey':0x4f,'action':'release'})
    play_break=s.inspect('break_add',{'kind':'pc','addr':base+symbols['native_input_done']})
    stopped=until({'seconds':time+5})
    s.inspect('break_remove',{'id':play_break['id']})
    check('actual round tail reaches playing within bound',stopped['pc'],base+symbols['native_input_done'])
    check('playing assignment follows tail takeover',num('game_lifecycle',2),1)
   else:
    until({'pc':base+symbols['native_input_done']})
   check('takeover held direction and confirmation consumed',num('game_input_bits',2),0)
   check('takeover switches to corrected entropy policy',num('game_entropy_policy'),0)
   from native_player_roles import assert_player_roles
   roles=assert_player_roles(mem,num)
   check('takeover preserves A human/B robot', {row['owner']:row['role'] for row in roles}, {'A':'human','B':'robot'})
   if tail:
    for port in (1,2):
     s.inspect('input_set_port',{'port':port,'device':'joystick'})
     s.inspect('input_joy',{'port':port,'red':True})
   before=mem('game_play_state',60)
   # The modern shadow has advanced from the original seed throughout playback.
   # Live takeover consumes that stream; it never seeds from CIA or the zeroed
   # historical observer word. Observe an actual call, not an assumed cadence.
   entropy_pc=base+symbols['native_entropy_bit']
   entropy_break=s.inspect('break_add',{'kind':'pc','addr':entropy_pc})
   stop=until({'seconds':time+10})
   s.inspect('break_remove',{'id':entropy_break['id']})
   atomic_json(directory/'takeover-observation.json',{'confirmation_lifecycle':confirmation_phase,
    'verified_input_ticks':index,'seconds':time,'stop_pc':stop['pc'],'expected_entropy_pc':entropy_pc,
    'canonical_state':mem('game_core_state',symbols['game_core_state_end']-symbols['game_core_state']).hex(),
    'fields':{name:num(name,size) for name,size in [('game_lifecycle',2),('game_mode',1),
      ('game_auto_continue',1),('game_entropy_policy',1),('game_match_seed',2),('game_entropy_state',2),
      ('ui_entropy_state',2),('game_input_bits',2),('game_player_controls',2),('game_actions',1),
      ('game_serve_clock',1),('game_lower_phase',1),('game_upper_phase',1),('game_score_flags',1)]},
    'checks':checks})
   check('live takeover reaches shared entropy routine within bound',stop['pc'],entropy_pc)
   state=mem('game_entropy_state',2)
   check('live takeover shadow stream remains nonzero',int.from_bytes(state,'big')!=0,True)
   s.inspect('step',{'count':1})
   until({'pc':base+symbols['native_input_done']})
   check('live takeover consumes preserved modern shadow state',mem('game_entropy_state',2)!=state,True)
   check('AI remains assigned after takeover',num('game_score_flags')&3,2 if num('game_mode')&16 else 1)
   check('ordinary world continues after takeover',mem('game_play_state',60)!=before,True)
   s.inspect('input_key',{'rawkey':0x44,'action':'release'})
   s.inspect('input_key',{'rawkey':0x4f,'action':'release'})
   s.inspect('capture_screenshot',{'path':str(directory/'taken-over.png')})
   return confirmation_phase
  takeover_confirmation_lifecycle=None
  for callback in range(30000):
   until({'pc':base+symbols['game_tick_dispatch']});life=num('game_lifecycle',2)
   if life in (6,7,8):break
   if life==1:
    from native_player_roles import assert_player_roles
    roles=assert_player_roles(mem,num)
    check('demo records human A against AI B', {row['owner']:row['role'] for row in roles}, {'A':'human','B':'robot'})
   if takeover_tail and life in (4,5):
    takeover_confirmation_lifecycle=take_over(tail=True);break
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
   if takeover and not takeover_tail and index==len(expected)//2:
    takeover_confirmation_lifecycle=take_over();index+=1;break
   if not takeover and index in (100,200,300,400):
    s.inspect('input_key',{'rawkey':(0x4f,0x4e,0x4c,0x4d)[index//100-1],'action':'press'})
   if not takeover and index in (150,250,350,450):
    s.inspect('input_key',{'rawkey':(0x4f,0x4e,0x4c,0x4d)[(index-50)//100-1],'action':'release'})
   index+=1;s.inspect('step',{'count':1})
  else:raise AssertionError('Full playback did not end within finite bound')
  if takeover:
   check('requested physical takeover occurred',takeover_confirmation_lifecycle is not None,True)
  if not takeover:
   check('all recorded input ticks reproduce native trajectory',index,len(expected))
   check('complete match award reproduced',list(mem('game_games_a',2)),recording['final_games'])
   check('normal match result lifecycle',life,6)
   s.inspect('capture_screenshot',{'path':str(directory/'complete-match.png')})
   from native_scoreboard_raster import assert_scoreboard_raster
   scoreboard=assert_scoreboard_raster(directory/'complete-match.png',list(mem('prepared_field_values',2)),recording['final_games'])
   check('completed match preserves all six authored WIN rows',all(row['matched'] for row in scoreboard),True)
  if not takeover:
   # After the independently frozen full match, retain every actual Copper
   # publication through first-play, returned-title idle and next attract entry.
   segments=s.inspect('segments.list')['current']
   located={n:(int(h),int(o,16)) for n,h,o in re.findall(r'^([A-Za-z_][\w]*)\s+(\d\d):([0-9A-Fa-f]{8})\s*$',(exe.parent/'native.lst').read_text(),re.M)}
   h,offset=located['title_copper'];title_pointer=segments[h]['start']+offset
   regs=s.inspect('custom_dump')['regs']
   end_state=dict(life=6,demo=255,idle=0,started=num('simulation_started_updates',2),completed=num('simulation_updates',2),ready_generation=num('ready_generation',2),ready=num('ready_generation',2) if num('display_ready') else None,
                  first_play=None,returned=None,title_published=False,title_ready=None,title_display=False,
                  first_title_publication=None,first_complete_title_capture=None,next_demo=None,next_seed=False,maximum_loops=0,
                  pointer=bytearray(((regs['COP1LCH']<<16)|regs['COP1LCL']).to_bytes(4,'big')))
   publications=[];tail_events=[];tail_checks=[]
   def event(message):
    capture=end_state['first_complete_title_capture']
    if capture and message.get('id')==capture['request_id']:
     assert 'error' not in message,message
     capture['reply']=message
     return
    if message.get('method')=='event.frame':
     row=message['params'];assert not row.get('dropped_notifications',0)
     publication=end_state['first_title_publication']
     if publication and not capture and row['position']['frame']>=publication['position']['frame']+2:
      assert row['position']['frame']==publication['position']['frame']+2,'First complete title frame telemetry missing'
      identifier=s.send_async('capture.screenshot',{'path':str(directory/'title-first-complete.png')})
      end_state['first_complete_title_capture']=dict(request_id=identifier,request_position=row['position'],publication=publication)
     return
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
      end_state['returned']=dict(callback=end_state['completed'],started=end_state['started'],position=position)
    if addr==base+symbols['game_title_display']:end_state['title_display']=bool(value)
    if addr==base+symbols['ready_completed'] and value and end_state['returned'] and end_state['title_display'] and end_state['title_ready'] is None:
     end_state['title_ready']=dict(started=end_state['started'],position=position)
    if addr==base+symbols['ready_generation']:end_state['ready_generation']=value
    if addr==base+symbols['display_ready']:end_state['ready']=end_state['ready_generation'] if value else None
    if addr==base+symbols['ui_demo']:
     end_state['demo']=value
     if value and end_state['returned']:
      assert end_state['idle']>=1800,'Next attract entered before bounded title idle'
      end_state['next_demo']=dict(callback=end_state['started'],position=position,idle=end_state['idle'])
    if addr==base+symbols['ui_entropy_state'] and value==recording['seed'] and end_state['next_demo']:end_state['next_seed']=True
    if 0xdff080<=addr and addr+size<=0xdff084:end_state['pointer'][addr-0xdff080:addr-0xdff080+size]=value.to_bytes(size,'big')
    if addr==0xdff088:
     pointer=int.from_bytes(end_state['pointer'],'big')
     assert end_state['ready'] is not None and end_state['ready']<=end_state['completed'],'Demo-end publication of incomplete ready scene'
     assert position['vpos']>=253,'Demo-end publication outside retained blank window'
     if end_state['returned'] and not end_state['next_demo']:
      assert pointer==title_pointer,{'label':'actual Copper returns to court during title idle','pointer':pointer,'title':title_pointer,'position':position}
      if end_state['first_title_publication'] is None:
       ready=end_state['title_ready'];assert ready,'Title published before complete construction'
       assert ready['started']==(end_state['returned']['started']+1)&65535,'Title construction did not finish next callback'
       assert 0<=position['cck']-ready['position']['cck']<=313*227,'Title publication exceeded one physical PAL field'
       end_state['first_title_publication']=dict(position=position,started=end_state['started'])
      end_state['title_published']=True
     publications.append(dict(pointer=pointer,position=position,lifecycle=end_state['life'],demo=end_state['demo']))
    tail_events.append(row)
   watches=[{'addr':base+symbols[n],'len':length,'access':'write'} for n,length in
            [('game_lifecycle',2),('ui_demo',1),('ui_idle',2),('ui_entropy_state',2),('simulation_started_updates',2),('simulation_updates',2),('ready_generation',2),('ready_completed',1),('game_title_display',1),('display_ready',1),('game_celebration_first_play',1),('game_celebration_loops',2)]]
   watches += [{'addr':0xdff080,'len':4,'access':'write'},{'addr':0xdff088,'len':2,'access':'write'}]
   s.notification_handler=event;s.inspect('events.subscribe',{'events':['mmio','frame'],'frame_interval':1,'mmio':watches})
   try:
    s.inspect('step',{'count':1});until({'seconds':time+54});s.inspect('events.unsubscribe');s.inspect('status');s.notification_handler=None
   finally:
    atomic_json(directory/'demo-end-publications.json',publications);atomic_json(directory/'demo-end-events.json',tail_events)
    atomic_json(directory/'demo-end-state.json',dict(end_state,pointer=end_state['pointer'].hex()))
   check('demo automatically returned after actual first complete tune',bool(end_state['returned'] and end_state['first_play']),True)
   check('only one completed tune before automatic demo return',end_state['maximum_loops'],1)
   check('actual title bank published throughout bounded idle',end_state['title_published'],True)
   check('next demo starts without physical input',bool(end_state['next_demo'] and end_state['next_seed']),True)
   check('next demo is ordinary active attract',num('ui_demo'),255)
   check('next demo resets game totals',list(mem('game_games_a',2)),[0,0])
   check('next demo resets default selector EXIT',num('ui_demo_choice'),0)
   # Preserve the actual publication timeline even if a subsequent pixel
   # assertion fails. Failed evidence must remain diagnostically useful.
   atomic_json(directory/'demo-end-publications.json',publications);atomic_json(directory/'demo-end-events.json',tail_events)
   end_state['pointer']=end_state['pointer'].hex();atomic_json(directory/'demo-end-state.json',end_state)
   from native_identity_raster import assert_menu_selection_raster
   assert end_state['first_complete_title_capture'] and 'reply' in end_state['first_complete_title_capture']
   assert_menu_selection_raster(directory/'title-first-complete.png',0,1)
   # Four logical callbacks can precede the first complete physical title scan.
   # Retain that screenshot diagnostically; publication+2 owns acceptance.
   try:assert_menu_selection_raster(directory/'title-idle-4.png',0,1);end_state['callback4_title_pixels']=True
   except AssertionError:end_state['callback4_title_pixels']=False
   for offset in (600,1200,1790):assert_menu_selection_raster(directory/f'title-idle-{offset}.png',0,1)
   atomic_json(directory/'demo-end-state.json',end_state)
   s.inspect('capture_screenshot',{'path':str(directory/'next-attract.png')})
   from native_identity_raster import assert_mode_raster,assert_footer_raster
   assert_mode_raster(directory/'next-attract.png',1)
   assert_footer_raster(directory/'next-attract.png',{0:'',2:'A WINS GAME',3:'B WINS GAME',4:'YOUR SERVE'}[num('ui_overlay_kind')],'DEMO - TAKE OVER / EXIT','EXIT')
  deadlines=num('missed_presentation_deadlines',2)
 target_log(directory)
 report={'resource_metrics':metrics.result(),'passed':True,'takeover':takeover,'takeover_tail':takeover_tail,'takeover_confirmation_lifecycle':takeover_confirmation_lifecycle,'verified_input_ticks':index,'checks':checks,'awards':awards,'observed_flight_side_changes':contacts,'missed_publications':deadlines,'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'native_modules':compiled_modules,'recording_sha256':hashlib.sha256(recording_path.read_bytes()).hexdigest(),'trajectory_fixture_sha256':fixture_manifest['payload_sha256'],'scope':'Local seeded native recording/replay equality, ordinary boot and physical input; no original-reference parity claim'}
 atomic_json(directory/'report.json',report);print(json.dumps({'passed':True,'takeover':takeover,'input_ticks':index,'flight_side_changes':contacts,'missed_publications':deadlines}))
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    cases=parser.add_mutually_exclusive_group()
    cases.add_argument('--takeover', action='store_true')
    cases.add_argument('--takeover-tail', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'build/tests' / ('demo-tail-takeover' if args.takeover_tail else 'demo-mid-takeover' if args.takeover else 'demo-full-repeat') / 'report.json'
    tracked_call([path], 'native-demo', 'maintained-native', 'ordinary title',
                 'scripts/run_demo_match_tests.py', None, lambda: run(args.takeover or args.takeover_tail,args.takeover_tail),
                 lambda path, report: [ROOT / 'build/amiga/interfaces/enhanced/baseline-rally'])
