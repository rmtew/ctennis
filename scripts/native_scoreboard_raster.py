"""Independent authored WIN/point UI expectations for actual PAL scanout.

No runtime-rendered golden: points use versioned selected-preview masks, WIN uses the
retained font and explicit authored placement; all remaining panel pixels black.
"""
from PIL import Image
from native_tools import ROOT
from native_square_scores import MASKS

RECTANGLES = ((0, 42, 48, 124), (208, 42, 256, 124))
BLUE, RED, GREY, WHITE = (85, 85, 238), (238, 51, 51), (51, 51, 51), (255, 255, 255)


def scoreboard_pixels(side, point, games):
    if side not in ('a', 'b') or not 0 <= point <= 6 or not 0 <= games <= 6:
        raise ValueError('Native scoreboard requires side a/b and variants0..6')
    colour = BLUE if side == 'a' else RED
    expected = [[(0, 0, 0)] * 48 for _ in range(82)]
    # Frozen square-option pixels, extracted before the renderer was written.
    mask = MASKS[point]
    for y in range(16):
        for x in range(16):
            if mask[y*2+x//8] & (128 >> (x%8)):
                expected[6+y][16+x] = colour
    # Exact native font columns with a single empty column between letters.
    font = (ROOT / 'assets/native/title/font.bin').read_bytes()
    for row in range(6):
        ink = colour if row < games else GREY
        for char, first, last, left in (('W', 0, 4, 17), ('I', 1, 3, 23), ('N', 0, 4, 27)):
            for y in range(8):
                for x in range(first, last+1):
                    if font[ord(char)*8+y] & (128 >> x):
                        expected[30+8*row+y][left+x-first] = ink
    for y in (1, 26, 81):  # native43,68,123: top, shared divider, closed bottom
        for x in range(11, 37):
            expected[y][x] = WHITE
    for y in range(1, 82):
        for x in (11, 36):
            expected[y][x] = WHITE
    return [pixel for row in expected for pixel in row for _ in range(2)]


def assert_scoreboard_raster(path, points, games):
    if len(points) != 2 or len(games) != 2:
        raise ValueError('Two logical players required')
    checks = []
    with Image.open(path) as picture:
        if picture.size != (716, 285):
            raise ValueError('Review native PAL viewport dimensions')
        raster = picture.convert('RGB')
        for side, point, count, (left, top, right, bottom) in zip(('a', 'b'), points, games, RECTANGLES):
            actual = list(raster.crop((126+2*left, 16+top, 126+2*right, 16+bottom)).get_flattened_data())
            expected = scoreboard_pixels(side, point, count)
            if actual != expected:
                raise AssertionError({'label': 'visible native scoreboard raster matches authored specification',
                    'side': side, 'point': point, 'games': count,
                    'different_pixels': sum(a != b for a, b in zip(actual, expected))})
            checks.append({'side': side, 'point': point, 'games': count, 'pixels': len(actual), 'matched': True})
    return checks


def assert_score_frames_raster(path):
    """All border pixels remain white even while a full-width status bank is active."""
    points = {(x,y) for y in (43,68,123) for x in range(11,37)}
    points |= {(x,y) for y in range(43,124) for x in (11,36)}
    with Image.open(path) as picture:
        if picture.size != (716,285):
            raise ValueError('Review native PAL viewport dimensions')
        raster=picture.convert('RGB')
        for offset in (0,208):
            for x,y in points:
                for doubled in (0,1):
                    if raster.getpixel((126+2*(offset+x)+doubled,16+y)) != WHITE:
                        raise AssertionError({'label':'stacked score/WIN frame remains white',
                                              'native_pixel':[offset+x,y]})
    return {'border_pixels':len(points)*4,'matched':True}
