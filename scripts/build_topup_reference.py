"""Private PR48 native reference, padded only at unreachable function tails."""
import hashlib,json,pathlib,shutil,subprocess
from build_match_core import load_image

root=pathlib.Path(__file__).resolve().parent.parent
candidate=root/'build/amiga/interfaces/enhanced/baseline-rally'
ci,cs=load_image(candidate)
out=root/'build/tests/topup-padded-pr48'
out.mkdir(exist_ok=False)
shutil.copytree(root/'amiga',out/'amiga')
for name in ('build','assets'):(out/name).symlink_to(root/name,target_is_directory=True)
regions=[('preview.s','game_preview_step','game_preview_release_current'),
         ('tutorial_deadline.s','tutorial_background','tutorial_background_class')]
sources={name:subprocess.check_output(['git','show','8b99f179:amiga/game/'+name],cwd=root,text=True) for name,_,_ in regions}
pads={name:0 for name,_,_ in regions}
for iteration in range(8):
    for name,_,end in regions:
        text=sources[name].replace('\n'+end+':',f'\n        dcb.b {pads[name]},0\n'+end+':')
        (out/'amiga/game'/name).write_text(text)
    subprocess.run([str(root/'.tools/vasm/vasmm68k_mot.exe'),'-Fhunkexe','-kick1hunks','-m68000','-DENHANCED_INTERFACE=1','-L',str(out/'native.lst'),'-o',str(out/'baseline-rally'),'amiga/main.s'],cwd=out,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    ri,rs=load_image(out/'baseline-rally')
    if all(rs[end]==cs[end] for _,_,end in regions):break
    for name,_,end in regions:
        pads[name]+=cs[end]-rs[end]
        assert pads[name]>=0 and pads[name]%2==0
else:raise AssertionError('Padding did not converge')
patches=[(cs[begin],cs[end]) for _,begin,end in regions]
assert [(a,len(b)) for a,b in ci]==[(a,len(b)) for a,b in ri]
for name,address in rs.items():
    if not any(lo<=address<hi for lo,hi in patches):assert cs[name]==address,name
outside=[a+j for (a,c),(b,r) in zip(ci,ri) for j,(x,y) in enumerate(zip(c,r)) if x!=y and not any(lo<=a+j<hi for lo,hi in patches)]
assert not outside,outside[:20]
audit=dict(schema=1,base_commit='8b99f1798801c2e4834cd548afa42ec8a8b917e0',candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),reference_sha256=hashlib.sha256((out/'baseline-rally').read_bytes()).hexdigest(),patch_ranges=patches,unreachable_padding=pads,loaded_bytes_outside_patch_equal=True,all_other_symbols_equal=True,source_sha256={n:hashlib.sha256(s.encode()).hexdigest() for n,s in sources.items()},hunk_sizes=[len(b) for a,b in ci])
(out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit))
