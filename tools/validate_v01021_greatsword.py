"""Form 6 v2 resource and source consistency validation."""
from pathlib import Path
import json, hashlib
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/oraclearsenal'
M = ASSETS / 'models/item/form_6.json'
T = ASSETS / 'textures/item'
B = ROOT / 'blockbench/form_6.bbmodel'
source = ROOT / 'art_sources/2026-10-24-greatsword-v2'
model = json.loads(M.read_text(encoding='utf-8'))
bb = json.loads(B.read_text(encoding='utf-8'))
assert model.get('parent') == 'minecraft:block/block'
assert len(model['elements']) == len(bb['elements']) == 114
assert sum(len(e['faces']) for e in model['elements']) == 684
assert len(model.get('display', {})) == 7
assert model.get('display') == bb.get('display')
assert len(model['textures']) == 5
for e in model['elements']:
    for lo, hi in zip(e['from'], e['to']):
        assert -16 <= lo < hi <= 32, e.get('name')
    for fc in e['faces'].values():
        assert fc['texture'][1:] in model['textures']
refmodel = json.loads((ASSETS / 'models/item/twin_serpent_staff.json').read_text())
assert refmodel['overrides'][5] == {'predicate': {'custom_model_data': 6}, 'model': 'oraclearsenal:item/form_6'}
for name in ('form6_metal','form6_blade','form6_folds','form6_guard'):
    assert (T / (name+'.png')).is_file()
    assert model['textures'].get(str({'form6_metal':1,'form6_blade':2,'form6_folds':3,'form6_guard':4}[name])) == 'oraclearsenal:item/'+name
im = Image.open(T / 'form6_blade.png')
assert im.size == (512, 512), im.size
assert 'A' in im.getbands(), im.mode
assert not (T / 'form6_blade.png.mcmeta').exists(), 'Removed animated file must stay removed' 
assert (ROOT / 'art_sources/2026-10-24-greatsword-v2/source/form_6.bbmodel').read_bytes() == B.read_bytes()
assert (ROOT / 'art_sources/2026-10-24-greatsword-v2/assets/oraclearsenal/models/item/form_6.json').read_bytes() == M.read_bytes()
for png in ('form6_metal.png','form6_blade.png','form6_folds.png','form6_guard.png'):
    assert (source / 'assets/oraclearsenal/textures/item' / png).read_bytes() == (T / png).read_bytes(), png
print('PASS: Form 6 v2 has 114 cuboids / 684 faces / 7 display slots / correct CMD 6 / static single-frame blade / exact BBModel and material match')
