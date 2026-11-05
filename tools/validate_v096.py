#!/usr/bin/env python3
"""Specific geometry and texture regression checks for reference-refined hand axe."""
from pathlib import Path
from PIL import Image
import base64,hashlib,json
root=Path(__file__).resolve().parents[1]
a=root/'src/main/resources/assets/oraclearsenal'
assert 'mod_version=0.9.6' in (root/'gradle.properties').read_text(encoding='utf-8')
model=json.loads((a/'models/item/form_1.json').read_text(encoding='utf-8'))
parts=model['elements']
planes=[e for e in parts if e.get('faces',{}).get('north',{}).get('texture')=='#ink_blade']
assert len(planes)==1
assert set(planes[0]['faces'])=={'north','south'}
assert len([e for e in parts if e is not planes[0]])>=9
assert all(0<=v<=16 for e in parts for v in e['from']+e['to'])
assert all(all(x<y for x,y in zip(e['from'],e['to'])) for e in parts)
assert abs(model['display']['thirdperson_righthand']['rotation'][1])<45, 'alpha plane edge-on in 3p'
assert abs(model['display']['firstperson_righthand']['rotation'][1])<45, 'alpha plane edge-on in 1p'
tex=a/'textures/item/hand_axe_blade_alpha.png'
im=Image.open(tex).convert('RGBA')
assert im.size==(768,768) and im.getchannel('A').getextrema()==(0,255)
def alpha(x,y):
    return im.getpixel((round(x*48),round((16-y)*48)))[3]
# Small top profile, no giant bearded axe blade in lower-left quadrant.
assert alpha(7.0,15.25)>180
assert alpha(8.45,14.35)>180, 'blade root must connect to the pole'
assert alpha(11.9,15.04)>180
assert alpha(5.0,9.0)==0 and alpha(4.2,7.2)==0, 'old huge axe texture survived'
assert alpha(10.5,10.5)==0
# Pole is long, very slim and reaches blade socket y~14.
shaft=[e for e in parts if e['to'][1]>=14 and e['from'][1]<2.0]
assert shaft and min(e['to'][0]-e['from'][0] for e in shaft)<.5
assert any(e['from'][0]<=8.45<=e['to'][0] and e['from'][1]<=14.1<=e['to'][1] for e in shaft), 'shaft/socket detached'
bb=json.loads((root/'blockbench/form_1.bbmodel').read_text(encoding='utf-8'))
assert len(bb['textures'])==2 and len(bb['elements'])==len(parts)
embedded=base64.b64decode(bb['textures'][1]['source'].split(',',1)[1])
assert hashlib.sha256(embedded).digest()==hashlib.sha256(tex.read_bytes()).digest()
assert any(e.get('name')=='small_hooked_axe_alpha_plane' for e in bb['elements'])
assert (root/'FORM_1_REFERENCE_HANDEXE_V096_PREVIEW.png').exists()
print('PASS: hand axe top blade, long narrow shaft, true alpha, exact BBModel texture, preview')
