"""Representative actual title scanout against committed font and retained layout."""
from PIL import Image
from native_tools import ROOT


def assert_ui_raster(path,page,players,selection,version,help_choice=2):
    if page==0:
        from native_identity_raster import assert_menu_selection_raster
        result=assert_menu_selection_raster(path,selection,players+1)
        return {'page':0,'checked_pixels':result['pixels'],'matched':True,'selection':selection,'players':players+1}
    # Fixed review specification, independent of the page baker and runtime.
    headings={1:'How to play',2:'Scoring and rules',3:'Controls',4:'Credits'}
    columns={
        1:[(100,'Move to ball',['Auto return']),(110,'Serve',['Press action']),
           (120,'Shot',['Hold at contact']),(130,'Changes',['Height and depth'])],
        2:[(100,'Points',['15/30/40/game']),(110,'Deuce',['Win two in a row']),
           (120,'Match',['Win six games']),(130,'Demo',['Left / right']),
           (140,'Confirm',['Enter or action']),(150,'Exit',['Escape'])],
        3:[(100,'A',['WASD / F']),(110,'',['Joystick (port 2) / Fire']),
           (120,'B',['Cursor keys / .']),(130,'',['Keypad 8426 / 0']),
           (140,'',['Joystick (port 1) / Fire']),(150,'Pause / resume',['P or Esc'])]}
    font=(ROOT/'assets/native/title/font-mac.bin').read_bytes()
    canvas=[[False]*256 for _ in range(116)]
    def text(y,x,value,inverted=False):
        assert 76<=y and y+8<=192 and 16<=x and x+len(value)*8<=240
        for column,char in enumerate(value):
            for row in range(8):
                byte=font[ord(char)*8+row]
                for bit in range(8):canvas[y-76+row][x+column*8+bit]=bool(byte&(128>>bit)) ^ inverted
    text(84,(256-len(headings[page])*8)//2,headings[page])
    if page==1:
        for i,value in enumerate(['Press action to serve.', 'Move close to the ball to', 'return it automatically.', 'Hold action as you return', 'the ball:', 'Near net: lower / deeper', 'Far back: higher / shorter']):text(100+i*10,24 if i>=5 else 16,value)
    elif page==2:
        for i,value in enumerate(['Points: 0, 15, 30, 40, game.', '40-all: win two in a row.', 'Win one: advantage (A).', 'Win: game. Lose: 40-all.', 'First to six games wins.', 'Two serve faults lose point.', 'Return before second bounce.']):text(100+i*9,16,value)
    elif page in columns:
        for y,label,details in columns[page]:
            text(y,16,label)
            for index,value in enumerate(details):text(y+index*10,240-len(value)*8,value)
    else:
        for i,value in enumerate(['Based on Champion Tennis','SG-1000 / SC-3000.','Font author unknown.','AI used via Sol-6.1.']):text(100+i*10,16,value)
    count='PAGE '+str(page)+' / 4';text(170,(256-len(count)*8)//2,count)
    for index,(x,value) in enumerate([(48,'BACK'),(112,'EXIT'),(176,'NEXT')]):text(182,x,value,index==help_choice)
    expected=[]
    for row in canvas:
        for ink in row:expected.extend([(255,255,255) if ink else (0,0,0)]*2)
    with Image.open(path) as image:
        assert image.size==(716,285),'Native PAL viewport changed'
        actual=list(image.convert('RGB').crop((126,92,638,208)).get_flattened_data())
    assert actual==expected,{'label':'full help columns/count/navigation/clearing','page':page,'choice':help_choice,'different_pixels':sum(a!=b for a,b in zip(actual,expected))}
    return {'page':page,'choice':help_choice,'checked_pixels':len(actual),'matched':True}


def assert_help_navigation_raster(path,page,choice):
    """Full bottom region: independent centred count, gaps, selected-word pixels."""
    font=(ROOT/'assets/native/title/font-mac.bin').read_bytes()
    canvas=[[False]*256 for _ in range(26)]
    def text(y,x,value,inverted=False):
        for column,char in enumerate(value):
            for row in range(8):
                byte=font[ord(char)*8+row]
                for bit in range(8):canvas[y+row][x+column*8+bit]=bool(byte&(128>>bit)) ^ inverted
    value='PAGE '+str(page)+' / 4';text(4,(256-len(value)*8)//2,value)
    for index,(x,value) in enumerate([(48,'BACK'),(112,'EXIT'),(176,'NEXT')]):text(16,x,value,index==choice)
    expected=[]
    for row in canvas:
        for ink in row:expected.extend([(255,255,255) if ink else (0,0,0)]*2)
    with Image.open(path) as image:
        actual=list(image.convert('RGB').crop((126,182,638,208)).get_flattened_data())
    assert actual==expected,{'label':'help navigation count/spacing/inversion/clearing','page':page,'choice':choice,'different_pixels':sum(a!=b for a,b in zip(actual,expected))}
    return {'page':page,'choice':choice,'pixels':len(actual),'matched':True}
