"""Procedurally author continuous 60 Hz keyframe tracks for PlayerAnimator v2.
60 Hz means *source curve sample density*, not a forced Minecraft render framerate.
Does not copy any third-party animation resources.
"""
from pathlib import Path
import json, math, bisect
ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'src/main/resources/assets/oraclearsenal/player_animations'
FPS=60
LIMITS={'torso':[62,55,35], 'head':[32,44,25], 'body':[42,55,35]}

def bounds(bone, values):
    lim=LIMITS.get(bone,[170,150,125])
    return [round(max(-lim[i],min(lim[i],float(v))),3) for i,v in enumerate(values)]

def interp(points,t):
    if t<=points[0][0]: return points[0][1]
    if t>=points[-1][0]: return points[-1][1]
    ix=bisect.bisect_right([p[0] for p in points],t)-1
    a,va=points[ix]; b,vb=points[ix+1]
    dt=b-a
    if dt<=1e-7:return vb
    # Piecewise cubic Hermite with no overshoot at extrema, bounded slopes.
    prev=points[ix-1] if ix>0 else None
    nxt=points[ix+2] if ix+2<len(points) else None
    u=(t-a)/dt; u2=u*u;u3=u2*u
    out=[]
    for n in range(3):
        d=(vb[n]-va[n])/dt
        dp=(va[n]-prev[1][n])/(a-prev[0]) if prev else d
        dn=(nxt[1][n]-vb[n])/(nxt[0]-b) if nxt else d
        m0=0 if dp*d<=0 else (2*dp*d/(dp+d) if abs(dp+d)>1e-8 else 0)
        m1=0 if dn*d<=0 else (2*dn*d/(dn+d) if abs(dn+d)>1e-8 else 0)
        m0=max(-3*abs(d),min(3*abs(d),m0))
        m1=max(-3*abs(d),min(3*abs(d),m1))
        out.append((2*u3-3*u2+1)*va[n]+(u3-2*u2+u)*dt*m0+(-2*u3+3*u2)*vb[n]+(u3-u2)*dt*m1)
    return out

def sample_data(poses, duration):
    bones={}
    for bone, tracks in poses.items():
        bones[bone]={}
        for kind, keyframes in tracks.items():
            points=sorted((float(t),[float(x) for x in vals]) for t,vals in keyframes.items())
            samples={}
            for frame in range(round(duration*FPS)+1):
                at=min(duration,frame/FPS)
                values=interp(points,at)
                if kind=='rotation': values=bounds(bone,values)
                else: values=[round(float(x),3) for x in values]
                samples[str(round(at,5))]=values
            bones[bone][kind]=samples
    return bones

def load(name):
    path=DIR/f'{name}.animation.json'
    obj=json.loads(path.read_text())
    return obj['animations'][name]

def save(name,poses,duration):
    obj={'format_version':'1.8.0','animations':{name:{'loop':False,'animation_length':duration,'bones':sample_data(poses,duration)}}}
    (DIR/f'{name}.animation.json').write_text(json.dumps(obj,separators=(',',':'))+'\n')

# Smooth the 21 v0.7 resources, honoring bone limits; retain original shapes and timings.
for file in list(DIR.glob('*.animation.json')):
    obj=json.loads(file.read_text()); name=list(obj['animations'])[0]; anim=obj['animations'][name]
    save(name,anim['bones'],float(anim['animation_length']))

# Build a reusable staged motion, with NO reset between hits: all poses live on one timeline.
FORM_STYLE=['slash_left','rapid_thrust','slash_right','rapid_thrust','heavy_down','heavy_down','rapid_thrust','long_whip','scythe_reap']

