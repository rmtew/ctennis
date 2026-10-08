"""Validate the preserved PAL execution after its sole activity-count gate fix.

No emulator or simulation executes. The original campaign stays failed.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from preview_native_extent import required_preview_native_extent

ROOT=Path(__file__).resolve().parents[1]
SOURCE_SHA='8f31716c571ca5fea05b7f1eebc621b2d523ea00dc885ea1c790a7f07e361f87'
SOURCE_COMMIT='4550f3d05ce2bf4a7f5d426c81dff863ecbba9fa'
SOURCE_DIR=ROOT/'build/acceptance/campaigns/4d8f6f5f8685498095c52a36e304b273/attempts/preview-native-pal/000002'
GATE='scripts/preview_native_extent.py'
OLD="integer(outside.get('count'),1) or outside['count']!=len(outside['writes'])"
NEW="integer(outside.get('count'),0) or outside['count']!=len(outside['writes'])"


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def gate_projection(current,expected):
    assert current.count(NEW)==1 and OLD not in current,'Unexpected validation correction'
    restored=current.replace(NEW,OLD).encode()
    assert hashlib.sha256(restored).hexdigest()==expected,'Validator changed beyond the one count predicate'


ARCHIVE_NAMES={'preview-native.compile.json','report.json','preview-native.lst','rpc.jsonl.gz',
    'emulator.log','native-results-unvalidated.json','main-preview-observer.s','receipt-unvalidated.json',
    'events.jsonl.gz','preview-native','observations-unvalidated.json'}


def archive_coverage(archive,files):
    assert archive['commit']==SOURCE_COMMIT,'Archive belongs to another execution'
    rows=archive['files']
    assert len(rows)==11 and {Path(r['archive']).name for r in rows}==ARCHIVE_NAMES,'Incomplete archived case coverage'
    for row in rows:
        name=Path(row['archive']).name
        assert row['archive']==str((SOURCE_DIR/'failed-artifacts'/name).relative_to(ROOT))
        assert row['source']==str(Path('build/tests/preview-native-pal')/name)
        if name=='report.json':assert row['sha256']==SOURCE_SHA
        elif name!='receipt-unvalidated.json':assert files[row['source']]==row['sha256'],'Archive differs from receipt-bound artifact'


def validate():
    source=SOURCE_DIR/'failed-artifacts/report.json'
    assert digest(source)==SOURCE_SHA,'Preserved execution receipt changed'
    report=json.loads(source.read_text());meta=report['evidence'];checks={}
    completion=SOURCE_DIR/'completion.json';completed=json.loads(completion.read_text())
    assert completed['state']=='failed' and completed['validation_error']=='Required case extent absent'
    assert completed['provenance']['commit']==SOURCE_COMMIT
    assert meta['state']=='complete' and report['passed'] is True
    files=meta['files'];current_gate=(ROOT/GATE).read_text()
    gate_projection(current_gate,files[GATE])
    for name,expected in files.items():
        actual=digest(ROOT/name)
        if name==GATE:
            checks[name]=dict(recorded_sha256=expected,current_sha256=actual,compatibility='exact one-predicate correction')
        else:
            assert actual==expected,('Consumed file drift',name)
            checks[name]=dict(sha256=actual,matched=True)
    for name,tool in meta['tools'].items():
        assert tool['path'] in files,('Tool lacks recorded binary binding',name)
        assert digest(ROOT/tool['path'])==files[tool['path']]
    products=meta['compiled_executables']
    assert len(products)==3 and report['executable_sha256'] in products.values()
    for name,expected in products.items():assert digest(ROOT/name)==expected,('Compiled product drift',name)
    archive=json.loads((SOURCE_DIR/'failure-archive-audit.json').read_text())
    archive_coverage(archive,files)
    raw={}
    for item in archive['files']:
        path=ROOT/item['archive']
        assert digest(path)==item['sha256'] and path.stat().st_size==item['bytes']
        raw[str(path.relative_to(ROOT))]=dict(sha256=item['sha256'],bytes=item['bytes'])
    outside=report['preview_native_validation']['outside_publication']
    assert type(outside['count']) is int and outside['count']==0 and outside['writes']==[]
    assert required_preview_native_extent('preview-native-pal',report),'Corrected required extent failed'
    return dict(schema=1,passed=True,acceptance_passed=False,
        execution='validation-only; reused preserved PAL execution; no emulator or core execution',
        scope='Corrected selective PAL required extent; independent completed evidence review required; no full native gate',
        runtime_commit=SOURCE_COMMIT,
        validation_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        original_report=dict(path=str(source.relative_to(ROOT)),sha256=SOURCE_SHA),
        original_failed_completion=dict(path=str(completion.relative_to(ROOT)),sha256=digest(completion),preserved=True),
        original_start=dict(path=str((SOURCE_DIR/'started.json').relative_to(ROOT)),sha256=digest(SOURCE_DIR/'started.json')),
        target=report['target'],required_extent=True,
        validator=dict(path=GATE,sha256=digest(ROOT/GATE),recorded_sha256=files[GATE],
            correction='outside-publication count >= 1 becomes count >= 0; exact rules, count/list equality and all guards retained'),
        validation_writer=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=digest(Path(__file__))),
        consumed_inputs=checks,tools=meta['tools'],compiled_executables=products,archived_artifacts=raw,
        original_campaign_state='failed; unchanged')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();output=args.output.resolve()
    assert output.is_relative_to((ROOT/'build/tests/preview-native-pal-validation').resolve()),'Use the separate PAL validation directory'
    protected={p.resolve() for p in (SOURCE_DIR/'failed-artifacts').iterdir() if p.is_file()}
    protected.add((SOURCE_DIR/'completion.json').resolve());protected.add((SOURCE_DIR/'started.json').resolve())
    assert output not in protected,'Validation must use a separate output'
    result=validate();output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,execution=result['execution'],output=str(output),sha256=digest(output),inputs=len(result['consumed_inputs']))))


if __name__=='__main__':main()
