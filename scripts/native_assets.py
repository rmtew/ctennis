"""Validate explicit versioned native inputs and emit two authored include outputs."""
import hashlib
import json
from native_tools import ROOT


def prepare():
    manifest = json.loads((ROOT / 'assets/native/manifest.json').read_text())
    if manifest['schema'] != 2:
        raise ValueError('Unsupported native asset manifest')
    declared = set()
    for item in manifest['files']:
        path = ROOT / item['path']
        if not path.is_relative_to(ROOT / 'assets/native') or item['path'] in declared:
            raise ValueError('Invalid native asset path')
        declared.add(item['path'])
        if not path.is_file():
            raise FileNotFoundError('Missing versioned native input: ' + item['path'])
        if path.stat().st_size != item['size_bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Incompatible versioned native input: ' + item['path'])
    actual = {str(p.relative_to(ROOT)) for p in (ROOT / 'assets/native').rglob('*')
              if p.is_file() and p.name not in ('README.md', 'manifest.json')}
    if actual != declared:
        raise ValueError('Undeclared or missing native asset files')
    recording = json.loads((ROOT / 'assets/interface/demo-inputs.json').read_text())
    packets = recording['packets']
    if recording['schema'] != 2 or sum(n for n, mask in packets) != recording['frames'] or any(
            type(n) is not int or not 0 < n < 65536 or type(mask) is not int or not 0 <= mask < 64
            for n, mask in packets):
        raise ValueError('Invalid native physical input recording')
    directory = ROOT / 'build/native'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'demo-inputs.i').write_text('ui_demo_packets:\n' + ''.join(
        f'        dc.w {n},{mask}\n' for n, mask in packets) + '        dc.w 0\n')
    return manifest


if __name__ == '__main__':
    manifest = prepare()
    print('Validated', len(manifest['files']), 'versioned native inputs')
