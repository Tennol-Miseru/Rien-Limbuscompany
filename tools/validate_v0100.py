#!/usr/bin/env python3
"""Validate the independent ink longsword, its actual BBModel/PNG and canonical 9 forms."""
from pathlib import Path
from PIL import Image
import base64, json, hashlib
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'src/main/resources/assets/oraclearsenal'
assert any(f'mod_version={v}' in (ROOT/'gradle.properties').read_text(encoding='utf8') for v in ('0.10.0','0.10.1'))
model=json.loads((A/'models/item/ink_longsword.json').read_text(encoding='utf8'))
elements=model['elements']; assert 15 <= len(elements) <= 40, len(elements)
assert model['textures']['blade']=='oraclearsenal:item/ink_longsword_blade_alpha'
planes=[x for x in elements if x.get('faces',{}).get('north',{}).get('texture')=='#blade']
assert len(planes)==1
assert set(planes[0]['faces'])=={'north','south'}
assert (planes[0]['to'][2]-planes[0]['from'][2])<.05
for e in elements:
    assert all(0<=a<b<=16 for a,b in zip(e['from'],e['to'])),e
assert abs((elements[0]['from'][0]+elements[0]['to'][0])/2-8)<0.01
for key in ('thirdperson_righthand','thirdperson_lefthand','firstperson_righthand'):
    assert abs(model['display'][key]['rotation'][1])<=35, f'{key}: alpha-plane should face camera'
path=A/'textures/item/ink_longsword_blade_alpha.png'
im=Image.open(path).convert('RGBA')
assert im.size==(768,768)
assert im.getchannel('A').getextrema()==(0,255)
assert im.getpixel((0,0))[3]==0
# Single middle-center axis and tapering toward the point.
def row_width(y):
    arr=[]; yy=int((16-y)*48)
    for x in range(768):
        if im.getpixel((x,yy))[3]>100:arr.append(x)
    return (min(arr), max(arr))
for y in (7,10,12,14.5):
    lo,hi=row_width(y)
    assert abs((lo+hi)/2-384)<7,(y,lo,hi)
assert (row_width(7)[1]-row_width(7)[0])>(row_width(14.5)[1]-row_width(14.5)[0])
bb=json.loads((ROOT/'blockbench/ink_longsword.bbmodel').read_text(encoding='utf8'))
assert len(bb['elements'])==len(elements)
embedded=base64.b64decode(bb['textures'][1]['source'].split(',',1)[1])
assert hashlib.sha256(embedded).digest()==hashlib.sha256(path.read_bytes()).digest()
assert (ROOT/'INK_LONGSWORD_MODEL_PREVIEW.png').exists()
reg=(ROOT/'src/main/java/io/github/oraclearsenal/OracleArsenal.java').read_text(encoding='utf8')
assert 'id("ink_longsword")' in reg and 'entries.accept(INK_LONGSWORD)' in reg
assert 'new SwordItem(Tiers.IRON' in reg
for locale in ('zh_cn','en_us'):
    language=json.loads((A/f'lang/{locale}.json').read_text(encoding='utf8'))
    assert language.get('item.oraclearsenal.ink_longsword')
recipe=json.loads((ROOT/'src/main/resources/data/oraclearsenal/recipe/ink_longsword.json').read_text(encoding='utf8'))
assert recipe['result']['id']=='oraclearsenal:ink_longsword'
assert recipe['pattern']==[' I ',' I ',' S ']
# Existing nine forms and Caduceus overrides remain unchanged.
main=json.loads((A/'models/item/twin_serpent_staff.json').read_text(encoding='utf8'))
assert len(main['overrides'])==9
for i,v in enumerate(main['overrides'],1):
    assert v['predicate']['custom_model_data']==i
    assert v['model']==f'oraclearsenal:item/form_{i}'
    json.loads((A/f'models/item/form_{i}.json').read_text(encoding='utf8'))
# regression: fix the invalid negative Y in the prior v0.9.9 sword
form3=json.loads((A/'models/item/form_3.json').read_text(encoding='utf8'))
assert all(all(0<=a<b<=16 for a,b in zip(e['from'],e['to'])) for e in form3['elements'])
print('PASS: v0.10.0 ink longsword model+alpha+bbmodel+item+recipe+9-form regression')
