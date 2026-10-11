"""A separate endpoint write must not invent another dense dispatch boundary."""
import unittest
from preview_extended_proof import dense_point_destination


class PointBoundaryTests(unittest.TestCase):
    def test_terminal_endpoint_is_separate_from_dense_append(self):
        symbols=dict(game_preview_endpoints=1000,game_preview_paths=2000)
        for variant in (0,1):
            for count in (1,257,513):
                self.assertFalse(dense_point_destination(symbols,variant,count,1000+8*variant))
                self.assertTrue(dense_point_destination(symbols,variant,count,2000+513*8*variant+8*(count-1)))
                with self.assertRaises(AssertionError):
                    dense_point_destination(symbols,variant,count,2000+513*8*variant+8*count)
