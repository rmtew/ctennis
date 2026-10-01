"""Prepare private native sprite planes/pose data; no runtime VDP decoding."""
import hashlib,json,struct
from pathlib import Path
from generate_amiga_sprite_probe import ROOT, SOURCE, pattern_row
from source_input_movement import ANIMATION_RECORDS, SPRITE_DESCRIPTORS

OUT=ROOT/'build/amiga/native-scene'
def generate():
    vram=(SOURCE/'sprite-f1310.vram').read_bytes()
    OUT.mkdir(parents=True,exist_ok=True)
    images=bytearray()
    for image in range(64):
        rows=[pattern_row(vram,image*4,row) for row in range(16)]
        for plane in (0,1):
            for bits in rows:images.extend(struct.pack('>HH',bits if plane==0 else 0,bits if plane==1 else 0))
    poses=bytearray()
    for index in range(14):
        p0,p1,p2,dy,dx=SPRITE_DESCRIPTORS[index*5:index*5+5]
        poses.extend(struct.pack('>HHHBB',p0*32,p1*32,p2*32,dy,dx))
    outputs={'sprite-images.bin':images,'poses.bin':poses,'animations.bin':ANIMATION_RECORDS}
    for name,data in outputs.items():(OUT/name).write_bytes(data)
    (OUT/'manifest.json').write_text(json.dumps({'kind':'native-scene-assets','source_capture_sha256':hashlib.sha256(vram).hexdigest(),
        'source_pose_constants_sha256':hashlib.sha256(SPRITE_DESCRIPTORS+ANIMATION_RECORDS).hexdigest(),
        'images':64,'variants_per_image':2,'bytes_per_variant':64,'poses':14,
        'outputs':{name:hashlib.sha256(data).hexdigest() for name,data in outputs.items()}},indent=2)+'\n')
if __name__=='__main__':generate()
