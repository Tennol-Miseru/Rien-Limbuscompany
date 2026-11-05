#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
assert 'mod_version=0.10.3' in (ROOT/'gradle.properties').read_text(encoding='utf8')
assert (ROOT/'src/main/resources/assets/oraclearsenal/textures/item/sledgehammer_head_alpha.png').exists()
obj=json.loads((ROOT/'src/main/resources/assets/oraclearsenal/models/item/form_5.json').read_text(encoding='utf8'))
assert obj['parent']=='minecraft:block/block'
assert obj['textures']['ink_head']=='oraclearsenal:item/sledgehammer_head_alpha'
assert len(obj['elements']) >= 15
assert (ROOT/'FORM_5_SLEDGEHAMMER_V103_PREVIEW.png').exists()
assert (ROOT/'blockbench/form_5.bbmodel').exists()
print('PASS: v0.10.3 form 5 sledgehammer assets')
