"""Matched native-window controller, supplied an already owned paused session.

No boot/build or runtime policy lives here. The controller supplies a candidate
image's declared one-time control word and a fresh native observer adapter. The
adapter must reuse actual input/stack/publication observers, not a physics model.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib

PROVIDER_CLOCK = 3546895
CLOCKS = {'PAL':3546895, 'NTSC':3579545}
READ_METHODS = {'status','regs.get','mem.read','mem_read','mem.digest',
                'beam.get','custom.read','custom.dump','segments.list','disasm'}
REGIONS = (('canonical','game_core_state','game_core_state_end'),
           ('history','game_history_state','game_history_state_end'),
           ('records','game_history_buffer','game_history_buffer_end'),
           ('preview','game_preview_storage','game_preview_storage_end'),
           ('seek','game_history_seek_storage','game_history_seek_storage_end'),
           ('tutorial','tutorial_state','tutorial_state_end'))


class ReadOnlyControl:
    """Observers can inspect; measured-window input and execution are fixed."""
    def __init__(self, session):self._session=session
    def inspect(self, method, arguments=None):
        assert method in READ_METHODS, 'Observer attempted execution/input/state mutation'
        return self._session.inspect(method, arguments)


@dataclass(frozen=True)
class Window:
    standard: str
    press_cck: int
    release_cck: int
    end_cck: int
    control_symbol: str
    disabled: int = 0
    enabled: int = 1

    def validate(self, anchor_cck):
        assert self.standard in CLOCKS
        assert anchor_cck < self.press_cck < self.release_cck < self.end_cck
        assert self.end_cck-anchor_cck <= 2*CLOCKS[self.standard], 'Matched window exceeds two physical seconds'
        assert 0<=self.disabled<=65535 and 0<=self.enabled<=65535 and self.disabled!=self.enabled
        return [dict(rawkey=0x22,action='press',cck=self.press_cck),
                dict(rawkey=0x22,action='release',cck=self.release_cck)]


def read(session, addr, width):
    value=bytes.fromhex(session.inspect('mem.read',dict(addr=addr,len=width))['data'])
    assert len(value)==width
    return value


def snapshot(session, symbols):
    status=session.inspect('status');assert status['state']=='paused'
    result=dict(cck=status['cck'],registers=session.inspect('regs.get'),regions={})
    for name,start,end in REGIONS:
        assert symbols[start]<symbols[end]
        result['regions'][name]=read(session,symbols[start],symbols[end]-symbols[start]).hex()
    assert len(bytes.fromhex(result['regions']['canonical']))==318
    assert len(bytes.fromhex(result['regions']['history']))==72
    return result


def require_anchor(session, symbols):
    value=snapshot(session,symbols);regs=value['registers']
    assert regs['pc']==symbols['main_loop'] and regs['a'][7]==symbols['game_stack_top'], 'Anchor is not settled main_loop/SP top'
    flags={'tutorial_active':(1,255),'tutorial_menu':(1,0),'game_preview_active':(1,0),
           'game_preview_explicit':(2,0),'game_history_seek_active':(1,0),
           'keyboard_ack':(1,0),'ready_completed':(1,0),'display_ready':(1,0),'ready_copper':(4,0),
           'tutorial_pending':(1,0),'tutorial_work_pending':(1,0),'tutorial_render_phase':(2,0),
           'tutorial_placement_dirty':(1,0),'tutorial_footer_ready':(2,0),
           'tutorial_footer_dirty':(1,0)}
    actual={name:int.from_bytes(read(session,symbols[name],width),'big') for name,(width,_) in flags.items()}
    assert actual=={name:expected for name,(_,expected) in flags.items()}, 'Anchor has active owner/ACK/menu/producer work'
    # D must be up before the one fresh measured edge. F may stay held.
    assert read(session,symbols['game_keyboard_matrix']+0x22,1)==b'\0', 'D already held at anchor'
    value['settled_flags']=actual
    return value


def configure_once(session, symbols, word, value):
    address=symbols[word]
    assert 0<=address<=524286 and address%2==0 and 0<=value<=65535
    before=read(session,0,524288)
    session.inspect('mem.write',dict(addr=address,data=value.to_bytes(2,'big').hex(),encoding='hex'))
    after=read(session,0,524288)
    assert after[address:address+2]==value.to_bytes(2,'big')
    assert before[:address]==after[:address] and before[address+2:]==after[address+2:], 'Configuration wrote outside declared word'
    return dict(symbol=word,addr=address,value=value,width=2,before=before[address:address+2].hex(),after=after[address:address+2].hex())


def validate_observation(result):
    """Fail closed on missing native coverage; no timing improvement inference."""
    needed=('canonical_history_frozen','complete_owner_states','ordered_output_events',
            'endpoint_points','input_ack','stack_timing','publications','epoch_cancellation')
    assert all(name in result for name in needed), 'Native adapter omitted required capture extent'
    assert result['canonical_history_frozen'] is True
    assert result['complete_owner_states'] and result['input_ack'] and result['endpoint_points']
    assert not result['stack_timing']['open_enclosing_calls'], 'Measured window ended inside owner'
    assert result.get('notification_loss',0)==0
    assert result['publications'] and all(r.get('native_sprite_check') for r in result['publications']), 'Publication lacks actual sprite/bank proof'
    assert result.get('resume_in_measured_window') is False, 'Resume belongs to separate extent'


def capture_pass(session, symbols, anchor, anchor_path, window, value, label, factory):
    """factory(readonly,symbols,label) supplies fresh watches/breakpoints/observer.

    Adapter methods: watches(), breakpoints(), observe(notification),
    at_stop(stop), finish(). Install existing actual native detectors here; it
    may not issue guest writes or input. Nothing stops adaptively on endpoint.
    """
    session.inspect('pause')
    session.inspect('events.unsubscribe')
    session.inspect('break.clear')
    session.observer=None
    session.inspect('state.load',dict(path=str(anchor_path)))
    restored=require_anchor(session,symbols)
    assert restored==anchor, 'State load failed exact settled-anchor restoration'
    configuration=configure_once(session,symbols,window.control_symbol,value)
    adapter=factory(ReadOnlyControl(session),symbols,label)
    session.observer=adapter
    for pc in adapter.breakpoints():session.inspect('break.add',dict(kind='pc',addr=pc))
    subscription=session.inspect('events.subscribe',dict(events=['mmio','frame'],mmio=adapter.watches()))
    assert subscription.get('dropped_notifications',0)==0
    schedule=window.validate(anchor['cck'])
    for event in schedule:
        session.inspect('input.key',dict(rawkey=event['rawkey'],action=event['action'],at_seconds=event['cck']/PROVIDER_CLOCK))
    stop=dict(cck=anchor['cck'])
    # Pump transport every <=1 physical millisecond. The end is fixed; an
    # endpoint/publication never shortens this window or alters queued input.
    for _ in range(32768):
        target=min(window.end_cck,stop['cck']+max(1,CLOCKS[window.standard]//1000))
        stop=session.inspect('run_until',dict(cck=target))
        adapter.at_stop(stop)
        if stop['cck']>=window.end_cck:break
    else:raise AssertionError('Matched window stop cap')
    result=adapter.finish();validate_observation(result)
    final=snapshot(session,symbols)
    assert all(final['regions'][name]==anchor['regions'][name] for name in ('canonical','history','records')),'Measured input changed frozen canonical/history/records'
    result.update(label=label,configuration=configuration,schedule=schedule,
                  start=anchor['cck'],requested_end=window.end_cck,actual_end=stop['cck'],
                  final=final)
    return result


def replay_identity(result):
    # Pass labels/RPC host save metadata are outside the emulated observation.
    return {name:value for name,value in result.items() if name not in ('label',)}


def matched_capture(session, symbols, anchor_path, window, factory):
    """Save one physical anchor; two baseline replays gate the enabled trial.

    Caller exclusively owns session/transport storage and saves a ReportRun
    receipt binding executable/listing/ROM/tool/anchor/raw hashes. The caller
    must not reuse an old directory or overwrite another campaign's artifacts.
    """
    anchor_path=Path(anchor_path)
    assert not anchor_path.exists(), 'Refusing to overwrite anchor evidence'
    anchor=require_anchor(session,symbols);window.validate(anchor['cck'])
    assert 0<=symbols[window.control_symbol]<=524286, 'Control word outside chip RAM'
    session.inspect('state.save',dict(path=str(anchor_path)))
    assert anchor_path.is_file()
    baseline=capture_pass(session,symbols,anchor,anchor_path,window,window.disabled,'baseline-1',factory)
    repeated=capture_pass(session,symbols,anchor,anchor_path,window,window.disabled,'baseline-2',factory)
    assert replay_identity(baseline)==replay_identity(repeated), 'Baseline state replay is not identical; enabled trial forbidden'
    candidate=capture_pass(session,symbols,anchor,anchor_path,window,window.enabled,'enabled',factory)
    return dict(execution='matched-native-planner-window',baseline_replay_equal=True,
                anchor=anchor,anchor_sha256=hashlib.sha256(anchor_path.read_bytes()).hexdigest(),
                passes=[baseline,repeated,candidate],normative_deadline_safety=False,
                scope='One fixed D input window per region; conditional cohort and semantic/timing analysis remain separate')
