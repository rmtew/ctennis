"""Bake authored static UI text with the committed font; no runtime/capture oracle."""
import re
from native_tools import ROOT


def prepare(version):
    source = (ROOT/'amiga/game/interface_text.s').read_text()
    text = dict(re.findall(r"^(ui_\w+): dc.b '([^']*)',0$", source, re.M))
    text.update(ui_empty='', ui_version=version.rstrip(b'\0').decode('ascii'))
    font = (ROOT/'assets/native/title/font-mac.bin').read_bytes()
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
    title_menu=None
    layouts={
        1:[(12,'ui_move_label',False),(12,'ui_move_detail',True),(22,'ui_move_wrap',True),
           (32,'ui_action_label',False),(32,'ui_action_detail',True),
           (42,'ui_net_label',False),(42,'ui_net_detail',True),(52,'ui_contact_detail',True),
           (62,'ui_rear_label',False),(62,'ui_rear_detail',True),(72,'ui_contact_detail',True)],
        2:[(12,'ui_points_label',False),(12,'ui_points_detail',True),
           (32,'ui_deuce_label',False),(32,'ui_deuce_detail',True),(42,'ui_deuce_wrap',True),
           (52,'ui_match_label',False),(52,'ui_match_detail',True),
           (62,'ui_demo_label',False),(62,'ui_demo_detail',True),(72,'ui_demo_wrap',True),(82,'ui_help_demo_exit',True)],
        3:[(12,'ui_a_label',False),(12,'ui_a_move',True),(22,'ui_a_action',True),
           (32,'ui_b_label',False),(32,'ui_b_move',True),(42,'ui_b_action',True),
           (52,'ui_keypad_label',False),(52,'ui_keypad_move',True),(62,'ui_keypad_action',True),
           (72,'ui_a_joy_label',False),(72,'ui_port2_detail',True),
           (82,'ui_b_joy_label',False),(82,'ui_port1_detail',True)]}
    for page,label in enumerate(('ui_menu_lines','ui_help_lines','ui_help_lines','ui_control_lines','ui_credit_lines')):
        plane=bytearray(116*32)
        if page==0:
            entries=[(69+i*11,name,menu_left) for i,name in enumerate(menu_names)]
        elif page in layouts:
            heading={1:'ui_how',2:'ui_scoring',3:'ui_controls'}[page]
            entries=[(0,heading,16)]
            for y,name,right in layouts[page]:
                width=len(text[name])*8
                if width>(112 if right else 80):raise ValueError('Help column width: '+name)
                if y+8>90:raise ValueError('Help body overlaps page count: '+name)
                entries.append((y,name,240-width if right else 16))
        else:entries=[(i*10,name,16) for i,name in enumerate(lines(label))]
        for y,name,x in entries:
            value=text[name]
            if any(ord(c)>=128 or (c!=' ' and not any(font[ord(c)*8:ord(c)*8+8])) for c in value):raise ValueError('Unavailable Font-Mac glyph: '+name)
            if len(value)>28:raise ValueError('UI line exceeds native width: '+name)
            if x<16 or x+len(value)*8>240:raise ValueError('Unsafe help/menu margin: '+name)
            draw(plane,y,x,value)
        if page==0:
            for x,value in [(80,'A'),(168,'B'),(120,'VS')]:draw(plane,24,x,value)
            title_menu=bytes(plane)
        else:
            count=text['ui_page'+str(page)]
            draw(plane,92,(256-len(count)*8)//2,count)
            draw(plane,106,48,text['ui_page_navigation'])
            output.extend(plane)
    path=ROOT/'build/native/ui-pages.bin'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(output)

    # Bottom-page navigation retains blank gaps and inverts only one word.
    navigation=bytearray()
    for choice in range(3):
        plane=bytearray(256)
        for index,(x,label) in enumerate([(48,'BACK'),(112,'EXIT'),(176,'NEXT')]):
            draw(plane,0,x,label,index==choice)
        navigation.extend(plane)
    (ROOT/'build/native/ui-help-options.bin').write_bytes(navigation)

    # Five selected menu rows; normal captions are in the colour-page caches.
    # All rows share the exact pixel edge of the widest menu/highlight block.
    menu=bytearray()
    for name,inverted in [(name,True) for name in menu_names]+[('ui_players_two',True)]:
        plane=bytearray(256);draw(plane,0,menu_left,text[name],inverted);menu.extend(plane)
    (ROOT/'build/native/ui-menu-options.bin').write_bytes(menu)

    # Second-row demo ownership: authored centered text with exactly one option
    # inverted. These two small caches avoid a two-line font redraw at awards.
    font = (ROOT/'assets/native/title/font.bin').read_bytes()
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

    # Pure title presentation: explicit ownership, retained ready poses and
    # white racket masks. No gameplay builder, state, or mode is consulted.
    atlas=(ROOT/'assets/native/scene/sprite-images.bin').read_bytes()
    human=(ROOT/'assets/native/scene/poses.bin').read_bytes()
    robot=(ROOT/'assets/native/scene/robot-poses.bin').read_bytes()
    font=(ROOT/'assets/native/title/font-mac.bin').read_bytes()
    figures=bytearray()
    for both_human in (False,True):
        planes=[bytearray(32*32) for _ in range(4)]
        for x,pose,table,colour in [(76,7,human,4),(164,0,human if both_human else robot,13)]:
            data=table[pose*8:pose*8+8]
            offsets=[int.from_bytes(data[n:n+2],'big') for n in (0,2,4)]
            dy=int.from_bytes(data[6:7],'big',signed=True);dx=int.from_bytes(data[7:8],'big',signed=True)
            for offset,px,py,index in [(offsets[1],x,0,colour),(offsets[2],x,16,colour),(offsets[0],x+dx,dy,15)]:
                for row in range(16):
                    mask=int.from_bytes(atlas[offset+row*4:offset+row*4+2],'big')
                    for bit in range(16):
                        if mask&(32768>>bit):
                            for n in range(4):
                                address=(py+row)*32+(px+bit)//8
                                flag=128>>((px+bit)%8)
                                if index&(1<<n):planes[n][address]|=flag
                                else:planes[n][address]&=~flag
        for n in range(4):
            combined=bytearray(title_menu)
            combined[36*32:68*32]=planes[n]
            if both_human:
                combined[80*32:88*32]=bytes(8*32)
                draw(combined,80,menu_left,text['ui_players_two'])
            figures.extend(combined)
    (ROOT/'build/native/ui-title-pages.bin').write_bytes(figures)
