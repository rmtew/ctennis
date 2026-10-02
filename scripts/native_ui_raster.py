"""Representative actual title scanout against committed font and retained layout."""
from PIL import Image
from native_tools import ROOT


def assert_ui_raster(path,page,players,selection,version):
    lines={0:[(144,4,'START GAME'),(152,4,'PLAYERS: '+str(players+1)),
              (144+selection*8,2,'*')],
           1:[(112,4,'HOW TO PLAY'),(120,4,'MOVE TO BALL: AUTO RETURNS.'),
              (136,4,'CONTACT, BOTH AT NET: LOB.')],
           2:[(112,4,'CONTROLS'),(128,4,'P1: WASD MOVE / F OR G ACT')],
           3:[(112,4,'BASELINE RALLY / CREDITS'),(128,4,version)]}[page]
    font=(ROOT/'assets/native/title/font.bin').read_bytes()
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
