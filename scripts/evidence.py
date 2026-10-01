"""Local report transactions and conservative, dependency-scoped freshness checks.

Checksums/manifests stay in ignored build/. No ROM, config or capture contents
are copied into public progress output. This is evidence integrity, not a game
model or a replacement test framework.
"""
import ast
import configparser
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parent.parent
TARGET = {'model': 'A500', 'cpu': '68000', 'chipset': 'OCS', 'video': 'PAL',
          'chip_bytes': 524288, 'slow_bytes': 0, 'fast_bytes': 0, 'kickstart': '1.3'}
SCHEMA = 1


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def key(path):
    path = Path(path).absolute()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def digest(path):
    path = Path(path)
    if not path.is_file():
        return None
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def snapshot(paths):
    return {key(p): digest(p) for p in sorted(set(Path(p).absolute() for p in paths))}


def changed(files):
    return [p for p, sha in files.items() if sha is None or digest(ROOT / p) != sha]


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(value, handle, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def python_inputs(entry):
    """Local import closure, plus explicit subprocess generator entry points."""
    pending = [Path(entry)]
    found = set()
    while pending:
        path = pending.pop()
        if path in found or not path.is_file():
            continue
        found.add(path)
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            names = ([node.module] if isinstance(node, ast.ImportFrom) else
                     [i.name for i in node.names] if isinstance(node, ast.Import) else [])
            for name in names:
                if name:
                    candidate = ROOT / 'scripts' / (name.split('.')[0] + '.py')
                    if candidate.is_file():
                        pending.append(candidate)
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if re.fullmatch(r'scripts/[\w-]+\.py', node.value):
                    pending.append(ROOT / node.value)
    return found


def assembly_inputs(entry):
    """Pre-build source closure; generated files are captured at compilation."""
    pending, found = [Path(entry)], set()
    while pending:
        path = pending.pop()
        if path in found or not path.is_file():
            continue
        found.add(path)
        for name in re.findall(r'(?im)\binclude\s+"([^"\r\n]+)"', path.read_text()):
            candidate = ROOT / name
            if not candidate.is_relative_to(ROOT / 'build'):
                pending.append(candidate)
    return found


def reference_inputs(path):
    """Follow existing recipe/phase references and declared media manifests."""
    path = Path(path)
    found = {path}
    if path.suffix != '.json' or not path.is_file():
        return found
    data = json.loads(path.read_text())
    def visit(value):
        if isinstance(value, dict):
            for k, v in value.items():
                if k in ('reference', 'parent_reference', 'initial_phase_reference') and isinstance(v, str):
                    target = ROOT / v
                    if target != path:
                        found.update(reference_inputs(target))
                elif k == 'continuous_parent' and isinstance(v, str):
                    target = ROOT / f'tests/reference/{v}.json'
                    if target != path:
                        found.update(reference_inputs(target))
                elif k == 'manifest' and isinstance(v, str):
                    found.update(reference_inputs(path.parent / v))
                else:
                    visit(v)
        elif isinstance(value, list):
            for v in value:
                visit(v)
    visit(data)
    if data.get('regime') in ('match', 'restarted-serve'):
        # regime_layout validates the extension recipe before accepting its phase.
        name = data['continuous_parent'].replace('-match', '-restart-complete')
        found.update(reference_inputs(ROOT / f'tests/cases/{name}.json'))
    if 'files' in data and isinstance(data['files'], dict):
        # Existing replacement mode manifest stores media in a/.
        found.update(path.parent / 'a' / name for name in data['files'])
    if 'samples' in data:
        for sample in data['samples']:
            frame = sample.get('frame')
            if frame is not None:
                found.update(path.parent / f'f{frame:05d}.{ext}' for ext in ('png', 'ram', 'vram', 'regs'))
    return found


def tool_info():
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini')
    paths = {'python': Path(sys.executable), 'vasm': ROOT / '.tools/vasm/vasmm68k_mot.exe',
             'copperline': Path(config.get('tools', 'copperline', fallback='missing-copperline')),
             'z80asm': ROOT / 'build/tools/z80asm.exe', 'z80dasm': ROOT / 'build/tools/z80dasm.exe'}
    flags = {'python': ['--version'], 'vasm': [], 'copperline': ['--version'],
             'z80asm': ['--version'], 'z80dasm': ['-h']}
    result, inputs = {}, set(paths.values())
    for name, path in paths.items():
        if path.is_file() and path.read_bytes()[:2] == b'#!':
            # Published setup's small Copperline wrapper. Refuse unrecognised
            # wrappers rather than fingerprinting only a launcher script.
            text = path.read_text()
            payload = re.search(r'\$ctennis_tools_dir/([^"\s]+)', text)
            if name != 'copperline' or not payload:
                raise ValueError(f'Unverified tool wrapper: {name}')
            actual = path.parent.parent / payload.group(1)
            inputs.add(actual)
        with tempfile.TemporaryDirectory(prefix='ctennis-version-') as directory:
            try:
                run = subprocess.run([str(path), *flags[name]], cwd=directory,
                                     capture_output=True, text=True, timeout=10)
                lines = (run.stdout + run.stderr).splitlines()
                version = next((line for line in lines if (name.lower() in line.lower() or name == 'z80asm' and 'Z80 assembler version' in line) and re.search(r'\d', line)), None)
            except (OSError, subprocess.TimeoutExpired):
                version = None
        result[name] = {'path': key(path), 'version': version}
    return result, inputs


def inputs_for(kind, runner, case=None):
    if kind in ('build','native-package'):
        # Ordinary assembly consumes only native sources, the assembler and
        # explicit prepared assets. Original-machine tools/ROMs/emulator are
        # test/asset preparation dependencies, not build requirements.
        paths = {ROOT/runner, ROOT/'scripts/native_tools.py',ROOT/'scripts/evidence.py',
                 Path(sys.executable),ROOT/'.tools/vasm/vasmm68k_mot.exe'}
        paths |= assembly_inputs(ROOT/'amiga/gameplay_integration_probe.s')
        paths.add(ROOT/'scripts/build_native_game.py')
        if kind=='native-package':
            paths.update((ROOT/'.tools/python').rglob('*.py'))
            paths.update((ROOT/'.tools/python').glob('amitools-*.dist-info/METADATA'))
        tools={}
        for name,path,flags in [('python',Path(sys.executable),['--version']),
                                ('vasm',ROOT/'.tools/vasm/vasmm68k_mot.exe',[])]:
            result=subprocess.run([str(path),*flags],capture_output=True,text=True,timeout=10)
            version=next(line for line in (result.stdout+result.stderr).splitlines() if name.lower() in line.lower())
            tools[name]={'path':key(path),'version':version}
        return paths,tools
    paths = python_inputs(ROOT / runner) | {ROOT / 'scripts/evidence.py', ROOT / 'config.local.ini'}
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / 'config.local.ini')
    paths.update(Path(config.get('inputs', name, fallback='missing-' + name)) for name in ('cartridge', 'amiga_rom'))
    paths.update(ROOT / 'analysis' / name for name in
                 ('rom-blocks.def', 'rom-symbols.def', 'rom-comments.tsv', 'rom-literal-operands.tsv'))
    entry = ROOT / ('amiga/tests/simulation_harness.s' if kind == 'replay' else 'amiga/gameplay_integration_probe.s')
    paths |= assembly_inputs(entry)
    if kind == 'replay':
        # Names reported mismatches; compared offsets remain in the case recipe.
        paths.add(ROOT / 'tests/state-fields.json')
    for case in ([case] if isinstance(case, str) else case or []):
        recipe = ROOT / 'tests/cases' / (case + '.json')
        paths |= {recipe} if kind == 'mode' else reference_inputs(recipe)
        if kind == 'mode':
            root_reference = ROOT / json.loads(recipe.read_text())['reference']
            if root_reference.exists():
                paths |= reference_inputs(root_reference)
        if case.startswith('movement-'):
            paths.add(ROOT / 'tests/reference/two-player-match.json')
            from movement_reference import MOVEMENT_PHASES
            parent = MOVEMENT_PHASES.get(case)
            if parent:
                paths |= reference_inputs(ROOT / f'tests/cases/{parent}.json')
        if case.startswith('contact-'):
            paths.add(ROOT / 'tests/reference/two-player-rally.json')
        if case in ('p1-title', 'p1-accept-one-player', 'p1-accept-two-player'):
            paths.add(ROOT / 'tests/cases/presentation.json')
            for mode in ('one', 'two') if case.endswith('two-player') else ('one',):
                retained = ROOT / f'tests/reference/presentation/{mode}-player-match/manifest.json'
                paths |= reference_inputs(retained if retained.exists() else ROOT / f'build/reference/mode-{mode}/manifest.json')
        if case.startswith('p3-input') or case == 'control-ownership':
            paths |= reference_inputs(ROOT / 'tests/cases/physical-input.json')
            if '--ownership' in sys.argv:
                paths.update(ROOT / 'build/reference/control-ownership' / n for n in ('reference.json','a.tsv','b.tsv'))
    if kind == 'native-package':
        paths.update((ROOT/'.tools/python').rglob('*.py'))
        paths.update((ROOT/'.tools/python').glob('amitools-*.dist-info/METADATA'))
    if kind in ('presentation', 'round-scenes', 'result-scenes'):
        recipe = json.loads((ROOT / f'tests/cases/{case}.json').read_text())
        if recipe.get('initial_phase_reference'):
            phase = Path(recipe['initial_phase_reference'])
            paths |= reference_inputs(ROOT / f'tests/cases/{phase.stem}.json')
        paths.add(ROOT / 'tests/cases/presentation.json')
        directories = {'tests/reference/presentation', *recipe.get('reference_directories', {}).values()}
        for directory in directories:
            paths |= reference_inputs(ROOT / directory / 'manifest.json')
            # Primary media has its own declared children (original matches).
            # Restart windows live in the explicitly declared supplemental
            # directories, not an invented primary restart child.
            if directory == 'tests/reference/presentation':
                continue
            media = ROOT / directory / recipe['source_case']
            paths |= reference_inputs(media / 'manifest.json')
            if media.exists():
                paths.update(p for p in media.iterdir() if p.is_file())
    if kind == 'audio':
        recipe = json.loads((ROOT / f'tests/cases/{case}.json').read_text())
        paths.add(ROOT / f'tests/reference/{recipe["source_case"]}.json')
        if recipe.get('presentation_case'):
            scene_recipe=ROOT / f'tests/cases/{recipe["presentation_case"]}.json'
            paths |= reference_inputs(scene_recipe)
            scene=json.loads(scene_recipe.read_text())
            paths.add(ROOT / f'tests/reference/{scene["source_case"]}.json')
            paths |= reference_inputs(ROOT / scene['presentation_reference_directory'] / scene['source_case'] / 'manifest.json')
            for source_name in ('one-player-match','two-player-match'):
                paths.add(ROOT / f'tests/reference/{source_name}.json')
        manifest_path = ROOT / recipe['reference']
        if manifest_path.exists():
            entry = json.loads(manifest_path.read_text())['references'][recipe['source_case']]
            entries = list(json.loads(manifest_path.read_text())['references'].values()) if recipe.get('presentation_case') else [entry]
            for item in entries:
                paths.update(manifest_path.parent / item['directory'] / name for name in item['files'])
    if kind == 'live-serve':
        paths.add(ROOT / 'build/reference/source-serve/run_a.tsv')
    if kind == 'ordinary-cadence':
        for mode in ('one', 'two'):
            paths.add(ROOT / f'tests/reference/audio/{mode}-player-match/a/frame-times.tsv')
            paths.add(ROOT / f'tests/reference/{mode}-player-match.json')
    if kind != 'replay':
        paths.update(ROOT / 'build/reference/source-timing' / name for name in
                     ('sprite-f1310.vram', 'sprite-f1310.ram', 'run_a.tsv'))
        title = ROOT / 'tests/reference/presentation/one-player-match/manifest.json'
        paths |= reference_inputs(title if title.exists() else ROOT / 'build/reference/mode-one/manifest.json')
    # Decoder implementations are runtime dependencies of the media checks.
    if kind in ('mode', 'live-serve', 'presentation', 'round-scenes', 'result-scenes'):
        # Pillow registers PNG decoders lazily on the first Image.open().
        from PIL import PngImagePlugin  # noqa: F401
    paths.update(Path(module.__file__) for name, module in list(sys.modules.items())
                 if (name == 'PIL' or name.startswith('PIL.')) and getattr(module, '__file__', None))
    tools, payloads = tool_info()
    return paths | payloads, tools


