"""Independent native status-bank pixels and accepted OCS palette, no captures."""
from PIL import Image
from native_tools import ROOT

# Frozen merged native palette; a product palette mutation must fail this guard.
PALETTE = (0x000,0x000,0x2c4,0x6d7,0x55e,0x77f,0x000,0x000,
           0x000,0xf77,0xdc5,0x000,0x000,0xc5b,0xccc,0xfff)


def status_pixels(variant):
    planes = [(ROOT/f'assets/native/court/score_bank_status_{variant}_p{p}.bin').read_bytes() for p in range(4)]
    if any(len(p)!=256 for p in planes): raise ValueError('Native status bank must be 256x8 planar')
    pixels=[]
    for y in range(8):
        for x in range(112,136):
            colour=sum(((p[y*32+x//8]>>(7-x%8))&1)<<n for n,p in enumerate(planes))
            rgb=tuple(((PALETTE[colour]>>shift)&15)*17 for shift in (8,4,0))
            pixels.extend((rgb,rgb))
    return pixels


def assert_status_raster(path, variant):
    with Image.open(path) as picture:
        # PAL active origin x126/y16; status starts native y96 (Copper line140).
        if picture.size!=(716,285): raise ValueError('Review native PAL viewport dimensions')
        actual=list(picture.convert('RGB').crop((350,112,398,120)).get_flattened_data())
    expected=status_pixels(variant)
    if actual!=expected:
        raise AssertionError({'label':'visible native status raster matches committed bank',
            'variant':variant,'different_pixels':sum(a!=b for a,b in zip(actual,expected))})
    return {'variant':variant,'pixels':len(actual),'asset_planes':4,'matched':True}
