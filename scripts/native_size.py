"""Exact, non-overlapping emitted-byte attribution for the native executable.

The pinned vasm listing supplies emitted statement addresses and bytes. Hunk
payloads verify active incbin bytes; unknown/gapped/overlapping extents fail.
No cartridge, capture, emulator or optimisation is a build dependency.
"""
import ast
from collections import defaultdict
import hashlib
import re
from native_tools import ROOT
from native_hunk import hunk_layout


def _count(expression, symbols):
    tree=ast.parse(re.sub(r'\$([0-9a-fA-F]+)',r'0x\1',expression),mode='eval')
    def value(node):
        if isinstance(node,ast.Expression):return value(node.body)
        if isinstance(node,ast.Constant) and type(node.value) is int:return node.value
        if isinstance(node,ast.Name) and node.id in symbols:return symbols[node.id]
        if isinstance(node,ast.BinOp):
            a,b=value(node.left),value(node.right)
            if isinstance(node.op,ast.Add):return a+b
            if isinstance(node.op,ast.Sub):return a-b
            if isinstance(node.op,ast.Mult):return a*b
        raise ValueError('Unsupported native reserve-count expression: '+expression)
    result=value(tree)
    if result<0:raise ValueError('Negative native reserve count')
    return result


def _units(listing):
    units=[];source=None;active=None
    for line in listing.splitlines():
        context=re.match(r'^Source: "([^"\r\n]+)"',line)
        if context:source=context[1]
        primary=re.match(r'^(\d\d):([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]+)\s+(\d+):\s*(.*)$',line)
        if primary:
            section,address,encoded,number,statement=primary.groups()
            active={'hunk':int(section),'start':int(address,16),'visible':len(encoded)//2,
                    'source':source,'line':int(number),'statement':statement,'encoded':encoded}
            if len(encoded)%2:raise ValueError('Odd listing byte encoding')
            units.append(active);continue
        if active is not None and re.match(r'^\s+\d+:\s*even\s*$',line):active['alignment_after']=True
        continuation=re.match(r'^(\d\d):([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]+)\s*$',line)
        if continuation:
            section,address,encoded=continuation.groups()
            if len(encoded)%2:raise ValueError('Odd listing byte encoding')
            if (active is None or int(section)!=active['hunk'] or int(address,16)!=active['start']+active['visible']):
                raise ValueError('Unassociated listing continuation')
            active['visible']+=len(encoded)//2
            active['encoded']+=encoded
    return units


def _asset_group(path):
    if path=='build/native/ui-pages.bin':return 'pre_rendered_ui_pages'
    if path=='build/native/ui-title-pages.bin':return 'pre_rendered_title_ui_pages'
    if path in ('build/native/ui-help-options.bin','build/native/ui-menu-options.bin','build/native/ui-demo-options.bin'):
        return 'pre_rendered_'+path.rsplit('/',1)[1][3:-4].replace('-','_')
    if path=='build/native/version.bin':return 'build_version_text'
    if '/audio/battle-hymn/' in path:
        return 'celebration_period_table' if path.endswith('periods.bin') else 'celebration_square_wave' if path.endswith('square.s8') else 'celebration_scores'
    if '/audio/' in path:
        if '/score-' in path:return 'audio_scores'
        if path.endswith('periods.bin'):return 'audio_period_table'
        if path.endswith('envelopes.bin'):return 'audio_envelopes'
    if path=='assets/native/court/square-led-definitions.bin':return 'square_led_construction_definitions'
    if '/court/' in path:
        if '/plane' in path:return 'court_bitplanes'
        for name,category in [('point','score_point_banks'),('games','score_game_banks'),('status','status_banks'),('mode','mode_banks')]:
            if '/score_bank_'+name+'_' in path:return category
    if '/title/' in path:return 'menu_font_mac' if path.endswith('/font-mac.bin') else 'font' if path.endswith('/font.bin') else 'title_bitplanes'
    if '/scene/' in path:
        return {'sprite-images.bin':'scene_sprite_variants','poses.bin':'scene_pose_table','robot-poses.bin':'scene_robot_pose_table','animations.bin':'scene_animation_table'}[path.rsplit('/',1)[1]]
    if '/sprites/' in path:return 'initial_hardware_sprites'
    raise ValueError('Undeclared native asset category: '+path)


