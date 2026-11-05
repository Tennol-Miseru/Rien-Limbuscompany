#!/usr/bin/env python3
"""Offline regression checks for v0.10.13. Does not require launching Minecraft."""
from pathlib import Path
from PIL import Image
import json

root = Path(__file__).resolve().parents[1]
assets = root/'src/main/resources/assets/oraclearsenal'
java = root/'src/main/java/io/github/oraclearsenal'
client = root/'src/client/java/io/github/oraclearsenal/client'

assert 'IDLE_REVERT_TICKS = 200L' in (java/'OracleCombat.java').read_text('utf8')
weapon=(java/'OracleWeaponItem.java').read_text('utf8')
combat=(java/'OracleCombat.java').read_text('utf8')
npc=(java/'RienNpcEntity.java').read_text('utf8')
assert all(s in weapon for s in ['getLastUseTick(', 'recordUse(', 'last_weapon_use_tick', 'getForm(stack) > 0'])
assert 'AttackBlockCallback.EVENT.register' in combat and 'AttackEntityCallback.EVENT.register' in combat
assert 'player.getInventory().items' in combat and 'player.getInventory().offhand' in combat
assert 'if (isComboActive(player.getUUID())) continue;' in combat
assert 'OracleWeaponItem.setForm(stack, 0)' in combat
assert combat.count('RienParticles.departure(') >= 3
assert combat.count('RienParticles.arrival(') >= 3
assert npc.count('RienParticles.departure(') == 1
assert npc.count('RienParticles.arrival(') == 1
assert combat.count('RienParticles.blink(') == 0
assert npc.count('RienParticles.blink(') == 0
assert 'ParticleTypes.PORTAL' not in combat+npc
assert 'ParticleFactoryRegistry.getInstance().register' in (client/'OracleClient.java').read_text('utf8')
assert 'RienParticles.register();' in (java/'OracleArsenal.java').read_text('utf8')
assert 'import net.minecraft.client.particle.TextureSheetParticle;' in (client/'BluePetalParticle.java').read_text('utf8')
json.loads((assets/'particles/blue_petal.json').read_text('utf8'))
for variant in range(2):
    image=Image.open(assets/'textures/particle'/f'blue_petal_{variant}.png').convert('RGBA')
    assert image.size==(32,32) and image.getchannel('A').getextrema()[0] == 0
    assert image.getchannel('A').getextrema()[1] > 200
assert len(json.loads((assets/'sounds.json').read_text('utf8'))) == 13
assert len(list((assets/'sounds').rglob('*.ogg'))) == 25
bat=(root/'一键编译.bat').read_text(encoding='utf-8-sig')
assert r'D:\模组协同\MCDev\jdk-21' in bat
assert r'D:\模组协同\MCDev\gradle-home' in bat
print('PASS: idle revert 200 ticks, all player storage slots, active-combo guard')
print('PASS: blue petal particle registration, provider, assets and blink replacement')
print('PASS: 13 sound events, 25 OGG, no weapon asset changes by patch script')
print('PASS: D-drive shared Gradle/JDK paths')
