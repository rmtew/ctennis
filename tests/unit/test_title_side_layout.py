"""Static title-cache contracts; no emulator/input/timing acceptance claim."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import native_ui_pages
from native_identity_raster import assert_menu_selection_raster


class SideTitleLayout(unittest.TestCase):
    def test_both_role_caches_and_all_selected_captions(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'assets').symlink_to(ROOT/'assets',target_is_directory=True)
            (root/'amiga').symlink_to(ROOT/'amiga',target_is_directory=True)
            with patch.object(native_ui_pages,'ROOT',root):
                native_ui_pages.prepare(b'BUILD 123abcd + LOCAL\0')
            pages=(root/'build/native/ui-title-pages.bin').read_bytes()
            options=(root/'build/native/ui-menu-options.bin').read_bytes()
            self.assertEqual(len(pages),2*4*116*32)
            self.assertEqual(len(options),4*8*32)
            palette=[tuple(((v>>s)&15)*17 for s in (8,4,0)) for v in
                     (0,0,0x2c4,0x6d7,0x55e,0x77f,0x555,0,0,0xf77,0xdc5,0,0,0xe33,0xccc,0xfff)]
            for players in (1,2):
                for selection in range(4):
                    with self.subTest(players=players,selection=selection):
                        planes=[bytearray(pages[((players-1)*4+n)*3712:((players-1)*4+n+1)*3712]) for n in range(4)]
                        selected=options[selection*256:(selection+1)*256]
                        # Cache only: impose the authored ownership rectangle.
                        # Execution of the native copy loop is covered by the
                        # physical-input target suite, not this host test.
                        for plane in planes:
                            for y in range(8):
                                start=(38+selection*11+y)*32+11
                                plane[start:start+10]=selected[y*32+11:y*32+21]
                        raw=Image.new('RGB',(716,285),'black')
                        for y in range(116):
                            for x in range(256):
                                colour=sum(((p[y*32+x//8]>>(7-x%8))&1)<<n for n,p in enumerate(planes))
                                for dx in range(2):raw.putpixel((126+2*x+dx,92+y),palette[colour])
                        path=root/'cache.png';raw.save(path)
                        self.assertTrue(assert_menu_selection_raster(path,selection,players,build_hash='123abcd')['inverted_menu_matched'])


if __name__=='__main__':unittest.main()
