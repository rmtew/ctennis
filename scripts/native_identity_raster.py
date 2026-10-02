"""CT12 actual scanout guards: complete mode field and logical player colours."""
from PIL import Image
from native_tools import ROOT
from native_status_raster import PALETTE


def assert_mode_raster(path, variant):
    planes = [(ROOT/f'assets/native/court/score_bank_mode_{variant}_p{p}.bin').read_bytes() for p in range(4)]
    expected=[]
    actual=[]
    with Image.open(path) as picture:
        assert picture.size==(716,285)
        raster=picture.convert('RGB')
        # Side labels only: the upper player's legs can cover the centre of
        # this background bank at Y34 after a game award.
        for left,right in ((0,48),(208,256)):
            expected.extend([(0,0,0)]*(2*(right-left)*2))  # two blank native rows below A/B
            for y in range(8):
                for x in range(left,right):
                    c=sum(((p[y*32+x//8]>>(7-x%8))&1)<<n for n,p in enumerate(planes))
                    rgb=tuple(((PALETTE[c]>>s)&15)*17 for s in (8,4,0))
                    expected.extend((rgb,rgb))
            actual.extend(raster.crop((126+2*left,48,126+2*right,58)).get_flattened_data())
    assert actual==expected,{'label':'centred A/B controller-role raster','variant':variant,'different_pixels':sum(a!=b for a,b in zip(actual,expected))}
    return {'variant':variant,'matched':True,'pixels':len(actual)}


def assert_logo_absent_initial_raster(path):
    with Image.open(path) as picture:
        assert picture.size==(716,285)
        pixels=list(picture.convert('RGB').crop((142,155,204,160)).get_flattened_data())
    assert all(pixel==(0,0,0) for pixel in pixels), 'residual court logo in initial native scanout'
    return {'logo_pixels_checked':len(pixels),'absent':True}



def assert_player_raster(path, exchanged):
    with Image.open(path) as picture:
        raster=picture.convert('RGB')
        counts=[]
        # Side scoreboards and the blue net posts lie outside these windows.
        for rect in ((260,16,510,104),(260,136,510,208)):
            colours=raster.crop(rect).getcolors(18000)
            counts.append({name:sum(n for n,c in colours if c==rgb) for name,rgb in
                           (('Blue',(85,85,238)),('Red',(238,51,51)))})
    expected=('Blue','Red') if exchanged else ('Red','Blue')
    for end,name,row in zip(('upper','lower'),expected,counts):
        assert row[name]>0,{'label':'actual player colour follows logical identity across ends','end':end,'expected':name,'counts':row}
    return {'exchanged':exchanged,'upper':counts[0],'lower':counts[1]}


def assert_title_raster(path):
    font=(ROOT/'assets/native/title/font.bin').read_bytes()
    with Image.open(path) as picture:
        raster=picture.convert('RGB')
        for text,x,y in (('BASELINE',64,16),('RALLY',88,48)):
            expected=[]
            for row in range(16):
                for c in text:
                    byte=font[ord(c)*8+row//2]
                    for bit in range(8):
                        rgb=(85,85,238) if byte&(128>>bit) else (0,0,0)
                        expected.extend([rgb]*4)
            left=126+2*x
            actual=list(raster.crop((left,16+y,left+len(text)*32,32+y)).get_flattened_data())
            assert actual==expected,{'label':'actual native Baseline Rally title','text':text}
    return {'title':'Baseline Rally','matched':True}


def assert_footer_raster(path, first, second, selected=None):
    """Compare the entire court footer against authored font cells, including blanks."""
    font=(ROOT/'assets/native/title/font.bin').read_bytes()
    expected=[]
    for text in (first,second):
        assert len(text)<=32
        left=(32-len(text))//2
        for row in range(8):
            for cell in range(32):
                column=cell-left
                byte=font[ord(text[column])*8+row] if 0<=column<len(text) else 0
                if text==second and selected is not None and left+text.index(selected)<=cell<left+text.index(selected)+len(selected):byte^=255
                for bit in range(8):
                    rgb=(255,255,255) if byte&(128>>bit) else (0,0,0)
                    expected.extend((rgb,rgb))
    with Image.open(path) as picture:
        actual=list(picture.convert('RGB').crop((126,208,638,224)).get_flattened_data())
    assert actual==expected,{'label':'centered complete two-row footer raster','first':first,'second':second,'selected':selected,'different_pixels':sum(a!=b for a,b in zip(actual,expected))}
    return {'first':first,'second':second,'selected':selected,'matched':True,'pixels':len(actual)}


def assert_menu_selection_raster(path, selection, players):
    """Independent title specification: ASCII, native ready masks and colours."""
    font=(ROOT/'assets/native/title/font-mac.bin').read_bytes()
    canvas=[[0]*256 for _ in range(96)]
    entries=[(49,'Start game'),(60,'Human vs Human' if players==2 else 'Human vs AI'),(71,'How to play'),(82,'Controls')]
    def text(y,x,value,inverted=False):
        for column,char in enumerate(value):
            for row in range(8):
                byte=font[ord(char)*8+row]
                for bit in range(8):canvas[y+row][x+column*8+bit]=15 if bool(byte&(128>>bit)) ^ inverted else 0
    for index,(y,value) in enumerate(entries):text(y,72,value,index==selection)
    for x,value in [(80,'A'),(168,'B'),(120,'VS')]:text(4,x,value)
    atlas=(ROOT/'assets/native/scene/sprite-images.bin').read_bytes()
    for x,colour,parts in [(76,4,[(5376,0,0),(5504,0,16),(2432,0,0)]),(164,13,[(1280 if players==2 else 8192,0,0),(1408 if players==2 else 8320,0,16),(1536,0,8)])]:
        for index,(offset,dx,dy) in enumerate(parts):
            for row in range(16):
                mask=int.from_bytes(atlas[offset+row*4:offset+row*4+2],'big')
                for bit in range(16):
                    if mask&(32768>>bit):canvas[16+dy+row][x+dx+bit]=15 if index==2 else colour
    palette=(0x000,0x000,0x2c4,0x6d7,0x55e,0x77f,0,0,0,0xf77,0xdc5,0,0,0xe33,0xccc,0xfff)
    expected=[]
    for row in canvas:
        for colour in row:
            rgb=tuple(((palette[colour]>>shift)&15)*17 for shift in (8,4,0));expected.extend((rgb,rgb))
    with Image.open(path) as picture:
        actual=list(picture.convert('RGB').crop((126,112,638,208)).get_flattened_data())
    assert actual==expected,{'label':'full title native figures and menu','selection':selection,'players':players,'different_pixels':sum(a!=b for a,b in zip(actual,expected))}
    return {'selection':selection,'players':players,'inverted_menu_matched':True,'pixels':len(actual)}
