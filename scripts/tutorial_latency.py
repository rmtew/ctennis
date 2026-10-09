"""Read-only emitted call/RTS stack bus timing; never a gameplay oracle."""
import re


def instruction_map(listing, segments, read):
    calls, returns = {}, set()
    for hunk, offset, encoded, mnemonic, operand in re.findall(
            r'^(\d\d):([\da-fA-F]{8})[ \t]+([\dA-F]+)[ \t]+[^\n]*?:[ \t]*(bsr|jsr|rts)(?:\.[swl])?[ \t]*([^\n]*)$',
            listing, re.M | re.I):
        address = segments[int(hunk)]['start'] + int(offset, 16)
        code = bytes.fromhex(encoded)
        opcode = int.from_bytes(code[:2], 'big')
        assert read(address, 2) == code[:2], 'Loaded call/return opcode differs from listing'
        if mnemonic.lower() == 'rts':
            assert opcode == 0x4e75 and len(code) == 2
            returns.add(address)
        else:
            assert opcode & 0xff00 == 0x6100 or opcode & 0xffc0 == 0x4e80
            assert len(code) in (2, 4, 6), 'Non-68000 call encoding'
            calls[address] = dict(return_pc=address+len(code), opcode=code.hex(),
                                  callee=operand.split(';')[0].strip())
    assert calls and returns
    return calls, returns


def category(callee):
    if callee in ('game_preview_request','game_preview_step','game_preview_result','game_preview_cancel'):
        return 'public-preview'
    if callee.endswith('_body'):
        return 'core-body'
    if any(word in callee for word in ('copy', 'restore', 'release_current', 'save_working')):
        return 'copy-restore'
    if any(word in callee for word in ('guard', 'unchanged', 'validate', 'admitted', 'remaining', 'read_sim_timer')):
        return 'guard-admission'
    return 'other'


class StackTiming:
    def __init__(self, calls, returns, bottom, top):
        self.calls, self.returns = calls, returns
        self.bottom, self.top = bottom, top
        self.pending = None
        self.stack, self.rows = [], []
        self.notifications = self.reads = self.writes = self.noncall_word_writes = 0

    def observe(self, row):
        a, size, value, pc = (row[k] for k in ('addr', 'size', 'value', 'pc'))
        assert row['access'] in ('read', 'write')
        if not (a < self.top and a+size > self.bottom):
            return
        assert self.bottom <= a < a+size <= self.top
        self.notifications += 1
        position = dict(row['position'])
        if row['access'] == 'write':
            self.writes += 1
            if size != 4:
                self.noncall_word_writes += 1
                return  # Pinned provider aggregates BSR/JSR write_long; IRQ frames use words.
            if pc not in self.calls:
                return  # Saves/exception frames are not invented call entries.
            call = self.calls[pc]
            assert value == call['return_pc'], 'Mismatched emitted call return value'
            assert a % 2 == 0, 'Unaligned emitted call return slot'
            if self.stack:
                assert a < self.stack[-1]['slot'], 'Non-LIFO call stack'
            self.stack.append(dict(call, entry_pc=pc, slot=a,
                entry=position, entry_store_complete=position, reads={},
                depth=len(self.stack), children=[],
                caller=self.stack[-1]['callee'] if self.stack else None))
        else:
            self.reads += 1
            if pc not in self.returns:
                return  # MOVEM dummy reads / restores never count as RTS.
            assert self.stack, 'RTS without an observed emitted call'
            frame = self.stack[-1]
            offset = a-frame['slot']
            assert 0 <= offset < offset+size <= 4, 'RTS reads a different return slot'
            data = value.to_bytes(size, 'big')
            expected = frame['return_pc'].to_bytes(4, 'big')
            assert data == expected[offset:offset+size], 'RTS return value mismatch'
            for i, byte in enumerate(data, offset):
                assert i not in frame['reads'], 'Duplicate RTS return-slot read'
                frame['reads'][i] = byte
            if len(frame['reads']) == 4:
                self.stack.pop()
                frame.pop('reads')
                frame.update(exit_pc=pc, exit=position,
                             elapsed_bus_cck=position['cck']-frame['entry']['cck'])
                children = frame.pop('children')
                assert all(frame['entry']['cck'] <= child[0] <= child[1] <= position['cck']
                           for child in children)
                for left, right in zip(children, children[1:]):
                    assert left[1] <= right[0], 'Overlapping direct-child spans'
                frame['exclusive_bus_cck'] = frame['elapsed_bus_cck']-sum(b-a for a,b in children)
                frame['child_spans'] = children
                frame['category'] = category(frame['callee'])
                assert frame['exclusive_bus_cck'] >= 0
                self.rows.append(frame)
                if self.stack:
                    self.stack[-1]['children'].append([frame['entry']['cck'], position['cck']])

    def result(self):
        assert self.pending is None, 'Partial emitted call entry at completed boundary'
        assert all(not f['reads'] for f in self.stack), 'Partially read RTS at completed boundary'
        assert self.rows and self.reads and self.writes
        # An enclosing main-loop call can remain open at simulation_update entry.
        # It is disclosed and omitted; completed descendants remain exact bus spans.
        return dict(protocol='emitted-call-stack-stores-and-matched-emitted-rts-stack-reads',
            calls=self.rows, open_enclosing_calls=[{k:v for k,v in f.items() if k != 'reads'}
                                                  for f in self.stack],
            stack_reads=self.reads, stack_writes=self.writes,
            stack_notifications=self.notifications,noncall_word_stack_writes=self.noncall_word_writes,
            uncertainty='First return-address store through final RTS return-address read only; '
                        'instruction pre-store/post-read CPU tails and IRQ work are not isolated. '
                        'Exclusive spans subtract completed direct children, not overlapping inclusive totals.')


