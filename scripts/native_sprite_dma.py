"""Check actual chip-bus sprite fetches against frozen native scene bytes.

This is a bus consumer, not a renderer or gameplay oracle. Memory starts from
Copperline's aligned snapshot and evolves only through recorded CPU writes.
"""
import hashlib
import json
import struct
from pathlib import Path

SLOT = struct.Struct('<HBBBBHIQI')


def analyse(path, addresses, standard='PAL', *, require_three=True, live_samples=None, cpu_events=None):
    if cpu_events is None:
        raise ValueError('Authoritative CPU MMIO events are required; raw slot data is not a RAM oracle')
    path = Path(path)
    memory = bytearray((path/'chip-ram.bin').read_bytes())
    copper_names = ['copperlist', 'copperlist_back', 'copperlist_third']
    sprite_names = ['sprite0', 'sprite_back', 'sprite_third']
    copper = [addresses[n] for n in copper_names]
    sprites = [addresses[n] for n in sprite_names]
    copper_size = addresses['copperlist_end']-addresses['copperlist']
    header_line = 25 if standard == 'PAL' else 20
    failures = []
    reported_word_disagreements = []
    live = {s['position']['frame']+1:s for s in (live_samples or [])}
    if len(live)!=len(live_samples or []):
        raise ValueError('Duplicate live sample field')
    checked_live_samples = 0
    encountered_live = set()
    def fail(reason, **details):
        # Preserve each distinct mechanism even when an early fault repeats.
        if sum(f['reason']==reason for f in failures) < 3:
            failures.append(dict(reason=reason, **details))
    def scalar(name, size=4):
        start = addresses[name]
        return int.from_bytes(memory[start:start+size], 'big')
    def index(pointer):
        return copper.index(pointer) if pointer in copper else None
    def snapshot(bank, generation):
        start = sprites[bank]
        return {'bank': bank, 'generation': generation,
                'title':bool(scalar('ready_title_display',1)),
                'data': bytes(memory[start:start+576])}
    initial = index(scalar('front_copper'))
    hardware = scalar('presentation_copper')
    current = snapshot(initial, 'inherited') if initial is not None and hardware in copper else None
    frozen = {}
    event_frames = {}
    events_by_byte = {}
    for event in cpu_events:
        if event.get('dropped_events',0) or event.get('dropped_notifications',0):
            raise ValueError('CPU MMIO telemetry was dropped')
        p=event['position']; f=p['frame']+1
        event_frames.setdefault(f,[]).append(event)
        for a in range(event['addr'],event['addr']+event['size']):
            events_by_byte.setdefault((f,a),[]).append(event)
    metadata_sizes={'front_copper':4,'back_copper':4,'ready_copper':4,'spare_copper':4,
        'display_ready':1,'ready_completed':1,'blank_seen':1,'ready_generation':2,'ready_title_display':1,'simulation_updates':2,
        'simulation_started_updates':2,'presentation_copper':4}
    watched=[(addresses[n],size) for n,size in metadata_sizes.items()] + [(a,copper_size) for a in copper] + [(a,576) for a in sprites]
    last_cpu_cop=None
    pointer_words = [0]*16
    last_pair = [None]*8
    pending = None
    last_sample = None
    beam_high = None
    beam_low = None
    cpu_pair = []
    full_frames = headers = pixels = terminators = 0
    publications = []
    generations = set()
    banks_seen = set()
    channels_seen = set()
    geometries = set()
    maximum_cpu_handover = 0
    pointer_completion = []
    last_frame = None
    strobe_fields = set()
    for line in (path/'profile.jsonl').read_text().splitlines():
        frame = json.loads(line)
        if 'slots_file' not in frame or not frame.get('traced'):
            fail('missing full slot telemetry', frame=frame.get('frame'))
            continue
        number, stride = frame['frame'], frame['line_cck']
        if last_frame is not None and number != last_frame+1:
            fail('nonconsecutive traced fields', previous=last_frame, frame=number)
        last_frame = number
        geometries.add((frame['rows'], stride))
        slot_bytes=(path/frame['slots_file']).read_bytes()
        field_events=sorted(event_frames.get(number,[]),key=lambda e:(e['position']['vpos'],e['position']['hpos']))
        event_cursor=0
        if len(slot_bytes)!=frame['rows']*stride*SLOT.size:
            fail('truncated or oversized slot field', frame=number, bytes=len(slot_bytes))
            continue
        if pending:
            fail('sprite pointer installation crossed automatic field restart', publication=pending)
            pending = None
        partial = frame['partial']
        if not partial:
            full_frames += 1
        reads = [dict(header=[], data=[], terminator=[]) for _ in range(8)]
        expected_field = current
        field_hardware = hardware
        if not partial and number in live:
            encountered_live.add(number)
            sample=live[number]
            if expected_field:
                if sample['front']!=copper[expected_field['bank']] or bytes.fromhex(sample['sprite_bytes'])!=expected_field['data']:
                    fail('live frozen bank differs from bus-derived completed scene', frame=number)
                else:
                    checked_live_samples += 1
            elif sample.get('installed')!=addresses['title_copper']:
                fail('live title sample has another installed list', frame=number)
        for offset, record in enumerate(SLOT.iter_unpack(slot_bytes)):
            reg, kind, channel, size, ipl, flags, address, value, events = record
            vpos, hpos = divmod(offset, stride)
            position = dict(frame=number, vpos=vpos, hpos=hpos)
            # CPU writes come from the independent typed MMIO stream: the
            # pinned raw sidecar's late CPU data annotator can overwrite either
            # CPU or DMA record values. It does not change their addresses.
            while event_cursor<len(field_events):
                e=field_events[event_cursor]; ep=e['position']
                if ep['vpos']*stride+ep['hpos']>offset:break
                event_cursor+=1
                if e['access']=='read' and e['addr'] in (0xdff004,0xdff006):
                    if e['addr']==0xdff006:
                        beam_low=(number,ep['vpos']*stride+ep['hpos'],e['value'],beam_high)
                    else:
                        high=e['value']&1
                        if beam_low and beam_low[3]==high:
                            measured=(high<<8)|(beam_low[2]>>8)
                            last_sample=(beam_low[0],beam_low[1],measured,beam_low[2]&255)
                        beam_high=high
                        beam_low=None
                if e['access']!='write':continue
                ea,es,ev=e['addr'],e['size'],e['value']
                if ea+es<=len(memory):
                    memory[ea:ea+es]=ev.to_bytes(es,'big')
                    if ea==addresses['blank_seen'] and not ev and number in strobe_fields and ep['vpos']>=253:
                        fail('blank latch reopened after publication in same bottom interval',position=ep)
                    if ea==addresses['display_ready'] and ev:
                        bank=index(scalar('ready_copper'))
                        if bank is None:fail('completed scene names unknown bank',position=ep)
                        else:frozen[bank]=snapshot(bank,scalar('ready_generation',2))
                    if not partial and ea==addresses['simulation_updates']:
                        f,b,r,sp=[scalar(n) for n in ('front_copper','back_copper','ready_copper','spare_copper')]
                        if set([f,b,r or sp])!=set(copper) or bool(r)==bool(sp):
                            fail('three-bank ownership is not exclusive',roles=[f,b,r,sp],position=ep)
                elif ea==0xdff080 and es==4:
                    last_cpu_cop=dict(frame=number,value=ev,position=ep)
            if kind==2 and size and flags&1 and address+size<=len(memory):
                if any(a<=address<a+n for a,n in watched):
                    candidates=events_by_byte.get((number,address),[])+events_by_byte.get((number+1,address),[])
                    covered=False
                    for e in candidates:
                        ep=e['position']; ef=ep['frame']+1
                        eo=ep['vpos']*stride+ep['hpos']+(frame['rows']*stride if ef==number+1 else 0)
                        if e['access']=='write' and address+size<=e['addr']+e['size'] and 0<=eo-offset<=16:
                            covered=True;break
                    if not covered:fail('raw CPU bank/state write lacks authoritative MMIO event',address=address,position=position)
                if not partial:
                    for bank,(cp,sp) in enumerate(zip(copper,sprites)):
                        if cp<=address<cp+copper_size or sp<=address<sp+576:
                            if bank==index(scalar('front_copper')) or bank==index(scalar('ready_copper')) or copper[bank]==hardware:
                                fail('CPU wrote an owned displayed/completed bank',bank=bank,address=address,position=position)
            if kind==2 and size and reg in (0x1080,0x1082,0x1088):
                if reg in (0x1080, 0x1082):
                    if reg == 0x1080:
                        cpu_pair = [(number, offset, value)]
                    else:
                        cpu_pair.append((number, offset, value))
                if reg == 0x1088:
                    if number in strobe_fields:fail('more than one presentation strobe in physical field',position=position)
                    strobe_fields.add(number)
                    if not scalar('ready_completed',1):fail('publication lacks completed scene latch',position=position)
                    selected = scalar('presentation_copper')
                    court = index(selected)
                    ready=scalar('ready_copper')
                    ready_generation=scalar('ready_generation',2)
                    ready_title=bool(scalar('ready_title_display',1))
                    expected_selected=addresses['title_copper'] if ready_title else ready
                    if selected!=expected_selected or not scalar('display_ready',1):
                        fail('strobe does not install current latest completed scene', selected=selected, expected=expected_selected, position=position)
                    if selected not in copper and selected!=addresses['title_copper']:
                        fail('unknown installed Copper list', selected=selected, position=position)
                    bound=index(ready)
                    if bound is not None and bound in frozen and frozen[bound]['generation']!=ready_generation:
                        fail('installed generation differs from current ready generation', position=position)
                    if not partial:
                        if vpos < 253:
                            fail('publication outside retired bottom interval', position=position)
                        if not last_sample or last_sample[0] != number:
                            fail('publication lacks beam sample in same field', position=position)
                        else:
                            latency = offset-last_sample[1]
                            maximum_cpu_handover = max(maximum_cpu_handover, latency)
                            if 'presentation_last_safe_line' in addresses:
                                bound = scalar('presentation_last_safe_line', 2)
                                if not 253<=last_sample[2]<=bound:
                                    fail('publication sampled after field-end guard', sample=last_sample, bound=bound)
                        if len(cpu_pair) != 2 or any(p[0] != number for p in cpu_pair):
                            fail('COP1LC pair straddled field restart', pair=cpu_pair, position=position)
                        elif last_cpu_cop is None or last_cpu_cop['frame']!=number or last_cpu_cop['value']!=selected:
                            fail('actual COP1LC pair differs from selected list',pair=cpu_pair,selected=selected,authoritative=last_cpu_cop)
                    hardware = selected
                    if court is not None:
                        current = frozen.get(court)
                        if current is None:
                            if not partial:
                                fail('publication lacks frozen completed scene', bank=court, position=position)
                            current = snapshot(court, scalar('ready_generation',2))
                        if current['generation']!=ready_generation or current['title']!=ready_title:
                            fail('frozen bank metadata differs from latest completed scene', position=position)
                        if not partial and isinstance(current['generation'], int):
                            if current['generation'] > scalar('simulation_updates', 2):
                                fail('publication precedes completed simulation update', position=position,
                                     generation=current['generation'])
                        pending = dict(frame=number, offset=offset, bank=court, pairs={}, position=position)
                    else:
                        current = None
                    if not partial:
                        publications.append(dict(position=position, bank=court,
                                                 generation=ready_generation, completed_generation=scalar('simulation_updates',2), completed_latch=bool(scalar('ready_completed',1))))
                    cpu_pair = []
            if kind == 3 and size and 0x120 <= reg <= 0x13e:
                slot = (reg-0x120)//2
                if not 0<=address<=len(memory)-2:
                    fail('Copper pointer MOVE has invalid source address',position=position,address=address)
                    continue
                operand=int.from_bytes(memory[address:address+2],'big')
                if value!=operand:
                    reported_word_disagreements.append(dict(engine='copper',position=position,actual=value,expected=operand))
                pointer_words[slot] = operand
                owner=index(hardware)
                if owner is None or address!=copper[owner]+70+4*slot:
                    fail('sprite pointer MOVE does not come from installed completed list',position=position,address=address)
                if slot & 1:
                    ch = slot//2
                    last_pair[ch] = (number, vpos, hpos)
                    if pending:
                        expected = sprites[pending['bank']]+72*ch
                        actual = pointer_words[slot-1]<<16 | pointer_words[slot]
                        if actual != expected:
                            fail('actual sprite pointer pair names wrong completed bank', channel=ch,
                                 expected=expected, actual=actual, position=position)
                        pending['pairs'][ch] = position
                        if len(pending['pairs']) == 8:
                            pointer_completion.append(dict(publication=pending['position'],
                                                           last_pair=position,
                                                           elapsed_cck=offset-pending['offset']))
                            pending = None
            if partial or kind != 7 or not size:
                continue
            if expected_field is None:
                fail('sprite DMA active on title field', position=position)
                continue
            ch = channel
            if not 0<=ch<8:
                fail('invalid sprite channel',channel=ch,position=position)
                continue
            hdr=expected_field['data'][72*ch:72*ch+4]
            pos,ctl=struct.unpack('>HH',hdr)
            sprite_start=(pos>>8)|((ctl&4)<<6)
            sprite_stop=(ctl>>8)|((ctl&2)<<7)
            hidden=(pos==0 and ctl==0)
            if not hidden and not (45<=sprite_start<=236 and sprite_stop-sprite_start==16 and sprite_stop<=252 and ctl&0xff<=1):
                fail('malformed visible sprite geometry',channel=ch,header=hdr.hex(),position=position)
            start = sprites[expected_field['bank']]+72*ch
            local = address-start
            word = dict(position=position, address=address, value=value)
            if reg in (0x144+8*ch, 0x146+8*ch):
                pixels += 1; reads[ch]['data'].append(word)
                if local in (0, 2):
                    fail('sprite header fetched as pixel data', channel=ch, position=position, address=address)
                pixel_index=len(reads[ch]['data'])-1
                expected_reg=0x144+8*ch+2*(pixel_index%2)
                if hidden:
                    fail('hidden sprite fetched pixel data',channel=ch,position=position)
                if reg!=expected_reg or vpos!=sprite_start+pixel_index//2 or hpos!=0x15+4*ch+2*(pixel_index%2):
                    fail('sprite pixel destination/row timing is invalid',channel=ch,position=position,reg=reg)
                expected_offset = 4+2*pixel_index
                if local != expected_offset or not 4 <= local <= 66:
                    fail('sprite pixel address progression is not header+4 through image', channel=ch,
                         position=position, address=address, expected=start+expected_offset)
            elif reg in (0x140+8*ch, 0x142+8*ch):
                if vpos == header_line:
                    headers += 1; reads[ch]['header'].append(word)
                    header_index=len(reads[ch]['header'])-1
                    if reg!=0x140+8*ch+2*header_index or hpos!=0x15+4*ch+2*header_index:
                        fail('sprite header register/slot order is invalid',channel=ch,position=position,reg=reg)
                    expected_offset = 2*header_index
                    if local != expected_offset:
                        fail('sprite header address belongs to another scene', channel=ch,
                             position=position, address=address, expected=start+expected_offset)
                    pair = last_pair[ch]
                    if pair is None or pair[0] != number or pair[1] >= header_line:
                        fail('pointer pair not complete before header line', channel=ch, pair=pair, position=position)
                else:
                    terminators += 1; reads[ch]['terminator'].append(word)
                    term_index=len(reads[ch]['terminator'])-1
                    if hidden or reg!=0x140+8*ch+2*term_index or vpos!=sprite_stop or hpos!=0x15+4*ch+2*term_index:
                        fail('sprite terminator register/row timing is invalid',channel=ch,position=position,reg=reg)
                    if local != 68+2*term_index:
                        fail('sprite control fetch is not its terminator', channel=ch, position=position, address=address)
            else:
                fail('unknown sprite DMA register', reg=reg, channel=ch, position=position)
            if 0 <= local <= 70:
                expected = int.from_bytes(expected_field['data'][ch*72+local:ch*72+local+2], 'big')
                if value != expected:
                    reported_word_disagreements.append(dict(channel=ch, position=position,
                         generation=expected_field['generation'], actual=value, expected=expected))
            channels_seen.add(ch); banks_seen.add(expected_field['bank'])
            generations.add(str(expected_field['generation']))
        if not partial and expected_field:
            for ch, events in enumerate(reads):
                if len(events['header']) != 2:
                    fail('field lacks both sprite header words', frame=number, channel=ch)
                pos = int.from_bytes(expected_field['data'][72*ch:72*ch+2], 'big')
                ctl = int.from_bytes(expected_field['data'][72*ch+2:72*ch+4], 'big')
                start = (pos>>8) | ((ctl&4)<<6)
                stop = (ctl>>8) | ((ctl&2)<<7)
                if pos==0 and ctl==0:
                    if events['data']:
                        fail('null header produced pixel DMA',frame=number,channel=ch)
                else:
                    if len(events['data']) != 32 or len(events['terminator']) != 2:
                        fail('visible sprite lacks complete image/terminator progression', frame=number,
                             channel=ch, data_words=len(events['data']), terminator_words=len(events['terminator']))
        while event_cursor<len(field_events):
            e=field_events[event_cursor];event_cursor+=1
            if e['access']=='write' and e['addr']+e['size']<=len(memory):
                memory[e['addr']:e['addr']+e['size']]=e['value'].to_bytes(e['size'],'big')
    for number in set(live)-encountered_live:
        fail('supplied live sample was not checked',frame=number)
    if pending:
        fail('capture ends before installed pointer pairs complete', publication=pending)
    if not full_frames:
        fail('no full traced fields')
    if require_three and banks_seen != {0,1,2}:
        fail('DMA did not cover all three physical banks', banks=sorted(banks_seen))
    return dict(passed=not failures, failures=failures, full_fields=full_frames,
                sprite_header_words=headers, sprite_pixel_words=pixels, sprite_terminator_words=terminators,
                banks=sorted(banks_seen), channels=sorted(channels_seen), generations=len(generations),
                publications=publications, pointer_completion=pointer_completion,
                independently_read_frozen_bank_samples=checked_live_samples,
                raw_sidecar_word_disagreements=reported_word_disagreements,
                data_value_limitation='Pinned Copperline update_last_cpu_trace_data can overwrite raw record data. RAM reconstruction uses authoritative CPU MMIO values; source addresses, frozen snapshots, destination/row timing and ownership remain strict. Raw sidecar data equality is diagnostic, not certified.',
                maximum_beam_sample_to_strobe_cck=maximum_cpu_handover,
                field_geometries=[list(g) for g in sorted(geometries)],
                standard=standard, header_line=header_line,
                baseline_sha256=hashlib.sha256((path/'chip-ram.bin').read_bytes()).hexdigest())


