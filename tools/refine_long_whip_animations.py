"""V0.8.8: long-whip animation pass, including the continuous CA's 8th beat.
Safe to re-run after any script which rewrites lacrimosa_full: never restarts the
critical-art clip, and only alters the 8th beat. No third-party assets.
"""
from pathlib import Path
import json, math
ROOT=Path(__file__).resolve().parents[1]
ANIM=ROOT/'src/main/resources/assets/oraclearsenal/player_animations'


def load(name):
    p=ANIM/(name+'.animation.json')
    doc=json.loads(p.read_text(encoding='utf8'))
    return p,doc,doc['animations'][name]

def dump(path,doc):
    path.write_text(json.dumps(doc,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')

def lerp(a,b,t):
    u=max(0.0,min(1.0,t)); u=u*u*(3-2*u)
    return [round(x+(y-x)*u,3) for x,y in zip(a,b)]

def staged_sample(t,stages):
    if t <= stages[0][0]: return stages[0][1]
    if t >= stages[-1][0]: return stages[-1][1]
    for (a,va),(b,vb) in zip(stages,stages[1:]):
        if a<=t<=b: return lerp(va,vb,(t-a)/(b-a))
    return stages[-1][1]

# New normal attack: distinct whip draw, circle, abrupt forward snap, follow through.
# Keep the old chain_whip clip only for old assets; no registration points to it.
path,doc,old=load('chain_whip')
new=json.loads(json.dumps(doc))
new['animations']={'long_whip':{
    'loop':False,'animation_length':.55,'bones':{}
}}
tracks={
    'right_arm':[(0.,[-32,38,15]),(.12,[-95,56,45]),(.22,[-158,68,44]),(.31,[-72,-62,-45]),(.38,[-118,-42,-28]),(.55,[-12,0,0])],
    'left_arm':[(0.,[-18,-8,-8]),(.12,[-28,-22,-10]),(.22,[-50,-18,-18]),(.31,[-52,10,8]),(.38,[-30,8,2]),(.55,[0,0,0])],
    'torso':[(0.,[2,6,0]),(.12,[2,13,0]),(.22,[4,15,0]),(.31,[6,-16,0]),(.38,[4,-8,0]),(.55,[0,0,0])],
    'head':[(0.,[0,0,0]),(.12,[0,7,0]),(.22,[0,10,0]),(.31,[0,-8,0]),(.38,[0,-4,0]),(.55,[0,0,0])]
}
for bone,keys in tracks.items():
    frames={}
    for i in range(34):
        t=min(.55,i/60)
        frames[str(round(t,5))]=staged_sample(t,keys)
    new['animations']['long_whip']['bones'][bone]={'rotation':frames}
dump(ANIM/'long_whip.animation.json',new)

# Dedicated short reference clips for artists, not separately restarted by CA.
for old_name,new_name in [
    ('crescendo_chain_lock','crescendo_long_whip_snap'),
    ('combo_chain_whip','combo_long_whip')
]:
    path,doc,anim=load(old_name)
    updated=json.loads(json.dumps(doc))
    updated['animations']={new_name:anim}
    dump(ANIM/(new_name+'.animation.json'),updated)

# Continuous CA: preserve original source clip + replace only 8th beat with
# two broad arm arcs and a crisp snap, keeping torso at < 20 degrees.
path,doc,ca=load('lacrimosa_full')
profiles={
    'right_arm':[(4.38,[-58,24,24]),(4.48,[-114,65,56]),(4.56,[-152,45,38]),(4.66,[-70,-64,-54]),(4.73,[-112,-36,-24]),(4.87,[-72,0,-8])],
    'left_arm':[(4.38,[-24,-12,-6]),(4.48,[-46,-16,-16]),(4.56,[-54,-12,-12]),(4.66,[-48,14,4]),(4.73,[-30,10,0]),(4.87,[-25,0,-4])],
    'torso':[(4.38,[2,8,0]),(4.48,[2,15,0]),(4.56,[4,17,0]),(4.66,[6,-16,0]),(4.73,[2,-8,0]),(4.87,[2,0,0])],
    'head':[(4.38,[0,5,0]),(4.48,[0,12,0]),(4.56,[0,10,0]),(4.66,[0,-9,0]),(4.73,[0,-6,0]),(4.87,[0,0,0])]
}
for bone,keys in profiles.items():
    frame_dict=ca['bones'][bone]['rotation']
    for ts,v in list(frame_dict.items()):
        t=float(ts)
        if t<4.30 or t>4.95: continue
        # Blend over 6 frames to not snap on either edge of replacement window.
        w=min(1.,(t-4.30)/.10,(4.95-t)/.10)
        frame_dict[ts]=[round(x,3) for x in lerp(v,staged_sample(t,keys),w)]
dump(path,doc)
print('Created long whip ordinary + reference clips and updated CA beat 8 in-place')