def compile_manifest(executable, listing):
    """Snapshot actual assembly sources/assets immediately after assembly."""
    text = Path(listing).read_text()
    sources = {ROOT / p for p in re.findall(r'^Source: "([^"\r\n]+)"', text, re.M)}
    assets = {ROOT / p for p in re.findall(r'^\w\w:[0-9A-Fa-f]{8}[^\n]*\bincbin\s+"([^"\r\n]+)"', text, re.M)}
    # Vasm truncates long instruction text. Recover only emitted incbin
    # prefixes, avoiding inactive conditional assets from the source file.
    candidates = {source: set(re.findall(r'(?im)\bincbin\s+"([^"\r\n]+)"', source.read_text()))
                  for source in sources if source.is_file()}
    active_source = None
    for line in text.splitlines():
        context = re.match(r'^Source: "([^"\r\n]+)"', line)
        if context:
            active_source = ROOT / context[1]
        match = re.match(r'^\w\w:[0-9A-Fa-f]{8}.*\bincbin\s+"([^"\r\n]*)$', line)
        if match:
            recovered = {ROOT / name for name in candidates.get(active_source, set())
                         if name.startswith(match[1])}
            if len(recovered) != 1:
                raise ValueError('Truncated compiled incbin cannot be resolved uniquely in its source')
            assets |= recovered
    symbols = sorted(re.findall(r'^([A-Za-z_][\w]*)\s+\d\d:[0-9A-Fa-f]{8}\s*$', text, re.M))
    value = {'files': snapshot(sources | assets | {Path(executable), Path(listing)}),
             'executable': key(executable), 'executable_sha256': digest(executable), 'symbols': symbols}
    atomic_json(str(executable) + '.compile.json', value)
    return value