class LatencyObserver:
    """Keep read probes entirely out of the write-only callback/surface observer."""
    def __init__(self, callbacks, timing):
        self.callbacks, self.timing = callbacks, timing
        self.dropped = 0
        self.timer_reads = []
        self.title_publication = self.title_ready = None

    def observe(self, message):
        row = message.get('params', {})
        if message.get('method', '').startswith('event.'):
            assert type(row.get('dropped_notifications')) is int
            assert row['dropped_notifications'] == 0
            for name in ('dropped_events', 'dropped_accesses', 'queue_overflow',
                         'access_overflow', 'notification_overflow', 'overflow'):
                assert row.get(name, 0) == 0, ('Latency probe lost accesses', name)
        if message.get('method') == 'event.mmio':
            assert row['access'] in ('read', 'write')
            if row['access']=='read' and row['addr'] in (0xbfd400,0xbfd500,0xbfd600,0xbfd700):
                assert row['size']==1
                self.timer_reads.append(dict(row, timer_parameters={n:self.callbacks.state[n]
                    for n in ('last_timer_count','simulation_phase','simulation_interval')}))
            self.timing.observe(row)
            if row['access'] == 'read':
                return
        self.callbacks.observe(message)
        surface=getattr(self.callbacks,'surfaces',None)
        if surface is not None:
            state=self.callbacks.state
            title=surface.hardware_copper==self.callbacks.symbols['title_copper']
            if not title or not state.get('game_title_display'):
                self.title_publication=self.title_ready=None
            elif message.get('method')=='event.mmio' and row['addr']==0xdff088:
                if state.get('simulation_started_updates') and self.title_publication is None:
                    assert state['display_ready'] and state['ready_completed'] and state['ready_title_display']
                    self.title_publication=dict(position=dict(row['position']),
                        copper=surface.hardware_copper, producer=dict(state))
            elif message.get('method')=='event.frame' and self.title_publication:
                if row['position']['frame']>=self.title_publication['position']['frame']+2:
                    self.title_ready=dict(position=dict(row['position']),publication=self.title_publication)


