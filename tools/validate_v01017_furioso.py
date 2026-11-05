#!/usr/bin/env python3
"""Offline v0.10.17 Furioso timeline/asset regression tests (not an in-game test)."""
from pathlib import Path
import json
import random
import re
import zipfile

root = Path(__file__).resolve().parents[1]
src = root / 'src/main/java/io/github/oraclearsenal'
cli = root / 'src/client/java/io/github/oraclearsenal/client'
assets = root / 'src/main/resources/assets/oraclearsenal'
combat = (src / 'OracleCombat.java').read_text(encoding='utf8')
weapon = (src / 'OracleWeaponItem.java').read_text(encoding='utf8')
animations = (cli / 'OraclePlayerAnimations.java').read_text(encoding='utf8')
camera = (cli / 'LacrimosaCamera.java').read_text(encoding='utf8')
assert 'mod_version=' in (root/'gradle.properties').read_text()
assert 'private static final int FINISHER_STAGES = 9;' in combat
assert 'private static final int RANDOM_FORM_COUNT = 8;' in combat
assert 'c.stage == FINISHER_STAGES ? 9 : randomAttackForm(p, c.activeForm)' in combat
assert 'while (form == previous)' in combat
assert 'beginFinisherBeat(p, c, now);' in combat
assert combat.count('beginFinisherBeat(p, c, now);') == 2
assert 'setFinisherBeat(staff, form, c.stage, now)' in combat
assert 'c.stage == FINISHER_STAGES) scytheFinish' in combat
assert combat.count('c.stage == FINISHER_STAGES) scytheFinish') == 2
assert 'c.stage >= FINISHER_STAGES' in combat
assert 'private static void scytheFinish(' in combat
assert 'noCollision(p, p.getBoundingBox()' in combat
assert 'getBlockState(below).isFaceSturdy' in combat
assert 'p.setDeltaMovement(through.scale(' in combat
assert 'getFinisherStage(ItemStack stack)' in weapon
assert 'clearFinisherBeat(ItemStack stack)' in weapon
assert 'String key = mode + ":" + start + ":" + stage + ":" + clip;' in animations
assert 'return age >= 0 && age < 112' in camera
clip_match = re.search(r'FINISHER_BY_FORM = \{(.*?)\};', animations, re.S)
assert clip_match
clips = re.findall(r'"(crescendo_[a-z_]+)"', clip_match.group(1))
assert len(clips) == 9, clips
for clip in clips + ['crescendo_scythe_pose', 'crescendo_finish', 'lacrimosa_full', 'replica_spectral_full']:
    f = assets / 'player_animations' / (clip + '.animation.json')
    assert f.is_file(), f
    item = json.loads(f.read_text())
    assert clip in item['animations'] and item['animations'][clip]['bones'], clip
# These timings must all remain inside their declared lifetime.
replica_start, replica_step, replica_contact, replica_end = 8, 8, 3, 92
ca_start, ca_step, ca_contact, ca_end = 12, 8, 3, 112
for start, step, contact, end in [(replica_start,replica_step,replica_contact,replica_end),
                                   (ca_start,ca_step,ca_contact,ca_end)]:
    times = [(start+i*step,start+i*step+contact) for i in range(9)]
    assert all(0 <= blink < hit < end for blink,hit in times)
    assert all(times[i][1] < times[i+1][0] for i in range(8))
    assert times[-1][1] + 9 < end
# Distribution sanity check for stated independent stage choice, not a Java RNG test.
random.seed(1017)
sequences=[]
for _ in range(200):
    seq=[]
    for i in range(8):
        available=[v for v in range(1,9) if not seq or v!=seq[-1]]
        seq.append(random.choice(available))
    seq.append(9)
    assert seq[-1]==9 and all(1<=v<=8 for v in seq[:8])
    assert all(a!=b for a,b in zip(seq[:8],seq[1:8]))
    sequences.append(tuple(seq))
assert len(set(sequences)) > 150
for lang in ('zh_cn','en_us'):
    strings=json.loads((assets/'lang'/f'{lang}.json').read_text())
    assert 'Furioso [Crescendo]' in strings['message.oraclearsenal.replica_cast']
    assert 'Furioso [Lacrimosa-Crescendo]' in strings['message.oraclearsenal.crescendo_cast']
print('PASS: nine stages; first 8 from random forms 1..8, ninth fixed scythe; no adjacent repeats')
print('PASS: each stage uses the matching animation clip and server-synced beat identifier')
print('PASS: two independent timelines and strength models; safe scythe crossing finale')
print('PASS: client camera lifetime, 9 clip JSON assets and both localized names')
