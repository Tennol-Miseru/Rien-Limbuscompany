#!/usr/bin/env python3
"""v0.9.6: Refine form I handaxe against user-provided Rien animation reference.

Source asset: narrow and small hooked ink blade on a long, near-black pole.
Exports one 768x768 RGBA blade, Minecraft model JSON, editable BBModel with
embedded exact PNG, and a model-derived preview. No generative imagery.
"""
from pathlib import Path
import base64, hashlib, json, math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/oraclearsenal'
TEX = ASSETS / 'textures/item'
MODELS = ASSETS / 'models/item'
BB = ROOT / 'blockbench'
for folder in (TEX, MODELS, BB): folder.mkdir(parents=True, exist_ok=True)
SIZE = 768
UNIT = SIZE / 16
# Head socket and haft are intentionally aligned at the SAME x coordinate.
SOCKET_X = 8.45
SOCKET_Y = 14.10

def pt(x, y):
    return (round(x * UNIT), round((16-y)*UNIT))

def bezier(a,b,c,d,n=70):
    return [((1-t)**3*a[0] + 3*(1-t)**2*t*b[0] + 3*(1-t)*t*t*c[0] + t**3*d[0],
             (1-t)**3*a[1] + 3*(1-t)**2*t*b[1] + 3*(1-t)*t*t*c[1] + t**3*d[1])
            for t in (i/n for i in range(n+1))]

def path_segments(segments):
    out=[]
    for seg in segments:
        out += bezier(*seg)[0 if not out else 1:]
    return out

def smooth_line(draw, segments, fill, thickness):
    draw.line([pt(*xy) for xy in path_segments(segments)],fill=fill,width=max(1,round(UNIT*thickness)),joint='curve')

def poly(draw, points, color):
    draw.polygon([pt(*p) for p in points], fill=color)

# In screenshot: short, narrow axe head with light silver outline;
# not a big bearded battle axe or huge double crescent.
# Main hooked heel at left (x6.3), long taper to the right (x12.15),
# on a very slim shaft at x8.45.
outer = [
    ((6.22,13.10),(6.10,13.84),(6.12,14.66),(6.75,15.72)),
    ((6.75,15.72),(7.16,15.94),(8.01,15.73),(8.72,15.60)),
    ((8.72,15.60),(9.80,15.42),(11.15,15.19),(12.32,14.95)),
]
inner = [
    ((12.32,14.95),(10.90,14.86),(9.86,14.76),(9.25,14.58)),
    ((9.25,14.58),(8.62,14.40),(8.14,14.02),(7.79,13.52)),
    ((7.79,13.52),(7.31,13.62),(6.70,13.42),(6.22,13.10)),
]
img=Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))
d=ImageDraw.Draw(img)
blade=path_segments(outer)+path_segments(inner)
poly(d,blade,(5,7,10,255))
# Thin metallic outline, carefully limited to the reference's leading edge.
smooth_line(d,outer,(158,161,167,227),.051)
smooth_line(d,inner,(80,87,96,197),.033)
# Subtle tapering graphite core; NO wide opaque second layer.
smooth_line(d,[
    ((6.55,14.79),(7.50,15.31),(8.91,15.30),(10.46,15.04)),
    ((10.46,15.04),(11.24,14.98),(11.66,14.93),(12.0,14.91)),
],(32,38,45,168),.055)
# Tiny inner crease where the hooked heel turns toward its socket.
smooth_line(d,[((6.65,13.62),(7.05,13.85),(7.43,14.20),(7.98,14.46))],(112,119,129,138),.028)
# Small dark hub at blade root aligned to x=8.45, y=14.1.
poly(d,[(8.16,14.46),(8.55,14.46),(8.77,14.02),(8.18,14.02)],(11,15,20,255))
poly(d,[(8.29,14.38),(8.64,14.37),(8.60,14.21),(8.31,14.21)],(93,80,57,222))
PNG=TEX/'hand_axe_blade_alpha.png'
img.save(PNG)

