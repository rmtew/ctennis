"""Finite CT13 native fixtures: initialise once, then actual dispatcher/input/scanout."""
import argparse, hashlib, json, re
from pathlib import Path
from build_native_game import build
from native_tools import ROOT, ASSEMBLER, run as assemble, emulator_config
from native_observation import code_symbols, target_log
from native_evidence import atomic_json, compile_manifest, tracked_call
from copperline_test_session import NativeControlSession
from ordinary_cadence import chip_memory
from PIL import Image

def run(winner, exchanged, mutant=False):
    _, ordinary=build(); config=emulator_config()
    label=f'ct13-{winner}-'+('exchanged' if exchanged else 'normal')+('-premature-completion' if mutant else '')
    directory=ROOT/'build/tests'/label;directory.mkdir(parents=True,exist_ok=True)
    blue=winner=='blue';games=(5,2) if blue else (2,5)
    points=(3,0) if blue else (0,3)
    outcome=0x82 ^ (0x40 if (not blue)^exchanged else 0)
    init='        moveq #1,d0\n        bsr game_new_match\n        bsr game_begin_active\n        move.b #$40,game_score_flags\n'
    for name,value in zip(('game_mode','game_point_a','game_point_b','game_games_a','game_games_b','game_contact'),
                          (0x80|(16 if exchanged else 0),*points,*games,outcome)):
        init+=f'        move.b #{value},{name}\n'
    source=(ROOT/'amiga/main.s').read_text().replace('        bsr     game_begin_title',init)
    if mutant:
        audio=(ROOT/'amiga/game/audio.s').read_text()
        audio=audio.replace('        tst.b   AV_DURATION(a0)\n        bne.s   .done\n','')
        path=directory/'premature-audio.s';path.write_text(audio)
        integration=(ROOT/'amiga/game/integration.s').read_text()
        marker='include "amiga/game/audio.s"'
        assert integration.count(marker)==1
        integration_path=directory/'premature-integration.s'
        integration_path.write_text(integration.replace(marker,f'include "{path}"'))
        source=source.replace('include "amiga/game/integration.s"',f'include "{integration_path}"')
    fixture=directory/'fixture.s';fixture.write_text(source)
    exe=directory/'native-fixture';listing=directory/'native.lst'
    assemble([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-DENHANCED_INTERFACE=1','-L',str(listing),'-o',str(exe),str(fixture)])
    compile_manifest(exe,listing);sym=code_symbols(listing.read_text());checks=[];rows=[];photos=[]
    notes=json.loads((ROOT/'assets/native/audio/battle-hymn/notes.json').read_text())['voices']
    previous_cursors=[0,0,0]
    def check(label,actual,expected):
        checks.append(dict(label=label,actual=actual,expected=expected))
        if actual!=expected:raise AssertionError(checks[-1])
    with NativeControlSession(directory) as s:
        s.inspect('session_launch',dict(binary=config['tools']['copperline'],run=str(exe),args=[
            '--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0',
            '--noaudio','--audio-wav',str(directory/'native.wav'),config['inputs']['amiga_rom']]))
        stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg',stop
        base=int(re.search(r'first hunk \$([0-9a-fA-F]+)',stop['detail'])[1],16)
        def mem(name,n=1):return bytes.fromhex(s.inspect('mem_read',dict(addr=base+sym[name],len=n))['data'])
        def num(name,n=1):return int.from_bytes(mem(name,n),'big')
        def raw(a,n):return bytes.fromhex(s.inspect('mem_read',dict(addr=a,len=n))['data'])
        for port in (1,2):
            s.inspect('input_set_port',dict(port=port,device='joystick'))
            s.inspect('input_joy',dict(port=port,red=True))
        pc=base+sym['simulation_update'];s.inspect('break_add',dict(kind='pc',addr=pc))
        award=None;first=None;last_loaded=False;frozen=None;pose_seen=set();loops=[];returned=None;paused=False
        previous_loop=0;initial_memory=None;early=False;early_release=False;pause_ticks=0
        for index in range(3500):
            stop=s.inspect('run_until',{'seconds':90});assert stop['pc']==pc,stop
            life=num('game_lifecycle',2);callback=num('simulation_updates',2)
            if life==6:
                if award is None:
                    award=callback;frozen=mem('game_point_a',2)+mem('game_games_a',2)
                    initial_memory=chip_memory(raw)
                    check('logical final totals',list(mem('game_games_a',2)),[6,2] if blue else [2,6])
                    check('logical winner',num('game_celebration_winner'),0 if blue else 1)
                elapsed=callback-award;voice=mem('game_audio_voices',96)
                gate=num('game_celebration_first_play');loop=num('game_celebration_loops',2)
                row=dict(callback=callback,elapsed=elapsed,seconds=stop['seconds'],gate=gate,loop=loop,
                         voices=voice.hex(),armed=num('game_celebration_armed'))
                rows.append(row)
                cursors=[voice[v*32+5] for v in range(3)]
                if cursors!=previous_cursors:
                    regs=s.inspect('custom_dump')['regs']
                    for v,channel in enumerate((0,1,3)):
                        if not cursors[v] or cursors[v]==previous_cursors[v]:continue
                        event_index=cursors[v]-1
                        if event_index>=len(notes[v]) or notes[v][event_index]['midi'] is None:continue
                        expected=notes[v][event_index]['paula_period_4byte_wave']
                        actual=int.from_bytes(voice[v*32+18:v*32+20],'big')
                        check('native score pitch matches independently authored note',actual,expected)
                        check('actual Paula period output matches note',regs[f'AUD{channel}PER'],expected)
                        check('actual Paula volume stays bounded',0<=regs[f'AUD{channel}VOL']<=64,True)
                    previous_cursors=cursors
                check('score frozen', (mem('game_point_a',2)+mem('game_games_a',2)).hex(),frozen.hex())
                if all(voice[v*32+6] for v in range(3)) and any(voice[v*32+12] for v in range(3)):
                    last_loaded=True
                    # Terminal rests last a complete beat. Loaded is not expired.
                    if first is None:check('last-loaded cannot unlock first play',gate,0)
                if elapsed==8:
                    for port in (1,2):s.inspect('input_joy',dict(port=port,red=False))
                if elapsed==16:
                    for port in (1,2):s.inspect('input_joy',dict(port=port,red=True))
                    early=True
                if elapsed==60:
                    photo=directory/'before-gate.png';s.inspect('capture_screenshot',{'path':str(photo)});photos.append(str(photo))
                if num('game_celebration_pose'):
                    obj=mem('game_scene_objects',64);upper=(not blue)^exchanged
                    wanted=3 if upper else 0;loser=0 if upper else 3
                    check('winner own half',num('game_celebration_upper'),255 if upper else 0)
                    check('winner remains visible',all(obj[(wanted+j)*8+5] for j in range(3)),True)
                    check('loser removed',all(obj[(loser+j)*8+5]==0 for j in range(3)),True)
                    check('ball/shadow removed',[obj[6*8+5],obj[7*8+5]],[0,0])
                    player=mem('game_play_state',20)[10 if upper else 0:20 if upper else 10]
                    check('own-half centred',player[3],120)
                    check('raised racket pose',player[4],11 if upper else 4)
                    check('own-half visual centre with small upward bounce',player[2] in ((50,51,52) if upper else (123,124,125)),True)
                    pose_seen.add(player[2])
                    if elapsed in (60,68,76):
                        photo=directory/f'bounce-{elapsed}.png';s.inspect('capture_screenshot',{'path':str(photo)})
                if gate and first is None:
                    first=callback;check('early input discarded and winning hold blocked',num('game_celebration_armed'),0)
                    check('gate waits full first duration',elapsed>=926,True)
                    check('last-loaded state observed before real completion',last_loaded,True)
                if loop!=previous_loop:
                    loops.append(row);previous_loop=loop
                # Pause after full play, verify native score/timers freeze and Paula silence.
                if first and not paused and callback-first==12:
                    s.inspect('input_key',dict(rawkey=0x19,action='press'))
                    for _ in range(12):
                        s.inspect('step',{'count':1});stop=s.inspect('run_until',{'pc':pc})
                        if num('ui_paused'):break
                    check('pause entered',num('ui_paused'),255)
                    pause_voice=mem('game_audio_voices',96);pause_loops=num('game_celebration_loops',2)
                    pause_callback=num('simulation_updates',2)
                    pause_clock=mem('game_audio_wait')+mem('game_celebration_audio_fraction')
                    s.inspect('input_key',dict(rawkey=0x19,action='release'))
                    for _ in range(8):s.inspect('step',{'count':1});s.inspect('run_until',{'pc':pc})
                    check('paused audio duration/envelope frozen',mem('game_audio_voices',96).hex(),pause_voice.hex())
                    check('paused fractional audio clock frozen',(mem('game_audio_wait')+mem('game_celebration_audio_fraction')).hex(),pause_clock.hex())
                    check('paused loop count frozen',num('game_celebration_loops',2),pause_loops)
                    regs=s.inspect('custom_dump')['regs'];check('pause mutes Paula',[regs[f'AUD{x}VOL'] for x in (0,1,3)],[0,0,0])
                    s.inspect('input_key',dict(rawkey=0x19,action='press'))
                    for _ in range(12):
                        s.inspect('step',{'count':1});s.inspect('run_until',{'pc':pc})
                        if not num('ui_paused'):break
                    check('pause resumed',num('ui_paused'),0);pause_ticks=num('simulation_updates',2)-pause_callback;s.inspect('input_key',dict(rawkey=0x19,action='release'));paused=True
                if loop>=2 and not early_release:
                    photo=directory/'ready-second-loop.png';s.inspect('capture_screenshot',{'path':str(photo)});photos.append(str(photo))
                    for port in (1,2):s.inspect('input_joy',dict(port=port,red=False))
                    release=callback;early_release=True
                if early_release and callback-release==8:
                    check('release arms continue',num('game_celebration_armed'),255)
                    for port in (1,2):s.inspect('input_joy',dict(port=port,red=True))
            elif award and life==2:
                returned=callback
                check('title clears final score',list(mem('game_point_a',2)+mem('game_games_a',2)),[0]*4)
                check('title clears celebration state',num('game_celebration_first_play')+num('game_celebration_loops',2),0)
                check('title audio muted',[mem('game_audio_voices',96)[v*32+15] for v in range(3)],[0]*3)
                # Held continue must not launch a game or repeatedly return to title.
                for _ in range(20):s.inspect('step',{'count':1});s.inspect('run_until',{'pc':pc});check('single title return under held fire',num('game_lifecycle',2),2)
                photo=directory/'returned-title.png';s.inspect('capture_screenshot',{'path':str(photo)});photos.append(str(photo))
                final_memory=chip_memory(raw);break
            s.inspect('step',{'count':1})
        else:raise AssertionError('Finite celebration completion not reached')
        check('two full cycles observed',len(loops)>=2,True)
        check('loop reload has no extra sequencer interval',loops[1]['callback']-loops[0]['callback']-pause_ticks,924)
        check('bounce visits at least three heights',len(pose_seen)>=3,True)
        check('early press and pause exercised',early and paused,True)
        check('first cycle includes complete score and queue startup',first-award,926)
        check('bounded chip RAM',initial_memory['used_chip_bytes']<524288 and final_memory['used_chip_bytes']<524288,True)
        check('no runtime allocation',final_memory['used_chip_bytes'],initial_memory['used_chip_bytes'])
        deadlines=num('missed_presentation_deadlines',2)
    # Inspect actual emitted audio, not host synthesis.
    from native_audio_checks import pcm16_window
    sound=pcm16_window(directory/'native.wav',rows[40]['seconds'],.2)
    check('native emitted Battle Hymn signal',any(x['nonzero_pcm16_samples'] for x in sound['channels']),True)
    # Exact footer pixels from the retained font, plus visible winner/absent loser.
    font=(ROOT/'assets/native/title/font.bin').read_bytes()
    text=('A WINS  ' if blue else 'B WINS  ')+('A 6 B 2' if blue else 'A 2 B 6')
    for ready,name in [(False,'before-gate.png'),(True,'ready-second-loop.png')]:
        with Image.open(directory/name) as picture:
            raster=picture.convert('RGB');check('PAL viewport',list(picture.size),[716,285])
            for y,line in [(208,text),(216,'PRESS FIRE TO CONTINUE' if ready else '')]:
                left=(32-len(line))//2
                line=' '*left+line+' '*(32-left-len(line))
                expected=[]
                for row in range(8):
                    for char in line:
                        byte=font[ord(char)*8+row]
                        for bit in range(7,-1,-1):
                            rgb=(255,255,255) if byte&(1<<bit) else (0,0,0)
                            expected.extend((rgb,rgb))
                actual=list(raster.crop((126,y,638,y+8)).get_flattened_data())
                check('exact native '+('continue' if y==216 else 'winner/totals')+' pixels',actual==expected,True)
            colours=raster.crop((300,40,470,208)).getcolors(40000)
            own=(85,85,238) if blue else (238,51,51);other=(238,51,51) if blue else (85,85,238)
            check('winner colour visible in actual court pixels',sum(n for n,c in colours if c==own)>0,True)
            check('loser colour absent in actual court pixels',sum(n for n,c in colours if c==other),0)
    # Real emulator loop breath, using the observed completion boundary.
    seam=pcm16_window(directory/'native.wav',loops[0]['seconds']-.15,.1)
    check('loop breath is digitally quiet',all(c['peak_pcm16']<=1 for c in seam['channels']),True)
    atomic_json(directory/'observations.json',rows)
    report=dict(passed=True,winner=winner,exchanged=exchanged,checks=checks,photos=photos,
                first_play_callback=first,award_callback=award,loop_boundaries=loops,title_callback=returned,
                memory=initial_memory,missed_publications=deadlines,emitted_audio=sound,
                executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
                scope='One-time native near-match fixture, actual dispatcher and physical inputs thereafter; emulator capture, no hardware/original-parity claim')
    atomic_json(directory/'report.json',report);target_log(directory)
    print(json.dumps({k:report[k] for k in ('passed','winner','exchanged','first_play_callback','award_callback','title_callback','missed_publications')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--winner',choices=('blue','red'),required=True);p.add_argument('--exchanged',action='store_true');p.add_argument('--self-test',action='store_true');a=p.parse_args()
    def execute():
        run(a.winner,a.exchanged)
        if a.self_test:
            try:run(a.winner,a.exchanged,True)
            except AssertionError as e:
                if not any(label in str(e) for label in ('last-loaded cannot unlock first play','gate waits full first duration')):raise
                fault_directory=directory.with_name(directory.name+'-premature-completion')
                atomic_json(fault_directory/'report.json',dict(passed=False,expected_rejection=True,failure=str(e),
                    executable_sha256=hashlib.sha256((fault_directory/'native-fixture').read_bytes()).hexdigest()))
                report=json.loads((directory/'report.json').read_text())
                report['premature_completion_control']={'rejected':True,'failure':str(e)}
                atomic_json(directory/'report.json',report)
                print('Premature-completion mutant rejected:',e)
            else:raise AssertionError('Premature completion mutant accepted')
    directory=ROOT/'build/tests'/('ct13-'+a.winner+'-'+('exchanged' if a.exchanged else 'normal'))
    tracked_call([directory/'report.json'],'native-celebration','maintained-native','one-time near-match fixture',
                 'scripts/run_celebration_tests.py',None,execute,lambda path,report:[directory/'native-fixture'])
