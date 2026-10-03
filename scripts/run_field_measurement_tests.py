"""Execute the actual startup measurement/cadence assembly with finite beam streams.
Only the beam-reader boundary is supplied by the fixture. No gameplay model,
intermediate state injection, or renderer/state expectations drive execution.
"""
import hashlib,json,re
from pathlib import Path
from native_tools import ROOT,ASSEMBLER,run,verify_build_tools,emulator_config
from native_observation import code_symbols
from copperline_test_session import NativeControlSession
from native_hunk import loaded_hunks
from native_evidence import atomic_json

CASES=[
 ('pal-short',[100,311,0,1,128,256,310,311,0],311,11838),
 ('pal-long',[100,312,0,1,128,256,311,312,0],312,11838),
 ('ntsc-short',[100,261,0,1,128,256,260,261,0],261,11947),
 ('ntsc-long',[100,262,0,1,128,256,261,262,0],262,11947),
 ('backsteps-before-and-after-wrap',[157,158,157,256,311,0,157,158,157,256,311,0],311,11838),
 ('255-boundary',[100,255,256,255,256,311,0,254,255,256,255,256,311,0],311,11838),
 ('reject-short-field',[100,311,0,256,259,0,1,311,0,256,311,0],311,11838),
 ('reject-gap',[100,311,0,256,280,0,1,261,0,256,261,0],261,11947),
 ('reject-long-field',[100,311,0,256,314,0,1,312,0,256,312,0],312,11838),
]

def execute(control=False):
 source=(ROOT/'amiga/main.s').read_text()
 measurement=source[source.index('measure_presentation_field:'):source.index(' ; Select once')]
 if control:measurement=(ROOT/'tests/fixtures/field-measurement/before-fix.s').read_text()
 cadence=source[source.index('select_simulation_cadence:'):source.index('; Copper-driven publication')]
 directory=ROOT/'build/tests/field-measurement'/('before-fix' if control else 'current');directory.mkdir(parents=True,exist_ok=True)
 lines=['        section code,code','NTSC_INTERVAL_WHOLE equ 11947','NTSC_INTERVAL_FRACTION equ 13180','start:']
 for i,(_,stream,_,_) in enumerate(CASES):
  lines += [f'        lea stream{i},a3',f'        lea end{i},a4','        move.l #11838,simulation_interval_whole','        move.w #14906,simulation_interval_fraction','        bsr measure_presentation_field','        bsr select_simulation_cadence',f'        lea result{i},a0','        move.w presentation_last_line,(a0)+','        move.w presentation_last_safe_line,(a0)+','        move.l simulation_interval,(a0)+','        move.w simulation_interval_fraction,(a0)+',f'        lea stream{i},a1','        move.l a3,d0','        sub.l a1,d0','        move.w d0,(a0)']
 lines+=['fixture_done:','        bra fixture_done',measurement,cadence,'read_presentation_line:','        cmpa.l a4,a3','        bcs.s .read','        st exhausted','        bra fixture_done','.read: move.w (a3)+,d0','        rts','exhausted: dc.b 0','        even','presentation_last_line: dc.w 0','presentation_last_safe_line: dc.w 0','simulation_interval_whole: dc.l 0','simulation_interval_fraction: dc.w 0','simulation_interval: dc.l 0','simulation_phase: dc.l 0']
 for i,(_,stream,_,_) in enumerate(CASES):lines += [f'stream{i}: dc.w '+','.join(map(str,stream)),f'end{i}:',f'result{i}: ds.b 12']
 fixture=directory/'fixture.s';fixture.write_text('\n'.join(lines)+'\n');exe=directory/'fixture';listing=directory/'fixture.lst'
 run([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-L',str(listing),'-o',str(exe),str(fixture)])
 symbols=code_symbols(listing.read_text());cfg=emulator_config()
 with NativeControlSession(directory) as s:
  s.inspect('session_launch',{'binary':cfg['tools']['copperline'],'run':str(exe),'args':['--chipset','OCS','--video','PAL','--cpu','68000','--chip','512K','--slow','0','--fast','0','--noaudio',cfg['inputs']['amiga_rom']]})
  stop=s.inspect('run_until',{'seconds':30});assert stop['reason']=='loadseg',stop
  seg=s.inspect('segments.list')['current'];base=seg[0]['start']
  def raw(a,n):return bytes.fromhex(s.inspect('mem_read',{'addr':a,'len':n})['data'])
  binding=loaded_hunks(exe,seg,raw)
  stop=s.inspect('run_until',{'pc':base+symbols['fixture_done']});assert stop['reason']=='target',stop
  exhausted=raw(base+symbols['exhausted'],1)!=b'\0'
  rows=[]
  for i,(name,stream,last,whole) in enumerate(CASES):
   b=raw(base+symbols[f'result{i}'],12);values=[int.from_bytes(b[a:z],'big') for a,z in [(0,2),(2,4),(4,8),(8,10),(10,12)]]
   expected=[last,last-4,whole,14906 if whole==11838 else 13180,len(stream)*2]
   rows.append({'case':name,'actual':values,'expected':expected,'passed':values==expected})
 report={'control':control,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'loaded_hunks':binding,'exhausted':exhausted,'rows':rows}
 atomic_json(directory/'report.json',report)
 if not control:assert not exhausted and all(r['passed'] for r in rows),report
 else:assert any(not r['passed'] for r in rows if r['case']=='backsteps-before-and-after-wrap'),report
 return report

if __name__=='__main__':
 verify_build_tools()
 positive=execute();negative=execute(True)
 print(json.dumps({'actual_assembly_cases_passed':len(positive['rows']),'before_fix_backstep_control_rejected':True}))
