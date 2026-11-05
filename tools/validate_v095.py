#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json, base64, hashlib
root=Path(__file__).resolve().parents[1]
assert 'mod_version=0.9.5' in (root/'gradle.properties').read_text(encoding='utf8')
a=root/'src/main/resources/assets/oraclearsenal'
# ---- form 1 hand axe ----
form1=json.loads((a/'models/item/form_1.json').read_text(encoding='utf8'))
planes=[e for e in form1['elements'] if e['faces'].get('north',{}).get('texture')=='#ink_blade']
assert len(planes)==1 and set(planes[0]['faces'])=={'north','south'}
solids=[e for e in form1['elements'] if e is not planes[0]]
assert len(solids)>=6
tex1=a/'textures/item/hand_axe_blade_alpha.png'
im1=Image.open(tex1).convert('RGBA')
assert im1.size==(768,768)
assert im1.getchannel('A').getextrema()==(0,255)
def alpha(img,x,y):
    px=max(0,min(img.size[0]-1,round(x*(img.size[0]/16))))
    py=max(0,min(img.size[1]-1,round((16-y)*(img.size[1]/16))))
    return img.getpixel((px,py))[3]
assert alpha(im1,11.6,9.8)>180, 'axe socket/body missing'
assert alpha(im1,7.9,11.3)>180, 'axe upper belly missing'
assert alpha(im1,4.2,7.2)>140, 'axe beard / lower cutting profile missing'
assert alpha(im1,14.6,14.8)==0 and alpha(im1,0.8,15.2)==0
bb1=json.loads((root/'blockbench/form_1.bbmodel').read_text(encoding='utf8'))
emb1=base64.b64decode(bb1['textures'][1]['source'].split(',',1)[1])
assert hashlib.sha256(emb1).digest()==hashlib.sha256(tex1.read_bytes()).digest()
assert (root/'FORM_1_HAND_AXE_ALPHA_PREVIEW.png').is_file()
# ---- form 9 scythe ----
form9=json.loads((a/'models/item/form_9.json').read_text(encoding='utf8'))
planes9=[e for e in form9['elements'] if e['faces'].get('north',{}).get('texture')=='#ink_blade']
assert len(planes9)==1 and set(planes9[0]['faces'])=={'north','south'}
tex9=a/'textures/item/giant_scythe_blade_alpha.png'
im9=Image.open(tex9).convert('RGBA')
assert im9.size==(768,768)
# main body preserved
assert alpha(im9,13.6,13.7)>90
assert alpha(im9,8.5,12.3)>150
assert alpha(im9,4.1,7.2)>120
# old decorative spike zones should now be empty/smoother
for x,y in [(11.05,13.36),(8.45,12.52),(6.1,11.45),(3.95,10.0)]:
    assert alpha(im9,x,y)<80, f'decorative spike remained at {(x,y)}'
bb9=json.loads((root/'blockbench/form_9.bbmodel').read_text(encoding='utf8'))
emb9=base64.b64decode(bb9['textures'][1]['source'].split(',',1)[1])
assert hashlib.sha256(emb9).digest()==hashlib.sha256(tex9.read_bytes()).digest()
assert (root/'FORM_9_SMOOTH_SCYTHE_V095_PREVIEW.png').is_file()
print('PASS: v0.9.5 alpha hand axe and smoothed scythe validated')
