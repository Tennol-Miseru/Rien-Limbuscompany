#!/usr/bin/env python3
"""Offline v0.10.18 regressions (not a Gradle or Minecraft runtime test)."""
from pathlib import Path
import json, re, struct
from PIL import Image

root=Path(__file__).resolve().parents[1]
java=root/'src/main/java/io/github/oraclearsenal'
client=root/'src/client/java/io/github/oraclearsenal/client'
assets=root/'src/main/resources/assets/oraclearsenal'

bat=(root/'一键编译.bat').read_bytes()
assert not bat.startswith(b'\xef\xbb\xbf')
assert bat.count(b'\n')==bat.count(b'\r\n') and bat.count(b'\r\r\n')==0
bt=bat.decode('utf8')
for loc in ('jdk-21','gradle-8.14.6','gradle-home'):
    assert ('D:'+chr(92)+'模组协同'+chr(92)+'MCDev'+chr(92)+loc) in bt, loc
assert r'E:\模组协同\MCDev' not in bt

b=(root/'build.gradle').read_text('utf8')
assert 'lo.doubleValue() < -16.0' in b and 'hi.doubleValue() > 32.0' in b
assert 'lo.doubleValue() >= hi.doubleValue()' in b
assert 'Math.abs(a - r.angle.doubleValue()) < 0.0001d' in b

hud=(client/'HermesProgressHud.java').read_text('utf8')
assert 'import net.minecraft.Util;' in hud
assert 'import net.minecraft.util.Util;' not in hud
assert 'hermes_progress_hud.png' in hud and 'graphics.fill(' not in hud
assert Image.open(assets/'textures/gui/hermes_progress.png').size==(129,125)
assert Image.open(assets/'textures/gui/hermes_progress_hud.png').size==(28,27)
assert 'Integer.toString(progress)' in hud and 'progress <= 0' in hud
assert 'progress > lastVisibleProgress' in hud and 'progress == 9' in hud

combat=(java/'OracleCombat.java').read_text('utf8')
npc=(java/'RienNpcEntity.java').read_text('utf8')
assert 'RienSounds.RIEN_EFFORT, SoundSource.PLAYERS' not in combat
assert 'if (source instanceof RienNpcEntity' in combat
assert 'RienSounds.RIEN_EFFORT' in npc and 'RienSounds.RIEN_LAUGH' in npc
assert 'RienSounds.playAttack' in combat
assert 'private static final long IDLE_REVERT_TICKS = 200L;' in combat

particles=(java/'RienParticles.java').read_text('utf8')
assert '1 + level.random.nextInt(2)' in particles
assert '2 + level.random.nextInt(2)' in particles
assert '3 + level.random.nextInt(3)' in particles
assert combat.count('RienParticles.departure(')>=3
assert combat.count('RienParticles.arrival(')>=3
assert npc.count('RienParticles.departure(')==1
assert npc.count('RienParticles.arrival(')==1
assert 'RienParticles.blink(' not in combat+npc
assert 'RienParticles.flourish(' not in npc

staff=json.loads((assets/'models/item/twin_serpent_staff.json').read_text('utf8'))
assert len(staff['elements'])==93
assert len(staff['overrides'])==10
for i,override in enumerate(staff['overrides'],1):
    assert override['model']==f'oraclearsenal:item/form_{i}'
allowed=(-45,-22.5,0,22.5,45)
rotations=[e['rotation'] for e in staff['elements'] if 'rotation' in e]
assert len(rotations)==48
assert all(r['axis']=='z' and any(abs(r['angle']-valid)<1e-4 for valid in allowed) for r in rotations)
assert (root/'blockbench/twin_serpent_staff.bbmodel').is_file()
assert Image.open(assets/'textures/item/twin_serpent_staff.png').size==(64,64)
assert (assets/'textures/item/twin_serpent_staff.png').read_bytes()==(assets/'textures/item/rien_knight_lance_grip.png').read_bytes()
assert len(json.loads((assets/'sounds.json').read_text('utf8')))==13
assert len(list((assets/'sounds').rglob('*.ogg')))==25
# The v0.10.18 checks remain applicable to later releases.
version_text = (root/'gradle.properties').read_text('utf8')
import re
match = re.search(r'^mod_version=(\d+)\.(\d+)\.(\d+)\s*$', version_text, re.M)
assert match and tuple(map(int, match.groups())) >= (0, 10, 18), match
print('PASS: D-drive BAT UTF-8/CRLF, Gradle numeric validation and HUD Util import')
print('PASS: whole Hermes icon, 1-9 pulse/zero-hide, no backdrop')
print('PASS: no player voice; NPC voice retained; 3-5 petals per teleport')
print('PASS: 93-element staff compatible rotations, 10 overrides, texture shared with lance grip')
print('PASS: unchanged 13/25 sound bank')
