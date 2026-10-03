"""Author the inspected B concept on the exact native title grid.

Intentional pixel adaptation, not a resampled/generated concept import.
Run from this checkout. Only the existing four title planes and their manifest
hashes change. Existing OCS colours, plane sizes and pixels below y76 remain.
"""
from pathlib import Path
import hashlib
import json
import math
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[2]
GLYPHS={
 'B':['11110','11011','11011','11110','11011','11011','11110'],
 'A':['01110','11011','11011','11111','11011','11011','11011'],
 'S':['01111','11000','11000','01110','00011','00011','11110'],
 'E':['11111','11000','11000','11110','11000','11000','11111'],
 'L':['11000','11000','11000','11000','11000','11000','11111'],
 'I':['11111','01110','01110','01110','01110','01110','11111'],
 'N':['11011','11011','11111','11111','11111','11011','11011'],
 'R':['11110','11011','11011','11110','11100','11010','11011'],
 'Y':['11011','11011','11011','01110','01110','01110','01110']}


def logo():
    im=Image.new('P',(256,76),0)
    draw=ImageDraw.Draw(im)
    def lettering(value,x,y,scale,gap,colour,shadow=False):
        for col,c in enumerate(value):
            for row,line in enumerate(GLYPHS[c]):
                for bit,on in enumerate(line):
                    if on=='1':
                        left=x+col*(5*scale+gap)+bit*scale;top=y+row*scale
                        if shadow:draw.rectangle((left-1,top+1,left+scale-1,top+scale),fill=15)
            # Paint each whole glyph over its down-left white edge.
            for row,line in enumerate(GLYPHS[c]):
                for bit,on in enumerate(line):
                    if on=='1':
                        left=x+col*(5*scale+gap)+bit*scale;top=y+row*scale
                        draw.rectangle((left,top,left+scale-1,top+scale-1),fill=colour)
    lettering('BASELINE',64,9,3,1,15)
    lettering('RALLY',72,34,4,3,4,True)
    # Paired racket heads tilt outwards; handles point inward beneath the title.
    left=Image.new('P',(256,76),0);ld=ImageDraw.Draw(left)
    ld.line((51,43,65,61),fill=15,width=4)
    ld.line((63,59,71,70),fill=4,width=6)
    ld.line((64,61,68,58),fill=15,width=1)
    ld.line((68,66,72,63),fill=15,width=1)
    angle=math.radians(-18);ca=math.cos(angle);sa=math.sin(angle)
    for y in range(3,49):
        for x in range(23,64):
            dx=x-43;dy=y-26
            u=ca*dx+sa*dy;v=-sa*dx+ca*dy
            q=(u/16)**2+(v/21)**2
            if q<=1:
                ink=4 if q>.82 else 15 if q>.68 else 0
                if q<=.68 and (abs((u+v+3)%7-3.5)<.6 or abs((u-v+3)%7-3.5)<.6):ink=15
                left.putpixel((x,y),ink)
    for y in range(76):
        for x in range(23,75):
            c=left.getpixel((x,y))
            if c:
                im.putpixel((x,y),c)
                im.putpixel((255-x,y),13 if c==4 else c)
    # Existing title palette's green slot2; no new ball colour.
    draw.line((82,69,112,69),fill=15,width=1)
    draw.line((143,69,173,69),fill=15,width=1)
    # A12x13 native ellipse is nearly circular in the established PAL display
    # aspect. Two white inward-curving seams read as a tennis ball, rather than
    # a dark diagonal slash. Clip seam endpoints to the green silhouette.
    ball=Image.new('P',(12,13),0);bd=ImageDraw.Draw(ball)
    bd.ellipse((0,0,11,12),fill=2)
    seams=Image.new('1',ball.size);sd=ImageDraw.Draw(seams)
    for curve in [[(2,1),(3,3),(4,5),(4,7),(3,9),(2,11)],
                  [(9,1),(8,3),(7,5),(7,7),(8,9),(9,11)]]:
        sd.line(curve,fill=1,width=1)
    for y in range(13):
        for x in range(12):
            if ball.getpixel((x,y)):
                im.putpixel((122+x,63+y),15 if seams.getpixel((x,y)) else 2)
    return im


def write():
    im=logo()
    for n in range(4):
        path=ROOT/f'assets/native/title/plane{n}.bin'
        plane=bytearray(path.read_bytes())
        plane[:76*32]=bytes(76*32)
        for y in range(76):
            for x in range(256):
                if im.getpixel((x,y))&(1<<n):plane[y*32+x//8]|=128>>(x%8)
        path.write_bytes(plane)
    path=ROOT/'assets/native/manifest.json';manifest=json.loads(path.read_text())
    for entry in manifest['files']:
        if entry['path'] in [f'assets/native/title/plane{n}.bin' for n in range(4)]:
            entry['sha256']=hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()
    note=' Title concept B is an intentional native pixel adaptation of the user-selected, visually inspected paired-racket concept: authored block lettering and racket frame in the existing title palette; the underlying retained title plane provenance remains recorded.'
    if note not in manifest['provenance']:manifest['provenance']+=note
    path.write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':write()
