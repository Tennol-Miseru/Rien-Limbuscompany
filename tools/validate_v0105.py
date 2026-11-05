#!/usr/bin/env python3
"""Asset and authoring regressions for the approved V0.10.5 Form IX scythe."""
from pathlib import Path
import hashlib
import base64
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'src/main/resources/assets/oraclearsenal'
assert 'mod_version=0.10.5' in (ROOT/'gradle.properties').read_text(encoding='utf8')
concept=ROOT/'tools/reference_assets/rien_scythe_concept_v105.png'
assert concept.is_file(), 'Approved image source absent from distributable zip'
texfile=A/'textures/item/giant_scythe_blade_alpha.png'
tex=Image.open(texfile)
assert tex.mode == 'RGBA' and tex.size == (1024,1024)
alpha=tex.getchannel('A')
assert alpha.getextrema() == (0,255)
assert alpha.getpixel((0,0)) == 0
assert alpha.getpixel((1023,1023)) == 0
assert alpha.getbbox() is not None
assert sum(p>200 for p in alpha.getdata()) > 50000, 'Scythe missing solid visible surface'
assert sum(p==0 for p in alpha.getdata()) > 500000, 'Background not fully transparent'
model=json.loads((A/'models/item/form_9.json').read_text(encoding='utf8'))
assert model['textures']['ink_blade'] == 'oraclearsenal:item/giant_scythe_blade_alpha'
planes=[e for e in model['elements'] if e['faces'].get('north',{}).get('texture')=='#ink_blade']
assert len(planes)==1 and set(planes[0]['faces'])=={'north','south'}
assert 0 < planes[0]['to'][2] - planes[0]['from'][2] < .05
assert len(model['elements']) >= 2
for e in model['elements']:
    assert all(0 <= v <= 16 for v in e['from']+e['to'])
    assert all(lo<hi for lo,hi in zip(e['from'],e['to']))
bb=json.loads((ROOT/'blockbench/form_9.bbmodel').read_text(encoding='utf8'))
assert len(bb['elements'])==len(model['elements'])
embedded=base64.b64decode(bb['textures'][1]['source'].split(',',1)[1])
assert hashlib.sha256(embedded).digest()==hashlib.sha256(texfile.read_bytes()).digest()
main=json.loads((A/'models/item/twin_serpent_staff.json').read_text(encoding='utf8'))
assert main['overrides'][8]['model']=='oraclearsenal:item/form_9'
assert main['overrides'][8]['predicate']['custom_model_data']==9
assert (ROOT/'FORM_9_SCYTHE_V105_MODEL_PREVIEW.png').is_file()
for name in ['form_3','form_5','form_6']:
    mdl=json.loads((A/f'models/item/{name}.json').read_text(encoding='utf8'))
    assert all(0<=v<=16 for e in mdl['elements'] for v in e['from']+e['to']),name
print('PASS: v0.10.5 scythe texture, transparent plane, BBModel, 9th form binding and legacy model bounds')
