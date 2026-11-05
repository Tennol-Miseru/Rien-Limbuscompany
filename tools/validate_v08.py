"""Validate V0.8.4 structure, timelines, and animation-smoothing invariants.
This does not substitute for a Loom compilation or an in-game animation test.
"""
from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]
res=root/'src/main/resources'
clips=res/'assets/oraclearsenal/player_animations'
java_main=root/'src/main/java/io/github/oraclearsenal/OracleCombat.java'
client=root/'src/client/java/io/github/oraclearsenal/client/OraclePlayerAnimations.java'
text=java_main.read_text(encoding='utf8')
ct=client.read_text(encoding='utf8')
assert 'mod_version=0.8.4' in (root/'gradle.properties').read_text(encoding='utf8')
assert 'private static final int REPLICA_WINDUP = 10;' in text
assert 'private static final int REPLICA_STEP = 8;' in text
assert 'private static final int CA_BLINK_START = 40;' in text
assert 'private static final int CA_CONTACT_DELAY = 4;' in text
assert 'private static final int CA_FIRST_HIT = CA_BLINK_START + CA_CONTACT_DELAY;' in text
assert 'private static final int CA_STEP = 7;' in text
assert 'private static final int CA_DURATION = 142;' in text
assert 'OracleWeaponItem.consumeReplica(stack)' in text
assert 'crescendoBlink(p, target, form)' in text
assert 'if (c.mode == Finisher.REPLICA)' in text
assert 'CA_BLINK_START + c.stage * CA_STEP' in text
assert 'c.stage >= 9' in text
assert '代行·赫尔墨斯 ' in text
assert '.withStyle(net.minecraft.ChatFormatting.BLACK)' in text
assert 'replica_spectral_full' in ct and 'lacrimosa_full' in ct
assert 'AbstractFadeModifier.standardFadeIn' in ct
assert 'layer.replaceAnimationWithFade' in ct
assert '"combo_" + BY_FORM' not in ct
assert '"crescendo_" + BY_FORM' not in ct
assert 'playable instanceof KeyframeAnimation' in ct
assert 'FirstPersonMode.THIRD_PERSON_MODEL' in ct
cam=(root/'src/client/java/io/github/oraclearsenal/client/LacrimosaCamera.java').read_text(encoding='utf8')
assert 'ClipContext' in cam and 'getAnimationMode(stack) != 4' in cam
mix=json.loads((res/'oraclearsenal.client.mixins.json').read_text(encoding='utf8'))
assert 'LacrimosaCameraMixin' in mix['client'] and 'LacrimosaHandsMixin' in mix['client']
clips_data={}
for file in clips.glob('*.animation.json'):
    data=json.loads(file.read_text(encoding='utf8'))
    name,anim=next(iter(data['animations'].items()))
    assert name==file.name.removesuffix('.animation.json')
    assert anim['loop'] is False
    for bone, channels in anim['bones'].items():
        assert 'rotation' in channels
        frames=channels['rotation']
        assert len(frames)>=12
        stamps=sorted(float(t) for t in frames)
        assert stamps[0]==0 and abs(stamps[-1]-anim['animation_length'])<1e-4
        assert max(b-a for a,b in zip(stamps,stamps[1:]))<.0175
        assert all(len(v)==3 for v in frames.values())
        if bone in ('torso','head','body'):
            caps={'torso':[62,55,35], 'head':[32,44,25], 'body':[42,55,35]}[bone]
            assert all(all(abs(v[i])<=caps[i]+1e-5 for i in range(3)) for v in frames.values())
    clips_data[name]=anim
assert len(clips_data)==23,len(clips_data)
assert abs(clips_data['replica_spectral_full']['animation_length']-4.7)<1e-6
assert abs(clips_data['lacrimosa_full']['animation_length']-7.1)<1e-6
for name in ('replica_spectral_full','lacrimosa_full'):
    assert len(clips_data[name]['bones'])==7
for language in ('en_us','zh_cn'):
    lang=json.loads((res/f'assets/oraclearsenal/lang/{language}.json').read_text(encoding='utf8'))
    assert lang['message.oraclearsenal.replica_progress'].startswith('代行·赫尔墨斯')
for ix in range(1,10):
    assert (res/f'assets/oraclearsenal/models/item/form_{ix}.json').is_file()
print(f'PASS: {len(clips_data)} dense animation clips; continuous 4.7/7.1s finishers; Hermione/Hermes HUD; client cinematic and server timings; preserved 9 forms')
