#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
assert 'mod_version=0.10.4' in (ROOT/'gradle.properties').read_text(encoding='utf8')
obj=json.loads((ROOT/'src/main/resources/assets/oraclearsenal/models/item/form_5.json').read_text(encoding='utf8'))
assert obj['textures']=={'palette':'oraclearsenal:item/palette','particle':'oraclearsenal:item/palette'}
assert len(obj['elements']) >= 35
assert (ROOT/'blockbench/form_5.bbmodel').exists()
assert (ROOT/'FORM_5_SLEDGEHAMMER_V104_PREVIEW.png').exists()
print('PASS: v0.10.4 form 5 hammer rebuild')
