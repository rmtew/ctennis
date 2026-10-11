"""Reconstruct completed scheduler telemetry stores from literal bus writes.

68000 long stores may arrive as high-first or low-first word writes. Do not
publish a partial value or splice halves from different guest instructions.
"""
from native_longword_observer import LongwordObserver


class CoherentWriteObserver:
    WIDTHS={'simulation_phase':4,'simulation_interval':4,
            'tutorial_job_kind':2,'tutorial_job_variant':2,'tutorial_job_budget':2,
            'tutorial_job_cost':4,'tutorial_jobs_completed':4}

    def __init__(self,symbols):
        self.symbols=symbols
        self.longs={name:LongwordObserver() for name,width in self.WIDTHS.items() if width==4}

    def observe(self,row):
        if row.get('access')!='write':return None
        for name,width in self.WIDTHS.items():
            base=self.symbols[name]
            if not base<=row['addr']<base+width:continue
            offset=row['addr']-base
            if width==4:
                value=self.longs[name].write(offset,row['value'],row['size'],row['pc'])
                if value is None:return None
            else:
                assert offset==0 and row['size']==2,'Incomplete scheduler word telemetry store'
                value=row['value']
            return dict(position=dict(row['position']),field=name,value=value,completed_store_pc=row['pc'])
        return None

    def require_complete(self):
        assert not any(observer.seen for observer in self.longs.values()),'Incomplete scheduler long telemetry at capture boundary'
