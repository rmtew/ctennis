"""Actual boot variant must differ from its symbol-rich debug identity."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from run_enhanced_menu_tests import execution_subject

class MenuSubjectTests(unittest.TestCase):
    def test_release_boot_binding_and_stale_package_debug_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);dev=root/'dev';release=root/'release';adf=root/'disk.adf'
            dev.write_bytes(b'payload+symbols');release.write_bytes(b'payload');adf.write_bytes(b'packaged release')
            (root/'native.lst').write_text('debug symbols')
            sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
            report={'executable':'release','executable_sha256':sha(release),
                    'adf':'disk.adf','adf_sha256':sha(adf),
                    'release':{'development_executable_sha256':sha(dev)}}
            with patch('run_enhanced_menu_tests.ROOT',root):
                self.assertEqual(execution_subject(dev)[0],dev)
                subject,debug=execution_subject(dev,report)
                self.assertEqual(subject,release)
                self.assertEqual(debug['executable_sha256'],sha(dev))
                self.assertNotEqual(sha(subject),debug['executable_sha256'])
                release.write_bytes(b'wrong')
                with self.assertRaisesRegex(ValueError,'release executable'):execution_subject(dev,report)
                release.write_bytes(b'payload');adf.write_bytes(b'wrong')
                with self.assertRaisesRegex(ValueError,'ADF'):execution_subject(dev,report)
                adf.write_bytes(b'packaged release');dev.write_bytes(b'wrong')
                with self.assertRaisesRegex(ValueError,'debug source'):execution_subject(dev,report)
