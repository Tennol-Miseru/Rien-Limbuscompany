#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
assert 'mod_version=0.10.2' in (ROOT/'gradle.properties').read_text(encoding='utf8')
for tex in ['greatsword_blade_alpha.png','colossal_blade_alpha.png']:
    assert (ROOT/'src/main/resources/assets/oraclearsenal/textures/item'/tex).exists(), tex
for mdl in ['form_3.json','form_6.json']:
    obj=json.loads((ROOT/'src/main/resources/assets/oraclearsenal/models/item'/mdl).read_text(encoding='utf8'))
    assert obj['parent']=='minecraft:block/block'
    assert len(obj['elements']) >= 10
assert (ROOT/'FORM_3_GREATSWORD_V102_PREVIEW.png').exists()
assert (ROOT/'FORM_6_COLOSSAL_V102_PREVIEW.png').exists()
assert (ROOT/'RIEN_GREATSWORD_COLOSSAL_V102_COMPARISON.png').exists()
print('PASS: v0.10.2 greatsword/colossal blade swap + straightening assets')
