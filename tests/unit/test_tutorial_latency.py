import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from tutorial_latency import StackTiming, LatencyObserver, instruction_map
class Tests(unittest.TestCase):
 def make(self):return StackTiming({100:dict(return_pc=104,callee='game_preview_step',opcode='61000002')},{200},1000,2000)
 def row(self,a,v,pc,access='write',cck=1):return dict(addr=a,value=v,pc=pc,access=access,size=2,position=dict(cck=cck))
 def start(self,t):
  t.observe(self.row(1500,0,100));t.observe(self.row(1502,104,100,cck=2))
 def test_listing_continuation_not_call(self):
  text='00:00000000 AE8C\n00:00000002 61000002 \t 82: bsr.s game_preview_step\n00:00000006 4E75 \t 83: rts\n'
  values={102:bytes.fromhex('6100'),106:bytes.fromhex('4e75')}
  calls,returns=instruction_map(text,[dict(start=100)],lambda a,n:values[a])
  self.assertEqual(calls[102]['callee'],'game_preview_step')
  self.assertEqual(calls[102]['return_pc'],106)
  self.assertEqual(returns,{106})
 def test_pair(self):
  t=self.make();self.start(t)
  t.observe(self.row(1500,0,198,'read',3)) # MOVEM dummy read never counts.
  self.assertFalse(t.stack[-1]['reads'])
  t.observe(self.row(1500,0,200,'read',4));t.observe(self.row(1502,104,200,'read',5))
  self.assertEqual(t.result()['calls'][0]['elapsed_bus_cck'],4)
 def test_bad_rts_value(self):
  t=self.make();self.start(t)
  with self.assertRaises(AssertionError):t.observe(self.row(1502,105,200,'read'))
 def test_bad_rts_slot(self):
  t=self.make();self.start(t)
  with self.assertRaises(AssertionError):t.observe(self.row(1498,0,200,'read'))
 def test_bad_call_value(self):
  with self.assertRaises(AssertionError):self.make().observe(self.row(1500,999,100))
 def test_read_not_forwarded(self):
  class Callback:
   def __init__(self):self.messages=[]
   def observe(self,m):self.messages.append(m)
  c=Callback();o=LatencyObserver(c,self.make())
  o.observe(dict(method='event.mmio',params=dict(self.row(1500,0,198,'read'),dropped_notifications=0)))
  self.assertEqual(c.messages,[])
 def test_loss(self):
  o=LatencyObserver(None,self.make())
  with self.assertRaises(AssertionError):o.observe(dict(method='event.frame',params=dict(dropped_notifications=1)))
 def test_diagnostic_cases_do_not_expand_release_catalog(self):
  from acceptance_cases import cases, diagnostic_cases
  ordinary={c.id for c in cases()}
  diagnostic={c.id for c in diagnostic_cases()}
  self.assertFalse(ordinary & diagnostic)
  self.assertEqual(diagnostic,{'tutorial-latency-pal','tutorial-latency-ntsc'})
 def test_unbound_measurement_cannot_pass_extent(self):
  from tutorial_latency import required_latency_extent
  self.assertFalse(required_latency_extent({'passed':True},'PAL'))
  self.assertFalse(required_latency_extent({'passed':True},'NTSC'))
if __name__=='__main__':unittest.main()
