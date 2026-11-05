#!/usr/bin/env python3
"""V0.10.1: render the eighth-form Long Whip from a tapering curved ink ribbon
and a small editable 3D hilt. No chains, weighted ends, or blocky whip links.
Produces game item JSON, embedded-texture BBModel and real-resource preview.
"""
from pathlib import Path
import base64, json, math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'src/main/resources/assets/oraclearsenal'
ITEM=A/'models/item'; TEX=A/'textures/item'; BB=ROOT/'blockbench'
for folder in (ITEM,TEX,BB): folder.mkdir(parents=True,exist_ok=True)
N=1024; S=N/16

def pt(x,y): return (round(x*S),round((16-y)*S))

def catmull_rom(points, divisions=22):
    """Uniform Catmull-Rom spline with no wild overshoots; returns image-space XY."""
    out=[]
    ext=[points[0]]+points+[points[-1]]
    for i in range(1,len(ext)-2):
        a,b,c,d=ext[i-1:i+3]
        for k in range(divisions):
            t=k/divisions;t2=t*t;t3=t2*t
            x=.5*((2*b[0])+(-a[0]+c[0])*t+(2*a[0]-5*b[0]+4*c[0]-d[0])*t2+(-a[0]+3*b[0]-3*c[0]+d[0])*t3)
            y=.5*((2*b[1])+(-a[1]+c[1])*t+(2*a[1]-5*b[1]+4*c[1]-d[1])*t2+(-a[1]+3*b[1]-3*c[1]+d[1])*t3)
            out.append((x,y))
    out.append(points[-1])
    return out

# Preserve the existing characteristic leftward snap trajectory instead of replacing it
# with a bulky loop. The final segment curves inward and drops to a needle point.
knots=[(8.0,5.10),(8.18,5.85),(8.55,6.73),(8.85,7.63),(8.84,8.48),
       (8.53,9.27),(7.96,10.16),(7.12,11.04),(6.24,11.92),
       (5.26,12.73),(4.22,13.49),(3.05,14.03),(2.18,13.86),
       (1.62,13.15),(1.42,12.34),(1.66,11.58),(2.12,11.06)]
curve=catmull_rom(knots)
# Arc-length based taper; thicker at the ferrule, narrow at the fast end.
dist=[0.0]
for a,b in zip(curve,curve[1:]): dist.append(dist[-1]+math.dist(a,b))
length=dist[-1]
left=[];right=[]
for i,(x,y) in enumerate(curve):
    prev=curve[max(0,i-1)]; nxt=curve[min(len(curve)-1,i+1)]
    dx,dy=nxt[0]-prev[0],nxt[1]-prev[1]
    norm=math.hypot(dx,dy) or 1
    nx,ny=-dy/norm,dx/norm
    t=dist[i]/length
    # thickness starts ~0.4 model units, strongly tapers to 0.03
    width=(.39*(1-t)**1.18 + .034)*(1-.04*math.sin(16*t))
    left.append((x+nx*width/2,y+ny*width/2))
    right.append((x-nx*width/2,y-ny*width/2))

im=Image.new('RGBA',(N,N),(0,0,0,0))
d=ImageDraw.Draw(im)
d.polygon([pt(*q) for q in left+right[::-1]],fill=(8,10,14,255))
# darker graphite interior material follows the actual curved spline, not a separate silhouette.
internal=[]; shine=[]
for i,(x,y) in enumerate(curve):
    prev=curve[max(0,i-1)];nxt=curve[min(len(curve)-1,i+1)]
    dx,dy=nxt[0]-prev[0],nxt[1]-prev[1]; norm=math.hypot(dx,dy) or 1
    nx,ny=-dy/norm,dx/norm; t=dist[i]/length
    internal.append(pt(x+nx*.035*(1-t),y+ny*.035*(1-t)))
    shine.append(pt(x-nx*.105*(1-t),y-ny*.105*(1-t)))
d.line(internal,fill=(64,72,82,175),width=3,joint='curve')
d.line(shine[:int(.84*len(shine))],fill=(144,151,161,145),width=2,joint='curve')
# Distinct tiny braided diagonal marks; never draw chain-links or blocks.
for fraction in [.11,.16,.21,.26,.31,.36,.41,.46,.51,.56]:
    j=min(len(curve)-3,max(2,int(fraction*(len(curve)-1))))
    x,y=curve[j]; dx=curve[j+2][0]-curve[j-2][0];dy=curve[j+2][1]-curve[j-2][1]
    r=math.hypot(dx,dy) or 1; tx,ty=dx/r,dy/r;nx,ny=-ty,tx
    half=.16*(1-fraction)
    pts=[pt(x+tx*.09+nx*half,y+ty*.09+ny*half),pt(x-tx*.09-nx*half,y-ty*.09-ny*half)]
    d.line(pts,fill=(101,106,116,125),width=2)
