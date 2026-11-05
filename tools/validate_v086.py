"""Offline V0.8.5 NPC regression checks; does not prove Gradle or runtime compatibility."""
from pathlib import Path
import json
from PIL import Image
root=Path(__file__).resolve().parents[1]
res=root/'src/main/resources/assets/oraclearsenal'
java=(root/'src/main/java/io/github/oraclearsenal/RienNpcEntity.java').read_text(encoding='utf8')
combat=(root/'src/main/java/io/github/oraclearsenal/OracleCombat.java').read_text(encoding='utf8')
render=(root/'src/client/java/io/github/oraclearsenal/client/RienNpcRenderer.java').read_text(encoding='utf8')
assert 'mod_version=0.8.6' in (root/'gradle.properties').read_text(encoding='utf8')
for token in (
    'Attributes.MAX_HEALTH, NEW_MAX_HEALTH',
    'NEW_MAX_HEALTH = 360.0f',
    'Attributes.ARMOR, 15',
    'MASK_REMOVED',
    'MASK_REMOVAL_DURATION = 28',
    'getHealth() <= getMaxHealth() * 0.5f',
    'new ItemStack(OracleArsenal.RIEN_MASK)',
    'this.spawnAtLocation(new ItemStack(OracleArsenal.RIEN_MASK))',
    'tag.putBoolean("RienMaskRemoved", hasRemovedMask())',
    'tag.getBoolean("RienMaskRemoved")',
    'NEW_MAX_HEALTH * ratio',
    'PAGER_READING_DURATION = 36',
    'new ItemStack(OracleArsenal.PRESCRIPT_PAGER)',
    'viewer.sendSystemMessage(',
    'restoreStaff();',
    'if (pagerReadingTicks > 0)',
    'SoundEvents.NOTE_BLOCK_PLING.value()',
):
    assert token in java,token
assert 'damage *= rien.hasRemovedMask() ? 2.2f : 1.75f' in combat
assert 'entity.hasRemovedMask() && entity.getMaskRemovalTicks() <= 14' in render
assert 'int pagerTicks = entity.getPagerReadingTicks();' in render
assert 'int maskTicks = entity.getMaskRemovalTicks();' in render
masked=Image.open(res/'textures/entity/rien.png').convert('RGBA')
unmasked=Image.open(res/'textures/entity/rien_unmasked.png').convert('RGBA')
assert masked.size==unmasked.size==(64,64)
assert masked.getpixel((14,12))!=unmasked.getpixel((14,12))
for locale in ('zh_cn','en_us'):
    data=json.loads((res/f'lang/{locale}.json').read_text(encoding='utf8'))
    assert data['message.oraclearsenal.rien_received'].count('%s')==1
    assert all(f'message.oraclearsenal.prescript.{i}' in data for i in range(64))
assert (root/'tools/generate_rien_npc_skin.py').read_text(encoding='utf8').count('rien_unmasked.png')>=1
assert 'ORACLE_TERMINAL' not in java
print('PASS: V0.8.5 NPC stats / half-health state / NBT / two skins / mask drop / pager timing / player-balanced damage isolation')
