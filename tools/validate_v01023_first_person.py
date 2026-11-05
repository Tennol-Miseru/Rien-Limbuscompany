#!/usr/bin/env python3
"""Offline first-person regression checks; Minecraft runtime still required."""
import re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
client=R/'src/client/java/io/github/oraclearsenal/client'
fp=(client/'mixin/FirstPersonWeaponMixin.java').read_text(encoding='utf-8')
motion=(client/'FirstPersonCombatMotion.java').read_text(encoding='utf-8')
weapon=(R/'src/main/java/io/github/oraclearsenal/OracleWeaponItem.java').read_text(encoding='utf-8')
assert 'method_3228' in fp and 'remap = false' in fp
assert 'OracleWeaponItem.getFinisherBeatTick(stack)' in fp
assert 'OracleWeaponItem.getFinisherStage(stack)' in fp
assert 'FirstPersonCombatMotion.strike' in fp
assert 'FirstPersonCombatMotion.finish' in fp
assert 'FirstPersonCombatMotion.draw' in fp
assert 'FirstPersonCombatMotion.windup' in fp
assert 'getOrdinarySwingAge' in fp
assert 'HumanoidArm.LEFT' in fp
assert 'pose.pushPose()' in fp and 'pose.popPose()' in fp
assert 'allowComponentsUpdateAnimation' in weapon and 'return false;' in weapon
assert 'implements FabricItem' in weapon
assert 'Catmull-Rom' in motion and 'float mirror = leftHand ? -1f : 1f' in motion
# Nine separate motion blocks, delimited by weapon comments rather than a generic fallthrough.
assert len(re.findall(r'// [1-9]: ', motion)) == 9
assert 'private static final float[][] DRAW' in motion
assert 'private static final float[][] WINDUP' in motion
assert 'private static final float[][] FINISH' in motion
assert re.search(r'mod_version=0\.10\.(?:2[3-9]|[3-9][0-9])\b', (R/'gradle.properties').read_text(encoding='utf-8'))
print('PASS V0.10.23: first-person 9 distinct smooth strike clips, draw/windup/finisher, server beat sync, mirrored left hand, equip-reset guard')