def executable_attribution(executable, listing_path, manifest, layout=None):
    layout=layout or hunk_layout(executable);blob=executable.read_bytes()
    listing=listing_path.read_text();units=_units(listing)
    symbols={name:int(offset,16) for name,offset in re.findall(r'^([A-Za-z_][\w]*)\s+(?:\d\d|E):([0-9A-Fa-f]{8})\s*$',listing,re.M)}
    categories=defaultdict(lambda:{'bytes':0,'by_hunk':defaultdict(int),'by_source':defaultdict(int),'instances':0})
    asset_instances=[];padding_instances=[];source_lines={};bss_instances=[]
    def add(category,size,hunk=None,source=None):
        categories[category]['bytes']+=size;categories[category]['instances']+=1
        if hunk is not None:categories[category]['by_hunk'][str(hunk)]+=size
        if source is not None:categories[category]['by_source'][source]+=size
    for hunk in layout['hunks']:
        rows=sorted((u for u in units if u['hunk']==hunk['index']),key=lambda u:u['start'])
        if not rows or rows[0]['start']!=0:raise ValueError('Native listing does not cover hunk start')
        if hunk['kind']=='bss':
            for index,unit in enumerate(rows):
                stop=rows[index+1]['start'] if index+1<len(rows) else hunk['bytes']
                body=re.sub(r'^[\w.]+:\s*','',unit['statement']).strip()
                token,expression=body.split(None,1)
                if token not in ('ds.b','ds.w','ds.l'):raise ValueError('Unsupported BSS declaration')
                size=_count(expression,symbols)*{'b':1,'w':2,'l':4}[token[-1]]
                if size!=stop-unit['start']:raise ValueError('BSS declaration does not reconcile')
                bss_instances.append({'category':'startup_generated_point_banks' if unit['source']=='amiga/square_score_storage.i' else 'reserved_bss',
                    'source':unit['source'],'hunk':hunk['index'],'offset':unit['start'],'bytes':size,'file_bytes':0})
            continue
        for index,unit in enumerate(rows):
            stop=rows[index+1]['start'] if index+1<len(rows) else hunk['bytes']
            available=stop-unit['start']
            if available<=0:raise ValueError('Overlapping emitted listing statements')
            start=hunk['file_offset']+unit['start']
            if blob[start:start+unit['visible']]!=bytes.fromhex(unit['encoded']):
                raise ValueError('Listing bytes differ from actual executable')
            statement=unit['statement'];body=re.sub(r'^[\w.]+:\s*','',statement).strip()
            token=body.split(None,1)[0].lower()
            size=unit['visible']
            if token=='incbin':
                source=unit['source']
                if source not in source_lines:source_lines[source]=(ROOT/source).read_text().splitlines()
                original=source_lines[source][unit['line']-1]
                path=re.search(r'\bincbin\s+"([^"\r\n]+)"',original)[1]
                if path not in manifest['files']:raise ValueError('Active incbin absent from compile manifest')
                payload=(ROOT/path).read_bytes();size=len(payload)
                file_start=hunk['file_offset']+unit['start']
                if blob[file_start:file_start+size]!=payload:raise ValueError('Incbin differs from actual executable: '+path)
                category=_asset_group(path)
                asset_instances.append({'path':path,'hunk':hunk['index'],'offset':unit['start'],
                                        'bytes':size,'sha256':hashlib.sha256(payload).hexdigest()})
            elif token.startswith('dcb.'):
                width={'b':1,'w':2,'l':4}[token[-1]]
                expression=body.split(None,1)[1].split(',',1)[0].strip()
                size=_count(expression,symbols)*width
                label=statement.split(':',1)[0] if ':' in statement else ''
                category={'game_stack_bottom':'reserved_native_stack','copperlist_back':'reserved_back_copper',
                          'sprite_back':'reserved_back_sprites','copperlist_third':'reserved_third_copper',
                          'sprite_third':'reserved_third_sprites','ui_overlay_plane':'reserved_ui_overlay'}.get(label,'reserved_state_and_work_buffers')
            elif token=='even':category='source_alignment_padding'
            elif token.startswith('dc.'):
                if unit['source']=='build/native/demo-inputs.i':category='replay_packets'
                elif unit['source']=='assets/native/court/score-patch-tables.i':category='score_patch_pointer_tables'
                elif unit['source'] in ('amiga/display.i','assets/native/court/score-cop-commands.i','assets/native/title/display.i'):category='front_court_and_title_copper_lists'
                elif unit['source']=='amiga/game/interface_text.s':category='ui_text_and_line_pointer_tables'
                elif statement.startswith('paula_square:'):category='paula_square_wave'
                else:category='other_initialized_tables_and_scalars'
            else:
                if hunk['kind']!='code':raise ValueError('CPU instruction emitted outside code hunk')
                category='cpu_instructions'
            if size>available or size<unit['visible']:raise ValueError('Statement exceeds its actual emitted extent')
            add(category,size,hunk['index'],unit['source'])
            slack=available-size
            if slack:
                alignment=slack==1 and unit.get('alignment_after')
                if not alignment and (index+1!=len(rows) or slack>3):raise ValueError(f'Unexplained payload gap: {unit} available={available} size={size}')
                padding=blob[hunk['file_offset']+unit['start']+size:hunk['file_offset']+stop]
                if any(padding) and not (not alignment and hunk['kind']=='code' and padding==b'\x4e\x71'):
                    raise ValueError('Unsupported alignment bytes')
                padding_instances.append({'hunk':hunk['index'],'offset':unit['start']+size,'bytes':slack,'hex':padding.hex()})
                add('source_alignment_padding' if alignment else 'hunk_payload_alignment_padding',slack,hunk['index'])
    metadata=layout['file_format']
    for category,key in [('hunk_header_table','header_table_bytes'),('hunk_record_headers_and_ends','hunk_headers_and_end_bytes'),
                         ('symbol_names','symbol_name_bytes'),('symbol_name_padding','symbol_name_padding_bytes'),
                         ('symbol_record_framing','symbol_framing_bytes')]:add(category,metadata[key])
    add('relocation_offsets',metadata['relocations']*4)
    add('relocation_record_framing',metadata['relocation_bytes']-metadata['relocations']*4)
    add('separate_debug_records',metadata['debug_bytes'])
    rows=[{'category':name,'bytes':value['bytes'],'by_hunk':dict(value['by_hunk']),'by_source':dict(value['by_source']),'instances':value['instances']} for name,value in sorted(categories.items())]
    accounted=sum(row['bytes'] for row in rows)
    if accounted!=len(blob):raise ValueError('Executable attribution does not reconcile')
    for hunk in layout['hunks']:
        if sum(row['by_hunk'].get(str(hunk['index']),0) for row in rows)!=(0 if hunk['kind']=='bss' else hunk['bytes']):
            raise ValueError('Payload attribution does not reconcile hunk '+str(hunk['index']))
    duplicates=defaultdict(list)
    for asset in asset_instances:duplicates[asset['sha256']].append(asset)
    repeated=[{'sha256':sha,'paths':[a['path'] for a in assets],'instances':len(assets),
               'bytes_per_instance':assets[0]['bytes'],'duplicate_bytes_beyond_first':sum(a['bytes'] for a in assets[1:])}
              for sha,assets in duplicates.items() if len(assets)>1]
    return {'schema':1,'executable_sha256':hashlib.sha256(blob).hexdigest(),'accounted_file_bytes':accounted,
            'reconciled':True,'categories':rows,'asset_instances':asset_instances,'padding_instances':padding_instances,
            'identical_incbin_payload_groups':repeated,
            'identical_incbin_duplicate_bytes':sum(g['duplicate_bytes_beyond_first'] for g in repeated),
            'bss_instances':bss_instances,'bss_ram_bytes':sum(r['bytes'] for r in bss_instances),
            'scope':'Mutually exclusive file-byte categories; code/data hunk sizes are a separate containing view, not added again. CPU instructions use actual emitted listing lengths, including operand extensions. Reserved dcb storage is file-backed, not HUNK_BSS. Zero debug means no emitted HUNK_DEBUG record; symbols are counted separately.'}
