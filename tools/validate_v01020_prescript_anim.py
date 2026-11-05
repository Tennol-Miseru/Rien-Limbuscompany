#!/usr/bin/env python3
"""Offline regression checks for v0.10.20 prescript delivery / V-key choreography.
Not a substitute for Minecraft runtime gameplay validation.
"""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
java = ROOT / "src/main/java/io/github/oraclearsenal"
client = ROOT / "src/client/java/io/github/oraclearsenal/client"
res = ROOT / "src/main/resources/assets/oraclearsenal"
pager = (java / "PrescriptPagerItem.java").read_text(encoding="utf-8")
combat = (java / "OracleCombat.java").read_text(encoding="utf-8")
player = (client / "OraclePlayerAnimations.java").read_text(encoding="utf-8")
assert "tickInventory(ServerPlayer player, long now)" in pager
assert "if (now % 20L == 0L) PrescriptPagerItem.tickInventory(player, now);" in combat
assert "private static final int FIRST_MIN = 1200;" in pager
assert "private static final int REPEAT_MIN = 3000;" in pager
assert "scheduleNext(serverPlayer, stack, level.getGameTime(), false)" in pager
assert "setShowRightItem(true).setShowLeftItem(true)" in player
assert "lacrimosa_opening" in player and "furioso_final_pose" in player
clips=['crescendo_handaxe_front','crescendo_awl_stab','crescendo_greatsword_cleave',
       'crescendo_rapier_uppercut','crescendo_hammer_front','crescendo_sword_down',
       'crescendo_lance_triple','crescendo_long_whip_snap','crescendo_scythe_reap']
for clip in clips + ['lacrimosa_opening', 'crescendo_scythe_pose', 'furioso_final_pose']:
    fp = res / 'player_animations' / (clip+'.animation.json')
    d=json.loads(fp.read_text(encoding='utf-8'))['animations'][clip]
    bones=d['bones']
    for b in ('right_arm','left_arm','torso','head','right_leg','left_leg','body'):
        assert 'rotation' in bones[b],(clip,b)
        assert any(any(abs(n) > .01 for n in v) for v in bones[b]['rotation'].values()), (clip,b,'static')
    assert 'position' in bones['body'],clip
    if clip == 'furioso_final_pose':
        assert d['animation_length'] >= 1.6
    else:
        assert 0.39 <= d['animation_length'] <= .73, (clip,d['animation_length'])
assert 'randomAttackForm(p, c.activeForm)' in combat and 'c.stage == FINISHER_STAGES ? 9' in combat
model=json.loads((res/'models/item/form_9.json').read_text(encoding='utf-8'))
assert len(model['elements']) == 615
assert sum(len(e['faces']) for e in model['elements']) == 2458
assert 'edges.size() != 614' in (ROOT/'build.gradle').read_text(encoding='utf-8')
print('PASS: pager inventory polling + cooldown, 9 full-body weapon strikes, dedicated intro/1.5s final pose, 615-element scythe.')