def faces(idx):
    u=(idx%4)*4; v=(idx//4)*4
    return {direction:{'uv':[u+.15,v+.15,u+3.85,v+3.85],'texture':'#palette'}
            for direction in ('north','south','east','west','up','down')}

def box(name, frm, to, material):
    assert all(0<=n<=16 for n in frm+to), (name, frm, to)
    assert all(a<b for a,b in zip(frm,to)),name
    return {'name':name,'from':frm,'to':to,'faces':faces(material)}

parts=[
    # Long and slender, almost ink-black shaft; no chunky gold block.
    box('black_shaft',[8.25,1.15,7.78],[8.65,14.52,8.19],13),
    box('shaft_glint',[8.34,3.10,8.20],[8.45,14.20,8.31],4),
    box('dark_grip',[8.05,1.17,7.62],[8.84,3.92,8.38],1),
    box('grip_side',[8.18,1.45,8.39],[8.64,3.69,8.54],3),
    box('pommel_black',[7.99,.85,7.56],[8.91,1.23,8.44],13),
    box('pommel_silver',[8.19,.73,7.76],[8.71,.86,8.25],6),
    box('blade_socket',[8.11,13.82,7.62],[8.79,14.53,8.38],1),
    box('blade_socket_edge',[8.26,14.02,8.39],[8.68,14.40,8.53],15),
    box('grip_brass_pin',[8.10,4.05,8.38],[8.80,4.22,8.53],9),
]
# Two very discreet grip wraps, not the previous thick, full-length stripes.
for i,y in enumerate([2.05,3.22]):
    parts.append(box(f'grip_wrap_{i}',[8.08,y,8.40],[8.81,y+.09,8.56],15 if i else 8))
# Single flat cutout for the entire curved head. Front/back share one UV footprint.
parts.append({
    'name':'small_hooked_axe_alpha_plane',
    'from':[0.01,0.01,8.76],'to':[15.99,15.99,8.78],
    'faces':{
        'north':{'uv':[0,0,16,16],'texture':'#ink_blade'},
        'south':{'uv':[0,0,16,16],'texture':'#ink_blade'},
    }
})
# Keep this alpha face visually broadside rather than edge-on (old y=90° bug).
display={
 'thirdperson_righthand':{'rotation':[0,12,-24],'translation':[0.15,4.65,0.1],'scale':[1.32,1.32,1.32]},
 'thirdperson_lefthand': {'rotation':[0,-12,24],'translation':[0.15,4.65,0.1],'scale':[1.32,1.32,1.32]},
 'firstperson_righthand': {'rotation':[0,18,18],'translation':[.50,4.1,1.1],'scale':[1.45,1.45,1.45]},
 'firstperson_lefthand': {'rotation':[0,-18,-18],'translation':[.50,4.1,1.1],'scale':[1.45,1.45,1.45]},
 'gui':{'rotation':[15,22,-24],'translation':[0,0,0],'scale':[1.25,1.25,1.25]},
 'ground':{'rotation':[0,14,0],'translation':[0,3,0],'scale':[.88,.88,.88]},
 'fixed':{'rotation':[0,0,-17],'translation':[0,0,0],'scale':[1.12,1.12,1.12]},
}
model={
    'parent':'minecraft:block/block','ambientocclusion':False,'gui_light':'front',
    'textures':{'palette':'oraclearsenal:item/palette',
                'ink_blade':'oraclearsenal:item/hand_axe_blade_alpha',
                'particle':'oraclearsenal:item/palette'},
    'display':display,
    'elements':[{k:v for k,v in e.items() if k!='name'} for e in parts]
}
(MODELS/'form_1.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
bb={
    'meta':{'format_version':'4.10','model_format':'java_block'},
    'name':'form_1','resolution':{'width':16,'height':16}, 'display':display,
    'textures':[
        {'name':'palette.png','id':'0','particle':True,
         'source':'data:image/png;base64,'+base64.b64encode((TEX/'palette.png').read_bytes()).decode('ascii')},
        {'name':PNG.name,'id':'1',
         'source':'data:image/png;base64,'+base64.b64encode(PNG.read_bytes()).decode('ascii')},
    ],'elements':[]
}
for e in parts:
    bb['elements'].append({
        'name':e['name'],'from':e['from'],'to':e['to'],
        'faces':{direction:{'uv':side['uv'],'texture':1 if side['texture']=='#ink_blade' else 0}
                 for direction,side in e['faces'].items()}
    })
(BB/'form_1.bbmodel').write_text(json.dumps(bb,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

# Preview renderer based on EXACT generated geometry/texture files.
mod=json.loads((MODELS/'form_1.json').read_text(encoding='utf8'))
weapon_png=Image.open(PNG).convert('RGBA')
W,H=1320,940
preview=Image.new('RGBA',(W,H),(236,236,231,255))
draw=ImageDraw.Draw(preview)
for y in range(H):
    k=y/H
    draw.line((0,y,W,y),fill=(int(240-15*k),int(240-13*k),int(236-8*k),255))
draw.rounded_rectangle((20,20,W-20,H-20),radius=24,outline=(84,91,95,255),width=3)
try:
    titlefont=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',30)
    descfont=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',20)
except OSError:
    titlefont=ImageFont.load_default();descfont=ImageFont.load_default()
draw.text((46,34),'里恩模组 / 第一式 · 手斧 — 参考动作模型重制',font=titlefont,fill=(20,27,33))
draw.text((46,84),'长柄 · 小型弯钩斧头 · 墨黑透明刀刃 · 金属薄刃缘',font=descfont,fill=(73,79,86))
draw.line((44,128,W-44,128), fill=(150,154,158),width=2)
# preview of original model coordinates. model y ranges 0..16.
ORIGIN_X=365; ORIGIN_Y=827; S=43
color_palette={1:'#16191f',3:'#1e262d',4:'#3b4047',6:'#acb4bb',8:'#75654c',9:'#967e52',13:'#0a0d10',15:'#6f7980'}
shaft=[e for e in mod['elements'] if e['faces'].get('north',{}).get('texture')=='#palette']
for e in shaft:
    mat_u,mat_v=e['faces']['north']['uv'][:2]; mat=int(mat_u//4)+4*int(mat_v//4)
    a,b,_=e['from'];c,d,_=e['to']
    draw.rectangle((ORIGIN_X+(a-8)*S,ORIGIN_Y-d*S,ORIGIN_X+(c-8)*S,ORIGIN_Y-b*S),fill=color_palette.get(mat,'#303438'))
orig=round(16*S)
preview.alpha_composite(weapon_png.resize((orig,orig),Image.Resampling.LANCZOS),
                        (round(ORIGIN_X-8*S),round(ORIGIN_Y-16*S)))
# Second panel shows the same rendered object tilted like reference (image rotation only).
angle=-29
crop=preview.crop((round(ORIGIN_X-8*S),round(ORIGIN_Y-16*S),round(ORIGIN_X+8*S),round(ORIGIN_Y)))
rot=crop.rotate(angle,expand=True,resample=Image.Resampling.BICUBIC,fillcolor=(0,0,0,0))
# don't composite original solid background; prepare a transparent model pane instead.
transparent=Image.new('RGBA',(orig,orig),(0,0,0,0)); local=ImageDraw.Draw(transparent)
for e in shaft:
    mat_u,mat_v=e['faces']['north']['uv'][:2]; mat=int(mat_u//4)+4*int(mat_v//4)
    a,b,_=e['from'];c,d,_=e['to']
    local.rectangle(((a)*S,(16-d)*S,c*S,(16-b)*S),fill=color_palette.get(mat,'#303438'))
transparent.alpha_composite(weapon_png.resize((orig,orig),Image.Resampling.LANCZOS),(0,0))
angled=transparent.rotate(-30,expand=True,resample=Image.Resampling.BICUBIC)
angled.thumbnail((500,650),Image.Resampling.LANCZOS)
preview.alpha_composite(angled,(780,round(220+(650-angled.height)/2)))
# vertical ruler/presentation callout
draw=ImageDraw.Draw(preview)
draw.text((54,862),'模型正视图（由 JSON 几何和透明 PNG 渲染）',font=descfont,fill=(58,65,71))
draw.text((810,862),'倾斜持握示意（相同模型）',font=descfont,fill=(58,65,71))
draw.text((46,899),'v0.9.6 · 双面透明平面刀头 + 独立 3D 细长柄 · 非游戏实机画面',font=descfont,fill=(62,69,75))
PREVIEW=ROOT/'FORM_1_REFERENCE_HANDEXE_V096_PREVIEW.png'
preview.convert('RGB').save(PREVIEW,optimize=True)
print('Created:',PNG,MODELS/'form_1.json',BB/'form_1.bbmodel',PREVIEW)
print('sha256 blade:',hashlib.sha256(PNG.read_bytes()).hexdigest())
