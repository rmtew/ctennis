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
   if life==1:
    from native_player_roles import assert_player_roles
    roles=assert_player_roles(mem,num)
    check('demo records human A against AI B', {row['owner']:row['role'] for row in roles}, {'A':'human','B':'robot'})
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
    s.inspect('input_key',{'rawkey':0x24,'action':'press'})
    for attempt in range(12):
     until({'pc':base+symbols['ui_sample']});before=frozen()
     until({'pc':base+symbols['ui_input_draw']})
     if not num('ui_demo'):
      check('mid-match takeover preserves world score audio clocks entropy',frozen().hex(),before.hex());break
    else:raise AssertionError('Mid-match G never took over')
    until({'pc':base+symbols['native_input_done']});check('takeover action consumed',num('game_player_controls')&32,0)
    roles=assert_player_roles(mem,num)
    check('takeover preserves A human/B robot', {row['owner']:row['role'] for row in roles}, {'A':'human','B':'robot'})
    state=mem('ui_entropy_state',2);before=mem('game_play_state',60)
    until({'seconds':time+1});check('live entropy stops advancing demo generator',mem('ui_entropy_state',2).hex(),state.hex())
    check('AI remains assigned after takeover',num('game_score_flags')&3,2 if num('game_mode')&16 else 1)
    check('ordinary world continues after takeover',mem('game_play_state',60)!=before,True)
    s.inspect('input_key',{'rawkey':0x24,'action':'release'})
    s.inspect('capture_screenshot',{'path':str(directory/'taken-over.png')});index+=1;break
   index+=1;s.inspect('step',{'count':1})
  else:raise AssertionError('Full playback did not end within finite bound')
  if not takeover:
   check('all recorded input ticks reproduce native trajectory',index,len(expected))
   check('complete match award reproduced',list(mem('game_games_a',2)),recording['final_games'])
   check('normal match result lifecycle',life,6)
   s.inspect('capture_screenshot',{'path':str(directory/'complete-match.png')})
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
