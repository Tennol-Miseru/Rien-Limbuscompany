#!/usr/bin/env python3
"""Offline static regression checks. Does NOT replace Gradle or runClient."""
from pathlib import Path
import json
import sys
import zipfile
import hashlib

base = Path(__file__).resolve().parents[1]
assets = base / 'src/main/resources/assets/oraclearsenal'
animations = assets / 'player_animations'
models = assets / 'models/item'

errors = []
def check(ok, msg):
    if not ok: errors.append(msg)
    print(('PASS' if ok else 'FAIL') + '  ' + msg)

check('mod_version=0.10.25' in (base/'gradle.properties').read_text(), 'release version')
check(all((base/p).exists() for p in (
    'src/main/java/io/github/oraclearsenal/CombatMovement.java',
    'src/main/java/io/github/oraclearsenal/CombatSwingPayload.java',
    'src/main/java/io/github/oraclearsenal/OracleCombat.java',
    'src/client/java/io/github/oraclearsenal/client/OraclePlayerAnimations.java',
)), 'client/server movement and intent wiring files')
for form in range(1, 10):
    f = animations/f'attack_form_{form}.animation.json'
    data = json.loads(f.read_text())
    animation = next(iter(data['animations'].values()))
    check(all(b in animation['bones'] for b in ('left_leg','right_leg','torso','body','right_arm','left_arm')),
          f'form {form}: independent full-body swing bones')
for clip in ('crescendo_lance_triple','attack_form_7','furioso_final_pose'):
    data = json.loads((animations/(clip+'.animation.json')).read_text())
    check(len(data['animations']) == 1, f'animation {clip} valid JSON')
models_data = json.loads((models/'twin_serpent_staff.json').read_text())
check(len(models_data['overrides'])==10 and
      [x['predicate']['custom_model_data'] for x in models_data['overrides']]==list(range(1,11)),
      'CustomModelData 1..10 mapping')
scythe=json.loads((models/'form_9.json').read_text())
check(len(scythe['elements']) == 615, 'scythe v3 mesh element count unchanged')
audio=json.loads((assets/'sounds.json').read_text())
sound_files=list((assets/'sounds').rglob('*.ogg'))
check(len(audio)==13 and len(sound_files)==25, 'original 13 sound events / 25 OGG clips')
bat=(base/'一键编译.bat').read_bytes()
check(bat[:3]!=b'\xef\xbb\xbf' and bat.count(b'\r\n')==bat.count(b'\n') and
      b'D:' in bat and b'GRADLE_USER_HOME' in bat, 'BAT D-drive, UTF-8 no BOM, CRLF')
# Optional asset parity against the original v0.10.24 source ZIP.
if len(sys.argv)>1:
    with zipfile.ZipFile(sys.argv[1]) as old:
        index={p for p in old.namelist() if p.startswith('OracleArsenal-Fabric-1.21.1/')}
        conserved=[p for p in index if '/src/main/resources/assets/oraclearsenal/' in p and
            ('/models/item/' in p or '/textures/' in p or '/sounds/' in p or p.endswith('sounds.json')) and not p.endswith('/')]
        check(all(hashlib.sha256((base/Path(p).relative_to('OracleArsenal-Fabric-1.21.1')).read_bytes()).digest()
                  == hashlib.sha256(old.read(p)).digest() for p in conserved),
              f'all {len(conserved)} original model/texture/audio assets byte-for-byte preserved')
if errors:
    print('\nFAILED:',len(errors),'checks')
    sys.exit(1)
print('\nStatic checks passed (NOT a Java/Gradle build).')
