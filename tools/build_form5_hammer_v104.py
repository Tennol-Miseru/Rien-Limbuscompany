#!/usr/bin/env python3
from pathlib import Path
import json, base64
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/oraclearsenal'
MODELS = ASSETS / 'models/item'
TEXTURES = ASSETS / 'textures/item'
BB = ROOT / 'blockbench'

# --- palette helpers ---
PALETTE_COLORS = {
    0:(9,11,15,255),
    1:(15,18,24,255),
    5:(104,111,122,255),
    8:(40,44,52,255),
    9:(114,92,61,255),
    10:(167,142,92,255),
    13:(26,29,35,255),
    14:(210,214,220,255),
    15:(86,92,102,255),
}

def uv_for_index(idx: int):
    u = (idx % 4) * 4
    v = (idx // 4) * 4
    return [u+0.15, v+0.15, u+3.85, v+3.85]

def faces(idx: int):
    return {f:{'uv':uv_for_index(idx), 'texture':'#palette'} for f in ('north','south','east','west','up','down')}

def box(frm, to, idx):
    return {'from':frm, 'to':to, 'faces':faces(idx)}

def add(lst, frm, to, idx):
    lst.append(box(frm,to,idx))

# --- model build ---
def build_form5_model():
    els=[]
    # lower spike and pommel
    add(els,[7.55,0.02,7.55],[8.45,0.32,8.45],13)
    add(els,[7.35,0.32,7.70],[8.65,0.58,8.30],13)
    add(els,[7.75,0.00,7.84],[8.25,0.18,8.16],14)
    # grip core
    add(els,[7.40,0.00,7.40],[8.60,5.40,8.60],8)
    # wrap rings
    for y in [0.45,1.05,1.65,2.25,2.85,3.45,4.05,4.65,5.05]:
        add(els,[7.24,y,7.24],[8.76,y+0.16,8.76],15)
    # gold guard / sword hilt feel
    add(els,[5.95,5.15,7.72],[10.05,5.58,8.28],10)
    add(els,[6.25,5.00,7.58],[6.95,5.73,8.42],9)
    add(els,[9.05,5.00,7.58],[9.75,5.73,8.42],9)
    # upper thorny shaft
    add(els,[7.55,5.58,7.55],[8.45,10.20,8.45],13)
    add(els,[7.22,6.20,7.70],[7.58,6.92,8.30],13)
    add(els,[8.42,6.85,7.72],[8.84,7.46,8.28],13)
    add(els,[7.18,7.60,7.76],[7.54,8.32,8.24],13)
    add(els,[8.48,8.22,7.76],[8.86,8.82,8.24],13)
    add(els,[7.30,9.10,7.76],[7.64,9.70,8.24],13)
    # head base collar and neck
    add(els,[6.90,10.10,6.90],[9.10,10.70,9.10],8)
    add(els,[6.60,10.60,6.60],[9.40,11.25,9.40],15)
    add(els,[6.95,11.10,6.95],[9.05,11.78,9.05],13)
    # left hammer block - silver frame, dark inset
    add(els,[1.00,11.20,5.30],[5.55,15.20,10.70],14)
    add(els,[1.50,11.68,5.76],[5.05,14.72,10.24],13)
    add(els,[1.76,12.88,5.52],[4.80,13.42,10.48],14)
    # bevel hints left
    add(els,[0.62,11.58,5.62],[1.00,14.82,10.38],15)
    add(els,[5.55,11.58,5.62],[5.95,14.82,10.38],15)
    # right hammer block
    add(els,[10.45,11.20,5.30],[15.00,15.20,10.70],14)
    add(els,[10.95,11.68,5.76],[14.50,14.72,10.24],13)
    add(els,[11.20,12.88,5.52],[14.24,13.42,10.48],14)
    add(els,[10.05,11.58,5.62],[10.45,14.82,10.38],15)
    add(els,[15.00,11.58,5.62],[15.38,14.82,10.38],15)
    # center hub between heads
    add(els,[5.95,11.45,5.80],[10.05,14.95,10.20],13)
    add(els,[5.65,12.10,5.55],[10.35,14.30,10.45],8)
    add(els,[6.25,12.54,5.34],[9.75,13.06,10.66],15)
    # upper outline caps to create boxy silhouette
    add(els,[1.10,15.20,5.50],[5.45,15.72,10.50],8)
    add(els,[10.55,15.20,5.50],[14.90,15.72,10.50],8)
    add(els,[6.12,14.95,6.02],[9.88,15.58,9.98],8)
    # lower support fins under head
    add(els,[4.78,10.90,7.00],[6.05,11.42,9.00],13)
    add(els,[9.95,10.90,7.00],[11.22,11.42,9.00],13)

    model={
        'parent':'minecraft:block/block',
        'ambientocclusion':False,
        'gui_light':'front',
        'textures':{
            'palette':'oraclearsenal:item/palette',
            'particle':'oraclearsenal:item/palette',
        },
        'display':{
            'thirdperson_righthand':{'rotation':[0,90,-30],'translation':[1.1,4.1,0.2],'scale':[1.62,1.62,1.62]},
            'thirdperson_lefthand':{'rotation':[0,-90,30],'translation':[1.1,4.1,0.2],'scale':[1.62,1.62,1.62]},
            'firstperson_righthand':{'rotation':[0,-92,24],'translation':[0.8,4.15,1.0],'scale':[1.84,1.84,1.84]},
            'firstperson_lefthand':{'rotation':[0,92,-24],'translation':[0.8,4.15,1.0],'scale':[1.84,1.84,1.84]},
            'gui':{'rotation':[18,224,0],'translation':[0,0,0],'scale':[1.05,1.05,1.05]},
            'ground':{'rotation':[0,0,0],'translation':[0,3.1,0],'scale':[0.86,0.86,0.86]},
            'fixed':{'rotation':[0,180,0],'translation':[0,0,0],'scale':[1.00,1.00,1.00]},
        },
        'elements':els,
    }
    return model

# --- bbmodel ---
def write_bbmodel(model, out_path: Path):
    palette_bytes=(TEXTURES/'palette.png').read_bytes()
    bb={
        'meta':{'format_version':'4.10','model_format':'java_block'},
        'name':'form_5',
        'resolution':{'width':16,'height':16},
        'display':model['display'],
        'textures':[{'name':'palette.png','id':'0','particle':True,'source':'data:image/png;base64,'+base64.b64encode(palette_bytes).decode('ascii')}],
        'elements':[]
    }
    for index, e in enumerate(model['elements']):
        bb['elements'].append({'name':f'part_{index+1:02}', 'from':e['from'],'to':e['to'],'faces':{f:{'uv':v['uv'],'texture':0} for f,v in e['faces'].items()}})
    out_path.write_text(json.dumps(bb, ensure_ascii=False, indent=2)+'\n', encoding='utf8')

# --- preview render ---
def render_preview(model, out_path: Path):
    W,H=1280,900
    img=Image.new('RGBA',(W,H),(239,236,231,255))
    dr=ImageDraw.Draw(img)
    for y in range(H):
        t=y/H
        dr.line((0,y,W,y), fill=(int(243-16*t), int(241-16*t), int(237-12*t),255))
    dr.rounded_rectangle((20,20,W-20,H-20), radius=26, outline=(66,71,76,255), width=3)
    try:
        title=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',30)
        sub=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
    except OSError:
        title=sub=ImageFont.load_default()
    dr.text((44,36),'Rien | Form V Sledgehammer', fill=(20,24,30,255), font=title)
    dr.text((44,84),'MODEL-ONLY REBUILD / reference-based double-headed black hammer', fill=(78,82,88,255), font=sub)
    dr.line((44,120,W-44,120), fill=(156,154,149,255), width=2)

    ox, oy = 410, 805
    sx, sy = 38.0, 38.0
    depth = 11.0

    elems=[]
    for e in model['elements']:
        x0,y0,z0=e['from']; x1,y1,z1=e['to']
        uv=e['faces']['north']['uv']
        idx=int(uv[0]//4)+4*int(uv[1]//4)
        color=PALETTE_COLORS.get(idx,(50,54,60,255))
        elems.append((z0+z1, y0+y1, x0,y0,z0,x1,y1,z1,color))
    # back to front, low to high
    elems.sort(key=lambda t:(t[0], t[1]))

    def shade(c, f):
        return tuple(max(0,min(255,int(ch*f))) for ch in c[:3]) + (255,)

    for _,__,x0,y0,z0,x1,y1,z1,c in elems:
        # front
        fx0 = ox + (x0-8)*sx
        fx1 = ox + (x1-8)*sx
        fy0 = oy - y1*sy
        fy1 = oy - y0*sy
        # depth offset for top/side illusion
        dx = (z1-8)*depth*0.55
        dy = -(z1-8)*depth*0.42
        dr.rectangle((fx0,fy0,fx1,fy1), fill=c)
        # top
        top=[(fx0,fy0),(fx1,fy0),(fx1+dx,fy0+dy),(fx0+dx,fy0+dy)]
        side=[(fx1,fy0),(fx1,fy1),(fx1+dx,fy1+dy),(fx1+dx,fy0+dy)]
        dr.polygon(top, fill=shade(c,1.15))
        dr.polygon(side, fill=shade(c,0.78))
        dr.line(top+[top[0]], fill=(18,21,26,180), width=1)
        dr.line(side+[side[0]], fill=(18,21,26,180), width=1)
    # highlight outlines / floor shadow
    dr.ellipse((220,792,650,848), fill=(0,0,0,28))
    # player scale silhouette
    px=1020; py=800; s=7
    sil=(117,120,116,255)
    dr.rectangle((px-18*s,py-20*s,px+18*s,py-2*s), fill=(112,120,132,255))
    dr.rectangle((px-12*s,py-30*s,px+12*s,py-20*s), fill=(192,191,183,255))
    dr.rectangle((px-18*s,py-2*s,px-2*s,py+18*s), fill=(77,83,95,255))
    dr.rectangle((px+2*s,py-2*s,px+18*s,py+18*s), fill=(77,83,95,255))
    dr.rectangle((px-27*s,py-20*s,px-18*s,py-4*s), fill=sil)
    dr.rectangle((px+18*s,py-20*s,px+27*s,py-4*s), fill=sil)
    dr.text((px-72,py+18),'PLAYER / 1.8m', fill=(60,64,70,255), font=sub)
    dr.text((44,H-48),'ACTUAL MODEL PREVIEW  |  generated after model update', fill=(49,53,59,255), font=sub)
    img.convert('RGB').save(out_path, quality=95)


def main():
    model=build_form5_model()
    model_path=MODELS/'form_5.json'
    model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    write_bbmodel(model, BB/'form_5.bbmodel')
    render_preview(model, ROOT/'FORM_5_SLEDGEHAMMER_V104_PREVIEW.png')
    print('Generated Form V sledgehammer v0.10.4')

if __name__=='__main__':
    main()
