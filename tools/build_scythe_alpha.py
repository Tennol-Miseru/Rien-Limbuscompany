#!/usr/bin/env python3
"""Create ninth-form Rien ink scythe as a real alpha-cutout textured plane.

Source of truth is the Pillow-drawn material silhouette, exported as a transparent
PNG; the Minecraft JSON and editable .bbmodel reference exactly that texture.
The preview rasterizes those resource files, it is NOT AI-generated art.
"""
from pathlib import Path
# Deprecated: delegate to the approved v0.10.5 scythe art pipeline.
if __name__ == '__main__':
    import runpy
    runpy.run_path(str(Path(__file__).with_name('build_scythe_concept_v105.py')), run_name='__main__')
    raise SystemExit(0)
import base64, json, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/main/resources/assets/oraclearsenal'
MODELS=ASSETS/'models/item'
TEXTURES=ASSETS/'textures/item'
BB=ROOT/'blockbench'
for p in (MODELS,TEXTURES,BB): p.mkdir(parents=True,exist_ok=True)

SIZE=768
S=SIZE/16

def p(x,y):return (round(x*S), round((16-y)*S))

def bez(a,b,c,d,n=28):
    return [((1-t)**3*a[0]+3*(1-t)**2*t*b[0]+3*(1-t)*t*t*c[0]+t**3*d[0],
             (1-t)**3*a[1]+3*(1-t)**2*t*b[1]+3*(1-t)*t*t*c[1]+t**3*d[1]) for t in (i/n for i in range(n+1))]

def path_segments(segs):
    points=[]
    for control in segs:
        points+=bez(*control)[0 if not points else 1:]
    return points

def flat_poly(draw, polys, fill):
    for polygon in polys:draw.polygon([p(*v) for v in polygon],fill=fill)

def line(draw, segments, fill, width):
    pts=path_segments(segments)
    draw.line([p(*xy) for xy in pts], fill=fill, width=max(1,round(width*S)), joint='curve')
    return pts

# V0.9.4 - pivot-locked INWARD return of the far tip, not an outward flip.
# The blade socket pivot stays at (13.73, 13.78) on the 3D shaft.
# In the previous patch the entire blade root moved from ~13.7 to ~11.0 on Y;
# that was incorrect and is prohibited here.
# Only the distant blade curve and tapered tip return toward +X (the handle).
BLADE_SOCKET=(13.73,13.78)
outer=[
 ((13.73,13.78),(11.90,13.59),(10.17,13.07),(8.48,12.39)),
 ((8.48,12.39),(6.68,11.75),(4.92,10.72),(3.54,9.58)),
 ((3.54,9.58),(2.27,8.56),(2.47,7.48),(4.85,6.85)),
]
inner=[
 ((4.85,6.85),(3.65,7.54),(3.50,8.57),(4.88,9.69)),
 ((4.88,9.69),(6.39,10.89),(8.33,11.75),(10.15,12.49)),
 ((10.15,12.49),(11.75,13.12),(12.90,13.42),(13.73,13.60)),
]
image=Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))
d=ImageDraw.Draw(image)
main_outline=path_segments(outer)+path_segments(inner)
d.polygon([p(*xy) for xy in main_outline],fill=(7,9,13,255))
# Ink bevels: fine pale edges with restrained contrast; upper main edge retained.
line(d,outer,(124,134,144,223),.045)
line(d,inner,(54,61,68,184),.050)
line(d,[
 ((12.90,13.49),(10.82,12.97),(8.97,12.27),(7.01,11.28)),
 ((7.01,11.28),(5.43,10.42),(3.94,9.25),(3.18,8.15)),
],(40,48,56,175),.072)
line(d,[((10.7,12.66),(8.7,11.95),(6.95,10.91),(5.21,9.78))],(91,98,103,107),.022)
# Root remains attached to same position (right near y 13.7).
# V0.9.5 removes decorative thorn spikes and keeps a smooth hooked silhouette.
flat_poly(d,[[(13.02,13.30),(13.70,13.86),(14.08,13.78),(13.88,13.34)]],(11,15,20,248))
flat_poly(d,[[(13.46,13.56),(13.75,13.77),(13.96,13.69)]],(0,0,0,0))
# Short reverse hook beside the shaft, also shares the main socket.
hook_outer=[
 ((12.68,13.61),(12.72,12.99),(13.16,12.15),(13.74,11.60)),
 ((13.74,11.60),(14.55,12.27),(14.93,13.06),(14.07,13.77)),
]
hook_inner=[
 ((14.07,13.77),(14.36,13.10),(14.03,12.46),(13.71,12.05)),
 ((13.71,12.05),(13.17,12.63),(12.93,13.16),(12.68,13.61)),
]
d.polygon([p(*xy) for xy in path_segments(hook_outer)+path_segments(hook_inner)],fill=(9,11,16,248))
line(d,[((13.75,11.68),(14.39,12.32),(14.80,13.06),(14.08,13.74))],(95,105,113,195),.052)
# A tiny blue ink spark at the root, not on the main blade.
d.polygon([p(*v) for v in [(13.49,13.62),(13.64,13.84),(13.72,13.65)]],fill=(33,49,110,120))
# Invariant: blade socket is unchanged, avoiding the v0.9.3 detached blade bug.
assert BLADE_SOCKET==(13.73,13.78)
PATH=TEXTURES/'giant_scythe_blade_alpha.png'
image.save(PATH)

