#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json, base64, hashlib
root=Path(__file__).resolve().parents[1]
assert 'mod_version=0.9.7' in (root/'gradle.properties').read_text(encoding='utf8')
assets=root/'src/main/resources/assets/oraclearsenal'
form=json.loads((assets/'models/item/form_3.json').read_text(encoding='utf8'))
planes=[e for e in form['elements'] if e['faces'].get('north',{}).get('texture')=='#ink_blade']
assert len(planes)==1 and set(planes[0]['faces'])=={'north','south'}
solids=[e for e in form['elements'] if e is not planes[0]]
assert len(solids)>=10
img=Image.open(assets/'textures/item/greatsword_blade_alpha.png').convert('RGBA')
assert img.size==(768,768)
assert img.getchannel('A').getextrema()==(0,255)
def alpha(x,y):
    px=max(0,min(img.size[0]-1,round(x*(img.size[0]/16))))
    py=max(0,min(img.size[1]-1,round((16-y)*(img.size[1]/16))))
    return img.getpixel((px,py))[3]
# key silhouette points
assert alpha(12.1,5.0)>180, 'blade root missing'
assert alpha(8.6,8.5)>180, 'mid blade missing'
assert alpha(3.0,14.8)>140, 'tip missing'
# dorsal spikes / finial
assert alpha(12.3,4.45)>120, 'top dorsal spike missing'
assert alpha(11.0,5.2)>120, 'mid dorsal spike missing'
assert alpha(9.8,5.7)>120, 'lower dorsal spike missing'
assert alpha(13.0,3.55)>120, 'finial thorn missing'
# background still transparent
assert alpha(0.8,15.2)==0 and alpha(15.2,15.2)==0
bb=json.loads((root/'blockbench/form_3.bbmodel').read_text(encoding='utf8'))
emb=base64.b64decode(bb['textures'][1]['source'].split(',',1)[1])
assert hashlib.sha256(emb).digest()==hashlib.sha256((assets/'textures/item/greatsword_blade_alpha.png').read_bytes()).digest()
assert (root/'FORM_3_GREATSWORD_ALPHA_PREVIEW.png').is_file()
print('PASS: v0.9.7 form_3 greatsword alpha model validated')
