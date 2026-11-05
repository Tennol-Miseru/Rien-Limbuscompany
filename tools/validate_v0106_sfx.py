#!/usr/bin/env python3
"""Offline sound packaging/integration checks; no Minecraft runtime required."""
from __future__ import annotations
import json, re, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/main/resources/assets/oraclearsenal'
manifest=json.loads((ASSETS/'sounds.json').read_text(encoding='utf8'))
assert len(manifest)==13, 'Must expose thirteen logical sound groups'
actual=[]
for group,detail in manifest.items():
    assert detail['subtitle']=='subtitles.oraclearsenal.'+group
    for desc in detail['sounds']:
        name=desc['name']
        assert name.startswith('oraclearsenal:')
        path=ASSETS/'sounds'/(name.split(':',1)[1]+'.ogg')
        assert path.is_file(),path
        assert path.read_bytes().startswith(b'OggS'),path
        actual.append(path)
assert len(actual)==len(set(actual))==25, 'All 25 approved clips must be used once'
for lang in ('en_us','zh_cn'):
    labels=json.loads((ASSETS/'lang'/f'{lang}.json').read_text(encoding='utf8'))
    for group in manifest:
        assert manifest[group]['subtitle'] in labels, (lang,group)
code_dir=ROOT/'src/main/java/io/github/oraclearsenal'
combat=(code_dir/'OracleCombat.java').read_text(encoding='utf8')
npc=(code_dir/'RienNpcEntity.java').read_text(encoding='utf8')
pager=(code_dir/'PrescriptPagerItem.java').read_text(encoding='utf8')
sounds=(code_dir/'RienSounds.java').read_text(encoding='utf8')
assert combat.count('RienSounds.playChange(')==3, 'normal blink + shared finisher stage + idle reversion'
assert npc.count('RienSounds.playChange(')==1, 'NPC morph should own its cue'
assert 'SoundEvents.ENDERMAN_TELEPORT' not in combat+npc
assert 'SoundEvents.END_PORTAL_SPAWN' not in combat+npc
assert 'SoundEvents.PLAYER_ATTACK_SWEEP' not in combat+npc
assert 'SoundEvents.NOTE_BLOCK_PLING' in pager and 'SoundEvents.NOTE_BLOCK_PLING' in npc, 'Pager and NPC should use the original pling sound'
assert 'target.isBlocking()' in combat and 'RienSounds.PARRY' in combat
assert 'RienSounds.SCYTHE_FINAL' in combat
assert 'RienSounds.MASK_SCARS' in npc and 'RienSounds.MASK_DROP' in npc
assert 'case 8 -> WHIP' in sounds
assert 'case 2, 4, 7 -> PIERCE' in sounds
assert 'case 5 -> IMPACT' in sounds
for event in manifest:
    if not re.search(r'registerSound\("'+re.escape(event)+r'"\)',sounds):
        raise AssertionError(f'Unregistered sound event {event}')
# Guard against stale Gradle counts and removed sounds returning in later archives.
script=(ROOT/'build.gradle').read_text(encoding='utf8')
assert "'mask_scars', 'crescendo_cue'" not in script, 'Old removed sound event in build.gradle'
assert 'allFiles.size() != 25 || allFiles.toSet().size() != 25' in script, 'Gradle expects wrong clip count'
assert '13 Rien sound events / 25 genuine OGG Vorbis clips' in script
assert 'crescendo_cue' not in manifest
assert not (ASSETS/'sounds/cinematic/sq2_1.ogg').exists()
assert {p.resolve() for p in (ASSETS/'sounds').rglob('*.ogg')}=={p.resolve() for p in actual}, 'Unreferenced audio left on disk'
assert 'crescendo_cue' not in sounds, 'Old cue was reintroduced in Java'
# Deliberately no mod_version assertion: this check must work in future source releases.
print('PASS: 25 OGG clips / 13 sound events / 2 subtitle languages')
print('PASS: normal blink, both finisher modes (shared stage), NPC play morph sound without teleport SFX')
print('PASS: weapon attack, parry, mask routes; old cinematic cue excluded')