class ReportRun:
    """A latest invocation replaces the old pass before any fallible work."""
    def __init__(self, reports, kind, subject, startup, paths=(), tools=None):
        self.reports = [Path(p) for p in reports]
        self.meta = {'schema': SCHEMA, 'run_id': uuid.uuid4().hex, 'started_utc': now(),
                     'state': 'incomplete', 'kind': kind, 'subject': subject, 'startup': startup,
                     'target': TARGET, 'environment': {'RUST_LOG': os.environ.get('RUST_LOG')},
                     'command': sys.argv, 'tools': tools or {}, 'files': snapshot(paths)}
        for report in self.reports:
            atomic_json(report, {'passed': False, 'first_difference': None, 'evidence': self.meta})

    def finalize(self, path, report, compiled=(), artifacts=()):
        meta = dict(self.meta, completed_utc=now(), state='complete')
        files = dict(meta['files'])
        for manifest in compiled:
            for name, sha in manifest['files'].items():
                if name in files and files[name] != sha:
                    # Changed source must never be made current by finalizing.
                    report = dict(report, passed=False, evidence_error='Input changed during compilation')
                files.setdefault(name, sha)
        files.update(snapshot(artifacts))
        meta['files'] = files
        meta['compiled_executables'] = {m['executable']: m['executable_sha256'] for m in compiled}
        if self.meta['kind'] in ('build','phase-build'):
            report = dict(report, compiled_symbols=[s for m in compiled for s in m['symbols']])
        meta['changed_during_run'] = changed(files)
        report = dict(report, evidence=meta)
        atomic_json(path, report)

    def abort(self, error):
        state = 'interrupted' if isinstance(error, KeyboardInterrupt) else 'failed'
        for path in self.reports:
            atomic_json(path, {'passed': False, 'first_difference': None, 'error': str(error),
                              'evidence': dict(self.meta, state=state, completed_utc=now())})


