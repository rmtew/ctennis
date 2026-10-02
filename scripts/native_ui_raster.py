"""Representative actual title scanout against committed font and retained layout."""
from PIL import Image
from native_tools import ROOT


def assert_ui_raster(path,page,players,selection,version):
    if page==0:
        from native_identity_raster import assert_menu_selection_raster
        result=assert_menu_selection_raster(path,selection,players+1)
        return {'page':0,'checked_pixels':result['pixels'],'matched':True,'selection':selection,'players':players+1}
    lines={1:[(96,2,'How to play'),(106,2,'Move to ball: auto return.'),
              (126,2,'At net: both actions lob.')],
           2:[(96,2,'Controls'),(106,2,'A: WASD MOVE / F OR G ACT')],
           3:[(96,2,'BASELINE RALLY / CREDITS'),(116,2,version)]}[page]
    font=(ROOT/'assets/native/title/font-mac.bin').read_bytes()
    with Image.open(path) as picture:
        assert picture.size==(716,285),'Native PAL viewport changed'
        picture=picture.convert('RGB')
        pixels=0
        for y,x,text in lines:
            expected=[]
            for row in range(8):
                for char in text:
                    byte=font[ord(char)*8+row]
                    for bit in range(7,-1,-1):
                        rgb=(255,255,255) if byte&(1<<bit) else (0,0,0)
                        expected.extend((rgb,rgb))
            left=126+x*16
            actual=list(picture.crop((left,16+y,left+len(text)*16,24+y)).get_flattened_data())
            assert actual==expected,{'field':'native UI scanout','page':page,'text':text,'different_pixels':sum(a!=b for a,b in zip(actual,expected))}
            pixels+=len(expected)
    return {'page':page,'checked_pixels':pixels,'matched':True}
