#!/usr/bin/env python3
"""Checks ninth form uses true RGBA alpha cutout and only one blade plane."""
import json
from pathlib import Path
from PIL import Image
r=Path(__file__).resolve().parents[1]
a=r/'src/main/resources/assets/oraclearsenal'
model=json.loads((a/'models/item/form_9.json').read_text(encoding='utf8'))
assert 'mod_version=0.9.1' in (r/'gradle.properties').read_text(encoding='utf8')
planes=[e for e in model['elements'] if e['faces'].get('north',{}).get('texture')=='#ink_blade']
assert len(planes)==1
plane=planes[0]
assert set(plane['faces'])=={'north','south'}
assert plane['faces']['south']['texture']=='#ink_blade'
assert 0 < plane['to'][2]-plane['from'][2] < 0.05
assert model['textures']['ink_blade']=='oraclearsenal:item/giant_scythe_blade_alpha'
assert model['display']['thirdperson_righthand']['scale'][0]>=2
assert model['display']['thirdperson_righthand']['rotation'][1] < 45
img=Image.open(a/'textures/item/giant_scythe_blade_alpha.png').convert('RGBA')
assert img.size==(768,768)
alpha=img.getchannel('A')
assert alpha.getextrema()==(0,255) and alpha.getbbox() is not None
assert img.getpixel((0,0))[3]==0
bb=json.loads((r/'blockbench/form_9.bbmodel').read_text(encoding='utf8'))
assert len(bb['textures'])==2
assert len(bb['elements'])==len(model['elements'])
assert any(e['name']=='crescent_alpha_plane' for e in bb['elements'])
assert len([e for e in model['elements'] if '#ink_blade' in str(e['faces'])]) == 1
assert (r/'FORM_9_ALPHA_SCYTHE_MODEL_PREVIEW.png').exists()
print('PASS: transparent curved scythe, dual-sided planar face, shaft, bbmodel and rendered preview')
