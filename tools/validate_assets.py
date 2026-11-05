"""Offline structural regression checks (not a replacement for running Gradle)."""
from pathlib import Path
from PIL import Image
import json

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'src/main/resources'
COUNT = 0
for file in RES.rglob('*.json'):
    json.loads(file.read_text(encoding='utf8'))
    COUNT += 1

MODID = 'oraclearsenal'
MODELS = RES / f'assets/{MODID}/models/item'
for i in range(1, 11):
    model = json.loads((MODELS / f'form_{i}.json').read_text(encoding='utf8'))
    assert len(model['elements']) >= (1 if i == 9 else 3), i
    for e in model['elements']:
        assert all(-16 <= x <= 32 for x in e['from'] + e['to']), e
        assert all(a < b for a, b in zip(e['from'], e['to'])), e

main = json.loads((MODELS / 'twin_serpent_staff.json').read_text(encoding='utf8'))
assert len(main['overrides']) == 10
assert [override['predicate']['custom_model_data'] for override in main['overrides']] == list(range(1, 11))
assert [override['model'] for override in main['overrides']] == [f'oraclearsenal:item/form_{i}' for i in range(1, 11)]
assert len(main['elements']) >= 8

pager = json.loads((MODELS / 'prescript_pager.json').read_text(encoding='utf8'))
assert len(pager['elements']) >= 12

for lang in ('zh_cn', 'en_us'):
    local = json.loads((RES / f'assets/{MODID}/lang/{lang}.json').read_text(encoding='utf8'))
    assert local['item.oraclearsenal.twin_serpent_staff']
    assert local['item.oraclearsenal.prescript_pager']
    lines = [local[f'message.oraclearsenal.prescript.{i}'] for i in range(64)]
    assert len(set(lines)) == 64, f'{lang}: duplicate pager prescripts'
    assert local['item.oraclearsenal.rien_mask']
    assert local['tooltip.oraclearsenal.rien_mask']
    assert 'item.oraclearsenal.oracle_terminal' not in local

assert Image.open(RES / f'assets/{MODID}/textures/item/palette.png').size == (64, 64)
for name in ('twin_serpent_staff', 'prescript_pager', 'rien_mask'):
    recipe = json.loads((RES / f'data/{MODID}/recipe/{name}.json').read_text())
    assert recipe['result']['id'] == f'{MODID}:{name}'
    assert len(recipe['pattern']) == 3
    assert set(''.join(recipe['pattern'])) - {' '} <= set(recipe['key'])
assert not (RES / f'data/{MODID}/recipe/oracle_terminal.json').exists()

mask_icon = Image.open(RES / f'assets/{MODID}/textures/item/rien_mask.png').convert('RGBA')
assert mask_icon.size == (64, 64) and 0 < mask_icon.getchannel('A').getbbox()[0] < 64
mask_model = json.loads((MODELS / 'rien_mask.json').read_text(encoding='utf8'))
assert mask_model['textures']['layer0'] == f'{MODID}:item/rien_mask'
armor_file = RES / f'assets/{MODID}/textures/models/armor/rien_mask_layer_1.png'
armor = Image.open(armor_file).convert('RGBA')
assert armor.size == (512, 256), armor.size
assert armor.getpixel((round(9 * 8), round(10 * 8)))[3] == 0
assert armor.getpixel((round(14 * 8), round(10 * 8)))[3] > 0
assert Image.open(RES / f'assets/{MODID}/textures/models/armor/rien_mask_layer_2.png').size == armor.size

java_main = (ROOT / 'src/main/java/io/github/oraclearsenal/OracleArsenal.java').read_text(encoding='utf8')
assert 'TWIN_SERPENT_STAFF' in java_main
assert 'ORACLE_TERMINAL' not in java_main
assert 'entries.accept(TWIN_SERPENT_STAFF)' in java_main
assert 'entries.accept(RIEN_MASK)' in java_main
mod = json.loads((RES / 'fabric.mod.json').read_text())
assert mod['id'] == MODID and mod['environment'] == '*'

npc_java = (ROOT / 'src/main/java/io/github/oraclearsenal/RienNpcEntity.java').read_text(encoding='utf8')
render_java = (ROOT / 'src/client/java/io/github/oraclearsenal/client/RienNpcRenderer.java').read_text(encoding='utf8')
assert 'new ItemStack(OracleArsenal.TWIN_SERPENT_STAFF)' in npc_java
assert 'OracleCombat.applyStage(this, target, stage, true)' in npc_java
assert 'extends PlayerModel<RienNpcEntity>' in render_java
npc_skin = Image.open(RES / 'assets/oraclearsenal/textures/entity/rien.png').convert('RGBA')
assert npc_skin.size == (64, 64)
print(f'PASS: {COUNT} JSON resources, single main weapon + 9 canonical forms + longsword morph, pager, wearable mask, Rien NPC and bilingual localization')
