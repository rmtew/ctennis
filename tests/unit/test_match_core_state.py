import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from match_core_state import FIELDS, STATE_BYTES, inventory, validate_record


class StateContractTests(unittest.TestCase):
    def setUp(self):
        self.symbols = {'game_core_state':0x10000,'game_core_state_end':0x10000+STATE_BYTES}
        offset = 0
        for name,size in FIELDS:
            self.symbols[name] = 0x10000+offset
            offset += size
        self.symbols.update(native_audio_scores=0x20000,native_audio_score_0=0x2001c,
            native_audio_score_1=0x202dc,native_audio_score_4=0x2056c,
            native_audio_score_5=0x205ec,native_audio_periods=0x205fc,
            native_victory_melody=0x21000,native_victory_bass=0x21220,
            native_victory_arpeggio=0x21430,native_victory_periods=0x21840)
        self.record = {'schema_version':1,'simulation_version':2,
                       'rules_sha256':'build-a','state':bytes(STATE_BYTES).hex()}

    def test_entire_inventory_including_reserved_bytes(self):
        fields = inventory(self.symbols)['fields']
        self.assertEqual(set(range(STATE_BYTES)),
            {byte for field in fields for byte in range(field['offset'],field['offset']+field['bytes'])})
        altered = dict(self.symbols,game_continue_pressed=self.symbols['game_continue_pressed']+1)
        with self.assertRaisesRegex(ValueError,'field'):
            inventory(altered)

    def test_reject_incompatible_envelopes(self):
        self.assertEqual(bytes(STATE_BYTES),validate_record(self.record,self.symbols,'build-a'))
        for key,value in [('schema_version',2),('simulation_version',1),
                          ('rules_sha256','build-b'),('state','00')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_record(dict(self.record,**{key:value}),self.symbols,'build-a')

    def test_audio_references_are_clip_ids_and_aligned_offsets(self):
        data = bytearray(STATE_BYTES)
        data[88:92] = (0x205ec-0x20000).to_bytes(4,'big')
        data[92] = 5
        self.assertEqual(bytes(data),validate_record(dict(self.record,state=data.hex()),self.symbols,'build-a'))
        for offset,clip in [(0x205ed-0x20000,5),(0x205ec-0x20000,7),(0xdff000,5)]:
            data[88:92] = offset.to_bytes(4,'big')
            data[92] = clip
            with self.subTest(offset=offset,clip=clip),self.assertRaises(ValueError):
                validate_record(dict(self.record,state=data.hex()),self.symbols,'build-a')


if __name__ == '__main__':
    unittest.main()
