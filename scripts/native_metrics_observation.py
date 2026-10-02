"""Read-only native bus timing; no diagnostic instructions in the product.

BSR stack stores to RTS return reads measure elapsed emulated time including
chip-bus contention. They exclude the few cycles outside those bus boundaries.
No CPU busy/wait split is inferred from host duration.
"""
import math
import re
from native_clock import CCK_HZ, INTERVAL_CCK

PROFILES = ('title', 'help', 'one-player-rally', 'two-player-rally', 'demo',
            'pause', 'match-end', 'celebration')


def distribution(values, budget):
    if not values:
        return None
    values = sorted(values)
    return {'samples': len(values), 'typical_median_cck': (values[(len(values)-1)//2]+values[len(values)//2])/2,
            'p95_cck': values[math.ceil(.95*len(values))-1], 'max_cck': values[-1],
            'budget_cck': float(budget), 'minimum_headroom_cck': float(budget)-values[-1]}


class MetricsObserver:
    def __init__(self, base, symbols, listing):
        self.base, self.symbols = base, symbols
        self.values = dict(game_lifecycle=0, game_mode=0, game_flight=0, ui_paused=0, ui_demo=0, ui_page=0)
        self.rows, self.current, self.pending = [], None, None
        self.dropped = 0
        self.first_title_publication = self.first_complete_title_frame = None
        self.timer_start = None
        self.timer_origin = None
        self.calls = {}
        for offset, text in re.findall(r'^00:([0-9A-Fa-f]{8})\s+[0-9A-Fa-f]+\s+\d+:\s*(.*)$', listing, re.M):
            if symbols['simulation_update'] <= int(offset,16) < symbols['prepare_title_display']:
                match = re.fullmatch(r'bsr\s+(game_render_sprites|game_tick_dispatch)', text.strip())
                if match:
                    self.calls[base+int(offset,16)] = 'render' if match[1]=='game_render_sprites' else 'dispatcher'
        if len(self.calls)!=4:
            raise ValueError('Native simulation render/dispatch call boundaries changed')
        # Main loop BSR leaves SP at top-4; these direct calls push at top-8.
        self.return_slot = base+symbols['game_stack_top']-8

    def watches(self):
        fields=[(n, 2 if n in ('game_lifecycle','simulation_started_updates','simulation_updates','simulation_timer_origin') else 1)
                for n in (*self.values, 'simulation_started_updates','simulation_updates','simulation_timer_origin')]
        return [{'addr':self.base+self.symbols[n],'len':length,'access':'write'} for n,length in fields]+[
            {'addr':self.return_slot,'len':4,'access':'access'},
            {'addr':0xdff088,'len':2,'access':'write'}, {'addr':0xbfde00,'len':1,'access':'write'}]

    def profile(self):
        v=self.values
        if v['ui_paused']: return 'pause'
        if v['ui_demo']: return 'demo'
        if v['game_lifecycle']==2: return 'help' if v['ui_page'] else 'title'
        if v['game_lifecycle']==1 and v['game_flight']:
            return 'two-player-rally' if v['game_mode']&128 else 'one-player-rally'
        if v['game_lifecycle']==6: return 'match-end'
        return 'transition-or-serve'

    def observe(self, message):
        method=message.get('method'); r=message.get('params',{})
        self.dropped += r.get('dropped_events',0)+r.get('dropped_notifications',0)
        if method=='event.frame':
            p=r['position']
            # The first boundary after publication can end a partial frame.
            # The next boundary ends a whole title frame, with no earlier switch.
            if (self.first_title_publication and not self.first_complete_title_frame
                    and p['frame']>=self.first_title_publication['frame']+2):
                self.first_complete_title_frame=p
            return
        if method!='event.mmio': return
        a,v,p=r['addr'],r['value'],r['position']
        for name in self.values:
            if a==self.base+self.symbols[name]: self.values[name]=v
        if a==self.base+self.symbols['simulation_timer_origin']: self.timer_origin=v
        if a==0xbfde00 and v==1 and self.timer_start is None: self.timer_start=p
        if a==0xdff088 and self.first_title_publication is None and self.values['game_lifecycle']==2:
            self.first_title_publication=p
        if a==self.base+self.symbols['simulation_started_updates']:
            if self.current: raise ValueError('Metrics callback completion missing')
            self.current={'callback':v,'entry':p,'profile':self.profile(),'phases':{}}
        if a==self.base+self.symbols['simulation_updates'] and self.current:
            self.current['completion']=p
            if self.pending: raise ValueError('Metrics call return missing')
            self.rows.append(self.current); self.current=None
        if self.current and self.return_slot<=a<a+r['size']<=self.return_slot+4:
            if r['access']=='write' and r['pc'] in self.calls:
                if self.pending is None:
                    self.pending={'phase':self.calls[r['pc']],'begin':p,'pc':r['pc']}
            elif r['access']=='read' and self.pending:
                # 68000 reads a long return as two words. End at the last word.
                if a+r['size']==self.return_slot+4:
                    phase=self.pending['phase']
                    if phase in self.current['phases']: raise ValueError('Duplicate measured native phase')
                    self.current['phases'][phase]=p['cck']-self.pending['begin']['cck']
                    self.pending=None

    def result(self, ui_regions=()):
        profiles={}
        origin=self.timer_start['cck']+(65535-self.timer_origin)*5 if self.timer_start and self.timer_origin is not None else None
        for profile in PROFILES:
            rows=[r for r in self.rows if r['profile']==profile]
            ui=[r['work_cck'] for r in ui_regions if (profile=='title' and r['kind']=='menu') or (profile=='help' and r['kind'] in ('help','controls','credits'))]
            phases={phase:distribution([r['phases'][phase] for r in rows if phase in r['phases']],INTERVAL_CCK)
                    for phase in ('render','dispatcher')}
            headrooms=[float(origin+r['callback']*INTERVAL_CCK-r['completion']['cck']) for r in rows] if origin is not None else []
            profiles[profile]={'minimum_deadline_headroom_cck':min(headrooms) if headrooms else None,
                'missed_deadlines':sum(h < -(10+(r['callback']-1)*5/(2*65536)) for h,r in zip(headrooms,rows)) if headrooms else None,
                'state':'measured' if rows else 'unmeasured',
                'callbacks':len(rows), 'ui_construction_render':distribution(ui,INTERVAL_CCK), 'update_including_render':distribution([
                    r['completion']['cck']-r['entry']['cck'] for r in rows],INTERVAL_CCK), **phases}
        return {'schema':1,'profiles':profiles,'extent':{'completed_callbacks':len(self.rows),
                'first_entry':self.rows[0]['entry'] if self.rows else None,
                'last_completion':self.rows[-1]['completion'] if self.rows else None,
                'pending_callback':self.current,'dropped_events':self.dropped},
            'clock':{'cck_hz':CCK_HZ,'simulation_tick_cck':float(INTERVAL_CCK),
                     'pal_display_frame_cck':227*312,'pal_display_frame_ms':227*312*1000/CCK_HZ},
            'boundaries':'Update counter write to completion counter write includes sampling/render/dispatcher. Render and dispatcher: direct BSR first stack-store to RTS last return-word read, including contention; excludes instruction prefix/suffix outside bus boundaries. Dispatcher is not update-minus-render. Profiles use state at callback entry, including input transition callbacks; differing phase sample counts expose calls skipped by a transition. UI construction: explicit clr-ui_dirty to UI-render ready bus writes, only observed redraws (not all idle ticks). Frozen pause ordinarily has no render/dispatcher call; null is intentional.',
            'host_wallclock':'unmeasured; never used as emulated work',
            'cpu_busy_vs_bus_wait':'unavailable in this bus-boundary observer',
            'first_title_publication':self.first_title_publication,
            'first_complete_title_frame':self.first_complete_title_frame,
            'assets_ready_and_controls_initialized':self.timer_start}
