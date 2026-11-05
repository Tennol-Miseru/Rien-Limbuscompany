#!/usr/bin/env python3
"""Static regression for V0.10.22 smooth strike curves and single-frame blade."""
from pathlib import Path
from PIL import Image
import base64, hashlib, io, json, re
R=Path(__file__).resolve().parents[1]
assets=R/'src/main/resources/assets/oraclearsenal'
tex=assets/'textures/item/form6_blade.png'
img=Image.open(tex)
assert img.size == (512,512) and img.mode == 'RGBA',img.size
assert not (tex.parent/(tex.name+'.mcmeta')).exists(),'Still animated'
for bp in [R/'blockbench/form_6.bbmodel',R/'art_sources/2026-10-24-greatsword-v2/source/form_6.bbmodel']:
 b=json.loads(bp.read_text(encoding='utf-8'))
 embedded=next(x for x in b['textures'] if x['name']=='form6_blade.png')
 assert (embedded['width'],embedded['height'])==(512,512),bp
 raw=base64.b64decode(embedded['source'].split(',',1)[-1]); e=Image.open(io.BytesIO(raw))
 assert hashlib.sha256(e.tobytes()).digest()==hashlib.sha256(img.tobytes()).digest(),bp
assert re.search(r'mod_version=0\.10\.(?:22|2[3-9]|[3-9][0-9])\b', (R/'gradle.properties').read_text(encoding='utf-8'))
normal = assets/'player_animations'
clips=['crescendo_handaxe_front','crescendo_awl_stab','crescendo_greatsword_cleave','crescendo_rapier_uppercut','crescendo_hammer_front','crescendo_sword_down','crescendo_lance_triple','crescendo_long_whip_snap','crescendo_scythe_reap']
for i,name in enumerate(clips,1):
    for label,clip,length,count in [('finisher',name,.4,33),('normal',f'attack_form_{i}',.55,45)]:
        a=json.loads((normal/f'{clip}.animation.json').read_text(encoding='utf-8'))['animations'][clip]
        assert a['loop'] is False and abs(a['animation_length']-length)<1e-6
        for bone in ['right_arm','left_arm','torso','head','right_leg','left_leg','body']:
            track=a['bones'][bone]['rotation']
            assert len(track)==count,(clip,bone,len(track))
            times=[float(t) for t in track]
            assert times==sorted(times) and times[0]==0 and abs(times[-1]-length)<1e-4
            assert all(len(v)==3 for v in track.values())
            if bone=='body':assert len(a['bones'][bone]['position'])==count
java=(R/'src/client/java/io/github/oraclearsenal/client/OraclePlayerAnimations.java').read_text(encoding='utf-8')
fp=(R/'src/client/java/io/github/oraclearsenal/client/mixin/FirstPersonWeaponMixin.java').read_text(encoding='utf-8')
combat=(R/'src/main/java/io/github/oraclearsenal/OracleCombat.java').read_text(encoding='utf-8')
assert 'player.getAttackAnim(0.0f)' in java and 'player.swinging' in java
assert 'fallbackAge >= 0 && fallbackAge < 12' in java and 'start = fallbackStart' in java
assert 'ordinaryServer' in java and 'FINISHER_BY_FORM' in java
assert 'getOrdinarySwingAge' in fp and ('weaponStroke(pose' in fp or 'FirstPersonCombatMotion.strike' in fp)
assert 'AttackBlockCallback.EVENT.register' in combat and 'OracleWeaponItem.setAnimation(held, 3,' in combat
assert 'c.stage == FINISHER_STAGES ? 9' in combat and 'randomAttackForm(p, c.activeForm)' in combat
assert 'JAVA_HOME=D:\\模组协同\\MCDev\\jdk-21' in (R/'一键编译.bat').read_text(encoding='utf-8')
print('PASS V0.10.22: static blade synced in BBModels; 9+9 full-body smooth animation clips; hit/block/air trigger paths; finisher mapping intact')
