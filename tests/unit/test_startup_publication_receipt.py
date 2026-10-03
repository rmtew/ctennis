import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import run_startup_publication_tests as startup

class StartupReceiptTests(unittest.TestCase):
    def test_failure_and_interrupt_supersede_previous_pass(self):
        for error,state in [(RuntimeError('package failed'),'failed'),(KeyboardInterrupt(),'interrupted')]:
            with self.subTest(state=state),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);report=root/'build/tests/startup-publication/report.json'
                report.parent.mkdir(parents=True);report.write_text('{"passed":true}')
                def failing_package(**kwargs):
                    self.assertEqual(json.loads(report.read_text()),{'passed':False,'state':'incomplete'})
                    raise error
                with patch.object(startup,'ROOT',root),patch.object(startup,'package',side_effect=failing_package):
                    with self.assertRaises(type(error)):startup.run()
                result=json.loads(report.read_text())
                self.assertFalse(result['passed']);self.assertEqual(result['state'],state)
