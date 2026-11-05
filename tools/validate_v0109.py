"""Current v0.10.9 compatibility checks for staff morph/old pager sound.
Run from project root or any working directory with Python 3.10+.
"""
from pathlib import Path
import json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/main/resources/assets/oraclearsenal'
MODELS=ASSETS/'models/item'
CODE=ROOT/'src/main/java/io/github/oraclearsenal'
CLIENT=ROOT/'src/client/java/io/github/oraclearsenal/client'
prop=(ROOT/'gradle.properties').read_text(encoding='utf8')
assert 'mod_version=0.10.9' in prop
staff=json.loads((MODELS/'twin_serpent_staff.json').read_text(encoding='utf8'))
overrides=staff.get('overrides')
assert isinstance(overrides,list) and len(overrides)==10, 'staff must dispatch all morph variants'
assert [(o['predicate']['custom_model_data'],o['model']) for o in overrides] == [
    (i, f'oraclearsenal:item/form_{i}') for i in range(1,11)]
for i in range(1,11):
    m=json.loads((MODELS/f'form_{i}.json').read_text(encoding='utf8'))
    assert m.get('elements'),f'form {i} missing elements'
    assert (ROOT/'blockbench'/f'form_{i}.bbmodel').exists()
    for elem in m['elements']:
        assert all(0 <= x < y <= 16 for x,y in zip(elem['from'],elem['to'])),(i,elem)
    for value in m.get('textures',{}).values():
        tex = value.split(':')[-1]
        assert (ASSETS/'textures'/f'{tex}.png').is_file(),(i,value)
longsword=json.loads((MODELS/'form_10.json').read_text(encoding='utf8'))
assert longsword['textures']['blade']=='oraclearsenal:item/ink_longsword_blade_alpha'
assert Image.open(ASSETS/'textures/item/ink_longsword_blade_alpha.png').getchannel('A').getextrema()==(0,255)
assert not (MODELS/'ink_longsword.json').exists()
assert not (ROOT/'src/main/resources/data/oraclearsenal/recipe/ink_longsword.json').exists()
java=(CODE/'OracleArsenal.java').read_text(encoding='utf8')
assert 'INK_LONGSWORD' not in java and 'id("ink_longsword")' not in java
item=(CODE/'OracleWeaponItem.java').read_text(encoding='utf8')
assert 'Math.min(10, data.copyTag().getInt("form"))' in item
combat=(CODE/'OracleCombat.java').read_text(encoding='utf8')
assert 'p.getRandom().nextInt(10) + 1' in combat
assert 'case 10 -> 4.0f' in combat
assert 'c.stage >= 9' in combat
assert 'if (form == 9) crescendoFinish' in combat and 'if (form == 9) caFinish' in combat
assert 'int form = ++c.stage' in combat
npc=(CODE/'RienNpcEntity.java').read_text(encoding='utf8')
assert 'this.random.nextInt(10) + 1' in npc
assert 'if (comboStage > 9)' in npc
assert npc.count('SoundEvents.NOTE_BLOCK_PLING.value()')==2
pager=(CODE/'PrescriptPagerItem.java').read_text(encoding='utf8')
assert 'SoundEvents.NOTE_BLOCK_PLING.value()' in pager
assert 'RienSounds.WEAPON_CHANGE' not in pager
assert 'RienSounds.playChange(' in combat and 'RienSounds.playChange(' in npc
anim=(CLIENT/'OraclePlayerAnimations.java').read_text(encoding='utf8')
assert '"scythe_reap", "slash_right"' in anim
assert 'Math.min(9, form - 1)' in anim
for lang in ('zh_cn','en_us'):
    d=json.loads((ASSETS/'lang'/f'{lang}.json').read_text(encoding='utf8'))
    assert 'form.oraclearsenal.10' in d
    assert 'item.oraclearsenal.ink_longsword' not in d
bat=(ROOT/'一键编译.bat').read_text(encoding='utf-8-sig')
for path in [r'E:\模组协同\MCDev\jdk-21',r'E:\模组协同\MCDev\gradle-8.14.6',r'E:\模组协同\MCDev\gradle-home']:
    assert path in bat,path
assert 'E:\\MCDev\\' not in bat
assert (ROOT/'INK_LONGSWORD_MODEL_PREVIEW.png').exists()
print('PASS: model routing 0..10, canonical nine-hit combos, NPC morph, old pager sound, shared build paths')
