"""Private padded actual-original input routine; fail closed byte/symbol audit."""
import sys, pathlib, subprocess, shutil, hashlib,json

from build_match_core import load_image
root=pathlib.Path(__file__).resolve().parent.parent; candidate=root/'build/amiga/interfaces/enhanced/baseline-rally'; ci,cs=load_image(candidate)
old=root/'build/tests/ui-scan-original-ad4/baseline-rally'; oi,os=load_image(old)
growth=(cs['ui_latch_live_controls']-cs['ui_sample'])-(os['ui_latch_live_controls']-os['ui_sample'])
assert growth>0 and growth%2==0
out=root/'build/tests/ui-scan-padded-reference-final';out.mkdir(exist_ok=False)
shutil.copytree(root/'amiga',out/'amiga')
for n in ('assets','build'): (out/n).symlink_to(root/n,target_is_directory=True)
src=subprocess.check_output(['git','show','6a0f749:amiga/game/interface_input.s'],text=True)
src=src.replace('\nui_latch_live_controls:',f'\n        dcb.b {growth-4},0\nui_latch_live_controls:')
(out/'amiga/game/interface_input.s').write_text(src)
subprocess.run([str(root/'.tools/vasm/vasmm68k_mot.exe'),'-Fhunkexe','-kick1hunks','-m68000','-DENHANCED_INTERFACE=1','-L',str(out/'native.lst'),'-o',str(out/'baseline-rally'),'amiga/main.s'],cwd=out,check=True,stdout=subprocess.DEVNULL)
ri,rs=load_image(out/'baseline-rally');assert [len(b) for a,b in ci]==[len(b) for a,b in ri]
# Internal ui_sample labels intentionally differ. External ui_resume branch is explicitly audited.
patches=[(cs['ui_sample'],cs['ui_latch_live_controls'])]
assert cs['ui_resume']==rs['ui_resume']
# Locate the sole branch operand outside sampler. ui_resume is only 36 bytes.
diff=[a+j for (a,c),(b,r) in zip(ci,ri) for j,(x,y) in enumerate(zip(c,r)) if x!=y and not any(lo<=a+j<hi for lo,hi in patches)]
assert len(diff)==1 and cs['ui_resume']<=diff[0]<cs['ui_return_title'], diff
patches.append((diff[0]&~1,(diff[0]&~1)+2))
for name in cs:
 if not (cs['ui_sample']<=cs[name]<cs['ui_latch_live_controls']): assert cs[name]==rs[name],name
report={'growth_bytes':growth,'patch_ranges':patches,'outside_differing_bytes':diff,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'reference_sha256':hashlib.sha256((out/'baseline-rally').read_bytes()).hexdigest(),'external_branch':'ui_resume -> ui_input_draw','unreachable_padding_bytes':growth-4}
(out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