# Tip ink glint: smallest possible, no metal weight.
xt,yt=curve[-1]
d.ellipse((pt(xt-.05,yt+.05)[0],pt(xt-.05,yt+.05)[1],pt(xt+.05,yt-.05)[0],pt(xt+.05,yt-.05)[1]),fill=(211,218,227,210))
tex_path=TEX/'long_whip_alpha.png'
im.save(tex_path)

def material_faces(material):
    u=4*(material%4); v=4*(material//4)
    return {f:{'uv':[u+.14,v+.14,u+3.86,v+3.86],'texture':'#palette'} for f in ('north','south','east','west','up','down')}

def cuboid(name,lo,hi,material):
    assert all(0<=a<b<=16 for a,b in zip(lo,hi)),(name,lo,hi)
    return {'name':name,'from':lo,'to':hi,'faces':material_faces(material)}
e=[]
def add(name,lo,hi,material):e.append(cuboid(name,lo,hi,material))
# One-handed grip, fine faceted bands, small guarded pommel.
add('black_core',[7.56,.83,7.54],[8.44,4.32,8.46],13)
add('charcoal_front',[7.69,1.02,8.46],[8.31,4.08,8.64],3)
for i,y in enumerate([1.12,1.51,1.90,2.29,2.68,3.07,3.46,3.85]):
    add(f'handle_binding_{i:02d}',[7.38,y,8.60],[8.62,y+.105,8.79],15 if i%2 else 4)
add('pommel_body',[7.26,.52,7.22],[8.74,1.02,8.78],1)
add('pommel_rim',[7.33,.73,7.28],[8.67,.99,8.72],9)
add('pommel_finial',[7.68,.30,7.62],[8.32,.52,8.38],10)
add('gold_ferrule',[7.25,4.09,7.26],[8.75,4.79,8.74],9)
add('collar_etching',[7.51,4.33,8.75],[8.49,4.53,8.96],10)
add('ink_socket',[7.66,4.73,7.63],[8.34,5.33,8.37],1)
add('neck_silver',[7.80,5.12,8.42],[8.20,5.30,8.62],6)
# Match xy coordinates used for whip sprite (x=8, y=5.1); double-sided RGBA plane.
e.append({'name':'whip_alpha_ribbon','from':[.01,.01,8.92],'to':[15.99,15.99,8.94],
          'faces':{'north':{'uv':[0,0,16,16],'texture':'#whip'},
                   'south':{'uv':[0,0,16,16],'texture':'#whip'}}})
# Do not use 90 degree yaw - it would hide the alpha plane from camera.
display={
 'thirdperson_righthand':{'rotation':[0,16,-12],'translation':[0.4,3.05,0],'scale':[1.48]*3},
 'thirdperson_lefthand': {'rotation':[0,-16,12],'translation':[-.4,3.05,0],'scale':[1.48]*3},
 'firstperson_righthand': {'rotation':[0,24,-6],'translation':[1.00,3.25,.50],'scale':[1.62]*3},
 'firstperson_lefthand': {'rotation':[0,-24,6],'translation':[-1.00,3.25,.50],'scale':[1.62]*3},
 'gui':{'rotation':[17,-23,0],'translation':[0,0,0],'scale':[1.13]*3},
 'ground':{'rotation':[0,0,0],'translation':[0,2.5,0],'scale':[.84]*3},
 'fixed':{'rotation':[0,0,0],'translation':[0,0,0],'scale':[.98]*3}
}
model={'parent':'minecraft:block/block','ambientocclusion':False,'gui_light':'front',
       'textures':{'palette':'oraclearsenal:item/palette','whip':'oraclearsenal:item/long_whip_alpha','particle':'oraclearsenal:item/palette'},
       'display':display,'elements':[{k:v for k,v in part.items() if k!='name'} for part in e]}
mpath=ITEM/'form_8.json'
mpath.write_text(json.dumps(model,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
bb={'meta':{'format_version':'4.10','model_format':'java_block'},'name':'form_8',
    'resolution':{'width':16,'height':16},'display':display,
    'textures':[{'id':'0','name':'palette.png','particle':True,
                 'source':'data:image/png;base64,'+base64.b64encode((TEX/'palette.png').read_bytes()).decode()},
                {'id':'1','name':tex_path.name,
                 'source':'data:image/png;base64,'+base64.b64encode(tex_path.read_bytes()).decode()}],
    'elements':[]}
for part in e:
    entry={k:part[k] for k in ['name','from','to']}
    entry['faces']={k:{'uv':v['uv'],'texture':1 if v['texture']=='#whip' else 0}
                    for k,v in part['faces'].items()}
    bb['elements'].append(entry)
(BB/'form_8.bbmodel').write_text(json.dumps(bb,indent=2,ensure_ascii=False)+'\n',encoding='utf8')

# Preview: render directly from real JSON elements + actual palette and RGBA whip.
model=json.loads(mpath.read_text(encoding='utf8'))
palette=Image.open(TEX/'palette.png').convert('RGBA'); sprite=Image.open(tex_path).convert('RGBA')
W,H=1280,900
out=Image.new('RGBA',(W,H),(237,235,232,255));D=ImageDraw.Draw(out)
D.rounded_rectangle((16,14,W-16,H-14),radius=24,fill=(240,239,235,255),outline=(89,93,101,255),width=2)
D.line((27,122,W-27,122),fill=(173,169,166,255),width=2)
try:
    ft=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',29)
    fs=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
except OSError:ft=fs=ImageFont.load_default()
D.text((42,35),'Rien / Form VIII · Long Whip',font=ft,fill=(24,29,34,255))
D.text((42,80),'Rendered from form_8.json + long_whip_alpha.png + Blockbench handle',font=fs,fill=(73,77,83,255))

def projection(x,y,z,yaw,roll,ox,oy,scale):
    x-=8;z-=8
    cs,sn=math.cos(math.radians(yaw)),math.sin(math.radians(yaw))
    xx=x*cs+z*sn;zz=-x*sn+z*cs
    cr,sr=math.cos(math.radians(roll)),math.sin(math.radians(roll))
    return (ox+(xx*cr-y*sr)*scale,oy-(xx*sr+y*cr)*scale,zz)

def render(ox,oy,scale,yaw,roll):
    proj=lambda x,y,z:projection(x,y,z,yaw,roll,ox,oy,scale)
    faces=[]
    for part in model['elements']:
        if part.get('faces',{}).get('north',{}).get('texture')!='#palette':continue
        a=part['from'];b=part['to'];uv=part['faces']['north']['uv'];
        col=palette.getpixel((min(63,round((uv[0]+uv[2])*2)),min(63,round((uv[1]+uv[3])*2))))
        verts=[proj(a[0],a[1],b[2]),proj(b[0],a[1],b[2]),proj(b[0],b[1],b[2]),proj(a[0],b[1],b[2])]
        faces.append((sum(q[2] for q in verts)/4,[(q[0],q[1]) for q in verts],col))
    faces.sort(key=lambda t:t[0])
    for _,points,color in faces:ImageDraw.Draw(out).polygon(points,fill=color)
    xy=[proj(x,y,8.93) for x,y in [(0,16),(16,16),(16,0),(0,0)]]
    src=np.float32([[0,0],[N-1,0],[N-1,N-1],[0,N-1]])
    dest=np.float32([[a,b] for a,b,_ in xy]); mat=cv2.getPerspectiveTransform(src,dest)
    warped=cv2.warpPerspective(np.array(sprite),mat,(W,H),flags=cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
    out.alpha_composite(Image.fromarray(warped,'RGBA'))

render(283,794,38.0,0,0)
render(760,794,37.0,23,-10)
D=ImageDraw.Draw(out)
D.text((155,807),'FRONT  /  Continuous ink ribbon',font=fs,fill=(65,70,75,255))
D.text((620,807),'ANGLED  /  Visible alpha plane',font=fs,fill=(65,70,75,255))
# real preview scale guide: generic 1.8m player
px=1100;by=787
D.rectangle((px-35,by-490,px+35,by-240),fill=(77,86,100,255))
D.rectangle((px-30,by-595,px+30,by-490),fill=(177,180,173,255))
D.rectangle((px-35,by-240,px-4,by),fill=(61,68,78,255))
D.rectangle((px+4,by-240,px+35,by),fill=(61,68,78,255))
D.rectangle((px-54,by-485,px-35,by-287),fill=(114,120,128,255))
D.rectangle((px+35,by-485,px+54,by-287),fill=(114,120,128,255))
D.text((1018,807),'PLAYER / scale guide',font=fs,fill=(65,70,75,255))
D.text((39,854),'1024 x 1024 transparent PNG     |     3D hilt + cutout ribbon     |     No chain links',font=fs,fill=(83,87,91,255))
preview=ROOT/'FORM_8_LONG_WHIP_V101_PREVIEW.png'
out.convert('RGB').save(preview)
print('Produced',mpath,tex_path,BB/'form_8.bbmodel',preview,sep='\n  ')