def status(path, subject=None, full=False, fresh_since=None):
    """Read-only classification; no existing report is upgraded/rebaselined."""
    path = Path(path)
    if not path.exists():
        return {'status': 'not run', 'freshness': 'none'}
    try:
        report = json.loads(path.read_text())
    except (OSError, ValueError):
        return {'status': 'stale', 'freshness': 'unverified', 'reason': 'Unreadable report'}
    if not isinstance(report, dict):
        return {'status': 'stale', 'freshness': 'unverified', 'reason': 'Malformed report'}
    meta = report.get('evidence', {})
    if not isinstance(meta, dict):
        return {'status': 'stale', 'freshness': 'unverified', 'reason': 'Malformed provenance'}
    if meta.get('schema') != SCHEMA:
        return {'status': 'stale', 'freshness': 'unverified', 'reason': 'Missing required provenance'}
    if meta.get('state') in ('incomplete', 'interrupted'):
        return {'status': 'interrupted', 'freshness': 'incomplete', 'reason': 'Latest invocation did not finalize'}
    try:
        stamp = dt.datetime.fromisoformat(meta['started_utc'])
        if stamp.tzinfo is None:
            raise ValueError('Timezone missing')
    except (KeyError, TypeError, ValueError):
        return {'status': 'stale', 'freshness': 'unverified', 'reason': 'Missing invocation timestamp'}
    freshness = ('fresh' if fresh_since and stamp >= dt.datetime.fromisoformat(fresh_since) else 'reused')
    if meta.get('state') == 'failed':
        return {'status': 'failed', 'freshness': freshness, 'reason': report.get('error')}
    if (not isinstance(meta.get('started_utc'), str)
            or not isinstance(meta.get('files'), dict) or not isinstance(meta.get('tools'), dict)
            or not isinstance(meta.get('compiled_executables'), dict)
            or not isinstance(meta.get('changed_during_run', []), list)
            or not isinstance(meta.get('optional_inputs_absent', []), list)
            or meta.get('state') != 'complete' or not meta.get('files') or not meta.get('tools')
            or not meta.get('compiled_executables')
            or any(not isinstance(t, dict) or not t.get('version') for t in meta.get('tools', {}).values())
            or meta.get('target') != TARGET or meta.get('environment', {}).get('RUST_LOG') != 'info'):
        return {'status': 'stale', 'freshness': 'unverified', 'reason': 'Incomplete target/tool/input provenance'}
    if any(not isinstance(p, str) for p in list(meta['files']) + list(meta['compiled_executables']) + meta.get('optional_inputs_absent', [])):
        return {'status': 'stale', 'freshness': 'unverified', 'reason': 'Malformed dependency paths'}
    differences = [p for p in meta.get('optional_inputs_absent', []) if (ROOT / p).exists()]
    differences += changed(meta['files']) + changed(meta['compiled_executables']) + meta.get('changed_during_run', [])
    if differences:
        return {'status': 'stale', 'freshness': 'invalidated', 'changed_dependencies': sorted(set(differences))}
    if report.get('subject') is not None and report['subject'] != meta.get('subject'):
        return {'status': 'stale', 'freshness': 'incompatible', 'reason': 'Recorded subject disagrees with result'}
    if report.get('executable_sha256') not in meta['compiled_executables'].values():
        return {'status': 'stale', 'freshness': 'unverified', 'reason': 'Executable provenance mismatch'}
    if subject and meta.get('subject') != subject:
        return {'status': 'stale', 'freshness': 'incompatible', 'reason': 'Subject mismatch'}
    if subject == 'maintained' and meta.get('kind') == 'replay' and report.get('entry_point') != 'game_source_tick':
        return {'status': 'stale', 'freshness': 'incompatible', 'reason': 'Maintained dispatcher entry point missing'}
    if full and (report.get('full_replay_executed') is not True or
                 report.get('updates') != report.get('reference_updates')
                 or not isinstance(report.get('updates'), int) or report['updates'] <= 0):
        return {'status': 'failed', 'freshness': 'compatible', 'reason': 'Partial replay cannot establish full acceptance'}
    if report.get('passed') is True and (report.get('first_difference') is not None or
            'updates_matched' in report and report['updates_matched'] != report.get('updates')):
        return {'status': 'failed', 'freshness': freshness, 'reason': 'Pass disagrees with observed extent/mismatch'}
    return {'status': 'passed' if report.get('passed') is True else 'failed', 'freshness': freshness,
            'started_utc': meta.get('started_utc'), 'startup': meta.get('startup'),
            'subject': meta.get('subject'), 'kind': meta.get('kind'), 'matched': report.get('updates_matched'),
            'executed': report.get('updates'), 'reference': report.get('reference_updates'),
            'first_difference': report.get('first_difference')}


