"""Read-only explicit title-UI construction boundaries; raw deadlines remain raw."""
import re
from fractions import Fraction
from native_clock import INTERVAL_CCK

class SetupObserver:
    def __init__(self, base, symbols, listing):
        self.base=base; self.symbols=symbols; self.page=0; self.selection=0; self.lifecycle=0
        self.started=0; self.pending=None; self.regions=[]; self.game_writes=[]
        instructions=[(int(address,16),text) for address,text in re.findall(r'^00:([0-9A-Fa-f]{8})\s+[0-9A-Fa-f]+\s+\d+:\s*(.*)$',listing,re.M)]
        body=[(a,t) for a,t in instructions if symbols['ui_render']<=a<symbols['ui_text']]
        self.begin_pc=[a for a,t in body if t.strip()=='clr.b   ui_dirty']
        self.end_pc=[a for a,t in body if t.strip()=='move.b  #1,display_ready']
        if len(self.begin_pc)!=1 or len(self.end_pc)!=1: raise ValueError('Explicit UI construction markers changed')
        # MMIO records identify the writing instruction (not a broad title state).
        self.begin_pc=self.begin_pc[0]+base; self.end_pc=self.end_pc[0]+base
    def watches(self):
        return [{'addr':self.base+self.symbols[n],'len':length,'access':'write'} for n,length in
            [('ui_dirty',1),('ui_page',1),('ui_selection',1),('game_play_state',60),('game_score_state',28)]]
    def observe(self,row):
        a=row['addr']; v=row['value']; p=row['position']; pc=row['pc']
        if a==self.base+self.symbols['ui_page']: self.page=v
        if a==self.base+self.symbols['ui_selection']: self.selection=v
        if a==self.base+self.symbols['game_lifecycle']: self.lifecycle=v
        if a==self.base+self.symbols['simulation_started_updates']: self.started=v
        if a==self.base+self.symbols['ui_dirty'] and v==0:
            if pc!=self.begin_pc: raise AssertionError({'field':'unrecognized setup entry','pc':pc,'expected':self.begin_pc})
            if self.pending is not None: raise AssertionError('Nested native UI construction')
            self.pending={'callback':self.started,'page':self.page,'selection':self.selection,
                'lifecycle_at_entry':self.lifecycle,'begin':p,'begin_pc':pc,'gameplay_writes':[]}
        if self.pending:
            for n,length in [('game_play_state',60),('game_score_state',28)]:
                start=self.base+self.symbols[n]
                if start<=a<start+length: self.pending['gameplay_writes'].append(row)
        if a==self.base+self.symbols['display_ready'] and v and pc==self.end_pc:
            if self.pending is None: raise AssertionError('UI setup completion without entry')
            self.pending.update(end=p,end_pc=pc,work_cck=p['cck']-self.pending['begin']['cck'],kind=('menu','help','controls','credits')[self.pending['page']])
            self.regions.append(self.pending); self.pending=None
    def proposal(self,callbacks,origin):
        rows={r['callback']:r for r in callbacks}; issues=[]; cases=[]; allowed=set()
        for region in self.regions:
            n=region['callback']; ticks=4 if region['page']==0 else 8; recovery_limit=6 if region['page']==0 else 10
            row=rows.get(n); case=dict(region,bound_cck=float(ticks*INTERVAL_CCK),bound_native_ticks=ticks,recovery_callback_bound=recovery_limit)
            if region['lifecycle_at_entry']!=2 or region['gameplay_writes']: issues.append({'field':'setup advanced gameplay','callback':n})
            if region['work_cck']>ticks*INTERVAL_CCK: issues.append({'field':'setup work budget','callback':n})
            if row is None or row['lifecycle']==1: issues.append({'field':'setup lacks non-advancing callback','callback':n}); cases.append(case); continue
            case['callback_work_cck']=row['completion']['cck']-row['entry']['cck']
            case['nonsetup_work_cck']=case['callback_work_cck']-region['work_cck']
            if case['nonsetup_work_cck']>=INTERVAL_CCK: issues.append({'field':'nonsetup callback work exceeds tick','callback':n})
            allowed.add(n); recovery=[]; recovered=False
            for k in range(n+1,n+recovery_limit+1):
                follow=rows.get(k)
                if follow is None: break
                phase=follow['completion']['cck']-origin-(k-1)*INTERVAL_CCK
                allowance=10+Fraction((k-1)*5,2*65536)
                if phase<INTERVAL_CCK+allowance:
                    recovered=True; case['recovered_at_callback']=k; break
                if follow['lifecycle']==1: issues.append({'field':'advancing gameplay during setup debt','callback':k}); break
                if follow['completion']['cck']-follow['entry']['cck']>=INTERVAL_CCK: issues.append({'field':'catch-up work exceeds tick','callback':k}); break
                allowed.add(k); recovery.append(k)
            if not recovered: issues.append({'field':'setup debt not recovered within bound','callback':n})
            case['catchup_callbacks']=recovery; cases.append(case)
        raw=[]; strict=[]
        for row in callbacks:
            n=row['callback']; ideal=(n-1)*INTERVAL_CCK; allowance=10+Fraction((n-1)*5,2*65536)
            phase=row['entry']['cck']-origin-ideal; end=row['completion']['cck']-origin-ideal
            if phase < -allowance or phase>=INTERVAL_CCK+allowance or end>=INTERVAL_CCK+allowance:
                item={'callback':n,'entry_phase_cck':float(phase),'completion_phase_cck':float(end),'lifecycle':row['lifecycle']};raw.append(item)
                if n not in allowed or row['lifecycle']==1: strict.append(item)
        if self.pending: issues.append({'field':'unfinished setup phase'})
        return {'proposal_only':True,'review_required':True,'raw_deadline_failures':raw,'strict_nonsetup_failures':strict,
            'setup_cases':cases,'issues':issues,'diagnostic_passed':not issues and not strict,
            'policy':'Explicit clr-ui_dirty to UI-render ready write only; 4 native ticks/menu or8/page; non-advancing catchup <=6/menu or10/page. All other callbacks retain original deadlines. Product timing unchanged.'}
