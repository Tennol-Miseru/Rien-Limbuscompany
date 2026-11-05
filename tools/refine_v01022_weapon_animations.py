#!/usr/bin/env python3
"""Regenerate 9 smooth 8-tick Furioso beats and 9 separate normal-attack clips.

Player Animator interpolates between keyframes during rendering. The 6-pose
source curves are treated as choreography anchors, not a frame-rate setting.
Shape-preserving cubic splines and full-body root motion make transitions
less abrupt without changing server attack timing, forms, or damage.
"""
from pathlib import Path
import json, bisect
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'tools/reference_assets/v01021_weapon_keyframes'
OUT=ROOT/'src/main/resources/assets/oraclearsenal/player_animations'
CLIPS=['crescendo_handaxe_front','crescendo_awl_stab','crescendo_greatsword_cleave',
       'crescendo_rapier_uppercut','crescendo_hammer_front','crescendo_sword_down',
       'crescendo_lance_triple','crescendo_long_whip_snap','crescendo_scythe_reap']

def pchip(pairs,x):
    """Continuous shape-preserving cubic, no surprise Euler-angle overshoots."""
    xx=[p[0] for p in pairs]; yy=[p[1] for p in pairs]
    n=len(xx)
    slopes=[(yy[i+1]-yy[i])/(xx[i+1]-xx[i]) for i in range(n-1)]
    deriv=[0.0]*n
    for k in range(1,n-1):
        a,b=slopes[k-1],slopes[k]
        if a*b>0:
            h0=xx[k]-xx[k-1];h1=xx[k+1]-xx[k]
            w0=2*h1+h0;w1=h1+2*h0
            deriv[k]=(w0+w1)/(w0/a+w1/b)
    # The motion is an attack, not an idle loop. Smooth starts and endings avoid twitch.
    deriv[0]=0.0;deriv[-1]=0.0
    if x<=xx[0]:return yy[0]
    if x>=xx[-1]:return yy[-1]
    i=bisect.bisect_right(xx,x)-1
    h=xx[i+1]-xx[i]; t=(x-xx[i])/h
    return ((2*t**3-3*t**2+1)*yy[i]+(t**3-2*t**2+t)*h*deriv[i]
            +(-2*t**3+3*t**2)*yy[i+1]+(t**3-t**2)*h*deriv[i+1])

def resample(source,source_length,duration,steps,strength):
    bones={}
    for bone,channels in source.items():
        target={}
        for channel,track in channels.items():
            if channel not in ('rotation','position') or not isinstance(track,dict):
                target[channel]=track
                continue
            anchors=sorted((float(t),v) for t,v in track.items())
            if not anchors or not isinstance(anchors[0][1],list):
                target[channel]=track
                continue
            components=[[ (t,float(v[i])) for t,v in anchors ] for i in range(3)]
            animation={}
            for j in range(steps+1):
                time=duration*j/steps
                t0=source_length*j/steps
                vals=[round(pchip(axis,t0)*strength,3) for axis in components]
                animation[f'{time:.4f}'.rstrip('0').rstrip('.') if j else '0']=vals
            target[channel]=animation
        bones[bone]=target
    return bones

for form,name in enumerate(CLIPS,1):
    data=json.loads((SRC/f'{name}.animation.json').read_text(encoding='utf-8'))
    original=data['animations'][name]
    assert abs(original['animation_length']-.4)<.01
    # 33 pose samples over .4s: meaningful easing while retaining the exact hit windows.
    original['bones']=resample(original['bones'],.4,.4,32,1.0)
    (OUT/f'{name}.animation.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Ordinary attacks get their OWN slightly slower and less exaggerated choreography.
    ordinary=f'attack_form_{form}'
    a={'format_version':'1.8.0','animations':{
        ordinary:{'loop':False,'animation_length':.55,
                  'bones':resample(json.loads((SRC/f'{name}.animation.json').read_text(encoding='utf-8'))['animations'][name]['bones'],.4,.55,44,.88)}
    }}
    (OUT/f'{ordinary}.animation.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Updated 9 Furioso full-body clips and 9 distinct ordinary-attack clips')
