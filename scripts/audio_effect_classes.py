"""Finite CT08 effect inventory and actual-register/output comparison.

Reuses the retained CT06 window and independent original WAV/PSG capture.
An interval may contain several repeated requests; this is class coverage, not
18 independent waveform equivalence claims or uninterrupted ordinary play.
"""
import json
from fractions import Fraction
from pathlib import Path
from audio_mute import pcm16_window
from maintained_state_contract import MAINTAINED_SCRATCH_OFFSETS

CLIPS = {0x1f04:0,0x1f52:1,0x1f96:2,0x1fb7:3,0x1fdc:4,0x1ff2:5}
CLASSES = ['intro-a','intro-b','result-a','result-b','ready-cue','strike']


def inventory(root, load_source):
    rows = []
    for name in ('one-player-match','two-player-match'):
        source, directory, _ = load_source({'reference':'tests/reference/audio/manifest.json','source_case':name})
        parent=json.loads((root/f'tests/reference/{name}.json').read_text())
        for interval, retained in source['intervals'].items():
            clips=set();rates=set()
            for event in retained['timed_writes']:
                ordinal=event.get('callback',0)
                if not event.get('retained_parent_event') or not 0<ordinal<=len(parent['updates']):continue
                ram=bytes.fromhex(parent['updates'][ordinal-1]['post_tail_ram'])
                rates.add(ram[0x82])
                for tone in range(3):
                    if event['tones_after'][tone]['attenuation']==15:continue
                    pointer=int.from_bytes(ram[0x85+14*tone:0x87+14*tone],'little')
                    if pointer not in CLIPS:raise ValueError('Audible original queue outside finite native clip inventory')
                    clips.add(CLIPS[pointer])
            rows.append({'source_case':name,'interval':interval,'trigger_callback':retained['trigger_callback'],
                         'classes':[CLASSES[n] for n in sorted(clips)] or ['silence'],
                         'source_cadences':sorted(rates),'original_wav':str(directory/retained['wav'])})
    if len(rows)!=18:raise ValueError('Original interval inventory changed')
    return rows


def compare_window(captured, parent, source, source_directory, first_update, last_update, measured_levels):
    differences=[];raw=[];checks=[];seen=set();wave_checks=[]
    expected_updates=list(range(first_update+1,last_update+1))
    states=captured['state_events'];ticks=captured['audio_ticks']
    if [r['update'] for r in states]!=expected_updates or [r['update'] for r in ticks]!=expected_updates:
        raise ValueError('Audio class window lacks consecutive state/service observations')
    by_tick={r['update']:r for r in ticks}
    for state,tick in zip(states,ticks):
        ordinal=state['update'];wanted=bytes.fromhex(parent['updates'][ordinal-1]['post_tail_ram'])
        actual=bytes.fromhex(state['post_tail_ram'])
        ds=[{'update':ordinal,'offset':n,'expected':wanted[n],'actual':actual[n]} for n in range(2,256) if wanted[n]!=actual[n]]
        raw.extend(ds);differences.extend(d for d in ds if d['offset'] not in MAINTAINED_SCRATCH_OFFSETS)
        due=bytes.fromhex(parent['updates'][ordinal-1]['entry_ram'])[0x83]==1
        for field,expected,actual in [('due',due,bool(tick['due'])),('wait',wanted[0x83],tick['wait']),('rate',wanted[0x82],tick['rate'])]:
            if expected!=actual:differences.append({'update':ordinal,'field':'native audio '+field,'expected':expected,'actual':actual})
    retained_count=len(json.loads((source_directory.parent.parent/f"{source['source_case']}.json").read_text())['updates'])
    events={}
    for event in source['timed_events']:
        if event.get('retained_parent_event') and event.get('context')=='callback':events.setdefault(event.get('callback'),[]).append(event)
    silence_seen=False
    for native in captured['audio_events']:
        ordinal=native['update'];original=events.get(ordinal,[])
        # The supplemental independently captured restart fixture continues
        # beyond the original audio recording; strict PSG/state checks still run.
        if ordinal>retained_count:continue
        if [e['value'] for e in original]!=list(bytes.fromhex(native['psg'])):raise ValueError('Original audio association changed')
        voices=bytes.fromhex(by_tick[ordinal]['voices'])
        original_state=original[-1]
        audible=False
        for tone,channel in enumerate((0,1,3)):
            state=original_state['tones_after'][tone]
            volume=measured_levels[state['attenuation']]
            actual_volume=native['registers'][f'AUD{channel}VOL']
            period=max(123,round(Fraction(3546895*8*state['divisor'],source['clock_hz'])))
            actual_period=native['registers'][f'AUD{channel}PER']
            checks.append({'update':ordinal,'tone':tone,'expected_volume':volume,'actual_volume':actual_volume,
                           'expected_period':period if volume else None,'actual_period':actual_period})
            if volume!=actual_volume:differences.append({'update':ordinal,'field':f'AUD{channel}VOL','expected':volume,'actual':actual_volume})
            if volume and period!=actual_period:differences.append({'update':ordinal,'field':f'AUD{channel}PER','expected':period,'actual':actual_period})
            clip=voices[32*tone+4]
            if volume and clip<6 and clip not in seen:
                source_time=original_state['time_attoseconds']/1e18
                expected=pcm16_window(source_directory/'a/source.wav',source_time+.002,.005)
                actual=pcm16_window(Path(captured['native_wav']),native['stop']['seconds']+.002,.005)
                original_signal=any(r['nonzero_pcm16_samples'] for r in expected['channels'])
                native_signal=any(r['nonzero_pcm16_samples'] for r in actual['channels'])
                if not original_signal:raise ValueError('Original class representative is inaudible')
                wave_checks.append({'class':CLASSES[clip],'update':ordinal,'expected_signal':True,'actual_signal':native_signal,
                                    'source':expected,'native':actual})
                if not native_signal:differences.append({'update':ordinal,'field':CLASSES[clip]+' emitted signal','expected':True,'actual':False})
                seen.add(clip)
            audible|=bool(volume)
        if not audible and not silence_seen and ordinal>12089:
            source_time=original_state['time_attoseconds']/1e18
            expected=pcm16_window(source_directory/'a/source.wav',source_time+.01,.02)
            actual=pcm16_window(Path(captured['native_wav']),native['stop']['seconds']+.01,.02)
            original_signal=any(r['nonzero_pcm16_samples'] for r in expected['channels'])
            native_signal=any(r['nonzero_pcm16_samples'] for r in actual['channels'])
            # Only claim a quiet representative established by original output.
            if not original_signal:
                wave_checks.append({'class':'silence','update':ordinal,'expected_signal':False,'actual_signal':native_signal,
                                    'source':expected,'native':actual})
                if native_signal:differences.append({'update':ordinal,'field':'emitted silence','expected':False,'actual':True})
                silence_seen=True
        if original_state['noise_audible_after']:raise ValueError('Active noise outside CT08 inventory')
    if not silence_seen:differences.append({'field':'emitted silence representative missing'})
    if seen!=set(range(6)):differences.append({'field':'finite audible classes','expected':CLASSES,'actual':[CLASSES[n] for n in sorted(seen)]})
    return {'first_difference':differences[0] if differences else None,'differences':differences,
            'raw_state_differences':raw,'checks':checks,'emitted_classes':wave_checks,
            'observed_callbacks':len(states),'due_callbacks':sum(bool(t['due']) for t in ticks),
            'two_tick_countdowns':sum(t['wait']==2 for t in ticks),'classes': [CLASSES[n] for n in sorted(seen)]}
