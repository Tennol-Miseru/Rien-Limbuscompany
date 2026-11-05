#!/usr/bin/env python3
import json
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1]
a=root/'src/main/resources/assets/oraclearsenal'
assert 'mod_version=0.9.3' in (root/'gradle.properties').read_text(encoding='utf8')
obj=json.loads((a/'models/item/form_9.json').read_text(encoding='utf8'))
faces=[e for e in obj['elements'] if e['faces'].get('north',{}).get('texture')=='#ink_blade']
assert len(faces)==1 and set(faces[0]['faces'])=={'north','south'}
solid=[e for e in obj['elements'] if e is not faces[0]]
assert len(solid)==22
tex=Image.open(a/'textures/item/giant_scythe_blade_alpha.png').convert('RGBA')
assert tex.size==(768,768)
assert tex.getchannel('A').getextrema()==(0,255)
def alpha_at(x,y):
    return tex.getpixel((round(x*48), round((16-y)*48)))[3]
# inward-curl silhouette present in upper-left / left-middle, with empty old horizontal belly area
assert alpha_at(4.1,4.7)>150
assert alpha_at(6.2,7.0)>150
assert alpha_at(9.5,9.3)>150
assert alpha_at(14.4,9.2)>120  # lower hook present
assert alpha_at(3.8,12.8)==0 and alpha_at(7.4,12.4)==0, 'old low horizontal blade should be gone'
assert (root/'FORM_9_INWARD_CURVE_V093_PREVIEW.png').is_file()
print('PASS: v0.9.3 corrected orientation + inward-curled alpha scythe')
