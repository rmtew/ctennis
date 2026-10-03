"""Bounded exact-release ADF cold boot and physical Start publication checks."""
import hashlib,json,re
from native_tools import ROOT,emulator_config
from native_evidence import atomic_json
from native_hunk import loaded_hunks
from build_native_adf import package
from copperline_test_session import NativeControlSession
from native_identity_raster import assert_title_raster,assert_logo_absent_initial_raster

def run():
 report=package(self_test=True);cfg=emulator_config();exe=ROOT/report['executable'];adf=ROOT/report['adf']
 listing=(ROOT/'build/amiga/interfaces/enhanced/native.lst').read_text()
 located={n:(int(h,16),int(o,16)) for n,h,o in re.findall(r'^([A-Za-z_]\w*)\s+([0-9A-Fa-f]{2}):([0-9A-Fa-f]{8})\s*$',listing,re.M)}
 cases=[]
 for standard,slow in [('PAL','0'),('NTSC','0'),('PAL','512K'),('NTSC','512K')]:
  directory=ROOT/'build/tests/startup-publication'/(standard.lower()+'-slow'+slow)
  with NativeControlSession(directory) as s:
   s.inspect('session_launch',{'binary':cfg['tools']['copperline'],'args':['--chipset','OCS','--video',standard,'--cpu','68000','--chip','512K','--slow',slow,'--fast','0','--noaudio','--floppy-drives','1','--floppy-speed','100',cfg['inputs']['amiga_rom']]})
   s.inspect('media.floppy.insert',{'drive':0,'path':str(adf),'write_protected':True})
   catch=s.inspect('break_add',{'kind':'loadseg','name':'baseline-rally'});s.inspect('machine.reset',{'kind':'cold'})
   stop=s.inspect('run_until',{'seconds':120});assert stop['reason']=='loadseg',stop
   s.inspect('break_remove',{'id':catch['id']});segments=s.inspect('segments.list')['current'];time=stop['seconds']
   def address(n):h,o=located[n];return segments[h]['start']+o
   def raw(a,n):return bytes.fromhex(s.inspect('mem_read',{'addr':a,'len':n})['data'])
   def number(n,k=1):return int.from_bytes(raw(address(n),k),'big')
   def advance(dt):
    nonlocal time
    stop=s.inspect('run_until',{'seconds':time+dt});time=stop['seconds']
   binding=loaded_hunks(exe,segments,raw)
   advance(2)
   last=number('presentation_last_line',2);safe=number('presentation_last_safe_line',2)
   whole=number('simulation_interval_whole',4);fraction=number('simulation_interval_fraction',2)
   assert last in (range(310,314) if standard=='PAL' else range(260,264)),last
   assert safe==last-4 and safe>=253
   assert (whole,fraction)==((11838,14906) if standard=='PAL' else (11947,13180))
   assert number('game_lifecycle',2)==2 and number('game_title_display')==255
   title=directory/'title.png';s.inspect('capture_screenshot',{'path':str(title)});assert_title_raster(title)
   s.inspect('input_key',{'rawkey':0x44,'action':'press'});advance(.11)
   s.inspect('input_key',{'rawkey':0x44,'action':'release'});advance(2)
   copper=number('presentation_copper',4)
   assert number('game_lifecycle',2)==1 and number('game_title_display')==0
   assert copper in [address(n) for n in ('copperlist','copperlist_back','copperlist_third')]
   hardware=(s.inspect('custom.read',{'reg':'COP1LCH'})['value']<<16)|s.inspect('custom.read',{'reg':'COP1LCL'})['value']
   assert hardware==copper,(hardware,copper)
   court=directory/'court.png';s.inspect('capture_screenshot',{'path':str(court)});assert_logo_absent_initial_raster(court)
   cases.append({'standard':standard,'slow_ram':slow,'loaded_hunks':binding,'last_line':last,'last_safe_line':safe,'cadence':[whole,fraction],'presentation_copper':copper,'hardware_cop1lc':hardware,'presentation_frames':number('presentation_frames',2),'court_sha256':hashlib.sha256(court.read_bytes()).hexdigest(),'passed':True})
   print(standard,slow,'cold Start passed',flush=True)
 result={'adf_sha256':hashlib.sha256(adf.read_bytes()).hexdigest(),'release_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'listing_sha256':hashlib.sha256(listing.encode()).hexdigest(),'cases':cases,'scope':'Copperline exact release cold boots; no WinUAE execution claim'}
 atomic_json(ROOT/'build/tests/startup-publication/report.json',result)
 return result
if __name__=='__main__':run()
