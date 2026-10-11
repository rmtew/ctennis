"""Read-only native tutorial capture transport and complete callback accounting.

Physical inputs are explicit RPC calls. Screenshots retain the original viewport;
the native view only selects the existing active pixels without interpolation.
This observer neither changes guest state nor supplies expected trajectories.
"""
import gzip
import hashlib
import json
import math
import re
from fractions import Fraction

from copperline_test_session import NativeControlSession

PRESENTATION_KEYS = ('tutorial_presentation_generation','tutorial_render_generation','tutorial_x','tutorial_y',
    'tutorial_active_variant','tutorial_potential_variant','tutorial_marker_ready','tutorial_waiting_ready',
    'tutorial_placement_ready','tutorial_ball_mode','tutorial_menu','tutorial_menu_selection')


def assert_native_text(path, y, text, selected=False):
    """Authored ASCII/font-cell contract against actual 256x208 scanout."""
    from PIL import Image
    from native_tools import ROOT
    assert len(text) <= 32 and 0 <= y <= 200
    font = (ROOT/'assets/native/title/font.bin').read_bytes()
    left = ((32-len(text))//2)*8
    with Image.open(path) as source:
        assert source.size == (256, 208)
        raster = source.convert('RGB')
        for column, char in enumerate(text):
            for row in range(8):
                byte = font[ord(char)*8+row] ^ (255 if selected else 0)
                for bit in range(8):
                    expected = (255,255,255) if byte & (128 >> bit) else (0,0,0)
                    actual = raster.getpixel((left+column*8+bit, y+row))
                    assert actual == expected, dict(text=text, selected=selected,
                        pixel=[left+column*8+bit, y+row], actual=actual, expected=expected)
    return dict(text=text, y=y, selected=selected, matched=True,
                pixels=len(text)*64)


def assert_tutorial_menu(path, selection):
    assert selection in (0,1,2)
    return [assert_native_text(path, y, text, selection == index)
            for index, (y, text) in enumerate(((132,'PLAY FROM HERE (NOT READY)'),
                (143,'RESUME LATEST'), (154,'CLOSE MENU')))]


def assert_court_origins(bank, symbols, base):
    """All initial and fixed restore operands, preserving native HUD strips."""
    entries = [('cop_bpl'+str(n)+'h', None, n, 0) for n in range(4)]
    entries += [('score_cop_'+str(244+n)+'_hi', 'score_cop_'+str(244+n)+'_lo', n, 42)
                for n in range(4)]
    entries += [('score_cop_point_restore'+str(n)+'_hi',
                 'score_cop_point_restore'+str(n)+'_lo', n, 64) for n in (0,2,3)]
    entries += [('score_cop_'+str(224+n)+'_hi', 'score_cop_'+str(224+n)+'_lo', n, 104)
                for n in (0,2,3)]
    entries += [('score_cop_games_restore_hi','score_cop_games_restore_lo',1,120)]
    for hi, lo, plane, row in entries:
        h = symbols[hi]-symbols['copperlist']+2
        l = symbols[lo]-symbols['copperlist']+2 if lo else h+4
        assert int.from_bytes(bank[h-2:h], 'big') == 0xe0+plane*4, hi
        assert int.from_bytes(bank[l-2:l], 'big') == 0xe2+plane*4, lo or hi
        pointer = int.from_bytes(bank[h:h+2], 'big')*65536+int.from_bytes(bank[l:l+2], 'big')
        assert pointer == base+plane*6144+row*32, (hi, pointer, base)
    return dict(matched=True, base=base, entries=len(entries))


def check_native_presentation(snapshot, paths):
    """Device-coordinate/immutable-image contract, not a trajectory oracle."""
    from native_tools import ROOT
    objects = bytes.fromhex(snapshot['objects'])
    sprites = bytes.fromhex(snapshot['sprite_bytes'])
    fields = snapshot['tutorial_fields']
    assert fields['tutorial_scene_layer'] == 2, 'Tutorial sprite order differs from native foreground order'
    visible = [objects[n:n+8] for n in range(0,64,8) if objects[n+5]]
    emitted = [sprites[n:n+72] for n in range(0,576,72) if any(sprites[n:n+4])]
    assert len(visible) == len(emitted), 'Native sprite visibility differs from prepared scene'
    image = (ROOT/'assets/native/scene/sprite-images.bin').read_bytes()
    for obj, stream in zip(visible,emitted):
        pos, ctl = int.from_bytes(stream[:2],'big'), int.from_bytes(stream[2:4],'big')
        x = ((pos&255)<<1)|(ctl&1)
        y = (pos>>8)|((ctl&4)<<6)
        stop = (ctl>>8)|((ctl&2)<<7)
        assert (x,y,stop) == (obj[1]+160,obj[0]+45,obj[0]+61), 'Native sprite header projection differs'
        frame = int.from_bytes(obj[2:4],'big')
        assert stream[4:68] in (image[frame:frame+64],image[frame+64:frame+128]), 'Sprite image is not the retained native frame'
        assert stream[68:72] == bytes(4), 'Native sprite terminator missing'
    ball = fields['tutorial_ball_mode']
    if fields['tutorial_menu']:
        assert not objects[53] and not objects[61], 'Ball/shadow overprinted menu'
        point = None
    elif not ball:
        original = bytes.fromhex(snapshot['original_objects'])
        assert objects[48:64] == original[48:64], 'Pending generation did not retain actual frozen ball/shadow'
        point = None
    else:
        assert fields['tutorial_presentation_generation'] == fields['tutorial_generation']
        variant = fields.get('tutorial_potential_variant', fields['tutorial_active_variant'])
        count = (fields['tutorial_counts']>>(16 if variant == 0 else 0))&65535
        assert len(paths) % 16 == 0
        capacity = len(paths)//16
        assert 0 < count <= capacity
        if ball == 1:
            endpoints = bytes.fromhex(snapshot['endpoint_points'])
            assert len(endpoints) == 16 and fields['tutorial_marker_ready']
            point = endpoints[variant*8:variant*8+8]
        else:
            index = fields['tutorial_animation_index']
            assert 0 <= index < count
            point = bytes(paths[variant*capacity*8+index*8:variant*capacity*8+index*8+8])
        assert objects[48:50] == bytes((point[3],point[2]))
        assert objects[56:58] == bytes((point[1],point[0]))
        assert bool(objects[53]) == bool(point[6]&15 and point[3]<192)
        assert bool(objects[61]) == bool(point[6]&240 and point[1]<192)
    return dict(matched=True, visible_sprites=len(visible),
                native_headers_and_images=True, actual_sample=point.hex() if point else None,
                scope='Queued/published native sprite RAM and actual endpoint or available dense sample; DMA fetch coverage remains separate.')


class CaptureSession(NativeControlSession):
    # First attempt measured 128 MiB over 8.66 observed guest seconds.
    # A 2 GiB streaming budget allows that rate over 120 seconds with margin;
    # it is an estimate, and overflow remains a failure.
    MAX_RAW_BYTES = 2048 * 1024 * 1024

    def __enter__(self):
        super().__enter__()
        self.raw_bytes = 0
        self.records = 0
        self.raw_overflow = False
        self.raw = gzip.open(self.directory / 'literal-rpc.jsonl.gz', 'wt')
        self.notification_handler = self.notification
        self.observer = None
        return self

    def record(self, value):
        row = json.dumps(value, separators=(',', ':')) + '\n'
        self.raw_bytes += len(row.encode())
        if self.raw_bytes > self.MAX_RAW_BYTES:
            self.raw_overflow = True
            raise AssertionError('Finite tutorial capture raw-byte cap exceeded')
        self.records += 1
        self.raw.write(row)

    def notification(self, value):
        self.record(dict(type='notification', value=value))
        if self.observer:
            self.observer.observe(value)

    def inspect(self, method, arguments=None):
        # A failed bounded recording must still shut down the owned emulator.
        if method == 'shutdown' and self.raw_overflow:
            return super().inspect(method, arguments)
        self.record(dict(type='request', method=method, arguments=arguments or {}))
        try:
            result = super().inspect(method, arguments)
        except BaseException as error:
            if not self.raw_overflow:
                self.record(dict(type='error', error=str(error)))
            raise
        self.record(dict(type='reply', method=method, result=result))
        self.raw.flush()
        return result

    def __exit__(self, *args):
        try:
            super().__exit__(*args)
        finally:
            self.raw.close()


class CallbackObserver:
    """Literal counter stores measure complete callbacks, including transitions."""
    def __init__(self, base, symbols):
        self.base = base
        self.symbols = symbols
        self.timer_start = None
        self.timer_origin = None
        self.started = self.completed = 0
        self.pending = None
        self.rows = []
        self.stack_min = base + symbols['game_stack_top']
        self.dropped = 0
        self.positions = []
        self.presentation_requests = []
        self.state = {}
        self.surfaces = None

    def watches(self, fields, read):
        self.fields = dict(fields, simulation_started_updates=2,
                           simulation_updates=2, simulation_timer_origin=2)
        self.bytes = {n:bytearray(read(self.base+self.symbols[n], size))
                      for n,size in self.fields.items()}
        self.state.update({n:int.from_bytes(data, 'big') for n,data in self.bytes.items()})
        return [dict(addr=self.base+self.symbols[n], len=size, access='write')
                for n, size in self.fields.items()] + [
            dict(addr=0xbfde00, len=1, access='write'),
            dict(addr=self.base+self.symbols['game_stack_bottom'],
                 len=self.symbols['game_stack_top']-self.symbols['game_stack_bottom'],
                 access='write')]

    def observe(self, message):
        row = message.get('params', {})
        if message.get('method', '').startswith('event.'):
            assert type(row.get('dropped_notifications')) is int, 'Missing explicit notification loss telemetry'
            assert row['dropped_notifications'] >= 0
            if 'dropped_events' in row:
                assert type(row['dropped_events']) is int and row['dropped_events'] >= 0
            for name in ('queue_overflow','access_overflow','notification_overflow','overflow','dropped_accesses'):
                if name in row:
                    assert type(row[name]) in (bool, int) and row[name] == 0, ('Overflow telemetry', name)
        self.dropped += row.get('dropped_events', 0)+row.get('dropped_notifications', 0)
        if self.dropped:
            raise AssertionError('Tutorial capture dropped literal notifications')
        if message.get('method') != 'event.mmio':
            if self.surfaces and message.get('method') == 'event.frame':
                self.surfaces.last_frame = row['position']['frame']
            return
        a, value, size, position = row['addr'], row['value'], row['size'], row['position']
        bottom = self.base+self.symbols['game_stack_bottom']
        top = self.base+self.symbols['game_stack_top']
        if bottom <= a < top:
            self.stack_min = min(self.stack_min, a)
        if a == 0xbfde00 and value == 1 and self.timer_start is None:
            self.timer_start = position
        for name, width in self.fields.items():
            address = self.base+self.symbols[name]
            left, right = max(a, address), min(a+size, address+width)
            if left < right:
                data = value.to_bytes(size, 'big')
                self.bytes[name][left-address:right-address] = data[left-a:right-a]
                self.state[name] = int.from_bytes(self.bytes[name], 'big')
                if name == 'tutorial_generation' and right == address+width:
                    self.presentation_requests.append(dict(generation=self.state[name],
                        x=self.state.get('tutorial_x'),y=self.state.get('tutorial_y'),
                        variant=self.state.get('tutorial_active_variant'),
                        callback=self.started,position=dict(position)))
        if 'missed_presentation_deadlines' in self.state:
            assert self.state['missed_presentation_deadlines'] == 0, 'Native presentation missed its deadline'
        if self.surfaces:
            self.surfaces.observe(row, self.state)
        if a == self.base+self.symbols['simulation_timer_origin']:
            self.timer_origin = value
        if a == self.base+self.symbols['simulation_started_updates']:
            assert value == self.started+1 and self.completed == self.started
            assert self.pending is None
            self.started = value
            self.pending = dict(callback=value, entry=position, state=dict(self.state))
        if a == self.base+self.symbols['simulation_updates']:
            assert value == self.completed+1 and value == self.started
            assert self.pending is not None
            self.completed = value
            self.pending.update(completion=position,
                                work_cck=position['cck']-self.pending['entry']['cck'])
            self.rows.append(self.pending)
            self.pending = None

    def result(self, interval_16_16):
        assert self.timer_start is not None and self.timer_origin is not None
        assert self.rows and not self.dropped and self.pending is None
        interval = Fraction(interval_16_16*5, 65536)
        origin = self.timer_start['cck']+(65535-self.timer_origin)*5
        for row in self.rows:
            ideal = origin+(row['callback']-1)*interval
            allowance = 10+Fraction((row['callback']-1)*5, 2*65536)
            row['entry_phase_cck'] = float(row['entry']['cck']-ideal)
            row['absolute_headroom_cck'] = float(ideal+interval-row['completion']['cck'])
            assert -allowance <= row['entry']['cck']-ideal < interval+allowance, row
            assert row['completion']['cck']-ideal < interval+allowance, row
        return dict(completed_callbacks=len(self.rows),
                    max_complete_callback_cck=max(r['work_cck'] for r in self.rows),
                    minimum_absolute_headroom_cck=min(r['absolute_headroom_cck'] for r in self.rows),
                    dropped_notifications=self.dropped,
                    stack_bytes=self.base+self.symbols['game_stack_top']-self.stack_min,
                    pending_callback=self.pending, callbacks=self.rows,
                    scope='Finite complete callback counter boundaries; all transitions retain deadlines.')


class SurfaceObserver:
    """Reconstruct actual Copper banks and guard queued/displayed pixel storage."""
    SIZE = 4*6144

    def __init__(self, symbols, read, verify_court_restores=False, last_line=311,
                 verify_sprites=False):
        assert last_line in (261,311)
        self.last_line = last_line
        self.symbols = symbols
        self.verify_court_restores = verify_court_restores
        self.court_queues = []
        self.court_publications = []
        length = symbols['copperlist_end']-symbols['copperlist']
        self.banks = {symbols[n]:bytearray(read(symbols[n], length))
                      for n in ('copperlist','copperlist_back','copperlist_third')}
        self.images = {symbols[n]:bytearray(read(symbols[n], self.SIZE))
                       for n in ('tutorial_surface0','tutorial_surface1')}
        self.static_base = symbols['plane0']
        self.static_image = bytes(read(self.static_base, self.SIZE))
        self.verify_sprites = verify_sprites
        self.sprite_images = ({symbols[n]:bytearray(read(symbols[n],576))
                               for n in ('sprite0','sprite_back','sprite_third')}
                              if verify_sprites else {})
        self.objects = bytearray(read(symbols['tutorial_scene_objects'],64)) if verify_sprites else bytearray()
        self.original_objects = bytearray(read(symbols['game_scene_objects'],64)) if verify_sprites else bytearray()
        self.path_bytes = bytearray(read(symbols['game_preview_paths'],symbols['game_preview_storage_end']-symbols['game_preview_paths'])) if verify_sprites else bytearray()
        self.endpoint_bytes = bytearray(read(symbols['game_preview_endpoints'],16)) if verify_sprites else bytearray()
        self.sprite_checks = []
        self.scene_first_fields = {}
        assert symbols['tutorial_surfaces_end']-symbols['tutorial_surface0'] == 2*self.SIZE
        self.offset = symbols['cop_bpl0h']-symbols['copperlist']
        self.cop1lc = bytearray(4)
        self.displayed = None
        self.queued = None
        self.hardware_copper = 0
        self.last_frame = 0
        self.first_fields = {}
        self.publications = []
        self.queue_records = []
        self.surface_writes = 0
        self.bank_writes = 0

    def watches(self):
        watches = [dict(addr=a,len=len(data),access='write')
                for a,data in (*self.banks.items(),*self.images.items(),*self.sprite_images.items())] + [
                    dict(addr=self.static_base,len=self.SIZE,access='write'),
                    dict(addr=0xdff080,len=4,access='write'),
                    dict(addr=0xdff088,len=2,access='write')]
        if self.verify_sprites:
            watches += [dict(addr=self.symbols['tutorial_scene_objects'],len=64,access='write'),
                        dict(addr=self.symbols['game_scene_objects'],len=64,access='write'),
                        dict(addr=self.symbols['game_preview_paths'],len=len(self.path_bytes),access='write'),
                        dict(addr=self.symbols['game_preview_endpoints'],len=16,access='write')]
        return watches

    def sprite_base(self, copper):
        bank = self.banks.get(copper)
        if bank is None or not self.verify_sprites:
            return None
        offset = self.symbols['cop_spr0h']-self.symbols['copperlist']
        pointers = [int.from_bytes(bank[offset+n*8+2:offset+n*8+4],'big')*65536+
                    int.from_bytes(bank[offset+n*8+6:offset+n*8+8],'big') for n in range(8)]
        assert pointers[0] in self.sprite_images and pointers == [pointers[0]+72*n for n in range(8)], 'Mixed native sprite banks'
        return pointers[0]

    def surface(self, copper):
        data = self.banks.get(copper)
        if data is None:
            return None
        pointers = []
        for n in range(4):
            p = self.offset+n*8
            assert int.from_bytes(data[p:p+2],'big') == 0xe0+n*4
            assert int.from_bytes(data[p+4:p+6],'big') == 0xe2+n*4
            pointers.append(int.from_bytes(data[p+2:p+4],'big')*65536+
                            int.from_bytes(data[p+6:p+8],'big'))
        if pointers[0] not in self.images and pointers[0] != self.static_base:
            return None
        assert pointers == [pointers[0]+n*6144 for n in range(4)], 'Mixed court bitplane origins'
        return pointers[0]

    def snapshot(self, copper, state, position, actual=False):
        image = self.surface(copper)
        if image is None:
            return None
        bank = self.banks[copper]
        pixels = self.static_image if image == self.static_base else self.images[image]
        queued = self.queued if actual and self.queued and self.queued['copper'] == copper else None
        result = dict(copper=copper, bank=bytes(bank).hex(),
                    bank_sha256=hashlib.sha256(bank).hexdigest(), surface=image,
                    surface_sha256=hashlib.sha256(pixels).hexdigest(),
                    generation=queued['generation'] if queued else state['tutorial_published_generation'],
                    ready_generation=state['ready_generation'], position=dict(position),
                    tutorial_fields=queued['tutorial_fields'] if queued else
                        {n:v for n,v in state.items() if n.startswith('tutorial_')})
        if self.verify_sprites:
            base = self.sprite_base(copper)
            result.update(sprite_base=base, sprite_bytes=bytes(self.sprite_images[base]).hex(),
                          sprite_sha256=hashlib.sha256(self.sprite_images[base]).hexdigest(),
                          objects=queued['objects'] if queued else bytes(self.objects).hex(),
                          original_objects=queued['original_objects'] if queued else bytes(self.original_objects).hex(),
                          endpoint_points=queued['endpoint_points'] if queued else bytes(self.endpoint_bytes).hex(),
                          endpoint_outcomes=queued['endpoint_outcomes'] if queued else state.get('game_preview_endpoint_outcomes',0),
                          endpoint_ready=queued['endpoint_ready'] if queued else state.get('game_preview_endpoint_ready',0),
                          endpoint_phases=queued['endpoint_phases'] if queued else state.get('game_preview_endpoint_phases',0),
                          endpoint_generation=queued['endpoint_generation'] if queued else state.get('game_preview_generation',0))
            if queued:
                result['native_sprite_check'] = queued.get('native_sprite_check')
            elif state['tutorial_active']:
                check = check_native_presentation(result, self.path_bytes)
                self.sprite_checks.append(dict(check, position=dict(position)))
                result['native_sprite_check'] = check
        return result

    def observe(self, row, state):
        a,size = row['addr'], row['size']
        data = row['value'].to_bytes(size,'big')
        queued_copper = state['ready_copper'] if state['display_ready'] and state['ready_completed'] else 0
        displayed_image = self.surface(self.hardware_copper)
        queued_image = self.surface(queued_copper)
        assert not (max(a,self.static_base) < min(a+size,self.static_base+self.SIZE)), 'Write to immutable original court'
        if self.verify_sprites:
            displayed_sprites = self.sprite_base(self.hardware_copper)
            queued_sprites = self.sprite_base(queued_copper)
            for start, shadow in self.sprite_images.items():
                if max(a,start) < min(a+size,start+len(shadow)):
                    assert start not in (displayed_sprites,queued_sprites), 'Write to displayed or eligible queued sprites'
                    assert start <= a and a+size <= start+len(shadow)
                    shadow[a-start:a-start+size] = data
            for name, shadow in (('tutorial_scene_objects',self.objects),('game_scene_objects',self.original_objects),('game_preview_paths',self.path_bytes),('game_preview_endpoints',self.endpoint_bytes)):
                start = self.symbols[name]
                if max(a,start) < min(a+size,start+len(shadow)):
                    # Canonical freeze/restore copies can straddle a subregion
                    # boundary. Reconstruct only the actual overlapping bytes.
                    left, right = max(a,start), min(a+size,start+len(shadow))
                    shadow[left-start:right-start] = data[left-a:right-a]
        for start, shadow in self.images.items():
            if max(a,start) < min(a+size,start+len(shadow)):
                assert start not in (displayed_image,queued_image), 'Write to displayed or eligible queued tutorial surface'
                assert start <= a and a+size <= start+len(shadow)
                assert state['tutorial_render_surface'] == start, 'Write outside private drawing owner'
                shadow[a-start:a-start+size] = data
                self.surface_writes += 1
        for start, shadow in self.banks.items():
            if max(a,start) < min(a+size,start+len(shadow)):
                assert start not in (self.hardware_copper,queued_copper), 'Write to displayed or eligible queued Copper bank'
                assert start <= a and a+size <= start+len(shadow)
                shadow[a-start:a-start+size] = data
                self.bank_writes += 1
        if 0xdff080 <= a and a+size <= 0xdff084:
            self.cop1lc[a-0xdff080:a-0xdff080+size] = data
        if a == self.symbols['ready_completed'] and row['value']:
            if self.verify_court_restores and queued_copper in self.banks:
                base = self.surface(queued_copper) or self.symbols['plane0']
                check = assert_court_origins(self.banks[queued_copper], self.symbols, base)
                self.court_queues.append(dict(check, copper=queued_copper,
                    position=dict(row['position']), after_resume=bool(state['tutorial_resume_count'])))
            self.queued = self.snapshot(queued_copper,state,row['position'])
            if self.queued:
                self.queue_records.append(self.queued)
        if a == 0xdff088:
            target = int.from_bytes(self.cop1lc,'big')
            expected = self.symbols['title_copper'] if state['ready_title_display'] else state['ready_copper']
            # Startup has no completed producer; all runtime strobes do.
            if state['simulation_started_updates']:
                assert state['display_ready'] and state['ready_completed']
                assert target == expected == state['presentation_copper'], 'Actual COPJMP selects an uncompleted bank'
                assert 253 <= row['position']['vpos'] <= self.last_line, 'Court publication outside guarded bottom interval'
            self.hardware_copper = target
            if self.verify_court_restores and target in self.banks:
                base = self.surface(target) or self.symbols['plane0']
                check = assert_court_origins(self.banks[target], self.symbols, base)
                self.court_publications.append(dict(check, copper=target,
                    position=dict(row['position']), after_resume=bool(state['tutorial_resume_count'])))
            self.displayed = self.snapshot(target,state,row['position'],actual=True)
            if self.displayed:
                assert self.queued is not None
                for name in ('copper','bank_sha256','surface','surface_sha256','generation','ready_generation'):
                    assert self.displayed[name] == self.queued[name], ('Publication changes queued image', name)
                if self.verify_sprites:
                    assert self.displayed['sprite_sha256'] == self.queued['sprite_sha256'], 'Publication changes queued sprites'
                self.publications.append(self.displayed)
                identity = (self.displayed['surface'],self.displayed['generation'])
                self.first_fields.setdefault(identity,row['position']['frame'])
                fields = self.displayed['tutorial_fields']
                key = tuple(fields.get(n) for n in PRESENTATION_KEYS)
                self.scene_first_fields.setdefault(key,dict(frame=row['position']['frame'],
                    position=dict(row['position']), ready_generation=self.displayed['ready_generation']))

    def current(self, generation):
        if not self.displayed or self.displayed['generation'] != generation:
            return False
        identity = (self.displayed['surface'],generation)
        return self.last_frame >= self.first_fields[identity]+2

    def current_presentation(self, fields):
        if not self.displayed:
            return None
        key = tuple(fields.get(n) for n in PRESENTATION_KEYS)
        if key != tuple(self.displayed['tutorial_fields'].get(n) for n in PRESENTATION_KEYS):
            return None
        first = self.scene_first_fields.get(key)
        return first if first and self.last_frame >= first['frame']+2 else None

    def completed_surface(self, generation):
        """Bind stable background only; latest sprite bank may not have scanned out."""
        assert self.current(generation)
        identity = (self.displayed['surface'], generation)
        return dict(surface=self.displayed['surface'], generation=generation,
                    surface_sha256=self.displayed['surface_sha256'],
                    first_publication_frame=self.first_fields[identity],
                    observation_frame=self.last_frame, scope='stable-background-only')

    def result(self):
        assert self.surface_writes and self.bank_writes and self.publications and self.queue_records
        if self.verify_court_restores:
            assert self.court_queues and self.court_publications
            resumed = {r['copper'] for r in self.court_publications
                       if r['after_resume'] and r['base'] == self.symbols['plane0']}
            assert resumed == set(self.banks), 'Not all resumed native banks were published'
        return dict(surface_write_count=self.surface_writes, bank_write_count=self.bank_writes,
                    protected_surface_writes=0, protected_bank_writes=0,
                    queues=self.queue_records, publications=self.publications,
                    court_queues=self.court_queues, court_publications=self.court_publications,
                    court_restores_verified=self.verify_court_restores,
                    native_sprite_checks=self.sprite_checks,
                    exact_queued_image_published=True,
                    scope='Literal full-surface/Copper writes and actual COP1LC/COPJMP; no displayed or eligible queued writes.')


def native_view(source, target):
    from PIL import Image
    with Image.open(source) as picture:
        assert picture.size in ((716,285),(716,235)), 'Review native viewport geometry'
        rgb = picture.convert('RGB')
        image = Image.new('RGB', (256, 208))
        pixels = [(rgb.getpixel((126+2*x, 16+y)))
                  for y in range(208) for x in range(256)]
        # Verify doubled horizontal samples really represent one native pixel.
        assert all(rgb.getpixel((126+2*x, 16+y)) == rgb.getpixel((127+2*x, 16+y))
                   for y in range(208) for x in range(256))
        image.putdata(pixels)
        image.save(target)


def animation(paths, output, duration_ms):
    from PIL import Image
    images = []
    for path in paths:
        with Image.open(path) as image:
            images.append(image.convert('RGB').copy())
    assert len(images) >= 2
    images[0].save(output, save_all=True, append_images=images[1:],
                   duration=duration_ms, loop=0, optimize=False)
    with Image.open(output) as result:
        return dict(frames=result.n_frames, geometry=list(result.size),
                    source_frames=len(paths))


def required_capture_extent(report):
    timing = report.get('timing') or {}
    raw = report.get('literal_rpc') or {}
    rows = report.get('screenshots') or []
    names = {r.get('name') for r in rows}
    count = report.get('frozen_boundaries')
    files = (report.get('evidence') or {}).get('files') or {}
    standard = (report.get('target') or {}).get('video')
    if standard not in ('PAL','NTSC'):
        return False
    directory = 'build/tests/tutorial-court-'+standard.lower()+'/'
    def bound(path):
        return (isinstance(path, str)
                and re.fullmatch(re.escape(directory)+r'[\w.-]+', path)
                and isinstance(files.get(path), str)
                and re.fullmatch(r'[0-9a-f]{64}', files[path]))
    target = dict(model='A500', cpu='68000', chipset='OCS', video=standard,
                  chip_bytes=524288, slow_bytes=0, fast_bytes=0, kickstart='1.3')
    expected_video = dict(zip(('presentation_last_line','simulation_interval_whole',
                              'simulation_interval_fraction'),
                             (311,11838,14906) if standard == 'PAL' else (261,11947,13180)))
    cck_hz = 3546895 if standard == 'PAL' else 3579545
    tick_seconds = ((expected_video['simulation_interval_whole']*65536+
                     expected_video['simulation_interval_fraction'])*5/(65536*cck_hz))
    maximum_drift = (312.5 if standard == 'PAL' else 262.5)*227/cck_hz+tick_seconds
    restored = report.get('resume_readback') or {}
    core = report.get('shared_core') or {}
    hunks = report.get('loaded_hunks') or []
    surfaces = report.get('surface_ownership') or {}
    visuals = report.get('visual_checks') or {}
    waiting = visuals.get('released-wait') or {}
    responsiveness = report.get('responsiveness') or {}
    responses = responsiveness.get('requests') or []
    animation_steps = responsiveness.get('animation_steps') or []
    animation_cadence = responsiveness.get('animation_cadence') or []
    def latency(value):
        return type(value) in (int,float) and math.isfinite(value) and value >= 0
    def fresh_held():
        edit = responsiveness.get('fresh_held_edit') or {}
        start,end = edit.get('start_seconds'),edit.get('end_seconds')
        if not (latency(start) and latency(end) and start < end):
            return False
        selected = [r for r in responses if r.get('variant') == 0
                    and latency((r.get('position') or {}).get('seconds'))
                    and start <= r['position']['seconds'] < end]
        samples = [r['endpoint_publication_seconds'] for r in selected
                   if latency(r.get('endpoint_publication_seconds'))]
        return (selected and samples
                and edit.get('generations') == [r.get('generation') for r in selected]
                and responsiveness.get('fresh_held_endpoint_seconds') == samples)
    def cadence(row):
        ticks = row.get('ticks')
        producer_ticks = row.get('producer_ticks')
        drift = row.get('drift_seconds')
        elapsed = row.get('elapsed_seconds')
        nominal = row.get('nominal_seconds')
        tolerance = row.get('maximum_drift_seconds')
        return (type(ticks) is int and ticks >= 20
                and type(producer_ticks) is int and abs(producer_ticks-ticks) <= 1
                and type(drift) in (int,float) and math.isfinite(drift)
                and latency(elapsed) and latency(nominal) and latency(tolerance)
                and math.isclose(nominal,ticks*tick_seconds,rel_tol=1e-9,abs_tol=1e-9)
                and math.isclose(drift,elapsed-nominal,rel_tol=1e-9,abs_tol=1e-9)
                and math.isclose(tolerance,maximum_drift,rel_tol=1e-9,abs_tol=1e-9)
                and abs(drift) <= maximum_drift)
    headroom = timing.get('minimum_absolute_headroom_cck')
    return (report.get('complete_state_bytes') == 318
            and report.get('public_history_bytes') == 72
            and report.get('target') == target
            and (report.get('evidence') or {}).get('actual_target') == target
            and report.get('native_video') == expected_video
            and type(report.get('missed_presentation_deadlines')) is int
            and report['missed_presentation_deadlines'] == 0
            and bound(report.get('capture')) and bound(report.get('literal_rpc_path'))
            and type(count) is int and count >= 2
            and type(timing.get('completed_callbacks')) is int
            and timing['completed_callbacks'] >= count
            and timing.get('pending_callback') is None
            and timing.get('dropped_notifications') == 0
            and type(headroom) in (int, float) and math.isfinite(headroom) and headroom > 0
            and type(raw.get('uncompressed_bytes')) is int
            and 0 < raw['uncompressed_bytes'] <= CaptureSession.MAX_RAW_BYTES
            and {'title','released-serve','edited-serve','held-serve','held-edited-serve',
                 'released-edited-serve','options','options-resume',
                 'resumed','resumed-1','resumed-2'} <= names
            and len([n for n in names if isinstance(n,str) and n.startswith('animation-')]) == 24
            and all(bound(r.get('source')) and bound(r.get('native'))
                    and r.get('source_geometry') in ([[716,285]] if standard == 'PAL'
                                                   else [[716,235],[716,285]])
                    and r.get('native_geometry') == [256,208] for r in rows)
            and all(isinstance(r.get('observed_surface'),dict)
                    and r['observed_surface'].get('generation') == (r.get('fields') or {}).get('tutorial_published_generation')
                    and isinstance(r['observed_surface'].get('surface_sha256'),str)
                    and re.fullmatch(r'[0-9a-f]{64}', r['observed_surface']['surface_sha256'])
                    and r['observed_surface'].get('scope') == 'stable-background-only'
                    and type(r['observed_surface'].get('first_publication_frame')) is int
                    and type(r['observed_surface'].get('observation_frame')) is int
                    and r['observed_surface']['observation_frame'] >= r['observed_surface']['first_publication_frame']+2
                    for r in rows if r.get('name') != 'title' and not r.get('name','').startswith('resumed'))
            and all(len(visuals.get(name, [])) == 3
                    and all(r.get('matched') is True and r.get('selected') is (index == selection)
                            for index,r in enumerate(visuals[name]))
                    for name, selection in (('options',0), ('options-resume',1)))
            and (waiting.get('raster') or {}).get('matched') is True
            and isinstance(waiting.get('state'),str) and len(waiting['state']) == 636
            and re.fullmatch(r'[0-9a-f]{636}', waiting['state'])
            and waiting.get('end') in (0,1) and waiting.get('ordinal') == 0xffff
            and waiting['state'][waiting['end']*20:waiting['end']*20+2] == '40'
            and waiting['state'][108+waiting['end']*2:110+waiting['end']*2] == '00'
            and waiting.get('phase') == 0x40 and waiting.get('ai') == 0
            and waiting.get('launches') == 0 and waiting.get('outcome') == 6
            and waiting.get('sample_count') == waiting.get('sample_limit') == 256
            and waiting.get('incomplete') is True and waiting.get('outgoing_shot_claimed') is False
            and bound(report.get('animation'))
            and report.get('animation_geometry') == [256,208]
            and type(report.get('animation_frames')) is int
            and 2 <= report['animation_frames'] <= 24
            and report.get('animation_source_frames') == 24
            and core == dict(bytes=17606, relocations=7, sink_branches=14,
                normalized_sha256='99c543c170c036137be81d07ebd30b522ef3abdff04bd7b1af38f00047bb99d5')
            and hunks and all(r.get('matched') is True
                and r.get('expected_sha256') == r.get('actual_sha256') for r in hunks)
            and isinstance(restored.get('state'), str) and len(restored['state']) == 636
            and restored.get('state') == restored.get('expected_state') == restored.get('backup')
            and isinstance(restored.get('history'), str) and len(restored['history']) == 144
            and restored.get('history') == restored.get('expected_history')
            and report.get('first_resumed_boundary_matches') is True
            and report.get('held_resume_no_pressed_edge') is True
            and surfaces.get('protected_surface_writes') == 0
            and surfaces.get('protected_bank_writes') == 0
            and surfaces.get('exact_queued_image_published') is True
            and surfaces.get('court_restores_verified') is True
            and surfaces.get('resumed_native_banks') == 3
            and responsiveness.get('latest_pose_matches') is True
            and responsiveness.get('trails_enabled') is False
            and latency(responsiveness.get('physical_movement_to_player_seconds'))
            and latency(responsiveness.get('physical_held_choice_to_endpoint_seconds'))
            and responsiveness.get('fresh_held_endpoint_seconds')
            and all(latency(r) for r in responsiveness['fresh_held_endpoint_seconds'])
            and fresh_held()
            and type(responsiveness.get('moving_publications')) is int
            and responsiveness['moving_publications'] >= 2
            and type(responsiveness.get('native_sprite_checks')) is int
            and responsiveness['native_sprite_checks'] > 0
            and responsiveness.get('animation_dense_samples') is True
            and responsiveness.get('animation_normal_speed') is True
            and animation_cadence
            and all(cadence(r) for r in animation_cadence)
            and len(animation_steps) >= 2
            and all(latency(r.get('interval_seconds')) and r['interval_seconds'] > 0
                    and type(r.get('previous_index')) is int
                    and type(r.get('index')) is int
                    and 0 < r['index']-r['previous_index'] <= 2 for r in animation_steps)
            and any(latency(r.get('endpoint_publication_seconds')) for r in responses)
            and any(r.get('variant') == 0 and latency(r.get('endpoint_publication_seconds')) for r in responses)
            and any(latency(r.get('waiting_publication_seconds')) for r in responses)
            and all(r.get('superseded_without_publication') is True
                    or latency(r.get('player_publication_seconds')) for r in responses)
            and all(type(surfaces.get(n)) is int and surfaces[n] > 0 for n in
                    ('surface_write_count','bank_write_count','queued_images','actual_publications'))
            and type((report.get('native_memory') or {}).get('chip_free_bytes')) is int
            and report['native_memory']['chip_free_bytes'] > 0)
