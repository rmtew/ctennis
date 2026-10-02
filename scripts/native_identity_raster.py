"""CT12 actual scanout guards: complete mode field and logical player colours."""
from PIL import Image
from native_tools import ROOT
from native_status_raster import PALETTE


def assert_mode_raster(path, variant):
    planes = [(ROOT/f'assets/native/court/score_bank_mode_{variant}_p{p}.bin').read_bytes() for p in range(4)]
    expected=[]
    for y in range(8):
        for x in range(200,256):
            c=sum(((p[y*32+x//8]>>(7-x%8))&1)<<n for n,p in enumerate(planes))
            rgb=tuple(((PALETTE[c]>>s)&15)*17 for s in (8,4,0))
            expected.extend((rgb,rgb))
    with Image.open(path) as picture:
        assert picture.size==(716,285)
        actual=list(picture.convert('RGB').crop((526,48,638,56)).get_flattened_data())
    assert actual==expected,{'label':'complete native mode raster','variant':variant,'different_pixels':sum(a!=b for a,b in zip(actual,expected))}
    return {'variant':variant,'matched':True,'pixels':len(actual)}


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
