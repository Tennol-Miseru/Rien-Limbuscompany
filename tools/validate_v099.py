#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json, base64, hashlib
root=Path(__file__).resolve().parents[1]
assert 'mod_version=0.9.9' in (root/'gradle.properties').read_text(encoding='utf8')
assets=root/'src/main/resources/assets/oraclearsenal'
form=json.loads((assets/'models/item/form_3.json').read_text(encoding='utf8'))
plane=[e for e in form['elements'] if e['faces'].get('north',{}).get('texture')=='#ink_blade']
assert len(plane)==1 and set(plane[0]['faces'])=={'north','south'}
img=Image.open(assets/'textures/item/greatsword_blade_alpha.png').convert('RGBA')
assert img.size==(768,768)
def alpha(x,y):
    px=max(0,min(img.size[0]-1,round(x*(img.size[0]/16))))
    py=max(0,min(img.size[1]-1,round((16-y)*(img.size[1]/16))))
    return img.getpixel((px,py))[3]
assert alpha(12.5,6.1)>180
assert alpha(9.7,8.3)>180
assert alpha(6.3,12.0)>180
assert alpha(2.25,14.7)>120
assert alpha(8.6,8.85)>180
assert alpha(7.7,9.65)>180
assert alpha(6.2,13.95)==0
assert alpha(12.3,5.45)>180
assert alpha(11.2,5.95)>180
assert alpha(9.8,6.7)>180
bb=json.loads((root/'blockbench/form_3.bbmodel').read_text(encoding='utf8'))
emb=base64.b64decode(bb['textures'][1]['source'].split(',',1)[1])
assert hashlib.sha256(emb).digest()==hashlib.sha256((assets/'textures/item/greatsword_blade_alpha.png').read_bytes()).digest()
assert (root/'FORM_3_GREATSWORD_ALPHA_PREVIEW.png').is_file()
print('PASS: v0.9.9 form_3 broad heavy greatsword validated')
