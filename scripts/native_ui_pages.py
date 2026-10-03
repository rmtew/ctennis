"""Bake authored static UI text with the committed font; no runtime/capture oracle."""
import re
from native_tools import ROOT


def prepare(version, release_version=None):
    if release_version is None:
        release_version=(ROOT/'amiga/VERSION').read_text().strip()
    if re.fullmatch(r'[0-9]+\.[0-9]+',release_version) is None:
        raise ValueError('Release version must be major.minor')
    source = (ROOT/'amiga/game/interface_text.s').read_text()
    text = dict(re.findall(r"^(ui_\w+): dc.b '([^']*)',0$", source, re.M))
    text.update(ui_empty='', ui_version=version.rstrip(b'\0').decode('ascii'))
    identity=re.fullmatch(r'BUILD ([0-9a-f]{7,12})(?: \+ LOCAL)?',text['ui_version'])
    if identity is None:raise ValueError('Title requires the native build identity')
    title_hash=identity[1]
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
    menu_width=max(len(text[name]) for name in menu_names)*8
    menu_left=(256-menu_width)//2
    # Runtime selection owns bytes11..20 (x88..167), enclosing the centred
    # five-cell menu without touching the figures. Edge bytes use byte copies.
    if (menu_left,menu_width)!=(108,40):raise ValueError('Title menu must fit native x108..147')
    output = bytearray()
    title_menu=None
    layouts={
        1:[(24,'ui_move_label',['ui_move_detail']),
           (34,'ui_serve_label',['ui_serve_detail']),
           (44,'ui_shot_label',['ui_shot_detail']),
           (54,'ui_changes_label',['ui_changes_detail'])],
        2:[(24,'ui_points_label',['ui_points_detail']),
           (34,'ui_deuce_label',['ui_deuce_detail']),
           (44,'ui_match_label',['ui_match_detail']),
           (54,'ui_demo_label',['ui_demo_detail']),
           (64,'ui_confirm_label',['ui_confirm_detail']),
           (74,'ui_exit_label',['ui_exit_detail'])],
        3:[(24,'ui_a_label',['ui_a_compact']),
           (34,'ui_empty',['ui_a_joy_compact']),
           (44,'ui_b_label',['ui_b_compact']),
           (54,'ui_empty',['ui_keypad_compact']),
           (64,'ui_empty',['ui_b_joy_compact']),
           (74,'ui_pause_label',['ui_pause_detail'])]}
    for page,label in enumerate(('ui_menu_lines','ui_help_lines','ui_help_lines','ui_control_lines','ui_credit_lines')):
        plane=bytearray(116*32)
        if page==0:
            entries=[(38+i*11,name,menu_left) for i,name in enumerate(menu_names)]
        elif page==1:
            entries=[(8,'ui_how',(256-len(text['ui_how'])*8)//2)]
            entries.extend((24+i*10,'ui_play_prose'+str(i),24 if i>=5 else 16) for i in range(7))
        elif page==2:
            entries=[(8,'ui_scoring',(256-len(text['ui_scoring'])*8)//2)]
            entries.extend((24+i*9,'ui_rule_prose'+str(i),16) for i in range(7))
        elif page in layouts:
            heading={1:'ui_how',2:'ui_scoring',3:'ui_controls'}[page]
            entries=[(8,heading,(256-len(text[heading])*8)//2)]
            for y,name,details in layouts[page]:
                label_width=len(text[name])*8
                available=240-(16+label_width+32)
                entries.append((y,name,16))
                for index,detail in enumerate(details):
                    width=len(text[detail])*8
                    if width>available:raise ValueError('Help row gap/width: '+detail)
                    row=y+index*10
                    if row+8>92:raise ValueError('Help body overlaps page count: '+detail)
                    entries.append((row,detail,240-width))
        else:
            names=lines(label)
            entries=[(8,names[0],(256-len(text[names[0]])*8)//2)]
            entries.extend((24+i*10,name,16) for i,name in enumerate(names[1:]))
        for y,name,x in entries:
            value=text[name]
            if any(ord(c)>=128 or (c!=' ' and not any(font[ord(c)*8:ord(c)*8+8])) for c in value):raise ValueError('Unavailable Font-Mac glyph: '+name)
            if len(value)>28:raise ValueError('UI line exceeds native width: '+name)
            if x<16 or x+len(value)*8>240:raise ValueError('Unsafe help/menu margin: '+name)
            draw(plane,y,x,value)
        if page==0:
            for x,value in [(44,'A'),(204,'B'),(120,'VS')]:draw(plane,16,x,value)
            title_menu=bytes(plane)
        else:
            count=text['ui_page'+str(page)]
            draw(plane,94,(256-len(count)*8)//2,count)
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

    # Four selected menu rows, shared by both modes; roles live under A/B.
    # All rows share the exact pixel edge of the widest menu/highlight block.
    menu=bytearray()
    for name,inverted in [(name,True) for name in menu_names]:
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
        for x,pose,table,colour in [(40,7,human,4),(200,0,human if both_human else robot,13)]:
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
            # Figures share menu scanlines, so retain the central text pixels.
            for offset,value in enumerate(planes[n]):combined[38*32+offset]|=value
            for centre,role in [(48,'ui_role_human'),(208,'ui_role_human' if both_human else 'ui_role_ai')]:
                draw(combined,26,centre-len(text[role])*4,text[role])
            figures.extend(combined)
    (ROOT/'build/native/ui-title-pages.bin').write_bytes(figures)

    # One monochrome row per standard; runtime copies it into grey planes1/2.
    identities=bytearray()
    for standard in ('PAL','NTSC'):
        label=f'{standard} {title_hash} {release_version}'
        if len(label)*8>240:raise ValueError('Title identity exceeds corner width')
        plane=bytearray(8*32)
        draw(plane,0,248-len(label)*8,label)
        identities.extend(plane)
    (ROOT/'build/native/ui-title-identities.bin').write_bytes(identities)