def tracked_call(reports, kind, subject, startup, runner, case, action, executables):
    """Small adapter for existing runners; their assertion schemas stay intact."""
    transaction = ReportRun(reports, kind, subject, startup)
    try:
        paths, tools = inputs_for(kind, runner, case)
        optional = []
        if kind == 'mode':
            recipe = json.loads((ROOT / 'tests/cases' / (case + '.json')).read_text())
            optional.append(ROOT / recipe['reference'])
        if kind != 'replay':
            optional.append(ROOT / 'tests/reference/presentation/one-player-match/manifest.json')
        transaction.meta.update(files=snapshot(paths), tools=tools,
                                optional_inputs_absent=[key(p) for p in optional if not p.exists()])
        result = action()
        for path in transaction.reports:
            report = json.loads(path.read_text())
            artifacts = []
            for name in ('capture', 'screenshot', 'gif', 'audio_wav', 'scored_screenshot','adf','startup_sequence'):
                value = report.get(name)
                if isinstance(value, str):
                    artifacts.append(ROOT / value)
            if kind in ('presentation', 'round-scenes', 'result-scenes', 'audio'):
                capture_path = Path(report['capture_report_path'])
                artifacts.append(capture_path)
                mutations = list(report.get('hardware_mutations', []))
                if kind == 'audio':
                    artifacts.append(Path(report['native_wav']))
                    mutations += [m for m in (report.get('mutation'), report.get('disconnected_waveform_mutation')) if m]
                for mutation in mutations:
                    changed_capture = Path(mutation['capture_report_path'])
                    if mutation.get('native_wav'):
                        artifacts.append(Path(mutation['native_wav']))
                    changed_exe = changed_capture.parent / 'native-application'
                    changed_manifest = Path(str(changed_exe) + '.compile.json')
                    artifacts.extend([changed_capture, changed_manifest, changed_exe])
                    artifacts.extend(ROOT / name for name in
                                     json.loads(changed_manifest.read_text())['files'])
                    artifacts.extend(p for p in changed_capture.parent.iterdir()
                                     if p.suffix in ('.png', '.log'))
                artifacts.extend(p for p in capture_path.parent.iterdir()
                                 if p.suffix in ('.png', '.log'))
            exes = executables(path, report)
            for exe in exes:
                if kind == 'replay':
                    artifacts.append(Path(str(exe) + '.log'))
                elif kind in ('mode', 'physical', 'ordinary-round', 'ordinary-cadence'):
                    artifacts.append(Path(exe).parent / ('emulator.log' if kind in ('ordinary-round', 'ordinary-cadence') else 'copperline.log'))
                    if kind == 'ordinary-cadence':
                        artifacts.extend(p for p in Path(exe).parent.iterdir()
                                         if p.suffix in ('.png', '.jsonl', '.record', '.json'))
                    if kind == 'mode':
                        artifacts.extend(Path(exe).parent / (r['stage'] + '.png')
                                         for r in report.get('observations', []) if 'pixel_sha256' in r)
                elif kind == 'live-serve':
                    artifacts.extend(Path(exe).parent / n for n in ('serve.log', 'serve-scored.log'))
            mutation = report.get('mutation')
            if isinstance(mutation, dict) and isinstance(mutation.get('capture'), str):
                artifacts.append(ROOT / mutation['capture'])
            if report.get('mutation_executable_sha256'):
                mutated = Path(str(exes[0]) + '-mutated')
                artifacts.extend([mutated, Path(str(mutated) + '.log')])
            manifests = [json.loads(Path(str(exe) + '.compile.json').read_text()) for exe in exes]
            transaction.meta['runner'] = runner
            if len(manifests) == 1:
                report.setdefault('executable_sha256', manifests[0]['executable_sha256'])
            if kind in ('build','phase-build'):
                report['passed'] = True
            transaction.finalize(path, report, manifests, artifacts)
        return result
    except BaseException as error:
        transaction.abort(error)
        raise
