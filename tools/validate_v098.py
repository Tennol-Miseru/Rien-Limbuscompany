#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json, base64, hashlib
root=Path(__file__).resolve().parents[1]
assert 'mod_version=0.9.8' in (root/'gradle.properties').read_text(encoding='utf8')
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
# straight blade checkpoints
assert alpha(12.1,5.5)>180, 'root missing'
assert alpha(9.0,8.9)>180, 'mid blade missing'
assert alpha(5.7,12.0)>180, 'lower mid blade missing'
assert alpha(2.45,15.12)>120, 'tip missing'
# expected transparent side gaps proving blade is narrow and straight-ish
assert alpha(7.2,12.9)==0, 'blade too wide / bent into side gap'
assert alpha(10.7,4.8)==0, 'unexpected fill near upper outside gap'
# dorsal spikes and finial
assert alpha(12.0,5.55)>180, 'top spike missing'
assert alpha(11.0,6.05)>180, 'mid spike missing'
assert alpha(10.0,6.6)>180, 'lower spike missing'
assert alpha(12.56,4.12)>120, 'finial thorn missing'
bb=json.loads((root/'blockbench/form_3.bbmodel').read_text(encoding='utf8'))
emb=base64.b64decode(bb['textures'][1]['source'].split(',',1)[1])
assert hashlib.sha256(emb).digest()==hashlib.sha256((assets/'textures/item/greatsword_blade_alpha.png').read_bytes()).digest()
assert (root/'FORM_3_GREATSWORD_ALPHA_PREVIEW.png').is_file()
print('PASS: v0.9.8 form_3 greatsword alpha model validated')
