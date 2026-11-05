#!/usr/bin/env python3
from pathlib import Path
import base64, json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/oraclearsenal'
MODELS = ASSETS / 'models/item'
TEXTURES = ASSETS / 'textures/item'
BB = ROOT / 'blockbench'
for p in (MODELS, TEXTURES, BB):
    p.mkdir(parents=True, exist_ok=True)

SIZE = 1024
S = SIZE / 16.0

def P(x, y):
    return (round(x * S), round((16 - y) * S))

def poly(draw, pts, fill):
    draw.polygon([P(*xy) for xy in pts], fill=fill)

def line(draw, pts, fill, width):
    draw.line([P(*xy) for xy in pts], fill=fill, width=max(1, round(width * S)), joint='curve')

# ---------- texture ----------
def make_hammer_head(path: Path):
    img = Image.new('RGBA', (SIZE, SIZE), (0,0,0,0))
    d = ImageDraw.Draw(img)
    # Main silhouette: asymmetrical heavy black sledgehammer head
    body = [
        (2.0, 10.2), (2.8, 9.1), (3.8, 8.4), (5.0, 8.0),
        (8.9, 8.0), (10.2, 8.35), (11.2, 9.05), (11.9, 10.1),
        (11.5, 10.9), (10.7, 11.45), (9.5, 11.78), (4.7, 11.82),
        (3.4, 11.48), (2.45, 10.92)
    ]
    poly(d, body, (10,12,16,255))
    # rear heavy butt / cap
    poly(d, [(1.2,9.8),(2.2,9.25),(2.2,11.1),(1.1,10.55)], (8,10,14,250))
    # top bevel shard / ink horn
    poly(d, [(8.7,7.95),(10.25,6.95),(11.05,8.15),(9.8,8.3)], (12,14,20,248))
    # underside wedge / chin
    poly(d, [(8.4,11.78),(10.6,12.6),(9.15,12.95),(7.9,12.22)], (12,14,20,246))
    # striking faces emphasis
    poly(d, [(2.05,9.95),(3.12,9.08),(3.28,11.22),(2.1,10.82)], (18,20,26,246))
    poly(d, [(10.95,9.15),(11.85,10.1),(10.9,10.92),(10.22,9.88)], (18,20,26,246))
    # socket hole silhouette
    poly(d, [(5.88,8.7),(6.92,8.55),(7.26,11.25),(6.18,11.42)], (25,29,36,210))
    poly(d, [(6.08,8.92),(6.72,8.84),(6.95,11.02),(6.30,11.12)], (55,60,68,170))
    # bright cutting highlight strokes
    line(d, [(2.55,10.88),(3.75,11.25),(5.4,11.44),(7.55,11.45),(9.2,11.12)], (205,210,216,240), 0.050)
    line(d, [(3.1,8.96),(4.6,8.42),(6.4,8.18),(8.6,8.2),(10.0,8.55)], (190,196,204,214), 0.044)
    line(d, [(8.75,8.05),(9.58,7.52),(10.18,7.18)], (214,218,223,184), 0.038)
    # subtle darker inner contour
    line(d, [(2.75,10.52),(4.3,10.98),(6.15,11.1),(8.15,10.98),(9.76,10.55)], (72,77,85,160), 0.036)
    # faint gold ring accent near socket
    poly(d, [(5.4,9.55),(5.82,9.42),(6.02,10.82),(5.6,10.9)], (148,118,70,226))
    poly(d, [(7.0,9.3),(7.42,9.24),(7.62,10.55),(7.2,10.62)], (148,118,70,226))
    img.save(path)

