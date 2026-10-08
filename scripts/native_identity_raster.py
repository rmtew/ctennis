"""Check visible mode labels, player colours and title identity."""
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
    # Compare actual scanout to the versioned, reviewed native logo planes;
    # these are authored assets, never goldens regenerated from the runtime.
    planes=[(ROOT/f'assets/native/title/plane{n}.bin').read_bytes() for n in range(4)]
    colours={0:(0,0,0),2:(34,204,68),4:(85,85,238),10:(221,204,85),13:(238,51,51),15:(255,255,255)}
    expected=[]
    for y in range(76):
        for x in range(256):
            index=sum(((p[y*32+x//8]>>(7-x%8))&1)<<n for n,p in enumerate(planes))
            expected.extend([colours[index]]*2)
    with Image.open(path) as picture:
        actual=list(picture.convert('RGB').crop((126,16,638,92)).get_flattened_data())
    assert actual==expected,{'label':'complete native racket-framed B title','different_pixels':sum(a!=b for a,b in zip(actual,expected))}
    return {'title':'Baseline Rally / B','matched':True,'pixels':len(actual)}


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


def assert_menu_selection_raster(path, selection, players, build_hash=None, standard="PAL", release_version=None):
    """Independent title specification: ASCII, native ready masks and colours."""
    font=(ROOT/'assets/native/title/font-mac.bin').read_bytes()
    canvas=[[0]*256 for _ in range(116)]
    entries=[(38,'Start',108),(49,'Mode',108),(60,'Help',108),(71,'Tutorial',96)]
    def text(y,x,value,inverted=False,ink=15):
        for column,char in enumerate(value):
            for row in range(8):
                byte=font[ord(char)*8+row]
                for bit in range(8):canvas[y+row][x+column*8+bit]=ink if bool(byte&(128>>bit)) ^ inverted else 0
    for index,(y,value,x) in enumerate(entries):text(y,x,value,index==selection)
    for x,value in [(44,'A'),(204,'B'),(120,'VS')]:text(16,x,value)
    text(26,28,'Human')
    text(26,188 if players==2 else 200,'Human' if players==2 else 'AI')
    if build_hash is None:
        build_hash=(ROOT/'build/native/version.bin').read_bytes().rstrip(b'\0').decode('ascii').split()[1]
    if release_version is None:release_version=(ROOT/'amiga/VERSION').read_text().strip()
    label=f'{standard} {build_hash} {release_version}'
    text(104,248-len(label)*8,label,ink=6)
    atlas=(ROOT/'assets/native/scene/sprite-images.bin').read_bytes()
    for x,colour,parts in [(40,4,[(5376,0,0),(5504,0,16),(2432,0,0)]),(200,13,[(1280 if players==2 else 8192,0,0),(1408 if players==2 else 8320,0,16),(1536,0,8)])]:
        for index,(offset,dx,dy) in enumerate(parts):
            for row in range(16):
                mask=int.from_bytes(atlas[offset+row*4:offset+row*4+2],'big')
                for bit in range(16):
                    if mask&(32768>>bit):canvas[38+dy+row][x+dx+bit]=15 if index==2 else colour
    palette=(0x000,0x000,0x2c4,0x6d7,0x55e,0x77f,0x555,0,0,0xf77,0xdc5,0,0,0xe33,0xccc,0xfff)
    expected=[]
    for row in canvas:
        for colour in row:
            rgb=tuple(((palette[colour]>>shift)&15)*17 for shift in (8,4,0));expected.extend((rgb,rgb))
    with Image.open(path) as picture:
        actual=list(picture.convert('RGB').crop((126,92,638,208)).get_flattened_data())
    assert actual==expected,{'label':'full title native figures and menu','selection':selection,'players':players,'different_pixels':sum(a!=b for a,b in zip(actual,expected))}
    return {'selection':selection,'players':players,'inverted_menu_matched':True,'pixels':len(actual)}
