"""Independent counterexamples to broad title exemptions or clock rebasing."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from native_setup_observation import SetupObserver
from native_clock import INTERVAL_CCK

class SetupPolicyTests(unittest.TestCase):
    def observer(self,region):
        observer=SetupObserver.__new__(SetupObserver);observer.regions=[region];observer.pending=None
        return observer
    def test_gameplay_cannot_use_setup_catchup_allowance(self):
        region={'callback':1,'page':0,'work_cck':220000,'lifecycle_at_entry':2,'gameplay_writes':[]}
        rows=[{'callback':n,'entry':{'cck':t},'completion':{'cck':t+7000},'lifecycle':1 if n==3 else 2} for n,t in enumerate([600,227000,236000,246000,255000],1)]
        rows[0]['completion']['cck']=225000
        result=self.observer(region).proposal(rows,0)
        self.assertFalse(result['diagnostic_passed'])
        self.assertTrue(any(row['callback']==3 for row in result['strict_nonsetup_failures']))
    def test_complete_timer_wrap_debt_must_not_be_rebased(self):
        region={'callback':1,'page':1,'work_cck':350000,'lifecycle_at_entry':2,'gameplay_writes':[]}
        rows=[{'callback':n,'entry':{'cck':float((n-1)*INTERVAL_CCK)+327700},'completion':{'cck':float((n-1)*INTERVAL_CCK)+335000},'lifecycle':2} for n in range(1,15)]
        result=self.observer(region).proposal(rows,0)
        self.assertFalse(result['diagnostic_passed'])
        self.assertTrue(any(row['field']=='setup debt not recovered within bound' for row in result['issues']))
        self.assertTrue(result['strict_nonsetup_failures'])
