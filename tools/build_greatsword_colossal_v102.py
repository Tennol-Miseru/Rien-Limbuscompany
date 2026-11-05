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


def make_blade(path: Path, kind: str):
    img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if kind == 'greatsword':
        lower = [(11.68, 5.98), (10.52, 7.10), (9.26, 8.32), (7.98, 9.56), (6.66, 10.84), (5.34, 12.08), (4.10, 13.18), (3.00, 14.10), (2.34, 14.66)]
        upper = [(1.70, 14.00), (2.38, 13.44), (3.40, 12.50), (4.60, 11.36), (5.90, 10.12), (7.22, 8.86), (8.56, 7.56), (9.88, 6.28), (11.10, 5.14)]
        main = lower + upper
        poly(d, main, (8, 10, 14, 255))
        poly(d, [(10.76, 5.82), (12.52, 5.88), (11.70, 4.72)], (12, 14, 20, 250))
        poly(d, [(10.02, 6.42), (11.50, 6.52), (10.78, 5.42)], (11, 13, 19, 238))
        poly(d, [(11.84, 5.20), (12.28, 3.92), (12.70, 5.02)], (15, 17, 22, 240))
        line(d, [(11.84, 5.80), (10.70, 6.88), (9.50, 8.04), (8.24, 9.24), (6.96, 10.48), (5.64, 11.72), (4.38, 12.84), (3.16, 13.88), (2.36, 14.50)], (196, 201, 206, 236), .052)
        line(d, [(11.22, 5.28), (10.12, 6.34), (8.90, 7.50), (7.64, 8.72), (6.34, 9.98), (5.02, 11.24), (3.86, 12.28), (2.92, 13.08)], (74, 80, 88, 168), .040)
        line(d, [(10.82, 5.74), (9.82, 6.70), (8.70, 7.78), (7.50, 8.94), (6.24, 10.16), (4.98, 11.34), (3.88, 12.30)], (98, 106, 114, 84), .024)
    else:
        lower = [(12.42, 6.18), (11.10, 7.42), (9.68, 8.76), (8.14, 10.18), (6.60, 11.60), (5.12, 12.90), (3.78, 14.00), (2.62, 14.86), (1.98, 15.26)]
        upper = [(1.22, 14.16), (1.88, 13.64), (2.98, 12.70), (4.30, 11.50), (5.72, 10.18), (7.24, 8.76), (8.82, 7.26), (10.34, 5.90), (11.72, 4.82)]
        main = lower + upper
        poly(d, main, (8, 10, 15, 255))
        # heavier inner mass at root
        poly(d, [(10.80, 5.34), (13.02, 5.42), (12.02, 4.02)], (11, 13, 19, 248))
        poly(d, [(10.10, 5.98), (12.44, 6.08), (11.18, 4.64)], (11, 13, 19, 246))
        poly(d, [(9.32, 6.66), (11.52, 6.78), (10.24, 5.46)], (11, 13, 19, 242))
        poly(d, [(12.22, 4.88), (12.72, 3.22), (13.20, 4.60)], (16, 18, 22, 246))
        line(d, [(12.38, 5.92), (11.08, 7.14), (9.68, 8.46), (8.18, 9.86), (6.64, 11.28), (5.16, 12.58), (3.86, 13.64), (2.72, 14.48), (2.02, 14.98)], (194, 199, 205, 238), .060)
        line(d, [(11.62, 5.16), (10.40, 6.30), (9.04, 7.58), (7.58, 8.96), (6.08, 10.36), (4.62, 11.66), (3.38, 12.72), (2.42, 13.44)], (72, 77, 86, 176), .046)
        line(d, [(11.12, 5.82), (9.98, 6.90), (8.70, 8.10), (7.32, 9.40), (5.88, 10.74), (4.46, 11.98), (3.28, 12.94)], (101, 108, 118, 88), .028)
    img.save(path)


