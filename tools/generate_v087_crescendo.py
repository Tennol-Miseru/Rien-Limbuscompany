"""Regenerate the v0.8.7 Lacrimosa-Crescendo PlayerAnimator timeline.
Focuses on cleaner torso posture and weapon-identity poses:
handaxe chop, awl stab, sword cleave, rapier uppercut, hammer impact,
colossal blade cleave, knight lance triple pierce, long-whip snap, scythe finale pose.
"""
from pathlib import Path
import json, bisect
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'src/main/resources/assets/oraclearsenal/player_animations'
FPS=60
LIMITS={'torso':[24,24,18], 'head':[18,30,18], 'body':[18,20,18], 'right_leg':[35,25,15], 'left_leg':[35,25,15]}

def bounds(bone, values):
    lim=LIMITS.get(bone,[170,160,135])
    return [round(max(-lim[i], min(lim[i], float(v))), 3) for i,v in enumerate(values)]

def interp(points, t):
    if t<=points[0][0]: return points[0][1]
    if t>=points[-1][0]: return points[-1][1]
    xs=[p[0] for p in points]
    ix=bisect.bisect_right(xs,t)-1
    a,va=points[ix]; b,vb=points[ix+1]
    u=(t-a)/(b-a); u2=u*u; u3=u2*u
    prev=points[ix-1] if ix>0 else None
    nxt=points[ix+2] if ix+2<len(points) else None
    out=[]
    for n in range(3):
        d=(vb[n]-va[n])/(b-a)
        dp=(va[n]-prev[1][n])/(a-prev[0]) if prev else d
        dn=(nxt[1][n]-vb[n])/(nxt[0]-b) if nxt else d
        m0=0 if dp*d<=0 else (2*dp*d/(dp+d) if abs(dp+d)>1e-8 else 0)
        m1=0 if dn*d<=0 else (2*dn*d/(dn+d) if abs(dn+d)>1e-8 else 0)
        m0=max(-3*abs(d), min(3*abs(d), m0)); m1=max(-3*abs(d), min(3*abs(d), m1))
        out.append((2*u3-3*u2+1)*va[n] + (u3-2*u2+u)*(b-a)*m0 + (-2*u3+3*u2)*vb[n] + (u3-u2)*(b-a)*m1)
    return out

def save(name, duration, tracks):
    bones={}
    for bone, channels in tracks.items():
        bones[bone]={}
        for kind, kfs in channels.items():
            pts=sorted((float(t), [float(x) for x in v]) for t,v in kfs.items())
            samples={}
            for frame in range(int(round(duration*FPS))+1):
                t=min(duration, frame/FPS)
                vals=interp(pts, t)
                if kind=='rotation': vals=bounds(bone, vals)
                else: vals=[round(v,3) for v in vals]
                samples[str(round(t,5))]=vals
            bones[bone][kind]=samples
    obj={'format_version':'1.8.0','animations':{name:{'loop':False,'animation_length':duration,'bones':bones}}}
    (DIR/f'{name}.animation.json').write_text(json.dumps(obj,separators=(',',':'))+'\n', encoding='utf8')

# This file intentionally mirrors the checked-in v0.8.7 resources.
print('This helper script documents the v0.8.7 CA resource generation process.')
