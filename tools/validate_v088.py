"""Structural regression check for the eighth-form long whip, not game runtime verification."""
from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
res=r/'src/main/resources/assets/oraclearsenal'
assert 'mod_version=0.8.8' in (r/'gradle.properties').read_text(encoding='utf8')
for lang,value in [('zh_cn','长鞭'),('en_us','Long Whip')]:
    d=json.loads((res/f'lang/{lang}.json').read_text(encoding='utf8'))
    assert d['form.oraclearsenal.8']==value
model=json.loads((res/'models/item/form_8.json').read_text(encoding='utf8'))
base=json.loads((res/'models/item/twin_serpent_staff.json').read_text(encoding='utf8'))
assert 'oraclearsenal:item/form_8' in [o['model'] for o in base['overrides']]
assert len(model['elements'])>=28
assert len([e for e in model['elements'] if e.get('rotation')])>=12
for el in model['elements']:
    assert len(el['from'])==len(el['to'])==3
    assert all(isinstance(v,(float,int)) and 0<=v<=16 for v in el['from']+el['to'])
    assert all(a<b for a,b in zip(el['from'],el['to']))
    if 'rotation' in el:
        rot=el['rotation']
        assert rot['axis']=='z' and rot['angle'] in (-45,-22.5,0,22.5,45)
assert not (res/'models/item/chain.json').exists()
bb=json.loads((r/'blockbench/form_8.bbmodel').read_text(encoding='utf8'))
part_names=' '.join(e.get('name','') for e in bb['elements'])
assert all(s not in part_names for s in ('lock_', 'link_', 'weight'))
assert 'continuous_lash_' in part_names and 'silver_tip' in part_names
java=(r/'src/main/java/io/github/oraclearsenal/OracleCombat.java').read_text(encoding='utf8')
assert '八式·长鞭' in java and '八式·锁链' not in java
assert 'Long whip: broad, fast lash' in java
first=(r/'src/client/java/io/github/oraclearsenal/client/mixin/FirstPersonWeaponMixin.java').read_text()
assert 'Ink-dark long whip' in first
client=(r/'src/client/java/io/github/oraclearsenal/client/OraclePlayerAnimations.java').read_text()
assert '"long_whip", "scythe_reap"' in client
for name in ('long_whip','crescendo_long_whip_snap','combo_long_whip','lacrimosa_full'):
    anim=json.loads((res/f'player_animations/{name}.animation.json').read_text(encoding='utf8'))['animations'][name]
    assert anim['animation_length']>0 and anim['loop'] is False
    assert 'right_arm' in anim['bones']
ca=json.loads((res/'player_animations/lacrimosa_full.animation.json').read_text(encoding='utf8'))['animations']['lacrimosa_full']
assert ca['animation_length']==7.1
frames=ca['bones']['torso']['rotation']
assert max(abs(float(v)) for t,values in frames.items() if 4.38<float(t)<4.87 for v in values)<=24.001
print('PASS: 8th form is long whip: naming, model, BBModel, valid rotations, action, CA timeline and unchanged model override')
