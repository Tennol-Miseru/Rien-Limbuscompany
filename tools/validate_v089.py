from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
res=r/'src/main/resources/assets/oraclearsenal'
assert 'mod_version=0.8.9' in (r/'gradle.properties').read_text(encoding='utf8')
model=json.loads((res/'models/item/form_3.json').read_text(encoding='utf8'))
assert len(model['elements']) >= 65
for el in model['elements']:
    assert len(el['from'])==len(el['to'])==3
    assert all(isinstance(v,(float,int)) and 0<=v<=16 for v in el['from']+el['to'])
    assert all(a<b for a,b in zip(el['from'],el['to']))
    if 'rotation' in el:
        rot=el['rotation']
        assert rot['axis'] in ('x','y','z')
        assert rot['angle'] in (-45,-22.5,0,22.5,45)
bb=json.loads((r/'blockbench/form_3.bbmodel').read_text(encoding='utf8'))
bb_names=' '.join(e.get('name','') for e in bb['elements'])
for key in ['guard_bar','central_fuller','tip_body','orn_l_71', 'tip_left_barb']:
    assert key in bb_names
assert len(bb['elements']) >= 65
print('PASS: v0.8.9 refined greatsword model is present and structurally valid')
