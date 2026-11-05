#!/usr/bin/env python3
"""Art and compatibility regression for the v0.10.1 Form VIII long whip."""
from pathlib import Path
import base64,hashlib,json
from PIL import Image
root=Path(__file__).resolve().parents[1]
a=root/'src/main/resources/assets/oraclearsenal'
assert 'mod_version=0.10.1' in (root/'gradle.properties').read_text(encoding='utf8')
mod=json.loads((a/'models/item/form_8.json').read_text(encoding='utf8'))
assert mod['parent']=='minecraft:block/block'
assert mod['textures']['whip']=='oraclearsenal:item/long_whip_alpha'
planes=[e for e in mod['elements'] if e['faces'].get('north',{}).get('texture')=='#whip']
assert len(planes)==1 and set(planes[0]['faces'])=={'north','south'}
assert planes[0]['to'][2]-planes[0]['from'][2] < .05
assert 10 <= len(mod['elements']) <= 22, len(mod['elements'])
for e in mod['elements']:
    assert all(0<=lo<hi<=16 for lo,hi in zip(e['from'],e['to'])),e
for hand in ('thirdperson_righthand','thirdperson_lefthand','firstperson_righthand','firstperson_lefthand'):
    assert abs(mod['display'][hand]['rotation'][1])<=30
p=a/'textures/item/long_whip_alpha.png'; image=Image.open(p).convert('RGBA')
assert image.size==(1024,1024)
assert image.getchannel('A').getextrema()==(0,255)
assert image.getpixel((0,0))[3]==0
# Actual curved path checkpoints including root, outer tip and swinging apex.
def alpha_at(x,y):
    return image.getpixel((min(1023,round(x*64)),min(1023,round((16-y)*64))))[3]
for x,y in [(8.0,5.1),(8.83,8.3),(6.24,11.92),(3.05,14.03),(1.42,12.34),(2.12,11.06)]:
    assert alpha_at(x,y)>80,(x,y,alpha_at(x,y))
for x,y in [(14,14),(1.1,4),(10,2),(12,10)]:
    assert alpha_at(x,y)==0,(x,y)
bb=json.loads((root/'blockbench/form_8.bbmodel').read_text(encoding='utf8'))
assert len(bb['elements'])==len(mod['elements'])
assert 'whip_alpha_ribbon' in [e['name'] for e in bb['elements']]
raw=base64.b64decode(bb['textures'][1]['source'].split(',',1)[1]);assert hashlib.sha256(raw).digest()==hashlib.sha256(p.read_bytes()).digest()
# Original variant mapping, naming and attack behavior preserved.
main=json.loads((a/'models/item/twin_serpent_staff.json').read_text(encoding='utf8'))
assert main['overrides'][7]['predicate']['custom_model_data']==8
assert main['overrides'][7]['model']=='oraclearsenal:item/form_8'
combat=(root/'src/main/java/io/github/oraclearsenal/OracleCombat.java').read_text(encoding='utf8')
assert 'case 8 ->' in combat and 'Long whip' in combat
for loc in ('zh_cn','en_us'):
    txt=(a/f'lang/{loc}.json').read_text(encoding='utf8')
    assert ('长鞭' if loc=='zh_cn' else 'Whip').lower() in txt.lower()
for preview in ('FORM_8_LONG_WHIP_V101_PREVIEW.png','RIEN_LONGSWORD_GREATSWORD_COMPARISON.png'):
    assert (root/preview).is_file()
print('PASS: v0.10.1 long whip alpha/geometry/BBModel, nine-form mapping, art previews')