def make_sequence(name,duration,first,step,script):
    # script = cinematic or replica
    pose_times={b:{} for b in ('right_arm','left_arm','torso','head','right_leg','left_leg','body')}
    def add(t, right=(0,0,0),left=(0,0,0),torso=(0,0,0),head=(0,0,0),right_leg=(0,0,0),left_leg=(0,0,0),body=(0,0,0)):
        data={'right_arm':right,'left_arm':left,'torso':torso,'head':head,'right_leg':right_leg,'left_leg':left_leg,'body':body}
        for b,v in data.items(): pose_times[b][round(t,5)]=list(v)
    add(0)
    if script=='cinematic':
        add(.3,(-25,22,25),(-25,-22,-20),(-9,0,0),(-5,17,0))
        add(.7,(-80,32,37),(-76,-32,-33),(-20,16,6),(-12,-12,0),(12,0,0),(-10,0,0))
        add(1.1,(-120,40,50),(-90,-35,-40),(-16,8,4),(-10,0,0),(-7,0,0),(10,0,0))
        add(1.45,(-30,-30,15),(-36,23,-30),(15,-25,-5),(9,8,0),(-24,0,0),(25,0,0))
        add(1.8,(-75,-15,30),(-48,13,-20),(8,20,4),(-5,-6,0),(14,0,0),(-14,0,0))
        add(2.01,(-50,15,25),(-32,-11,-27),(5,0,0),(0,0,0))
    else:
        add(.15,(-62,30,28),(-52,-27,-20),(-10,0,0),(-5,0,0))
        add(.35,(-115,12,24),(-86,-12,-24),(-19,8,0),(-8,-6,0))
        add(.49,(-66,5,25),(-52,-5,-20),(-10,0,0))

    for i in range(9):
        at=first+i*step
        sign=1 if i%2==0 else -1
        form=i+1
        if form in (2,4,7):
            preR=(-80,sign*12,30); hitR=(-110,-sign*25,-14); hitL=(-40,0,-16)
        elif form in (5,6):
            preR=(-145,-5,12);hitR=(-46,sign*13,18);hitL=(-70,-sign*15,-28)
        elif form==8:
            preR=(-60,55,45);hitR=(-130,-65,-60);hitL=(-52,20,12)
        elif form==9:
            preR=(-155,-35,-20);hitR=(-92,70,-80);hitL=(-85,-30,-35)
        else:
            preR=(-60,sign*40,sign*35);hitR=(-122,-sign*48,-sign*40);hitL=(-42,sign*14,-18)
        # A stepped anticipation -> accelerated impact -> follow-through -> recovery.
        gap=min(.26,step*.77)
        add(at-.045,preR,(-48,-sign*20,-25),(-12,sign*16,sign*5),(-6,-sign*10,0),
            (sign*10,0,0),(-sign*8,0,0))
        add(at+gap*.30,hitR,hitL,(20,-sign*23,sign*8),(5,sign*15,0),
            (-sign*18,0,0),(sign*14,0,0))
        add(at+gap*.72,(-62,-sign*20,-sign*22),(-30,0,-10),(8,-sign*10,0),(2,0,0))
        add(at+gap*.98,(-55,sign*15,sign*22),(-28,-sign*10,-15),(-7,sign*10,0))
    after=first+8*step
    if script=='cinematic':
        add(after+.58,(-155,-50,-25),(-105,32,-24),(-30,28,5),(-14,0,0),(-20,0,0),(15,0,0))
        add(after+1.04,(-80,18,-35),(-80,-18,-15),(15,-10,-4),(12,12,0))
        add(after+1.52,(-35,0,6),(-45,0,-5),(0,0,0),(0,0,0))
        add(duration-.12,(-12,0,0),(-10,0,0),(0,0,0))
    else:
        add(after+.48,(-95,-40,-28),(-65,16,3),(-18,0,0))
        add(duration-.20,(-25,0,0),(-20,0,0),(0,0,0))
    add(duration)
    poses={b:{'rotation':{str(t):v for t,v in tr.items()}} for b,tr in pose_times.items()}
    save(name,poses,duration)

# replica 94 ticks/4.7s; hits at ticks 10,18,...74, scythe finish at 74, recover through tick 94.
make_sequence('replica_spectral_full',4.7,.5,.4,'replica')
# CA 142 ticks/7.1s; first hit tick 42 (2.1s), ninth tick 98 (4.9s), cinematic 2.2s finale.
make_sequence('lacrimosa_full',7.1,2.1,.35,'cinematic')

print('Smoothed all original clips and created two continuous 60Hz cinematic tracks.')
