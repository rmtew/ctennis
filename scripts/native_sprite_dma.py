"""Check actual chip-bus sprite fetches against frozen native scene bytes.

This is a bus consumer, not a renderer or gameplay oracle. Memory starts from
Copperline's aligned snapshot and evolves only through recorded CPU writes.
"""
import hashlib
import json
import struct
from pathlib import Path

SLOT = struct.Struct('<HBBBBHIQI')


def analyse(path, addresses, standard='PAL', *, require_three=True, live_samples=None):
    path = Path(path)
    memory = bytearray((path/'chip-ram.bin').read_bytes())
    copper_names = ['copperlist', 'copperlist_back', 'copperlist_third']
    sprite_names = ['sprite0', 'sprite_back', 'sprite_third']
    if not require_three:
        copper_names = copper_names[:2]; sprite_names = sprite_names[:2]
    copper = [addresses[n] for n in copper_names]
    sprites = [addresses[n] for n in sprite_names]
    copper_size = addresses['copperlist_end']-addresses['copperlist']
    header_line = 25 if standard == 'PAL' else 20
    failures = []
    reported_word_disagreements = []
    live = {s['position']['frame']+1:s for s in (live_samples or [])}
    checked_live_samples = 0
    def fail(reason, **details):
        if len(failures) < 40:
            failures.append(dict(reason=reason, **details))
    def scalar(name, size=4):
        start = addresses[name]
        return int.from_bytes(memory[start:start+size], 'big')
    def index(pointer):
        return copper.index(pointer) if pointer in copper else None
    def snapshot(bank, generation):
        start = sprites[bank]
        return {'bank': bank, 'generation': generation,
                'data': bytes(memory[start:start+576])}
    initial = index(scalar('front_copper'))
    current = snapshot(initial, 'inherited') if initial is not None else None
    hardware = scalar('presentation_copper')
    frozen = {}
    pointer_words = [0]*16
    last_pair = [None]*8
    pending = None
    last_sample = None
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
    for line in (path/'profile.jsonl').read_text().splitlines():
        frame = json.loads(line)
        if 'slots_file' not in frame:
            continue
        number, stride = frame['frame'], frame['line_cck']
        geometries.add((frame['rows'], stride))
        if pending:
            fail('sprite pointer installation crossed automatic field restart', publication=pending)
            pending = None
        partial = frame['partial']
        if not partial:
            full_frames += 1
        reads = [dict(header=[], data=[], terminator=[]) for _ in range(8)]
        expected_field = current
        field_hardware = hardware
        if not partial and expected_field and number in live:
            sample=live[number]
            if sample['front']!=copper[expected_field['bank']] or bytes.fromhex(sample['sprite_bytes'])!=expected_field['data']:
                fail('live frozen bank differs from bus-derived completed scene', frame=number)
            else:
                checked_live_samples += 1
        for offset, record in enumerate(SLOT.iter_unpack((path/frame['slots_file']).read_bytes())):
            reg, kind, channel, size, ipl, flags, address, value, events = record
            vpos, hpos = divmod(offset, stride)
            position = dict(frame=number, vpos=vpos, hpos=hpos)
            if kind == 2 and size and (flags & 1 or reg in (0x1080,0x1082,0x1088)):
                if address+size <= len(memory):
                    if not partial:
                        for bank, (cp, sp) in enumerate(zip(copper, sprites)):
                            if cp <= address < cp+copper_size or sp <= address < sp+576:
                                if (bank == index(scalar('front_copper')) or
                                    bank == index(scalar('ready_copper')) or
                                    copper[bank] == hardware):
                                    fail('CPU wrote an owned displayed/completed bank', bank=bank,
                                         address=address, position=position)
                    memory[address:address+size] = value.to_bytes(size, 'big')
                    if address == addresses['display_ready'] and value:
                        bank = index(scalar('ready_copper'))
                        if bank is None:
                            fail('completed scene names unknown bank', position=position)
                        else:
                            frozen[bank] = snapshot(bank, scalar('ready_generation', 2))
                    if not partial and address == addresses['simulation_updates']:
                        f, b, r, s = [scalar(n) for n in
                                      ('front_copper','back_copper','ready_copper','spare_copper')]
                        roles = [f, b, r or s]
                        if set(roles) != set(copper) or bool(r) == bool(s):
                            fail('three-bank ownership is not exclusive', roles=[f,b,r,s], position=position)
                if reg in (0x1080, 0x1082):
                    if reg == 0x1080:
                        cpu_pair = [(number, offset, value)]
                    else:
                        cpu_pair.append((number, offset, value))
                if reg == 0x1088:
                    selected = scalar('presentation_copper')
                    court = index(selected)
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
                                if last_sample[2] > bound:
                                    fail('publication sampled after field-end guard', sample=last_sample, bound=bound)
                        if len(cpu_pair) != 2 or any(p[0] != number for p in cpu_pair):
                            fail('COP1LC pair straddled field restart', pair=cpu_pair, position=position)
                        elif (cpu_pair[0][2]<<16 | cpu_pair[1][2]) != selected:
                            fail('actual COP1LC pair differs from selected list', pair=cpu_pair, selected=selected)
                    hardware = selected
                    if court is not None:
                        current = frozen.get(court)
                        if current is None:
                            if not partial:
                                fail('publication lacks frozen completed scene', bank=court, position=position)
                            current = snapshot(court, scalar('ready_generation',2))
                        if not partial and isinstance(current['generation'], int):
                            if current['generation'] > scalar('simulation_updates', 2):
                                fail('publication precedes completed simulation update', position=position,
                                     generation=current['generation'])
                        pending = dict(frame=number, offset=offset, bank=court, pairs={}, position=position)
                    else:
                        current = None
                    if not partial:
                        publications.append(dict(position=position, bank=court,
                                                 generation=current['generation'] if current else 'title'))
                    cpu_pair = []
            if kind == 2 and size and not flags & 1 and reg == 0x1006:
                last_sample = (number, offset, vpos, hpos)
            if kind == 3 and size and 0x120 <= reg <= 0x13e:
                slot = (reg-0x120)//2
                pointer_words[slot] = value
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
            start = sprites[expected_field['bank']]+72*ch
            local = address-start
            word = dict(position=position, address=address, value=value)
            if reg in (0x144+8*ch, 0x146+8*ch):
                pixels += 1; reads[ch]['data'].append(word)
                if local in (0, 2):
                    fail('sprite header fetched as pixel data', channel=ch, position=position, address=address)
                expected_offset = 4+2*(len(reads[ch]['data'])-1)
                if local != expected_offset or not 4 <= local <= 66:
                    fail('sprite pixel address progression is not header+4 through image', channel=ch,
                         position=position, address=address, expected=start+expected_offset)
            elif reg in (0x140+8*ch, 0x142+8*ch):
                if vpos == header_line:
                    headers += 1; reads[ch]['header'].append(word)
                    expected_offset = 2*(len(reads[ch]['header'])-1)
                    if local != expected_offset:
                        fail('sprite header address belongs to another scene', channel=ch,
                             position=position, address=address, expected=start+expected_offset)
                    pair = last_pair[ch]
                    if pair is None or pair[0] != number or pair[1] >= header_line:
                        fail('pointer pair not complete before header line', channel=ch, pair=pair, position=position)
                else:
                    terminators += 1; reads[ch]['terminator'].append(word)
                    if local not in (68,70):
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
                if start and stop-start == 16:
                    if len(events['data']) != 32 or len(events['terminator']) != 2:
                        fail('visible sprite lacks complete image/terminator progression', frame=number,
                             channel=ch, data_words=len(events['data']), terminator_words=len(events['terminator']))
        last_frame = number
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
                data_value_limitation='Pinned Copperline update_last_cpu_trace_data can overwrite a DMA record data field. Address, owner, progression and frozen-memory checks remain strict; raw data field equality is diagnostic, not certified.',
                maximum_beam_sample_to_strobe_cck=maximum_cpu_handover,
                field_geometries=[list(g) for g in sorted(geometries)],
                standard=standard, header_line=header_line,
                baseline_sha256=hashlib.sha256((path/'chip-ram.bin').read_bytes()).hexdigest())
