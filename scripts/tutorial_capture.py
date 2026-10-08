"""Read-only native tutorial capture transport and complete callback accounting.

Physical inputs are explicit RPC calls. Screenshots retain the original viewport;
the native view only selects the existing active pixels without interpolation.
This observer neither changes guest state nor supplies expected trajectories.
"""
import gzip
import json
import math
import re
from fractions import Fraction

from copperline_test_session import NativeControlSession


class CaptureSession(NativeControlSession):
    MAX_RAW_BYTES = 64 * 1024 * 1024

    def __enter__(self):
        super().__enter__()
        self.raw_bytes = 0
        self.records = 0
        self.raw = gzip.open(self.directory / 'literal-rpc.jsonl.gz', 'wt')
        self.notification_handler = self.notification
        self.observer = None
        return self

    def record(self, value):
        row = json.dumps(value, separators=(',', ':')) + '\n'
        self.raw_bytes += len(row.encode())
        if self.raw_bytes > self.MAX_RAW_BYTES:
            raise AssertionError('Finite tutorial capture raw-byte cap exceeded')
        self.records += 1
        self.raw.write(row)

    def notification(self, value):
        self.record(dict(type='notification', value=value))
        if self.observer:
            self.observer.observe(value)

    def inspect(self, method, arguments=None):
        self.record(dict(type='request', method=method, arguments=arguments or {}))
        try:
            result = super().inspect(method, arguments)
        except BaseException as error:
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
        self.state = {}

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


def native_view(source, target):
    from PIL import Image
    with Image.open(source) as picture:
        assert picture.size == (716, 285), 'Review native PAL viewport geometry'
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
    def bound(path):
        return (isinstance(path, str)
                and re.fullmatch(r'build/tests/tutorial-court-pal/[\w.-]+', path)
                and isinstance(files.get(path), str)
                and re.fullmatch(r'[0-9a-f]{64}', files[path]))
    target = dict(model='A500', cpu='68000', chipset='OCS', video='PAL',
                  chip_bytes=524288, slow_bytes=0, fast_bytes=0, kickstart='1.3')
    restored = report.get('resume_readback') or {}
    core = report.get('shared_core') or {}
    hunks = report.get('loaded_hunks') or []
    headroom = timing.get('minimum_absolute_headroom_cck')
    return (report.get('complete_state_bytes') == 318
            and report.get('public_history_bytes') == 72
            and report.get('target') == target
            and (report.get('evidence') or {}).get('actual_target') == target
            and report.get('native_video') == dict(presentation_last_line=311,
                simulation_interval_whole=11838, simulation_interval_fraction=14906)
            and bound(report.get('capture')) and bound(report.get('literal_rpc_path'))
            and type(count) is int and count >= 2
            and type(timing.get('completed_callbacks')) is int
            and timing['completed_callbacks'] >= count
            and timing.get('pending_callback') is None
            and timing.get('dropped_notifications') == 0
            and type(headroom) in (int, float) and math.isfinite(headroom) and headroom > 0
            and type(raw.get('uncompressed_bytes')) is int
            and 0 < raw['uncompressed_bytes'] <= CaptureSession.MAX_RAW_BYTES
            and {'title','released-serve','edited-serve','held-serve',
                 'released-edited-serve','options','resumed'} <= names
            and len([n for n in names if isinstance(n,str) and n.startswith('animation-')]) == 24
            and all(bound(r.get('source')) and bound(r.get('native'))
                    and r.get('source_geometry') == [716,285]
                    and r.get('native_geometry') == [256,208] for r in rows)
            and bound(report.get('animation'))
            and report.get('animation_geometry') == [256,208]
            and type(report.get('animation_frames')) is int
            and 2 <= report['animation_frames'] <= 24
            and report.get('animation_source_frames') == 24
            and core == dict(bytes=18020, relocations=257, sink_branches=14,
                normalized_sha256='9a457929bc223b843132bb53af7d604ed574441e32c4651eb69897aa0b48689d')
            and hunks and all(r.get('matched') is True
                and r.get('expected_sha256') == r.get('actual_sha256') for r in hunks)
            and isinstance(restored.get('state'), str) and len(restored['state']) == 636
            and restored.get('state') == restored.get('expected_state') == restored.get('backup')
            and isinstance(restored.get('history'), str) and len(restored['history']) == 144
            and restored.get('history') == restored.get('expected_history')
            and report.get('first_resumed_boundary_matches') is True
            and report.get('held_resume_no_pressed_edge') is True
            and type((report.get('native_memory') or {}).get('chip_free_bytes')) is int
            and report['native_memory']['chip_free_bytes'] > 0)
