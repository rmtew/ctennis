"""Native-only report transactions and conservative dependency freshness.

Reuses the established receipt and compiled-byte integrity logic. No historical
source recipes, cartridge fingerprints, emulator adapters or aggregate gates.
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
from native_tools import ROOT, ASSEMBLER

TARGET = {'model': 'A500', 'cpu': '68000', 'chipset': 'OCS', 'video': 'PAL',
          'chip_bytes': 524288, 'slow_bytes': 0, 'fast_bytes': 0, 'kickstart': '1.3'}
SCHEMA = 2

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
             'executable': key(executable), 'executable_sha256': digest(executable), 'symbols': symbols,
             'interface_flavor': 'enhanced' if 'game_enhanced_interface' in symbols else 'original'}
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
        flavors = {m.get('interface_flavor') for m in compiled}
        if len(flavors)==1 and None not in flavors:
            flavor=next(iter(flavors))
            if report.get('interface_flavor',flavor)!=flavor:
                report=dict(report,passed=False,evidence_error='Compiled interface flavor mismatch')
            report=dict(report,interface_flavor=flavor)
            meta['interface_flavor']=flavor
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

def status(path, subject=None, full=False, fresh_since=None, interface_flavor=None):
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
    if interface_flavor and (meta.get('interface_flavor') != interface_flavor
                             or report.get('interface_flavor') != interface_flavor):
        return {'status':'stale','freshness':'incompatible','reason':'Interface flavor mismatch or unverified'}
    if subject and meta.get('subject') != subject:
        return {'status': 'stale', 'freshness': 'incompatible', 'reason': 'Subject mismatch'}
    if subject == 'maintained' and meta.get('kind') == 'replay' and report.get('entry_point') != 'game_tick_dispatch':
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

def inputs_for(kind, runner, case=None):
    paths = python_inputs(ROOT / runner) | assembly_inputs(ROOT / 'amiga/main.s')
    paths |= {ROOT / 'scripts/native_evidence.py', ROOT / 'tools.lock.json', Path(sys.executable), ASSEMBLER}
    paths.update((ROOT / 'assets').rglob('*'))
    paths.update((ROOT / 'tests/fixtures/native-demo').rglob('*'))
    tools = {}
    entries = [('python', Path(sys.executable), ['--version']), ('vasm', ASSEMBLER, [])]
    if kind not in ('build', 'native-package'):
        config = configparser.ConfigParser(interpolation=None)
        config.read(ROOT / 'config.local.ini')
        paths.add(ROOT / 'config.local.ini')
        # Kickstart is an emulator input only, never a build/package input.
        paths.add(Path(config.get('inputs', 'amiga_rom', fallback='missing-kickstart')))
        entries.append(('copperline', Path(config.get('tools', 'copperline', fallback='missing-copperline')), ['--version']))
    if kind in ('native-feedback','native-contract','native-scoreboard','native-demo'):
        import PIL
        from PIL import PngImagePlugin
        lock = json.loads((ROOT / 'tools.lock.json').read_text())
        if PIL.__version__ != lock['pillow_version']:
            raise ValueError('Use pinned Pillow ' + lock['pillow_version'])
        paths.update(Path(PIL.__file__).parent.rglob('*.py'))
        paths.update(Path(PIL.__file__).parent.glob('*.so'))
        tools['pillow'] = {'version': PIL.__version__, 'path': key(Path(PIL.__file__).parent)}
    if kind == 'native-package':
        paths.update((ROOT / '.tools/python').rglob('*.py'))
        paths.update((ROOT / '.tools/python').glob('amitools-*.dist-info/METADATA'))
    for name, path, flags in entries:
        paths.add(path)
        if path.is_file() and path.read_bytes()[:2] == b'#!':
            match = re.search(r'\$ctennis_tools_dir/([^"\s]+)', path.read_text())
            if name != 'copperline' or not match:
                raise ValueError('Unverified native tool wrapper: ' + name)
            paths.add(path.parent.parent / match.group(1))
        with tempfile.TemporaryDirectory(prefix='ctennis-version-') as directory:
            result = subprocess.run([str(path), *flags], cwd=directory, capture_output=True, text=True, timeout=10)
        version = next((line for line in (result.stdout + result.stderr).splitlines()
                        if name.lower() in line.lower() and re.search(r'\d', line)), None)
        if not version:
            raise ValueError('Missing native tool version: ' + name)
        tools[name] = {'path': key(path), 'version': version}
    return {p for p in paths if not p.is_dir()}, tools


def tracked_call(reports, kind, subject, startup, runner, case, action, executables):
    transaction = ReportRun(reports, kind, subject, startup)
    try:
        paths, tools = inputs_for(kind, runner, case)
        transaction.meta.update(files=snapshot(paths), tools=tools, runner=runner,
                                commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
        result = action()
        for path in transaction.reports:
            report = json.loads(path.read_text())
            exes = [Path(exe) for exe in executables(path, report)]
            manifests = [json.loads(Path(str(exe) + '.compile.json').read_text()) for exe in exes]
            artifacts = []
            for name in ('capture', 'screenshot', 'audio_wav', 'adf', 'startup_sequence'):
                value = report.get(name)
                if isinstance(value, str):
                    artifacts.append(ROOT / value)
            for directory in {Path(path).parent, *(exe.parent for exe in exes)}:
                artifacts.extend(p for p in directory.iterdir() if p.is_file()
                                 and p.suffix in ('.png', '.log', '.jsonl', '.record', '.wav'))
            for control in report.get('compiled_fault_controls', []):
                directory = ROOT / control['artifact_directory']
                directory.resolve().relative_to((ROOT / 'build').resolve())
                artifacts.extend(p for p in directory.rglob('*') if p.is_file())
            if len(manifests) == 1:
                report.setdefault('executable_sha256', manifests[0]['executable_sha256'])
            if kind == 'build':
                report['passed'] = True
            transaction.finalize(path, report, manifests, artifacts)
        return result
    except BaseException as error:
        transaction.abort(error)
        raise
