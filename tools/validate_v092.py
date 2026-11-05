#!/usr/bin/env python3
"""Structural and alpha silhouette regression checks for v0.9.2.
This is an offline test, not a Minecraft in-game rendering test.
"""
import json
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1]
a=root/'src/main/resources/assets/oraclearsenal'
assert 'mod_version=0.9.2' in (root/'gradle.properties').read_text(encoding='utf-8')
obj=json.loads((a/'models/item/form_9.json').read_text(encoding='utf-8'))
faces=[e for e in obj['elements'] if e['faces'].get('north',{}).get('texture')=='#ink_blade']
assert len(faces)==1
assert set(faces[0]['faces'])=={'north','south'}
assert obj['textures']['ink_blade']=='oraclearsenal:item/giant_scythe_blade_alpha'
assert obj['display']['thirdperson_righthand']['scale'][0]>=2
solid=[e for e in obj['elements'] if e is not faces[0]]
assert len(solid)==22
assert all(e['from'][0]>=12 for e in solid), '3D shaft must sit at the right-side root'
tex=Image.open(a/'textures/item/giant_scythe_blade_alpha.png').convert('RGBA')
assert tex.size==(768,768)
assert tex.getchannel('A').getextrema()==(0,255)
def alpha_at(x,y):
 return tex.getpixel((round(x*48),round((16-y)*48)))[3]
# The shallow crescent stretches far to the left, with open space below it.
assert alpha_at(2.0,12.6)>200
assert alpha_at(7.5,12.45)>200
assert alpha_at(10.5,12.5)>200
assert alpha_at(13.5,8.0)==0, 'Old deep C-shaped hooked blade must be absent'
assert alpha_at(4.0,9.0)==0
assert alpha_at(12.8,15.0)>150, 'Separate short raised horn must be present'
bb=json.loads((root/'blockbench/form_9.bbmodel').read_text(encoding='utf8'))
assert len(bb['textures'])==2
assert len(bb['elements'])==len(obj['elements'])
assert any(el['name']=='crescent_alpha_plane' for el in bb['elements'])
assert (root/'FORM_9_REFERENCE_CURVE_V092_PREVIEW.png').is_file()
print('PASS: v0.9.2 long shallow alpha crescent, raised hook, two-sided plane, shifted 3D grip, bbmodel and rendered preview')
