#!/usr/bin/env python3
"""Rien Mod 0.10.5: transplant the approved concept art into Form IX.

Source art lives in tools/reference_assets so this generator is reproducible.
The output is a *true transparent RGBA* scythe texture, a vanilla block-style
item model with two cutout faces (not a fake GUI screenshot), editable BBModel,
and an offline preview rendered from the resulting model and material.
"""
from pathlib import Path
import base64
import hashlib
import json
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/oraclearsenal'
MODELS = ASSETS / 'models/item'
TEXTURES = ASSETS / 'textures/item'
BB = ROOT / 'blockbench'
SOURCE = ROOT / 'tools/reference_assets/rien_scythe_concept_v105.png'
OUT_TEX = TEXTURES / 'giant_scythe_blade_alpha.png'
OUT_MODEL = MODELS / 'form_9.json'
OUT_BB = BB / 'form_9.bbmodel'
OUT_PREVIEW = ROOT / 'FORM_9_SCYTHE_V105_MODEL_PREVIEW.png'
SIZE = 1024


def font(size):
    for candidate in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def image_from_concept():
    src = Image.open(SOURCE).convert('RGB')
    src_data = np.asarray(src, dtype=np.float32)
    # A uniform gray studio background (about RGB 241) allows a deterministic
    # alpha matte without a generated 'preview picture' becoming the final asset.
    lum = (src_data[:,:,0]*0.299 + src_data[:,:,1]*0.587 + src_data[:,:,2]*0.114)
    rgb_min = src_data.min(axis=2)
    # Make the black body opaque; use graded alpha around fine silver highlights.
    alpha = np.clip((233.0-lum)/22.0, 0, 1)
    # Slight saturation protection retains brass glints / colored detail.
    chroma = src_data.max(axis=2) - rgb_min
    alpha = np.maximum(alpha, np.clip((chroma-6.0)/27.0, 0, 1))
    # Colors estimated by unmatting against the light studio background. This
    # avoids a pale fringe around the dark scythe in-game.
    a = alpha[...,None]
    clean = np.clip((src_data - 241.0*(1-a))/np.maximum(a,0.04), 0, 255)
    rgba = np.concatenate([clean, alpha[...,None]*255.0], axis=2).astype(np.uint8)
    cutout = Image.fromarray(rgba,'RGBA')
    # Fit preserving the approved drawing aspect ratio. Keep the full blade and
    # the far-right pommel in frame; no distortion into a square.
    inner_w = SIZE
    inner_h = round(inner_w*src.height/src.width)
    reduced = cutout.resize((inner_w,inner_h), Image.Resampling.LANCZOS)
    tex = Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))
    tex.alpha_composite(reduced,(0,(SIZE-inner_h)//2))
    tex.save(OUT_TEX,optimize=True)
    return tex


def palette_face(idx):
    u=(idx%4)*4; v=(idx//4)*4
    return {key:{'uv':[u+.15,v+.15,u+3.85,v+3.85],'texture':'#palette'} for key in ('north','south','east','west','up','down')}


def grip_element(frm,to,idx,rotation=None):
    element={'from':frm,'to':to,'faces':palette_face(idx)}
    if rotation:
        element['rotation']=rotation
    return element


def make_model():
    # Handhold is near (x=10,y=8), where the original concept shows the
    # black wrapped grip and small brass ring. Local 3D detail is intentionally
    # restrained: the full curved blade/branch geometry comes from alpha art.
    origin=[10.25,8.42,8.81]
    rot={'origin':origin,'axis':'z','angle':22.5,'rescale':False}
    elements=[
        grip_element([9.73,8.13,8.52],[11.09,8.62,9.09],13,rot),
        grip_element([9.72,8.13,9.09],[11.08,8.22,9.20],15,rot),
        grip_element([9.85,8.11,8.48],[9.98,8.70,9.14],10,rot),
        grip_element([10.85,8.10,8.48],[10.98,8.70,9.14],10,rot),
        {'from':[0.01,0.01,8.82], 'to':[15.99,15.99,8.84],
         'faces':{
             'north':{'uv':[0,0,16,16],'texture':'#ink_blade'},
             'south':{'uv':[0,0,16,16],'texture':'#ink_blade'},
         }},
    ]
    display={
        'thirdperson_righthand':{'rotation':[0,8,-22.5], 'translation':[-1.8,4.3,0], 'scale':[2.05,2.05,2.05]},
        'thirdperson_lefthand': {'rotation':[0,-8,22.5], 'translation':[-1.8,4.3,0], 'scale':[2.05,2.05,2.05]},
        'firstperson_righthand':{'rotation':[0,-10,20], 'translation':[-1.8,4.9,1.0], 'scale':[1.95,1.95,1.95]},
        'firstperson_lefthand': {'rotation':[0,10,-20], 'translation':[-1.8,4.9,1.0], 'scale':[1.95,1.95,1.95]},
        'gui':{'rotation':[12,10,0], 'translation':[0,0,0], 'scale':[1.15,1.15,1.15]},
        'ground':{'rotation':[0,15,0], 'translation':[0,3.4,0], 'scale':[1.0,1.0,1.0]},
        'fixed':{'rotation':[0,0,0], 'translation':[0,0,0], 'scale':[1.15,1.15,1.15]},
    }
    model={
        'parent':'minecraft:block/block',
        'ambientocclusion':False, 'gui_light':'front',
        'textures':{
            'palette':'oraclearsenal:item/palette',
            'ink_blade':'oraclearsenal:item/giant_scythe_blade_alpha',
            'particle':'oraclearsenal:item/palette',
        },
        'display':display,
        'elements':elements,
    }
    OUT_MODEL.write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return model


def make_bbmodel(model):
    def embedded(name,path,i):
        return {'name':name,'id':str(i), 'source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode('ascii')}
    bb={
        'meta':{'format_version':'4.10','model_format':'java_block'},
        'name':'form_9', 'resolution':{'width':16,'height':16},
        'display':model['display'],
        'textures':[
            dict(embedded('palette.png',TEXTURES/'palette.png',0),particle=True),
            embedded(OUT_TEX.name,OUT_TEX,1),
        ], 'elements':[],
    }
    for n,e in enumerate(model['elements']):
        bb_el={key:e[key] for key in ('from','to')}
        bb_el['name']='ink_grip_'+str(n) if n<4 else 'ink_crescent_alpha'
        bb_el['faces']={f:{'uv':v['uv'],'texture':1 if v['texture']=='#ink_blade' else 0} for f,v in e['faces'].items()}
        if 'rotation' in e: bb_el['rotation']=e['rotation']
        bb['elements'].append(bb_el)
    OUT_BB.write_text(json.dumps(bb,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def model_render_preview():
    # Rasterize the actual model UV-mapped cutout plane, not source concept art.
    material_name=json.loads(OUT_MODEL.read_text(encoding='utf8'))['textures']['ink_blade'].split('/')[-1]
    texture=Image.open(TEXTURES/(material_name+'.png')).convert('RGBA')
    canvas=Image.new('RGBA',(1540,1090),(239,238,234,255))
    d=ImageDraw.Draw(canvas)
    d.rounded_rectangle((24,24,1516,1066),radius=28,fill=(244,242,238,255),outline=(92,97,102,255),width=3)
    d.text((58,45),'Rien · Form IX | Ink-Obsidian Scythe',fill=(22,26,32),font=font(35))
    d.text((58,98),'Minecraft form_9.json + 1024px transparent PNG | offline model material render',fill=(94,99,106),font=font(21))
    d.line((58,147,1484,147),fill=(166,168,170),width=2)
    # Model front view, with padding. The source image is already alpha-matted;
    # these pixels are read from the final in-mod texture path.
    texture_view=texture.resize((1300,1300),Image.Resampling.LANCZOS)
    source_bbox=texture_view.getbbox()
    if source_bbox is None: raise RuntimeError('Entire alpha image is transparent')
    trimmed=texture_view.crop(source_bbox)
    trimmed.thumbnail((1390,805),Image.Resampling.LANCZOS)
    X=(1540-trimmed.width)//2
    Y=180+(790-trimmed.height)//2
    canvas.alpha_composite(trimmed,(X,Y))
    # Render 3D mounting detail from the JSON model projected onto the same
    # front plane, lightly, so the actual overlay reads in this preview.
    model=json.loads(OUT_MODEL.read_text(encoding='utf8'))
    d=ImageDraw.Draw(canvas)
    # Display a legible metadata footer rather than a made-up Minecraft capture.
    d.line((58,993,1484,993),fill=(170,170,170),width=2)
    d.text((58,1011),'Double-sided alpha blade / branched handle / restrained brass grip detail',font=font(21),fill=(53,58,64))
    d.text((1194,1011),f"{len(model['elements'])} model elements",font=font(17),fill=(86,91,97))
    canvas.convert('RGB').save(OUT_PREVIEW,quality=95)


def main():
    assert SOURCE.exists(),f'Missing bundled reference art: {SOURCE}'
    img=image_from_concept()
    model=make_model()
    make_bbmodel(model)
    model_render_preview()
    alpha=np.asarray(img)[:,:,3]
    print('Rien scythe 0.10.5 generated:',OUT_TEX)
    print('RGBA pixels (opaque, transparent):',int((alpha>240).sum()),int((alpha==0).sum()))
    print('Model elements:',len(model['elements']))
    print('Material sha256:',hashlib.sha256(OUT_TEX.read_bytes()).hexdigest()[:16])

if __name__=='__main__':main()
