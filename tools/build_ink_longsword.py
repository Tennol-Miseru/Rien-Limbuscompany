#!/usr/bin/env python3
"""Rien V0.10.0 · Ink Longsword.
Builds form 10 as a morph of the single Oracle staff; canonical finisher retains nine stages.
One coherent, axial RGBA cutout blade + detailed 3D black/gold hilt.
Preview is rendered from the generated real model JSON and PNG texture.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, base64, math
import numpy as np
import cv2

ROOT = Path(__file__).resolve().parents[1]
AS = ROOT / 'src/main/resources/assets/oraclearsenal'
ITEM = AS / 'models/item'
TX = AS / 'textures/item'
BB = ROOT / 'blockbench'
N = 768
S = N/16

def pt(x,y): return (round(x*S),round((16-y)*S))
def polygon(draw, coords, fill): draw.polygon([pt(*a) for a in coords], fill=fill)
def line(draw, coords, color, wd): draw.line([pt(*a) for a in coords], fill=color, width=max(1, round(S*wd)), joint='curve')

# Physical art direction: centered true sword with a pronounced shoulder, tapered flats,
# bilateral sharpened edges and a long central ridge. NO tilted blade axis.
blade = Image.new('RGBA',(N,N),(0,0,0,0))
d = ImageDraw.Draw(blade)
blade_outline = [
    (6.35,5.20),(6.28,5.92),(6.34,7.35),(6.48,9.18),
    (6.78,11.35),(7.12,13.10),(7.54,14.72),(8.00,15.72),
    (8.46,14.72),(8.88,13.10),(9.22,11.35),(9.52,9.18),
    (9.66,7.35),(9.72,5.92),(9.65,5.20)
]
polygon(d,blade_outline,(11,14,19,255))
# Dark inner beveled sword faces taper proportionally to the point.
polygon(d,[(6.46,5.42),(6.47,7.35),(6.66,9.14),(6.98,11.31),(7.32,13.10),(7.72,14.65),(8,15.63),
           (8,5.25)],(28,32,38,255))
polygon(d,[(8,5.25),(8,15.63),(8.28,14.65),(8.68,13.10),(9.02,11.31),(9.34,9.14),(9.53,7.35),(9.54,5.42)],(18,21,27,255))
# Broad, continuous cutting edges, with a restrained cold-silver glimmer.
line(d,[(6.36,5.54),(6.35,7.35),(6.48,9.18),(6.78,11.35),(7.12,13.10),(7.54,14.72),(8,15.72)],(156,162,169,246),.080)
line(d,[(9.64,5.54),(9.65,7.35),(9.52,9.18),(9.22,11.35),(8.88,13.10),(8.46,14.72),(8,15.72)],(181,187,194,244),.076)
line(d,[(6.52,5.48),(6.55,7.28),(6.68,9.10),(6.96,11.22),(7.30,12.99),(7.64,14.52)],(71,78,87,190),.033)
line(d,[(9.48,5.48),(9.45,7.28),(9.32,9.10),(9.04,11.22),(8.70,12.99),(8.36,14.52)],(83,90,98,175),.030)
# Central ridge and elegant narrow fuller confined to lower portion.
line(d,[(8,5.43),(8,7.15),(8,9.30),(8,11.35),(8,13.68),(8,15.12)],(109,118,127,175),.042)
line(d,[(7.83,6.4),(7.83,8.05),(7.92,9.60)],(8,12,17,255),.065)
line(d,[(8.17,6.4),(8.17,8.05),(8.08,9.60)],(8,12,17,255),.065)
# Rectangular ricasso / engraved insignia near blade root.
polygon(d,[(7.52,5.24),(8.48,5.24),(8.30,6.38),(7.7,6.38)],(25,28,34,255))
line(d,[(8,5.53),(7.73,5.86),(8,6.16),(8.27,5.86),(8,5.53)],(188,154,95,220),.07)
line(d,[(8,6.16),(8,6.72)],(190,162,106,195),.055)
# Controlled saw-toothed highlight fragments, not spikes or broad decorative tangles.
for y in (8.2,10.0,11.9):
    line(d,[(6.68+(y-8)*.14,y),(6.80+(y-8)*.13,y+.24)],(157,163,171,92),.03)
    line(d,[(9.32-(y-8)*.14,y),(9.20-(y-8)*.13,y+.24)],(157,163,171,80),.03)

png = TX/'ink_longsword_blade_alpha.png'
blade.save(png)

# Model helpers: each solid mapped to real palette swatches.
def face(m):
    u,v=(m%4)*4,(m//4)*4
    return {k:{'uv':[u+.12,v+.12,u+3.88,v+3.88],'texture':'#palette'} for k in ['north','south','east','west','up','down']}

def cuboid(name,lo,hi,mat):
    assert all(0 <= a < b <= 16 for a,b in zip(lo,hi)),(name,lo,hi)
    return {'name':name,'from':lo,'to':hi,'faces':face(mat)}
E=[]
def add(name,lo,hi,mat): E.append(cuboid(name,lo,hi,mat))
# 3D grip is in the same line as the blade: x=8 throughout.
add('black_grip_core',[7.53,0.86,7.53],[8.47,4.45,8.47],13)
add('grip_front_facet',[7.66,1.03,8.47],[8.34,4.34,8.67],3)
# alternating tightly-bound fabric wraps
for i,y in enumerate([1.08,1.43,1.78,2.13,2.48,2.83,3.18,3.53,3.88,4.23]):
    add(f'wrap_{i:02d}',[7.36,y,8.57],[8.64,y+.105,8.77],15 if i%2 else 4)
# restrained faceted pommel, aged-gold tiny cap
add('pommel_main',[7.26,0.40,7.26],[8.74,1.04,8.74],1)
add('pommel_collar',[7.34,0.78,7.34],[8.66,1.04,8.66],9)
add('pommel_point',[7.67,0.20,7.67],[8.33,0.40,8.33],10)
# low-profile crossguard and subtle flared hooked quillons
add('gold_iron_guard_core',[5.60,4.41,7.34],[10.40,4.83,8.66],9)
add('guard_dark_ridge',[5.43,4.55,8.65],[10.57,4.74,8.92],13)
add('left_quillon',[5.15,4.58,7.48],[5.76,5.15,8.52],4)
add('right_quillon',[10.24,4.58,7.48],[10.85,5.15,8.52],4)
add('left_quillon_tip',[5.10,5.02,7.64],[5.50,5.35,8.36],6)
add('right_quillon_tip',[10.50,5.02,7.64],[10.90,5.35,8.36],6)
add('center_habaki',[7.18,4.69,7.29],[8.82,5.38,8.71],1)
add('habaki_gold_front',[7.46,4.94,8.71],[8.54,5.30,8.89],10)
# thin double sided blade mapped to RGBA asset
E.append({'name':'ink_longsword_alpha_blade','from':[0.01,0.01,8.94],'to':[15.99,15.99,8.96],
          'faces':{'north':{'uv':[0,0,16,16],'texture':'#blade'},'south':{'uv':[0,0,16,16],'texture':'#blade'}}})

# Unlike prior attempts, NO 90-degree side-on Y rotation on an alpha plane.
display={
    'thirdperson_righthand':{'rotation':[0,18,-8],'translation':[0,2.8,0],'scale':[1.35]*3},
    'thirdperson_lefthand':{'rotation':[0,-18,8],'translation':[0,2.8,0],'scale':[1.35]*3},
    'firstperson_righthand':{'rotation':[0,26,2],'translation':[1.1,3.2,0.5],'scale':[1.48]*3},
    'firstperson_lefthand':{'rotation':[0,-26,-2],'translation':[-1.1,3.2,0.5],'scale':[1.48]*3},
    'gui':{'rotation':[18,-25,0],'translation':[0,0,0],'scale':[1.15]*3},
    'ground':{'rotation':[0,0,0],'translation':[0,3,0],'scale':[.78]*3},
    'fixed':{'rotation':[0,0,0],'translation':[0,0,0],'scale':[1.0]*3}
}
model={'parent':'minecraft:block/block','ambientocclusion':False,'gui_light':'front',
       'textures':{'palette':'oraclearsenal:item/palette',
                   'blade':'oraclearsenal:item/ink_longsword_blade_alpha',
                   'particle':'oraclearsenal:item/palette'},
       'display':display,'elements':[{k:v for k,v in e.items() if k!='name'} for e in E]}
model_path=ITEM/'form_10.json'
model_path.write_text(json.dumps(model,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
bb={'meta':{'format_version':'4.10','model_format':'java_block'},'name':'form_10',
    'resolution':{'width':16,'height':16},'display':display,
    'textures':[{'id':'0','name':'palette.png','particle':True,
                 'source':'data:image/png;base64,'+base64.b64encode((TX/'palette.png').read_bytes()).decode()},
                {'id':'1','name':png.name,'source':'data:image/png;base64,'+base64.b64encode(png.read_bytes()).decode()}],
    'elements':[]}
for e in E:
    v={k:e[k] for k in ['name','from','to']}
    v['faces']={side:{'uv':f['uv'],'texture':1 if f['texture']=='#blade' else 0} for side,f in e['faces'].items()}
    bb['elements'].append(v)
(BB/'form_10.bbmodel').write_text(json.dumps(bb,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

# --------- Preview renderer: generated JSON and PNG as source ---------
model=json.loads(model_path.read_text(encoding='utf-8'))
rgba=Image.open(TX/'ink_longsword_blade_alpha.png').convert('RGBA')
palette=Image.open(TX/'palette.png').convert('RGBA')
W,H=1320,870
out=Image.new('RGBA',(W,H),(237,235,231,255))
D=ImageDraw.Draw(out)
D.rounded_rectangle((16,15,W-16,H-15),radius=24,fill=(240,238,234,255),outline=(90,94,102,255),width=2)
D.line((27,111,W-27,111),fill=(168,166,164,255),width=2)
try:
    ft=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',29)
    fs=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
except OSError:
    ft=fs=ImageFont.load_default()
D.text((40,35),'Rien / Ink Longsword',fill=(19,24,29,255),font=ft)
D.text((40,77),'Generated from form_10.json + RGBA texture + Blockbench geometry',fill=(66,71,78,255),font=fs)

# 3D projection from actual JSON elements, not an invented drawing.
def project(x,y,z,yaw,roll,ox,oy,scale):
    # move origin to (8,0,8); rotate about Y and Z, orthographic
    x-=8; z-=8
    ca,sa=math.cos(math.radians(yaw)),math.sin(math.radians(yaw))
    xx=x*ca+z*sa; zz=-x*sa+z*ca
    cr,sr=math.cos(math.radians(roll)),math.sin(math.radians(roll))
    xr=xx*cr-y*sr; yr=xx*sr+y*cr
    return (ox+xr*scale,oy-yr*scale,zz)

# Draw z-sorted 3D cuboids with palette samples; preview intentionally simple,
# while correctly reflecting component position, shaft axis and alpha blade.
def render(ox,oy,sc,yaw,roll):
    projection=lambda x,y,z: project(x,y,z,yaw,roll,ox,oy,sc)
    shape=[]
    solids=[e for e in model['elements'] if e['faces'].get('north',{}).get('texture')=='#palette']
    # back-side then front-side painting from world z
    for e in solids:
        x0,y0,z0=e['from'];x1,y1,z1=e['to']
        uv=e['faces']['north']['uv']; cx=int((uv[0]+uv[2])*0.5/16*palette.width)
        cy=int((uv[1]+uv[3])*0.5/16*palette.height)
        col=palette.getpixel((min(63,cx),min(63,cy)))
        pts=[projection(x0,y0,z1),projection(x1,y0,z1),projection(x1,y1,z1),projection(x0,y1,z1)]
        shape.append((sum(p[2] for p in pts)/4,[(p[0],p[1]) for p in pts],col))
    # back of all handle boxes (and blade at z8.95)
    shape.sort(key=lambda x:x[0])
    # painter order, alpha blade is over handle in upper region only
    for _,pts,col in shape:
        ImageDraw.Draw(out).polygon(pts,fill=col)
    # Homography of PNG into the projected 16x16 blade plane
    corners=[projection(x,y,8.95) for x,y in [(0,16),(16,16),(16,0),(0,0)]]
    src=np.float32([[0,0],[N-1,0],[N-1,N-1],[0,N-1]])
    dst=np.float32([[a,b] for a,b,_ in corners])
    matrix=cv2.getPerspectiveTransform(src,dst)
    warped=cv2.warpPerspective(np.array(rgba),matrix,(W,H),flags=cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
    out.alpha_composite(Image.fromarray(warped,'RGBA'))

# Front and angled previews. Second view uses actual model geometry + alpha texture.
render(282,762,36.3,0,0)
render(724,763,35.5,25,-8)
D=ImageDraw.Draw(out)
D.text((140,786),'FRONT / blade centered on grip',font=fs,fill=(60,66,73,255))
D.text((592,786),'THREE-QUARTER / tilted display',font=fs,fill=(60,66,73,255))
# player size bar, scale comparison using typical Minecraft 1.8 block player.
px=1115;by=762
# Player proxy ≈ one Minecraft player tall in this preview, not clipped by title.
D.rectangle((px-33,by-474,px+33,by-230), fill=(78,87,100,255))
D.rectangle((px-30,by-572,px+30,by-474),fill=(172,176,171,255))
D.rectangle((px-33,by-230,px-4,by),fill=(59,66,77,255))
D.rectangle((px+4,by-230,px+33,by),fill=(59,66,77,255))
D.rectangle((px-51,by-470,px-33,by-275),fill=(115,121,128,255))
D.rectangle((px+33,by-470,px+51,by-275),fill=(115,121,128,255))
D.text((1015,786),'PLAYER / scale guide',font=fs,fill=(60,66,73,255))
D.text((37,834),'1.21.1 Fabric     |     real BBModel + RGBA blade     |     3D hilt',font=fs,fill=(81,86,93,255))
prev=ROOT/'INK_LONGSWORD_MODEL_PREVIEW.png'
out.convert('RGB').save(prev)
print('Generated:',model_path,png,BB/'form_10.bbmodel',prev,sep='\n - ')
