import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from coherent_capture_archive import archive_previous
from native_evidence import digest

RUN='0123456789abcdef0123456789abcdef'


class CoherentArchive(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)/'coherent-contact-native-pal'

    def failed_capture(self):
        self.directory.mkdir()
        report=dict(passed=False,error='dropped_events',evidence=dict(run_id=RUN,state='failed'))
        (self.directory/'report.json').write_text(json.dumps(report))
        (self.directory/'literal-rpc.jsonl.gz').write_bytes(b'original literal bytes')
        (self.directory/'emulator.log').write_bytes(b'original emulator log\n')
        return {p.name:(p.read_bytes(),digest(p)) for p in self.directory.iterdir()}

    def test_failed_receipt_raw_and_log_preserved_exactly(self):
        before=self.failed_capture();target=archive_previous(self.directory)
        self.assertFalse(self.directory.exists())
        self.assertEqual(target.name,RUN)
        for name,(data,sha) in before.items():
            self.assertEqual((target/name).read_bytes(),data)
            self.assertEqual(digest(target/name),sha)
        manifest=json.loads((target/'archive-manifest.json').read_text())
        self.assertEqual(manifest['files'],{name:v[1] for name,v in before.items()})
        self.assertEqual(manifest['receipt_state'],'failed')
        self.assertFalse(manifest['receipt_passed'])
        self.assertFalse(manifest['acceptance_upgraded'])

    def test_missing_and_empty_skip(self):
        self.assertIsNone(archive_previous(self.directory))
        self.directory.mkdir()
        self.assertIsNone(archive_previous(self.directory))
        self.assertTrue(self.directory.exists())
        self.assertFalse((self.directory.parent/(self.directory.name+'-attempts')).exists())

    def test_collision_rejects_without_changing_previous_bytes(self):
        before=self.failed_capture()
        target=self.directory.parent/(self.directory.name+'-attempts')/RUN
        target.mkdir(parents=True);(target/'already').write_bytes(b'keep')
        with self.assertRaises(FileExistsError):archive_previous(self.directory)
        for name,(data,_) in before.items():self.assertEqual((self.directory/name).read_bytes(),data)
        self.assertEqual((target/'already').read_bytes(),b'keep')

    def test_missing_run_identity_blocks_latest_overwrite(self):
        self.directory.mkdir();(self.directory/'report.json').write_text('{}')
        (self.directory/'literal-rpc.jsonl.gz').write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError,'valid run identity'):archive_previous(self.directory)
        self.assertEqual((self.directory/'literal-rpc.jsonl.gz').read_bytes(),b'keep')


if __name__=='__main__':unittest.main()
