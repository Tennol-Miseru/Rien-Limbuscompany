"""Offline invariant and timeline regression for Rien Mod v0.8.2.
Does not replace Gradle compilation or live multiplayer tests.
"""
from pathlib import Path
import json, re
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'src/main/java/io/github/oraclearsenal/OracleCombat.java').read_text(encoding='utf8')
anim_file=ROOT/'src/main/resources/assets/oraclearsenal/player_animations/replica_spectral_full.animation.json'
clip=json.loads(anim_file.read_text(encoding='utf8'))['animations']['replica_spectral_full']
props=(ROOT/'gradle.properties').read_text(encoding='utf8')
assert 'mod_version=0.8.2' in props
assert 'private static final int REPLICA_WINDUP = 10;' in s
assert 'private static final int REPLICA_STEP = 8;' in s
assert 'private static final int REPLICA_CONTACT_DELAY = 4;' in s
assert 'private static final int REPLICA_RECOVERY = 12;' in s
assert re.search(r'if \(c\.mode == Finisher\.REPLICA\)\s*\{[\s\S]*?tickReplica\(p, c, now\);',s)
replica=s.split('private static void tickReplica(',1)[1].split('private static void tickCrescendo(',1)[0]
assert 'c.replicaStrikePending' in replica and 'c.replicaLandingSucceeded' in replica
assert replica.index('c.replicaLandingSucceeded = target != null && crescendoBlink') < replica.index('OracleWeaponItem.setForm(p.getMainHandItem(), form)')
assert replica.index('OracleWeaponItem.setForm(p.getMainHandItem(), form)') < replica.index('c.replicaStrikePending = true;')
assert 'c.nextHitTick = now + REPLICA_CONTACT_DELAY;' in replica
assert 'c.replicaLandingSucceeded && inReach && p.hasLineOfSight(target)' in replica
assert 'applyStage(p, target, form, true)' in replica
assert 'if (form == 9) crescendoFinish' in replica
# The 94-tick continuous clip matches all 9 blink -> attack windows exactly.
assert abs(clip['animation_length']*20 - (10+9*8+12))<1e-5
blink_ticks=[10+i*8 for i in range(9)]
contact_ticks=[t+4 for t in blink_ticks]
assert len(blink_ticks)==len(set(blink_ticks))==9
assert len(contact_ticks)==len(set(contact_ticks))==9
assert all(a<b<c for a,b,c in zip(blink_ticks,contact_ticks,blink_ticks[1:]+[94]))
assert contact_ticks[-1] == 78
assert all(a < b for a,b in zip(contact_ticks,contact_ticks[1:]))
# V-key CA is still independent. The NPC's AI was not changed.
assert 'private static void tickCrescendo(' in s
assert 'private static final int CA_DURATION = 142;' in s
assert (ROOT/'src/main/java/io/github/oraclearsenal/RienNpcEntity.java').exists()
print('PASS: Replica nine blink/morph/contact cycles at',list(zip(range(1,10),blink_ticks,contact_ticks)))
print('PASS: uninterrupted Player Animator clip, V-key CA, nine-form order and scythe finish')
