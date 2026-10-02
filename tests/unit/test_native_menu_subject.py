"""Actual boot variant must differ from its symbol-rich debug identity."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from run_enhanced_menu_tests import execution_subject, sampled_joystick_takeover

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

    def test_takeover_waits_for_physical_sample_and_keeps_state_assertion(self):
        from unittest.mock import Mock
        until=Mock();number=Mock(side_effect=[0,255,32,0])
        rows=sampled_joystick_takeover(until,number,lambda:b'unchanged',1,2)
        self.assertEqual([r['physical_p1_bits'] for r in rows],[0,32])
        self.assertEqual(until.call_count,4)
        with self.assertRaisesRegex(AssertionError,'did not take over'):
            sampled_joystick_takeover(until,Mock(side_effect=[32,255]),lambda:b'unchanged',1,2)
        with self.assertRaisesRegex(AssertionError,'changed native state'):
            sampled_joystick_takeover(until,Mock(side_effect=[32,0]),Mock(side_effect=[b'a',b'b']),1,2)
        with self.assertRaisesRegex(AssertionError,'bounded'):
            sampled_joystick_takeover(until,Mock(side_effect=[0,255]*2),lambda:b'unchanged',1,2,limit=2)
