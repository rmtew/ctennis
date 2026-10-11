"""Manifest-bound supplemental CPU boundary proof; no native observer run."""
import json
import os

from build_match_core import build
from build_native_game import build as build_native
from check_shared_core_bytes import run as original_bytes
from match_core_cpu import cpu_tool_inputs
from native_evidence import (ReportRun, atomic_json, compile_manifest, digest,
                             inputs_for, snapshot, status)
from native_tools import ROOT
from predictor_boundary_proof import run, required_extent
from predictor_proof import byte_audit


def main():
    output = ROOT/'build/tests/predictor-boundaries-cpu/report.json'
    transaction = ReportRun([output], 'predictor-boundaries-cpu', 'maintained-native', 'actual68000CPU')
    try:
        paths, tools = inputs_for('build', 'scripts/run_predictor_boundaries.py')
        cpu_paths, tools['machine68k'] = cpu_tool_inputs()
        transaction.meta.update(files=snapshot(paths|cpu_paths), tools=tools,
                                runner='scripts/run_predictor_boundaries.py')
        transaction.meta['environment']['PYTHONPATH'] = os.environ.get('PYTHONPATH')
        executable, listing = build(); build_native()
        native = ROOT/'build/amiga/interfaces/enhanced/baseline-rally'
        assert digest(executable) == '788a827f1041edafbf0e83815967ed386802256380f8998fab2f575477282655'
        assert digest(native) == 'f24bb18c1a8b1443a67d951be7bdc77cca8f6578be65cfb7ea4b08d017e95a66'
        validation = run(executable, output.parent/'raw')
        validation['original_core_bytes'] = original_bytes()
        validation['predictor_bytes'] = byte_audit(executable, native)
        atomic_json(output.parent/'results-unvalidated.json', validation)
        transaction.finalize(output, dict(passed=True, execution='actual-68000-cpu-only',
            executable_sha256=digest(executable), native_executable_sha256=digest(native), validation=validation),
            [compile_manifest(executable, listing), compile_manifest(native, native.parent/'native.lst')],
            list((output.parent/'raw').glob('*.json'))+[output.parent/'results-unvalidated.json'])
        verdict = status(output)
        assert verdict['status'] == 'passed', verdict
        assert required_extent(json.loads(output.read_text()))
        print(json.dumps(dict(passed=True, report=str(output), sha256=digest(output))), flush=True)
    except BaseException as error:
        transaction.abort(error); raise


if __name__ == '__main__':
    main()
