from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
assert 'mod_version=0.9.0' in (r/'gradle.properties').read_text(encoding='utf8')
model=json.loads((r/'src/main/resources/assets/oraclearsenal/models/item/form_9.json').read_text(encoding='utf8'))
assert len(model['elements']) >= 50
assert model['display']['thirdperson_righthand']['scale'][0] >= 1.8
assert model['display']['firstperson_righthand']['scale'][0] >= 2.0
bb=json.loads((r/'blockbench/form_9.bbmodel').read_text(encoding='utf8'))
names=' '.join(e.get('name','') for e in bb['elements'])
for key in ['shaft_main','root_branch_main','blade_0','inner_blade_0','heel_hook','crimson_tail_main']:
    assert key in names
assert (r/'FORM_9_GIANT_SCYTHE_PREVIEW.png').exists()
print('PASS: v0.9.0 giant scythe refinement is present')
