"""Validate CA nine teleport -> morph -> strike beats against continuous movie timing.
This is a source/timing regression check, not a live Gradle/game test.
"""
from pathlib import Path
import json, re
r=Path(__file__).resolve().parents[1]
s=(r/'src/main/java/io/github/oraclearsenal/OracleCombat.java').read_text(encoding='utf8')
assert 'mod_version=0.8.4' in (r/'gradle.properties').read_text(encoding='utf8')
assert 'private static final int CA_BLINK_START = 40;' in s
assert 'private static final int CA_CONTACT_DELAY = 4;' in s
assert 'private static final int CA_STEP = 7;' in s
assert 'private static final int CA_DURATION = 142;' in s
ca=s.split('private static void tickCrescendo(',1)[1].split('public static boolean blinkAndMorph(',1)[0]
assert 'c.caStrikePending' in ca and 'c.caLandingSucceeded' in ca
assert ca.count('++c.stage')==1
assert ca.index('c.caLandingSucceeded = target != null') < ca.index('OracleWeaponItem.setForm(p.getMainHandItem(), form)') < ca.index('c.caStrikePending = true;')
assert 'c.nextHitTick = now + CA_CONTACT_DELAY;' in ca
assert 'CA_BLINK_START + c.stage * CA_STEP' in ca
assert 'c.caLandingSucceeded && inReach && p.hasLineOfSight(target)' in ca
assert 'applyStage(p, target, form, true)' in ca
assert 'if (form == 9) caFinish(p, target)' in ca
assert 'c.caLastAnchor != null && crescendoBlinkAt' in ca
assert 'form == 1 || form == 5 || form == 9' not in ca
assert 'No opening teleport' in s and s.count('teleportFacing(p, target, safe);') == 0
assert 'private static boolean crescendoBlinkAt(' in s
assert 'pos.distanceToSqr(before) < .8 * .8' in s
assert 'if (!level.noCollision(p, moved)) continue;' in s
rep=s.split('private static void tickReplica(',1)[1].split('private static void tickCrescendo(',1)[0]
assert 'REPLICA_CONTACT_DELAY' in rep and 'c.replicaStrikePending' in rep
# Camera and continuous PlayerAnimator clip are unmodified and present.
cam=(r/'src/client/java/io/github/oraclearsenal/client/LacrimosaCamera.java').read_text(encoding='utf8')
anim=(r/'src/client/java/io/github/oraclearsenal/client/OraclePlayerAnimations.java').read_text(encoding='utf8')
assert 'Shot sample(' in cam and 'age >= 0 && age < 142' in cam
assert 'lacrimosa_full' in anim and 'replica_spectral_full' in anim
clip=json.loads((r/'src/main/resources/assets/oraclearsenal/player_animations/lacrimosa_full.animation.json').read_text(encoding='utf8'))['animations']['lacrimosa_full']
assert clip['animation_length']==7.1
blinks=[40+i*7 for i in range(9)]
hits=[b+4 for b in blinks]
assert blinks==[40,47,54,61,68,75,82,89,96]
assert hits==[44,51,58,65,72,79,86,93,100]
assert len(set(blinks))==len(set(hits))==9
assert all(b<h<n for b,h,n in zip(blinks,hits,blinks[1:]+[142]))
print('PASS: 9 unique CA blink/morph/hit windows:',list(zip(range(1,10),blinks,hits)))
print('PASS: 142-tick unbroken Player Animator CA clip and film camera retained; Replica unchanged')