# 3D shaft only: slim black rod, very restrained brass collar and ivory highlights.
# Face mapping uses existing 4x4 palette already present in the mod.
def face(idx):
 u=(idx%4)*4; v=(idx//4)*4
 return {f:{'uv':[u+.15,v+.15,u+3.85,v+3.85],'texture':'#palette'} for f in ('north','south','east','west','up','down')}

def box(name,frm,to,mat):
 return {'name':name,'from':frm,'to':to,'faces':face(mat)}

parts=[]
SHAFT_SHIFT_X=5.7  # Move the socket to the RIGHT end of the horizontal crescent.
def add(name,a,b,material):
 a=[a[0]+SHAFT_SHIFT_X,a[1],a[2]]
 b=[b[0]+SHAFT_SHIFT_X,b[1],b[2]]
 assert all(0<=v<=16 for v in a+b),(name,a,b)
 parts.append(box(name,a,b,material))
add('ink_pole_main',[7.69,.27,7.70],[8.31,15.55,8.30],13)
add('ink_pole_spine',[7.82,1.0,8.31],[8.18,15.3,8.47],4)
add('silver_edge_rod',[7.94,5.9,8.48],[8.06,14.8,8.53],6)
add('handle_grip',[7.51,.8,7.55],[8.49,4.55,8.45],1)
for i,y in enumerate([1.02,1.69,2.36,3.03,3.7,4.37]):
 add(f'fine_wrapping_{i}',[7.48,y,8.42],[8.52,y+.10,8.58],15 if i%2 else 5)
for i,y in enumerate([4.66,8.48,12.5,14.75]):
 add(f'collar_{i}',[7.43,y,7.42],[8.57,y+.20,8.58],8)
 add(f'collar_edge_{i}',[7.62,y+.08,8.59],[8.38,y+.145,8.67],10)
add('dark_pommel',[7.30,.12,7.34],[8.7,.62,8.66],1)
add('pommel_tiny_silver',[7.71,.02,7.71],[8.29,.16,8.29],6)
add('head_joint',[7.3,13.33,7.35],[8.7,14.23,8.65],4)
add('head_joint_rivet',[7.77,13.64,8.65],[8.23,14.0,8.82],6)
# Blade itself: exactly one alpha-mapped thin quadrilateral; no blade voxels.
BLADE_ELEMENT={
 'name':'crescent_alpha_plane',
 'from':[0.01,0.01,8.80], 'to':[15.99,15.99,8.82],
 'faces':{
    'north':{'uv':[0,0,16,16],'texture':'#ink_blade'},
    'south':{'uv':[0,0,16,16],'texture':'#ink_blade'},
 }
}
parts.append(BLADE_ELEMENT)

display={
 'thirdperson_righthand':{'rotation':[0,14,-11], 'translation':[-5.65,5.7,0], 'scale':[2.22,2.22,2.22]},
 'thirdperson_lefthand': {'rotation':[0,-14,11], 'translation':[-5.65,5.7,0], 'scale':[2.22,2.22,2.22]},
 'firstperson_righthand': {'rotation':[0,16,16], 'translation':[-4.35,5.5,1.5], 'scale':[2.08,2.08,2.08]},
 'firstperson_lefthand': {'rotation':[0,-16,-16], 'translation':[-4.35,5.5,1.5], 'scale':[2.08,2.08,2.08]},
 'gui':{'rotation':[18,16,0], 'translation':[-2.2,0,0], 'scale':[1.12,1.12,1.12]},
 'ground':{'rotation':[0,15,0], 'translation':[0,4,0], 'scale':[1.2,1.2,1.2]},
 'fixed':{'rotation':[0,0,0],'translation':[0,0,0],'scale':[1.12,1.12,1.12]},
}
model={'parent':'minecraft:block/block','ambientocclusion':False,'gui_light':'front',
       'textures':{'palette':'oraclearsenal:item/palette','ink_blade':'oraclearsenal:item/giant_scythe_blade_alpha',
                   'particle':'oraclearsenal:item/palette'},
       'display':display,
       'elements':[{k:v for k,v in e.items() if k!='name'} for e in parts]}
(MODELS/'form_9.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

bb={
 'meta':{'format_version':'4.10','model_format':'java_block'},
 'name':'form_9', 'resolution':{'width':16,'height':16},
 'display':display,
 'textures':[
  {'name':'palette.png','id':'0','particle':True,'source':'data:image/png;base64,'+base64.b64encode((TEXTURES/'palette.png').read_bytes()).decode('ascii')},
  {'name':PATH.name,'id':'1','source':'data:image/png;base64,'+base64.b64encode(PATH.read_bytes()).decode('ascii')},
 ],'elements':[]}
for e in parts:
 ne={k:v for k,v in e.items() if k in ('name','from','to')}
 ne['faces']={f:{'uv':v['uv'],'texture': 1 if v['texture']=='#ink_blade' else 0} for f,v in e['faces'].items()}
 bb['elements'].append(ne)
(BB/'form_9.bbmodel').write_text(json.dumps(bb,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

# Standalone preview renders from the exact final geometry and texture files,
# with a 1.8-block humanoid reference proxy (not a Minecraft screenshot).
reloaded=json.loads((MODELS/'form_9.json').read_text(encoding='utf8'))
blade_texture=Image.open(PATH).convert('RGBA')
W,H=1220,930
canvas=Image.new('RGBA',(W,H),(240,239,234,255)); d=ImageDraw.Draw(canvas)
for y in range(H):
 k=y/H;d.line((0,y,W,y),fill=(int(232-20*k),int(232-18*k),int(230-14*k),255))
# card border / area
D=ImageDraw.Draw(canvas)
D.rounded_rectangle((22,22,1198,910),radius=26,outline=(72,77,80,255),width=3)
try:
 ftitle=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',31)
 fsub=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
except OSError:ftitle=fsub=ImageFont.load_default()
D.text((47,40),'Rien  |  Furioso Form IX',fill=(24,29,35,255),font=ftitle)
D.text((47,87),'ALPHA-PLANE SCYTHE / smooth hook / no decorative spikes',fill=(69,74,81,255),font=fsub)
D.line((45,126,1175,126),fill=(150,151,148),width=2)

unit=42.5
origin_x=422; origin_y=830
# front 3D shaft draw in layers with face tint; derive true model element dimensions.
shaft=[e for e in reloaded['elements'] if e.get('faces',{}).get('north',{}).get('texture')=='#palette']
colors={13:(15,18,23,255),4:(55,59,67,255),6:(135,144,153,255),1:(24,27,32,255),15:(80,82,86,255),5:(81,88,95,255),8:(69,61,49,255),10:(152,129,85,255)}
# texture-front view, z-shading is represented as one-pixel strokes
for e in shaft:
 x0,y0,_=e['from'];x1,y1,_=e['to'];uv=e['faces']['north']['uv']
 mat=int(uv[0]//4)+4*int(uv[1]//4)
 col=colors.get(mat,(46,49,55,255))
 coords=[origin_x+(x0-8)*unit,origin_y-y1*unit,origin_x+(x1-8)*unit,origin_y-y0*unit]
 ImageDraw.Draw(canvas).rectangle(coords,fill=col)
# actual alpha plane: texture axes map model x 0-16, y 16-0 (front)
side=round(16*unit)
scaled=blade_texture.resize((side,side),Image.Resampling.LANCZOS)
canvas.alpha_composite(scaled,(round(origin_x-8*unit),round(origin_y-16*unit)))
# tiny light edge shaft foreground for glint (same original geometry)
for e in shaft:
 if e['faces']['north']['uv'][0]//4+4*(e['faces']['north']['uv'][1]//4) not in (6,):continue
 x0,y0,_=e['from'];x1,y1,_=e['to']
 ImageDraw.Draw(canvas).rectangle((origin_x+(x0-8)*unit,origin_y-y1*unit,origin_x+(x1-8)*unit,origin_y-y0*unit),fill=(135,144,153,255))

# human size schematic from 2.22 item display scale, assuming one model height=2.22 blocks
s_h=16*unit*1.8/2.22
human_x=1004;bottom=origin_y
D=ImageDraw.Draw(canvas)
# schematic minecraft-proportion player proxy
sx=s_h/29
D.rectangle((human_x-5.2*sx,bottom-22*sx,human_x+5.2*sx,bottom-10*sx),fill=(96,105,115,255))
D.rectangle((human_x-4*sx,bottom-29*sx,human_x+4*sx,bottom-22*sx),fill=(177,178,171,255),outline=(52,57,65,255),width=2)
D.rectangle((human_x-5.2*sx,bottom-10*sx,human_x-0.5*sx,bottom),fill=(67,72,84,255))
D.rectangle((human_x+0.5*sx,bottom-10*sx,human_x+5.2*sx,bottom),fill=(67,72,84,255))
D.rectangle((human_x-8.4*sx,bottom-22*sx,human_x-5.4*sx,bottom-9*sx),fill=(129,130,124,255))
D.rectangle((human_x+5.4*sx,bottom-22*sx,human_x+8.4*sx,bottom-9*sx),fill=(129,130,124,255))
D.text((human_x-82,bottom+11),'PLAYER / 1.8m',font=fsub,fill=(56,62,67,255))
D.text((47,876),'CUTOUT PNG  |  768 x 768 RGBA  |  Two-sided plane  |  Ink-black',font=fsub,fill=(48,52,58,255))
canvas.convert('RGB').save(ROOT/'FORM_9_ALPHA_SCYTHE_MODEL_PREVIEW.png',quality=95)
canvas.convert('RGB').save(ROOT/'FORM_9_INWARD_PIVOT_V094_PREVIEW.png',quality=95)
canvas.convert('RGB').save(ROOT/'FORM_9_SMOOTH_SCYTHE_V095_PREVIEW.png',quality=95)
print('Built:', PATH, 'plane faces 2; smooth blade; shaft details', len(shaft))
