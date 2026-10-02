"""Independent native status-bank pixels and accepted OCS palette, no captures."""
from PIL import Image
from native_tools import ROOT

# Approved WIN UI palette: removed score decorations release1/3;6 was unused.
# Court/net colours and logical Blue/Red stay unchanged.
PALETTE = (0x000,0xe33,0x2c4,0x333,0x55e,0x77f,0x333,0x000,
           0x000,0xf77,0xdc5,0x000,0x000,0xe33,0xccc,0xfff)


def status_pixels(variant):
    planes = [(ROOT/f'assets/native/court/score_bank_status_{variant}_p{p}.bin').read_bytes() for p in range(4)]
    if any(len(p)!=256 for p in planes): raise ValueError('Native status bank must be 256x8 planar')
    pixels=[]
    for y in range(8):
        for x in range(80,176):
            colour=sum(((p[y*32+x//8]>>(7-x%8))&1)<<n for n,p in enumerate(planes))
            rgb=tuple(((PALETTE[colour]>>shift)&15)*17 for shift in (8,4,0))
            pixels.extend((rgb,rgb))
    return pixels


def assert_status_raster(path, variant):
    with Image.open(path) as picture:
        # PAL active origin x126/y16; status occupies native x80..175/y0..7 (Copper lines44..51).
        if picture.size!=(716,285): raise ValueError('Review native PAL viewport dimensions')
        actual=list(picture.convert('RGB').crop((286,16,478,24)).get_flattened_data())
    expected=status_pixels(variant)
    if actual!=expected:
        raise AssertionError({'label':'visible native status raster matches committed bank',
            'variant':variant,'different_pixels':sum(a!=b for a,b in zip(actual,expected))})
    return {'variant':variant,'pixels':len(actual),'asset_planes':4,'matched':True}