# ---------- model ----------
def face(idx):
    u = (idx % 4) * 4
    v = (idx // 4) * 4
    return {f: {'uv':[u+0.15,v+0.15,u+3.85,v+3.85], 'texture':'#palette'} for f in ('north','south','east','west','up','down')}

def box(frm,to,mat):
    return {'from':frm, 'to':to, 'faces':face(mat)}

def build_model():
    els=[]
    add=lambda a,b,m: els.append(box(a,b,m))
    # long wrapped handle
    add([7.30,0.15,7.30],[8.70,8.05,8.70],8)
    for i,y in enumerate([0.55,1.05,1.55,2.05,2.55,3.05,3.55,4.05,4.55,5.05,5.55,6.05,6.55,7.05,7.55]):
        add([7.15,y,8.70],[8.85,y+0.12,8.94],15 if i%2 else 5)
    add([7.05,0.00,7.05],[8.95,0.48,8.95],9)
    add([7.42,-0.18,7.42],[8.58,0.00,8.58],14)
    # neck / transition with guard ring
    add([6.78,7.85,6.78],[9.22,8.30,9.22],9)
    add([7.18,8.15,7.18],[8.82,8.95,8.82],1)
    # hammer head support frame around socket
    add([5.65,8.88,7.55],[10.35,9.30,8.45],13)
    add([5.15,9.25,7.64],[10.80,9.60,8.36],13)
    add([5.70,10.80,7.60],[10.30,11.12,8.40],13)
    add([6.12,11.10,7.66],[9.88,11.42,8.34],13)
    add([5.55,9.40,7.60],[5.95,10.98,8.40],13)
    add([10.05,9.40,7.60],[10.45,10.98,8.40],13)
    # rear counterweight tooth at back
    add([4.80,9.55,7.82],[5.50,10.65,8.18],13)
    add([4.30,9.88,7.90],[4.82,10.34,8.10],13)
    # top and bottom horn details
    add([8.95,8.34,7.84],[10.55,9.20,8.16],13)
    add([9.95,7.62,7.88],[11.25,8.28,8.12],13)
    add([8.58,11.35,7.86],[10.20,12.08,8.14],13)
    add([9.75,12.00,7.92],[10.92,12.78,8.08],13)
    # alpha plane for main head silhouette
    els.append({
        'from':[0.01,0.01,8.91], 'to':[15.99,15.99,8.93],
        'faces':{
            'north':{'uv':[0,0,16,16], 'texture':'#ink_head'},
            'south':{'uv':[0,0,16,16], 'texture':'#ink_head'},
        }
    })
    model={
        'parent':'minecraft:block/block',
        'ambientocclusion':False,
        'gui_light':'front',
        'textures':{
            'palette':'oraclearsenal:item/palette',
            'ink_head':'oraclearsenal:item/sledgehammer_head_alpha',
            'particle':'oraclearsenal:item/palette',
        },
        'display':{
            'thirdperson_righthand':{'rotation':[0,88,-34],'translation':[0.9,4.2,0],'scale':[1.70,1.70,1.70]},
            'thirdperson_lefthand':{'rotation':[0,-88,34],'translation':[0.9,4.2,0],'scale':[1.70,1.70,1.70]},
            'firstperson_righthand':{'rotation':[0,-92,24],'translation':[1.15,4.0,1.0],'scale':[1.95,1.95,1.95]},
            'firstperson_lefthand':{'rotation':[0,92,-24],'translation':[1.15,4.0,1.0],'scale':[1.95,1.95,1.95]},
            'gui':{'rotation':[24,228,0],'translation':[0,0,0],'scale':[1.14,1.14,1.14]},
            'ground':{'rotation':[0,0,0],'translation':[0,3,0],'scale':[0.94,0.94,0.94]},
            'fixed':{'rotation':[0,180,0],'translation':[0,0,0],'scale':[1.00,1.00,1.00]},
        },
        'elements':els,
    }
    return model


def write_bbmodel(model: dict, tex_path: Path, out_path: Path):
    palette_bytes=(TEXTURES/'palette.png').read_bytes()
    tex_bytes=tex_path.read_bytes()
    bb={
        'meta':{'format_version':'4.10','model_format':'java_block'},
        'name':'form_5',
        'resolution':{'width':16,'height':16},
        'display':model['display'],
        'textures':[
            {'name':'palette.png','id':'0','particle':True,'source':'data:image/png;base64,'+base64.b64encode(palette_bytes).decode('ascii')},
            {'name':tex_path.name,'id':'1','source':'data:image/png;base64,'+base64.b64encode(tex_bytes).decode('ascii')},
        ],
        'elements':[]
    }
    for e in model['elements']:
        bb['elements'].append({
            'from':e['from'], 'to':e['to'],
            'faces':{f:{'uv':v['uv'], 'texture':1 if v['texture']=='#ink_head' else 0} for f,v in e['faces'].items()}
        })
    out_path.write_text(json.dumps(bb, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def render_preview(model_path: Path, tex_path: Path, out_path: Path):
    obj=json.loads(model_path.read_text(encoding='utf8'))
    tex=Image.open(tex_path).convert('RGBA')
    W,H=1180,880
    canvas=Image.new('RGBA',(W,H),(242,239,235,255))
    dr=ImageDraw.Draw(canvas)
    for y in range(H):
        t=y/H
        dr.line((0,y,W,y), fill=(int(237-18*t),int(234-14*t),int(230-10*t),255))
    dr.rounded_rectangle((20,20,W-20,H-20), radius=24, outline=(70,74,78,255), width=3)
    try:
        f1=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',30)
        f2=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
    except OSError:
        f1=f2=ImageFont.load_default()
    dr.text((42,36),'Rien | Form V Sledgehammer', fill=(20,24,30,255), font=f1)
    dr.text((42,82),'INK-BLACK HEAVY HAMMER / alpha silhouette head + 3D shaft', fill=(74,78,84,255), font=f2)
    dr.line((42,120,W-42,120), fill=(154,153,148), width=2)
    unit=34.0
    ox=420
    oy=790
    solids=[e for e in obj['elements'] if e['faces'].get('north',{}).get('texture')=='#palette']
    colors={13:(17,20,26,255),1:(24,28,34,255),15:(79,83,89,255),5:(84,90,98,255),8:(36,40,47,255),9:(118,94,60,255),10:(163,133,84,255),14:(228,232,236,255)}
    for e in solids:
        x0,y0,_=e['from']; x1,y1,_=e['to']
        uv=e['faces']['north']['uv']; idx=int(uv[0]//4)+4*int(uv[1]//4)
        col=colors.get(idx,(46,49,54,255))
        dr.rectangle((ox+(x0-8)*unit, oy-y1*unit, ox+(x1-8)*unit, oy-y0*unit), fill=col)
    side=round(16*unit)
    canvas.alpha_composite(tex.resize((side,side), Image.Resampling.LANCZOS), (round(ox-8*unit), round(oy-16*unit)))
    proxy_x=940
    bottom=oy
    sx=(16*unit*1.82/1.66)/29
    for rect,fill in [
        ((proxy_x-5.2*sx,bottom-22*sx,proxy_x+5.2*sx,bottom-10*sx),(97,104,114,255)),
        ((proxy_x-4*sx,bottom-29*sx,proxy_x+4*sx,bottom-22*sx),(179,179,172,255)),
        ((proxy_x-5.2*sx,bottom-10*sx,proxy_x-0.4*sx,bottom),(66,71,82,255)),
        ((proxy_x+0.4*sx,bottom-10*sx,proxy_x+5.2*sx,bottom),(66,71,82,255)),
        ((proxy_x-8.2*sx,bottom-22*sx,proxy_x-5.4*sx,bottom-9*sx),(130,131,124,255)),
        ((proxy_x+5.4*sx,bottom-22*sx,proxy_x+8.2*sx,bottom-9*sx),(130,131,124,255)),
    ]:
        dr.rectangle(rect, fill=fill)
    dr.text((proxy_x-84,bottom+10),'PLAYER / 1.8m',font=f2,fill=(57,62,67,255))
    dr.text((42,H-48),'ACTUAL MODEL PREVIEW  |  generated after model update',font=f2,fill=(48,52,58,255))
    canvas.convert('RGB').save(out_path, quality=95)


def main():
    tex = TEXTURES/'sledgehammer_head_alpha.png'
    make_hammer_head(tex)
    model=build_model()
    model_path=MODELS/'form_5.json'
    model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    write_bbmodel(model, tex, BB/'form_5.bbmodel')
    render_preview(model_path, tex, ROOT/'FORM_5_SLEDGEHAMMER_V103_PREVIEW.png')
    print('Generated Form V sledgehammer v0.10.3')

if __name__=='__main__':
    main()
