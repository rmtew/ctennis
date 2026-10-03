"""Execute the actual startup selector with every possible OS frequency byte."""
import hashlib,json
from native_tools import ROOT,ASSEMBLER,run,verify_build_tools,emulator_config
from native_observation import code_symbols
from copperline_test_session import NativeControlSession
from native_hunk import loaded_hunks
from native_evidence import atomic_json


def execute():
 source=(ROOT/'amiga/main.s').read_text()
 constants=source[source.index('SIM_INTERVAL_WHOLE equ'):source.index('start:')]
 selector=source[source.index('select_video_standard:'):source.index('; Copper-driven publication')]
 directory=ROOT/'build/tests/video-standard';directory.mkdir(parents=True,exist_ok=True)
 # Poison all timing state before each invocation. Invalid input must leave it
 # intact; valid input must replace every bound/interval, independent of defaults.
 lines=['        section code,code',constants,'start:','        lea exec_fixture,a6','        lea results,a4','        moveq #0,d6','.next:', '        move.b d6,EXEC_VBLANK_FREQUENCY(a6)','        lea timing_state,a0','        moveq #8,d7','.poison:','        move.w #$a5a5,(a0)+','        dbra d7,.poison','        bsr select_video_standard','        move.l d0,(a4)+','        lea timing_state,a0','        moveq #8,d7','.copy:','        move.w (a0)+,(a4)+','        dbra d7,.copy','        addq.w #1,d6','        cmpi.w #256,d6','        bcs.s .next','fixture_done:','        bra fixture_done',selector,'timing_state:','presentation_last_line: dc.w 0','presentation_last_safe_line: dc.w 0','simulation_interval_whole: dc.l 0','simulation_interval_fraction: dc.w 0','simulation_interval: dc.l 0','simulation_phase: dc.l 0','exec_fixture: ds.b EXEC_VBLANK_FREQUENCY+2','results: ds.b 256*22']
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
  data=raw(base+symbols['results'],256*22)
 rows=[]
 for frequency in range(256):
  b=data[frequency*22:(frequency+1)*22]
  expected=(20).to_bytes(4,'big')+bytes([0xa5])*18
  if frequency in (50,60):
   last,whole,fraction=(311,11838,14906) if frequency==50 else (261,11947,13180)
   expected=b''.join(n.to_bytes(z,'big') for n,z in [(0,4),(last,2),(last-4,2),(whole,4),(fraction,2),(whole,4),(whole,4)])
  rows.append({'frequency':frequency,'actual':b.hex(),'expected':expected.hex(),'passed':b==expected})
 result={'passed':all(r['passed'] for r in rows),'state':'complete','source_sha256':hashlib.sha256(source.encode()).hexdigest(),'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'loaded_hunks':binding,'rows':rows}
 atomic_json(directory/'report.json',result)
 assert result['passed'],result
 print('Actual startup selector: 256 byte values passed',flush=True)
 return result


def main():
 report=ROOT/'build/tests/video-standard/report.json'
 atomic_json(report,{'passed':False,'state':'incomplete'})
 try:
  verify_build_tools();return execute()
 except BaseException as error:
  atomic_json(report,{'passed':False,'state':'interrupted' if isinstance(error,KeyboardInterrupt) else 'failed','error':str(error)})
  raise

if __name__=='__main__':main()