def legacy_header_control(path, sprite_banks):
    """Two-bank release adapter: reject its original header-as-DATA mechanism.

    No triple-bank symbols, new bottom-window policy or RAM baseline required.
    This deliberately has a narrower legacy extent than analyse().
    """
    path = Path(path); faults = []; records = []; last = None
    for line in (path/'profile.jsonl').read_text().splitlines():
        d=json.loads(line)
        if not d.get('traced') or 'slots_file' not in d:
            raise ValueError('Legacy negative control lacks full slot telemetry')
        if last is not None and d['frame']!=last+1:
            raise ValueError('Legacy negative control has a field gap')
        last=d['frame']; raw=(path/d['slots_file']).read_bytes()
        if len(raw)!=d['rows']*d['line_cck']*SLOT.size:
            raise ValueError('Legacy negative control has truncated slots')
        records.append(d['frame'])
        for k,r in enumerate(SLOT.iter_unpack(raw)):
            reg,kind,ch,size,ipl,flags,addr,data,events=r
            if kind!=7 or size!=2 or reg not in (0x144+8*ch,0x146+8*ch):continue
            for b in sprite_banks:
                if addr in (b+72*ch,b+72*ch+2):
                    vp,hp=divmod(k,d['line_cck'])
                    faults.append(dict(reason='sprite header fetched as pixel data',frame=d['frame'],
                                       vpos=vp,hpos=hp,channel=ch,address=addr))
    if not records:
        raise ValueError('Legacy negative control has no fields')
    return dict(passed=not faults,failures=faults,fields=len(records),
                scope='Actual two-bank sprite header addresses read as DATA/DATB; no new ownership symbols or bottom policy assertions')
