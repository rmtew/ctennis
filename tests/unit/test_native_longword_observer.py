import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from native_longword_observer import LongwordObserver


class NativeLongwordObserver(unittest.TestCase):
    def test_low_first_borrow_waits_for_high_word(self):
        observer = LongwordObserver()
        self.assertEqual(observer.write(0, 0x00040a80, 4, 100), 264832)
        self.assertIsNone(observer.write(2, 0xfad8, 2, 200))
        self.assertEqual(observer.write(0, 3, 2, 200), 260824)
        self.assertFalse(observer.seen)

    def test_high_first_carry_and_next_full_store(self):
        observer = LongwordObserver()
        self.assertIsNone(observer.write(0, 4, 2, 200))
        self.assertEqual(observer.write(2, 0x0a80, 2, 200), 264832)
        self.assertEqual(observer.write(0, 0x0003fad8, 4, 300), 260824)

    def test_missing_word_cannot_be_combined_with_another_instruction(self):
        observer = LongwordObserver()
        self.assertIsNone(observer.write(2, 0xfad8, 2, 200))
        with self.assertRaisesRegex(ValueError, 'Incomplete long store'):
            observer.write(0, 3, 2, 202)

    def test_repeated_half_is_not_a_complete_long_store(self):
        observer = LongwordObserver()
        self.assertIsNone(observer.write(2, 0xfad8, 2, 200))
        with self.assertRaisesRegex(ValueError, 'Incomplete long store'):
            observer.write(2, 0xfad8, 2, 200)
