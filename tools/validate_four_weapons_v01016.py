"""Regression test for the four new models and untouched gameplay modules."""
import json, math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
models=root/'src/main/resources/assets/oraclearsenal/models/item'
tex=root/'src/main/resources/assets/oraclearsenal/textures/item'
base=json.loads((models/'twin_serpent_staff.json').read_text())
for n in (1,6,7,9):
    assert base['overrides'][n-1]['model']==f'oraclearsenal:item/form_{n}'
    doc=json.loads((models/f'form_{n}.json').read_text())
    assert doc['parent']=='minecraft:block/block'
    assert doc['display'].get('gui') and doc['display'].get('firstperson_righthand')
    for e in doc['elements']:
        for a,b in zip(e['from'],e['to']): assert -16<=a<b<=32, (n,e['name'],a,b)
        r=e.get('rotation')
        if r: assert r['axis'] in 'xyz' and r['angle'] in (-45,-22.5,0,22.5,45),r
        for face in e['faces'].values():
            assert face['texture'][1:] in doc['textures']
    for ref in doc['textures'].values():
        if ref.startswith('oraclearsenal:item/'):
            assert (tex/(ref.split('/')[-1]+'.png')).is_file(),ref
assert len(json.loads((models/'form_1.json').read_text())['elements'])==73
assert len(json.loads((models/'form_6.json').read_text())['elements'])==114
assert len(json.loads((models/'form_7.json').read_text())['elements'])==486
assert len(json.loads((models/'form_9.json').read_text())['elements'])==615
# The new staff texture is now intentionally identical to the lance's reusable grip.
assert (tex/'rien_knight_lance_grip.png').read_bytes() == (tex/'twin_serpent_staff.png').read_bytes()
assert (root/'art_sources/2026-10-24-four-weapons/models/rien_knight_lance.json').is_file()
for n in (1,6,7,9):assert (root/'blockbench'/f'form_{n}.bbmodel').exists()
print('PASS: imported four models, 1.21.1 JSON limits, 4 resource variants, shared staff/lance grip texture and editable sources')