def face(idx):
    u = (idx % 4) * 4
    v = (idx // 4) * 4
    return {f: {'uv': [u + .15, v + .15, u + 3.85, v + 3.85], 'texture': '#palette'} for f in ('north','south','east','west','up','down')}


def box(frm, to, mat):
    return {'from': frm, 'to': to, 'faces': face(mat)}


def make_model(kind: str, blade_tex: str):
    els = []
    add = lambda a,b,m: els.append(box(a,b,m))
    if kind == 'greatsword':
        # moderate heavy sword
        add([7.42, 0.20, 7.42], [8.58, 4.96, 8.58], 8)
        for i,y in enumerate([0.58,1.02,1.46,1.90,2.34,2.78,3.22,3.66,4.10]):
            add([7.26, y, 8.62], [8.74, y+0.10, 8.82], 15 if i%2 else 5)
        add([7.18, 0.00, 7.18], [8.82, 0.44, 8.82], 9)
        add([7.52, 0.02, 7.52], [8.48, 0.22, 8.48], 14)
        add([6.28, 4.58, 7.18], [9.82, 5.02, 8.82], 9)
        add([6.58, 4.76, 8.82], [9.56, 4.92, 9.02], 10)
        add([7.22, 4.84, 7.22], [8.78, 5.64, 8.78], 1)
        add([8.72, 5.12, 8.16], [11.10, 5.36, 8.86], 13)
        add([8.56, 5.56, 8.12], [10.52, 5.78, 8.82], 13)
        add([8.66, 5.56, 8.14], [9.10, 6.70, 8.86], 13)
        plane_scale = (8.90, 8.92)
        display = {
            'thirdperson_righthand': {'rotation':[0,88,-34],'translation':[0.9,4.0,0],'scale':[1.70,1.70,1.70]},
            'thirdperson_lefthand': {'rotation':[0,-88,34],'translation':[0.9,4.0,0],'scale':[1.70,1.70,1.70]},
            'firstperson_righthand': {'rotation':[0,-92,26],'translation':[1.2,4.1,1.0],'scale':[1.90,1.90,1.90]},
            'firstperson_lefthand': {'rotation':[0,92,-26],'translation':[1.2,4.1,1.0],'scale':[1.90,1.90,1.90]},
            'gui': {'rotation':[22,228,0],'translation':[0,0,0],'scale':[1.12,1.12,1.12]},
            'ground': {'rotation':[0,0,0],'translation':[0,3,0],'scale':[0.92,0.92,0.92]},
            'fixed': {'rotation':[0,180,0],'translation':[0,0,0],'scale':[1.00,1.00,1.00]},
        }
    else:
        # colossal blade / extra large sword
        add([7.26, 0.20, 7.26], [8.74, 5.58, 8.74], 8)
        for i,y in enumerate([0.60,1.08,1.56,2.04,2.52,3.00,3.48,3.96,4.44,4.92]):
            add([7.10, y, 8.76], [8.90, y+0.12, 8.98], 15 if i%2 else 5)
        add([7.00, 0.00, 7.00], [9.00, 0.48, 9.00], 9)
        add([7.44, 0.02, 7.44], [8.56, 0.24, 8.56], 14)
        add([5.96, 5.10, 7.04], [10.34, 5.60, 8.96], 9)
        add([6.22, 5.28, 8.96], [10.00, 5.46, 9.20], 10)
        add([7.06, 5.34, 7.06], [8.94, 6.34, 8.94], 1)
        add([8.90, 5.66, 8.12], [12.26, 5.96, 8.94], 13)
        add([8.68, 6.22, 8.08], [11.62, 6.48, 8.90], 13)
        add([8.46, 6.82, 8.04], [10.98, 7.06, 8.86], 13)
        add([8.92, 6.12, 8.10], [9.40, 7.56, 8.90], 13)
        display = {
            'thirdperson_righthand': {'rotation':[0,88,-34],'translation':[1.1,4.5,0],'scale':[2.08,2.08,2.08]},
            'thirdperson_lefthand': {'rotation':[0,-88,34],'translation':[1.1,4.5,0],'scale':[2.08,2.08,2.08]},
            'firstperson_righthand': {'rotation':[0,-92,24],'translation':[1.35,4.4,1.0],'scale':[2.36,2.36,2.36]},
            'firstperson_lefthand': {'rotation':[0,92,-24],'translation':[1.35,4.4,1.0],'scale':[2.36,2.36,2.36]},
            'gui': {'rotation':[22,228,0],'translation':[0,0,0],'scale':[1.22,1.22,1.22]},
            'ground': {'rotation':[0,0,0],'translation':[0,3,0],'scale':[1.02,1.02,1.02]},
            'fixed': {'rotation':[0,180,0],'translation':[0,0,0],'scale':[1.14,1.14,1.14]},
        }
    els.append({
        'from':[0.01,0.01,8.90], 'to':[15.99,15.99,8.92],
        'faces':{
            'north':{'uv':[0,0,16,16],'texture':'#ink_blade'},
            'south':{'uv':[0,0,16,16],'texture':'#ink_blade'},
        }
    })
    return {
        'parent':'minecraft:block/block',
        'ambientocclusion':False,
        'gui_light':'front',
        'textures': {'palette':'oraclearsenal:item/palette','ink_blade':f'oraclearsenal:item/{blade_tex}','particle':'oraclearsenal:item/palette'},
        'display': display,
        'elements': els,
    }


def write_model(name: str, model: dict, tex_path: Path):
    (MODELS / f'{name}.json').write_text(json.dumps(model, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    bb = {
        'meta': {'format_version':'4.10','model_format':'java_block'},
        'name': name,
        'resolution': {'width':16,'height':16},
        'display': model['display'],
        'textures': [
            {'name':'palette.png','id':'0','particle':True,'source':'data:image/png;base64,' + base64.b64encode((TEXTURES/'palette.png').read_bytes()).decode('ascii')},
            {'name':tex_path.name,'id':'1','source':'data:image/png;base64,' + base64.b64encode(tex_path.read_bytes()).decode('ascii')},
        ],
        'elements': []
    }
    for index, e in enumerate(model['elements']):
        item = {'name': f'part_{index+1:02}', 'from':e['from'],'to':e['to']}
        item['faces'] = {f:{'uv':v['uv'],'texture':1 if v['texture']=='#ink_blade' else 0} for f,v in e['faces'].items()}
        bb['elements'].append(item)
    (BB / f'{name}.bbmodel').write_text(json.dumps(bb, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def render_preview(model_path: Path, tex_path: Path, out_path: Path, title: str, subtitle: str, proxy_scale=1.7):
    obj = json.loads(model_path.read_text(encoding='utf8'))
    blade = Image.open(tex_path).convert('RGBA')
    W,H = 1180,880
    canvas = Image.new('RGBA',(W,H),(242,239,235,255))
    dr = ImageDraw.Draw(canvas)
    for y in range(H):
        t=y/H
        dr.line((0,y,W,y), fill=(int(237-18*t),int(234-14*t),int(230-10*t),255))
    dr.rounded_rectangle((20,20,W-20,H-20), radius=24, outline=(70,74,78,255), width=3)
    try:
        f1=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',30)
        f2=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
    except OSError:
        f1=f2=ImageFont.load_default()
    dr.text((42,36), title, fill=(20,24,30,255), font=f1)
    dr.text((42,82), subtitle, fill=(74,78,84,255), font=f2)
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
    canvas.alpha_composite(blade.resize((side,side), Image.Resampling.LANCZOS), (round(ox-8*unit), round(oy-16*unit)))
    proxy_x=940
    bottom=oy
    s_h = 16*unit*proxy_scale/1.66
    sx = s_h/29
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
    dr.text((42,H-48),'ACTUAL MODEL PREVIEW  |  cutout alpha blade + 3D hilt',font=f2,fill=(48,52,58,255))
    canvas.convert('RGB').save(out_path, quality=95)


def make_comparison(left_path: Path, right_path: Path, out_path: Path):
    left=Image.open(left_path).convert('RGB')
    right=Image.open(right_path).convert('RGB')
    W,H=2200,980
    canvas=Image.new('RGB',(W,H),(243,240,236))
    d=ImageDraw.Draw(canvas)
    try:
        f1=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',34)
        f2=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
    except OSError:
        f1=f2=ImageFont.load_default()
    d.text((40,28),'Rien Mod / Greatsword vs Colossal Blade (V0.10.2)',font=f1,fill=(18,22,28))
    d.text((40,76),'Left: Form III Greatsword (reshaped & straighter)    Right: Form VI Colossal Blade (heavy swapped design)',font=f2,fill=(82,86,92))
    d.rounded_rectangle((30,120,1070,930),radius=24,outline=(80,84,88),width=3,fill=(250,248,245))
    d.rounded_rectangle((1130,120,2170,930),radius=24,outline=(80,84,88),width=3,fill=(250,248,245))
    l=left.resize((1000,746), Image.Resampling.LANCZOS)
    r=right.resize((1000,746), Image.Resampling.LANCZOS)
    canvas.paste(l,(50,150)); canvas.paste(r,(1150,150))
    d.text((390,900),'Form III · 大剑',font=f1,fill=(25,28,34))
    d.text((1460,900),'Form VI · 特大剑',font=f1,fill=(25,28,34))
    canvas.save(out_path, quality=95)

# generate textures
tex3 = TEXTURES / 'greatsword_blade_alpha.png'
tex6 = TEXTURES / 'colossal_blade_alpha.png'
make_blade(tex3, 'greatsword')
make_blade(tex6, 'colossal')
# models
m3 = make_model('greatsword', 'greatsword_blade_alpha')
m6 = make_model('colossal', 'colossal_blade_alpha')
write_model('form_3', m3, tex3)
write_model('form_6', m6, tex6)
# previews
p3 = ROOT / 'FORM_3_GREATSWORD_V102_PREVIEW.png'
p6 = ROOT / 'FORM_6_COLOSSAL_V102_PREVIEW.png'
pc = ROOT / 'RIEN_GREATSWORD_COLOSSAL_V102_COMPARISON.png'
render_preview(MODELS/'form_3.json', tex3, p3, 'Rien | Form III Greatsword', 'STRAIGHTENED / moderated weight / now less colossal', proxy_scale=1.60)
render_preview(MODELS/'form_6.json', tex6, p6, 'Rien | Form VI Colossal Blade', 'SWAPPED HEAVIER SHAPE / broader & bigger than form III', proxy_scale=2.00)
make_comparison(p3,p6,pc)
print('Generated V0.10.2 greatsword + colossal blade models/previews')
