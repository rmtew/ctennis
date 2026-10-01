"""Delivery observations must verify relocated bytes, not a program name."""
import sys,struct,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from native_hunk import loaded_hunks

class LoadedHunkTests(unittest.TestCase):
    def check_image(self, changed=False, block=1004):
        words=[1011,0,2,0,1,1,1,1001,1,16,block,1,1,0,0,1010,1002,1,5,1010]
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'native';path.write_bytes(struct.pack('>'+str(len(words))+'I',*words))
            actual={0x100:struct.pack('>I',0x210+int(changed)),0x200:struct.pack('>I',5)}
            return loaded_hunks(path,[{'start':0x100,'size':4},{'start':0x200,'size':4}],lambda a,n:actual[a])
    def test_actual_relocation_matches(self):
        self.assertTrue(all(h['matched'] for h in self.check_image()))
    def test_same_program_name_wrong_loaded_bytes_rejected(self):
        with self.assertRaisesRegex(ValueError,'differs'):self.check_image(changed=True)
    def test_linker_symbols_are_not_loaded_data(self):
        words=[1011,0,1,0,0,1,1001,1,7,1008,1,0x666f6f00,0,0,1010]
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'native';path.write_bytes(struct.pack('>'+str(len(words))+'I',*words))
            checks=loaded_hunks(path,[{'start':0x100,'size':4}],lambda a,n:struct.pack('>I',7))
            self.assertTrue(checks[0]['matched'])

    def test_unsupported_block_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unsupported'):self.check_image(block=1005)

if __name__=='__main__':unittest.main()
