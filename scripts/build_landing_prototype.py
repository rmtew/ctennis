"""Assemble a test-only query beside the unchanged shared core."""
from pathlib import Path
from native_tools import ROOT, ASSEMBLER, run, verify_build_tools
from native_evidence import compile_manifest


def build():
    verify_build_tools()
    directory=ROOT/'build/tests/guarded-landing-cpu'
    directory.mkdir(parents=True,exist_ok=True)
    source=directory/'standalone-landing.s'
    source.write_text((ROOT/'amiga/standalone.s').read_text()+
        '\n        section landing_prototype,code\n        include "scripts/fixtures/guarded_landing.s"\n')
    executable,listing=directory/'landing-core',directory/'landing-core.lst'
    run([str(ASSEMBLER),'-Fhunkexe','-kick1hunks','-m68000','-L',str(listing),
        '-o',str(executable),str(source.relative_to(ROOT))])
    return executable,listing,compile_manifest(executable,listing)


if __name__=='__main__':
    print(build()[0])
