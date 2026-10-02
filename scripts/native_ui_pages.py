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
    output = bytearray()
    for page, label in enumerate(('ui_menu_lines','ui_help_lines','ui_control_lines','ui_credit_lines')):
        plane = bytearray(80*32)
        entries = [(32+i*8, name, 4) for i,name in enumerate(lines(label))] if page==0 else [(i*8,name,4) for i,name in enumerate(lines(label))]
        if page==0: entries.append((72,'ui_menu_hint',4))
        for y,name,x in entries:
            value=text[name]
            if len(value)>28: raise ValueError('UI line exceeds native width: '+name)
            for column,char in enumerate(value):
                for row in range(8): plane[(y+row)*32+x+column]=font[ord(char)*8+row]
        output.extend(plane)
    path=ROOT/'build/native/ui-pages.bin'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(output)
