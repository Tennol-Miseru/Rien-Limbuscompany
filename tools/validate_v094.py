#!/usr/bin/env python3
"""Validate model/texture anchor and returning-tip shape for Rien scythe v0.9.4.
Offline structural validation; does not prove in-game renderer transparency.
"""
from pathlib import Path
from PIL import Image
import json,base64,io,hashlib,ast
root=Path(__file__).resolve().parents[1]
assert 'mod_version=0.9.4' in (root/'gradle.properties').read_text(encoding='utf8')
a=root/'src/main/resources/assets/oraclearsenal'
model=json.loads((a/'models/item/form_9.json').read_text(encoding='utf8'))
planes=[e for e in model['elements'] if e['faces'].get('north',{}).get('texture')=='#ink_blade']
assert len(planes)==1 and set(planes[0]['faces'])=={'north','south'}
shafts=[e for e in model['elements'] if e is not planes[0]]
assert len(shafts)==22
assert any(e['from'][0]<=13.73<=e['to'][0] and e['from'][1]<=13.78<=e['to'][1] for e in shafts), '3D shaft anchor lost'
tex_path=a/'textures/item/giant_scythe_blade_alpha.png'
tex=Image.open(tex_path).convert('RGBA')
assert tex.size==(768,768)
assert tex.getchannel('A').getextrema()==(0,255)
def alpha(x,y):
 px=max(0,min(767,round(x*48)));py=max(0,min(767,round((16-y)*48)))
 return tex.getpixel((px,py))[3]
# Corrected root near old shaft joint: AND far tip that returns inward to the right.
assert alpha(13.65,13.70)>90, 'blade root detached from 3D shaft'
assert alpha(10,12.8)>180, 'blade mid arc absent'
assert alpha(3.5,8.8)>180, 'leftmost back of curved blade absent'
assert alpha(4.8,6.85)>160, 'inward returning tip absent'
assert alpha(10,5)==0, 'unexpected blade fill far below curve'
# Source-path control points make direction & root location explicit and deterministic.
src=(root/'tools/build_scythe_alpha.py').read_text(encoding='utf8')
assert 'BLADE_SOCKET=(13.73,13.78)' in src
assert '((13.73,13.78),' in src
assert '(4.85,6.85)' in src
assert '((4.85,6.85),' in src
# BBModel embeds the exact current PNG: preview and game source won't diverge.
bb=json.loads((root/'blockbench/form_9.bbmodel').read_text(encoding='utf8'))
emb=base64.b64decode(bb['textures'][1]['source'].split(',',1)[1])
assert hashlib.sha256(emb).digest()==hashlib.sha256(tex_path.read_bytes()).digest()
assert len(bb['elements'])==len(model['elements'])
assert (root/'FORM_9_INWARD_PIVOT_V094_PREVIEW.png').is_file()
print('PASS: v0.9.4 root locked to 3D shaft, inward-returning blade tip, alpha texture and embedded BBModel agree')
