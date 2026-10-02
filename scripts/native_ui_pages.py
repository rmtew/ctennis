"""Bake authored static UI text with the committed font; no runtime/capture oracle."""
import re
from native_tools import ROOT


def prepare(version):
    source = (ROOT/'amiga/game/interface_text.s').read_text()
    text = dict(re.findall(r"^(ui_\w+): dc.b '([^']*)',0$", source, re.M))
    text.update(ui_empty='', ui_version=version.rstrip(b'\0').decode('ascii'))
    font = (ROOT/'assets/native/title/font.bin').read_bytes()
    def lines(label):
        match = re.search(r'^'+label+r':(?: dc.l|\n\s+dc.l) ([^\n]+)', source, re.M)
        return match[1].split(',')
    def draw(plane, y, x, value, inverted=False):
        for column,char in enumerate(value):
            for row in range(8):
                byte=font[ord(char)*8+row] ^ (255 if inverted else 0)
                offset=(y+row)*32+x//8+column
                shift=x%8
                plane[offset]|=byte>>shift
                if shift:plane[offset+1]|=(byte<<(8-shift))&255
    menu_names=lines('ui_menu_lines')
    menu_width=max(len(text[name]) for name in menu_names+['ui_players_two'])*8
    menu_left=(256-menu_width)//2
    output = bytearray()
    for page, label in enumerate(('ui_menu_lines','ui_help_lines','ui_control_lines','ui_credit_lines')):
        plane = bytearray(80*32)
        entries = [(32+i*8, name, menu_left) for i,name in enumerate(lines(label))] if page==0 else [(i*8,name,32) for i,name in enumerate(lines(label))]
        for y,name,x in entries:
            value=text[name]
            if len(value)>28: raise ValueError('UI line exceeds native width: '+name)
            draw(plane,y,x,value)
        output.extend(plane)
    path=ROOT/'build/native/ui-pages.bin'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(output)

    # Five selected existing menu rows, plus normal player-count2 override.
    # All rows share the exact pixel edge of the widest menu/highlight block.
    menu=bytearray()
    for name,inverted in [(name,True) for name in menu_names]+[('ui_players_two',True),('ui_players_two',False)]:
        plane=bytearray(256);draw(plane,0,menu_left,text[name],inverted);menu.extend(plane)
    (ROOT/'build/native/ui-menu-options.bin').write_bytes(menu)

    # Second-row demo ownership: authored centered text with exactly one option
    # inverted. These two small caches avoid a two-line font redraw at awards.
    value=text['ui_demo_selector']
    if len(value)>32:raise ValueError('Demo selector exceeds court viewport')
    left=(32-len(value))//2
    output=bytearray()
    for choice,option in [(0,'EXIT'),(1,'TAKE OVER')]:
        plane=bytearray(256);begin=left+value.index(option);end=begin+len(option)
        for row in range(8):
            for column,char in enumerate(value):
                byte=font[ord(char)*8+row]
                if begin<=left+column<end:byte^=255
                plane[row*32+left+column]=byte
        output.extend(plane)
    (ROOT/'build/native/ui-demo-options.bin').write_bytes(output)