def required_latency_extent(report, standard):
    """Finite measurement extent, separate from tutorial acceptance."""
    import json
    import math
    from native_tools import ROOT
    from native_evidence import digest, TARGET
    target=dict(TARGET, video=standard)
    mode=standard.lower()
    relative='build/tests/tutorial-latency-'+mode+'/latency.json'
    evidence=report.get('evidence') or {}
    files=evidence.get('files') or {}
    if not (report.get('passed') is True and report.get('target')==target
            and evidence.get('actual_target')==target
            and report.get('capture')==relative
            and files.get(relative)==digest(ROOT/relative)
            and report.get('executable_sha256')=='7c6a89d70efa2689c78767f56febbd9dea2b66f33e552e447ff83af2353ae849'
            and report.get('full318_history72_backup_guard') is True
            and type(report.get('frozen_boundaries')) is int and report['frozen_boundaries']>0
            and report.get('dropped_notifications')==0
            and report.get('physical_clock_hz')==(3546895 if standard=='PAL' else 3579545)
            and report.get('provider_seconds_clock_hz')==3546895
            and report.get('actual_video')==([311,11838,14906] if standard=='PAL' else [261,11947,13180])
            and report.get('declared_caps')==dict(physical_seconds=30,callbacks=2048,boundary_stops=8192,uncompressed_transcript_bytes=512*1024*1024)):
        return False
    try: capture=json.loads((ROOT/relative).read_text())
    except (OSError,ValueError):return False
    title=report.get('title_ready') or {}
    publication=title.get('publication') or {}
    producer=publication.get('producer') or {}
    probe=capture.get('probe_symbols') or {}
    open_calls=(capture.get('stack_timing') or {}).get('open_enclosing_calls') or []
    if not (title==capture.get('title_ready') and publication.get('copper')==probe.get('title_copper')
            and producer.get('ready_completed') and producer.get('display_ready')
            and producer.get('ready_title_display') and producer.get('game_title_display')
            and title.get('position',{}).get('frame',-1)>=publication.get('position',{}).get('frame',0)+2
            and len(open_calls)==1 and open_calls[0].get('depth')==0
            and open_calls[0].get('caller') is None
            and open_calls[0].get('entry_pc')==probe.get('simulation_update_call_pc')
            and capture.get('final_stop',{}).get('pc')==probe.get('simulation_update')
            and open_calls[0].get('entry_store_complete',{}).get('cck',float('inf'))<=capture.get('final_stop',{}).get('cck',-1)):
        return False
    endpoints=report.get('endpoints') or []
    timing=report.get('timing') or {}
    stack=capture.get('stack_timing') or {}
    raw=capture.get('literal_rpc') or {}
    if not (endpoints==capture.get('endpoints') and len(endpoints)==2
            and [e.get('label') for e in endpoints]==['initial-held','fresh-D-edit']
            and endpoints[0].get('generation')!=endpoints[1].get('generation')
            and timing==capture.get('timing') and type(timing.get('completed_callbacks')) is int and timing['completed_callbacks']>0
            and timing.get('completed_callbacks',2049)<=2048
            and timing.get('dropped_notifications')==0 and timing.get('pending_callback') is None
            and type(timing.get('minimum_absolute_headroom_cck')) in (int,float)
            and math.isfinite(timing['minimum_absolute_headroom_cck'])
            and timing['minimum_absolute_headroom_cck']>0
            and stack.get('stack_reads',0)>0 and stack.get('stack_writes',0)>0
            and any(r.get('category')=='core-body' for r in stack.get('calls',[]))
            and any(r.get('callee')=='game_preview_step' for r in stack.get('calls',[]))
            and [r.get('callee') for r in stack.get('open_enclosing_calls',[])]==['simulation_update']
            and raw.get('records',0)>0 and 0<raw.get('uncompressed_bytes',0)<=512*1024*1024
            and capture.get('timer_reads') and capture.get('boundaries')):
        return False
    for endpoint in endpoints:
        scene=endpoint.get('first_actual_publication') or {}
        fields=scene.get('tutorial_fields') or {}
        cck=endpoint.get('latency_cck')
        seconds=endpoint.get('physical_latency_seconds')
        if not (type(cck) is int and cck>=0 and type(seconds) in (int,float)
                and math.isfinite(seconds) and 0<=seconds<=30
                and scene.get('position',{}).get('cck',-1)-endpoint.get('request',{}).get('cck',0)==cck
                and math.isclose(seconds,cck/report['physical_clock_hz'],abs_tol=1e-12)
                and fields.get('tutorial_generation')==endpoint.get('generation')
                and fields.get('tutorial_marker_generation')==endpoint.get('generation')
                and fields.get('tutorial_active_variant')==0 and fields.get('tutorial_ball_mode')==1
                and fields.get('tutorial_marker_ready') and fields.get('tutorial_placement_ready')
                and not fields.get('tutorial_placement_dirty')
                and (scene.get('native_sprite_check') or {}).get('matched') is True):
            return False
    return True
