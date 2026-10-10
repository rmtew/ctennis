"""Native footer ownership and complete-field association for UX capture."""
from coherent_publication import CoherentSurfaceObserver

class UXSurfaceObserver(CoherentSurfaceObserver):
    def __init__(self, symbols, read, **kwargs):
        super().__init__(symbols,read,**kwargs)
        self.footers={symbols[n]:bytearray(read(symbols[n],512)) for n in ('tutorial_footer0','tutorial_footer1')}
        self.markers=bytearray(read(symbols['tutorial_canvas_markers'],40))
        self.footer_writes=0
    def watches(self):
        return super().watches()+[dict(addr=a,len=512,access='write') for a in self.footers]+[dict(addr=self.symbols['tutorial_canvas_markers'],len=40,access='write')]
    def footer(self,copper):
        bank=self.banks.get(copper)
        if bank is None:return None
        off=self.symbols['ui_overlay_pointer0']-self.symbols['copperlist']
        pointers=[int.from_bytes(bank[off+8*n+2:off+8*n+4],'big')*65536+int.from_bytes(bank[off+8*n+6:off+8*n+8],'big') for n in range(4)]
        assert len(set(pointers))==1,'Mixed footer bitplane identities'
        return pointers[0]
    def snapshot(self,copper,state,position,actual=False):
        row=super().snapshot(copper,state,position,actual=actual)
        if row is not None:
            row['live_prediction_generation']=state.get('tutorial_generation')
            fields=row['tutorial_fields']
            retained=actual and fields.get('tutorial_generation')!=state.get('tutorial_generation')
            row['retained_neutral_pose']=bool(retained)
            if retained:
                assert not fields['tutorial_ball_mode'] and not fields['tutorial_menu'] and not fields['tutorial_marker_ready'],'Stale prediction-bearing publication'
                assert fields['tutorial_active_variant']==state['tutorial_active_variant'],'Retained pose crosses variant change'
                assert fields['tutorial_input_source']==state['tutorial_input_source'],'Retained pose crosses control source change'
            address=self.footer(copper)
            row['footer_address']=address
            if state.get('tutorial_active') and row['surface'] in self.images:
                expected=self.symbols['tutorial_footer0'] if row['surface']==self.symbols['tutorial_surface0'] else self.symbols['tutorial_footer1']
                assert address==expected,'Footer does not belong to its canvas'
                row['footer_bytes']=bytes(self.footers[address]).hex()
                if actual and self.queued and self.queued['copper']==copper:
                    assert row['footer_bytes']==self.queued['footer_bytes'],'Publication changes queued footer'
                    row['landing']=self.queued['landing']
                    if retained:
                        assert not row['landing']['valid'],'Retained pose includes old landing cue'
                else:
                    offset=0 if row['surface']==self.symbols['tutorial_surface0'] else 20
                    meta=self.markers[offset:offset+20]
                    landing=dict(valid=bool(meta[4]),x=int.from_bytes(meta[:2],'big'),y=int.from_bytes(meta[2:4],'big'))
                    fields=row['tutorial_fields']
                    if landing['valid']:
                        assert fields['tutorial_marker_ready'] and not fields['tutorial_menu'] and not fields['tutorial_waiting_ready'],'Unqualified landing cue'
                        assert fields['tutorial_marker_generation']==fields['tutorial_generation']==row['endpoint_generation'],'Stale landing cue'
                        variant=fields['tutorial_active_variant'];point=bytes.fromhex(row['endpoint_points'])[variant*8:variant*8+8]
                        assert (landing['x'],landing['y'])==(point[0],point[1]+1),'Landing cue differs from actual endpoint ground'
                        canvas=self.images[row['surface']]
                        for dx,dy in ((-2,0),(-1,0),(0,0),(1,0),(2,0),(0,-2),(0,-1),(0,1),(0,2)):
                            x,y=landing['x']+dx,landing['y']+dy
                            if not (0<=x<256 and 0<=y<192) or (96<=x<160 and 4<=y<12):continue
                            assert all(canvas[p*6144+y*32+x//8]&(128>>(x%8)) for p in range(4)),'Incomplete landing cross raster'
                    row['landing']=landing
        return row
    def observe(self,row,state):
        a,n=row['addr'],row['size']
        start=self.symbols['tutorial_canvas_markers']
        if max(a,start)<min(a+n,start+40):
            left,right=max(a,start),min(a+n,start+40)
            self.markers[left-start:right-start]=row['value'].to_bytes(n,'big')[left-a:right-a]
        queued=state['ready_copper'] if state['display_ready'] and state['ready_completed'] else 0
        for start,data in self.footers.items():
            if max(a,start)<min(a+n,start+512):
                assert start not in (self.footer(self.hardware_copper),self.footer(queued)), 'Write to displayed/eligible queued footer'
                assert start<=a and a+n<=start+512
                expected=self.symbols['tutorial_footer0'] if state['tutorial_render_surface']==self.symbols['tutorial_surface0'] else self.symbols['tutorial_footer1']
                assert start==expected,'Footer write outside its free-canvas owner'
                data[a-start:a-start+n]=row['value'].to_bytes(n,'big')
                self.footer_writes+=1
        super().observe(row,state)
