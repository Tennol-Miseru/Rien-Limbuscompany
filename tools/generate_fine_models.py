"""Rien Mod V0.9.0
Hand-authored-style Blockbench item models for the ink-dark arsenal.
Exports both .bbmodel sources and vanilla JSON item models.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, random, base64, copy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/oraclearsenal'
MODELS = ASSETS / 'models/item'
TEX = ASSETS / 'textures/item'
BB = ROOT / 'blockbench'
BB.mkdir(exist_ok=True)

# Materials: deep black ink, graphite, silver edge, aged gold, a touch of blue and crimson.
PALETTE = [
    '#050608', '#0c1015', '#151a21', '#1e252e',
    '#313844', '#5c6570', '#939da7', '#d7dde4',
    '#6a512f', '#9e7a42', '#d4b06d', '#5a0f15',
    '#2348a6', '#0a0d12', '#eef2f7', '#4b525b',
]

def rgb(h):
    return tuple(int(h[i:i+2], 16) for i in (1,3,5))

# 4x4 material palette texture.
img = Image.new('RGBA', (64,64))
p = img.load(); rng = random.Random(20261022)
for i,hexv in enumerate(PALETTE):
    base = rgb(hexv)
    x0=(i%4)*16; y0=(i//4)*16
    for y in range(y0,y0+16):
        for x in range(x0,x0+16):
            n = rng.randint(-6,6)
            if (x+y+i)%9==0: n += 5
            if (x*3+y*5+i)%23==0: n -= 5
            p[x,y] = tuple(max(0,min(255,c+n)) for c in base)+(255,)
img.save(TEX/'palette.png')

def face(material):
    u=(material%4)*4; v=(material//4)*4
    return {d:{'uv':[u+.15,v+.15,u+3.85,v+3.85],'texture':'#palette'} for d in ['north','south','east','west','up','down']}

class Model:
    def __init__(self,name):
        self.name=name
        self.e=[]
    def add(self,x0,y0,z0,x1,y1,z1,m,name=None,*,rot=None):
        """Append a named part. Rotation is keyword-only to prevent text labels
        accidentally being exported as rotation metadata (v0.8.5 regression).
        """
        if not (0 <= x0 < x1 <= 16 and 0 <= y0 < y1 <= 16 and 0 <= z0 < z1 <= 16):
            raise ValueError((self.name,x0,y0,z0,x1,y1,z1))
        if name is not None and not isinstance(name, str):
            raise TypeError(f'{self.name}: part name must be text, got {name!r}')
        el={'from':[round(x0,3),round(y0,3),round(z0,3)],'to':[round(x1,3),round(y1,3),round(z1,3)],'faces':face(m)}
        if rot is not None:
            if (not isinstance(rot, (tuple,list)) or len(rot) != 3
                    or not isinstance(rot[0], (tuple,list)) or len(rot[0]) != 3
                    or any(not isinstance(v, (int,float)) for v in rot[0])
                    or rot[1] not in ('x','y','z')
                    or not isinstance(rot[2], (int,float))
                    or float(rot[2]) not in (-45,-22.5,0,22.5,45)):
                raise ValueError(f'{self.name}: invalid rotation: {rot!r}')
            el['rotation']={'origin':list(rot[0]),'axis':rot[1],'angle':rot[2],'rescale':True}
        if name: el['name']=name
        self.e.append(el); return self
    def rod(self,y0,y1,r=.34,m=8):
        return self.add(8-r,y0,8-r,8+r,y1,8+r,m)
    def handle(self,top=4.8,r=.56,m=8,gold=True,guard=True,pommel=True):
        self.rod(1.0,top,r,m)
        # wraps
        yy=1.2
        while yy < top-.1:
            self.add(7.25,yy,8.84,8.75,yy+.11,9.04,10 if gold else 15)
            yy += .52
        if pommel:
            self.add(7.18,.82,7.18,8.82,1.42,8.82,9 if gold else 15)
            self.add(7.52,.62,7.52,8.48,.82,8.48,14)
        if guard:
            self.add(5.3,top-.18,7.3,10.7,top+.32,8.7,9 if gold else 15)
            self.add(5.0,top+.02,7.44,11.0,top+.18,8.56,10 if gold else 6)
            self.add(5.2,top-.28,7.5,5.55,top+.45,8.5,10 if gold else 15)
            self.add(10.45,top-.28,7.5,10.8,top+.45,8.5,10 if gold else 15)
        return self
    def spine(self,y0,y1,w=1.8,core=13,edge=7):
        self.add(8-w/2,y0,7.12,8+w/2,y1,8.88,core)
        self.add(8-w/2+.12,y0+.05,8.88,8+w/2-.12,y1-.05,9.04,edge)
        self.add(8-w/2,y0+.08,7.2,8-w/2+.22,y1-.08,8.8,4)
        self.add(8+w/2-.22,y0+.08,7.2,8+w/2,y1-.08,8.8,4)
        return self
    def export(self,overrides=False):
        display = copy.deepcopy(GIANT_SCYTHE_DISPLAY if self.name == 'form_9' else DISPLAY)
        data={
            'parent':'minecraft:block/block','ambientocclusion':False,'gui_light':'front',
            'textures':{'palette':'oraclearsenal:item/palette','particle':'oraclearsenal:item/palette'},
            'display':display,'elements':[{'from':e['from'],'to':e['to'],'faces':e['faces'], **({'rotation':e['rotation']} if 'rotation' in e else {})} for e in self.e]
        }
        if overrides:
            data['overrides']=[{'predicate':{'custom_model_data':i},'model':f'oraclearsenal:item/form_{i}'} for i in range(1,11)]
        (MODELS/f'{self.name}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        bb={
            'meta':{'format_version':'4.10','model_format':'java_block'},
            'name':self.name,
            'resolution':{'width':64,'height':64},
            'elements':[],
            'textures':[{
                'name':'palette.png','id':'0','particle':True,
                'source':'data:image/png;base64,'+base64.b64encode((TEX/'palette.png').read_bytes()).decode()
            }],
            'display':display
        }
        for i,e in enumerate(self.e):
            el={k:v for k,v in e.items() if k in ('from','to','rotation')}
            el['name']=e.get('name',f'part_{i:03d}')
            el['faces']={k:{'uv':v['uv'],'texture':0} for k,v in e['faces'].items()}
            bb['elements'].append(el)
        (BB/f'{self.name}.bbmodel').write_text(json.dumps(bb,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        return data

DISPLAY={
    'thirdperson_righthand': {'rotation':[0,90,-22],'translation':[0,3.9,0],'scale':[1.28,1.28,1.28]},
    'thirdperson_lefthand':  {'rotation':[0,-90,22],'translation':[0,3.9,0],'scale':[1.28,1.28,1.28]},
    'firstperson_righthand': {'rotation':[0,-92,24],'translation':[1.0,3.75,1.0],'scale':[1.58,1.58,1.58]},
    'firstperson_lefthand':  {'rotation':[0,92,-24],'translation':[1.0,3.75,1.0],'scale':[1.58,1.58,1.58]},
    'gui': {'rotation':[24,225,0],'translation':[0,0,0],'scale':[1.12,1.12,1.12]},
    'ground': {'rotation':[0,0,0],'translation':[0,3,0],'scale':[0.88,0.88,0.88]},
    'fixed': {'rotation':[0,180,0],'translation':[0,0,0],'scale':[1,1,1]}
}

GIANT_SCYTHE_DISPLAY={
    'thirdperson_righthand': {'rotation':[0,92,-18],'translation':[0,5.55,0],'scale':[1.88,1.88,1.88]},
    'thirdperson_lefthand':  {'rotation':[0,-92,18],'translation':[0,5.55,0],'scale':[1.88,1.88,1.88]},
    'firstperson_righthand': {'rotation':[0,-94,24],'translation':[1.25,5.45,1.1],'scale':[2.05,2.05,2.05]},
    'firstperson_lefthand':  {'rotation':[0,94,-24],'translation':[1.25,5.45,1.1],'scale':[2.05,2.05,2.05]},
    'gui': {'rotation':[24,225,0],'translation':[0,0,0],'scale':[1.2,1.2,1.2]},
    'ground': {'rotation':[0,0,0],'translation':[0,4,0],'scale':[1.02,1.02,1.02]},
    'fixed': {'rotation':[0,180,0],'translation':[0,0,0],'scale':[1.12,1.12,1.12]}
}

# ----- Weapon designs -----

def twin_serpent_staff():
    m=Model('twin_serpent_staff')
    # main cross body
    m.add(2.9,6.15,7.1,13.1,6.95,8.9,13,'body')
    m.add(3.2,6.4,8.92,12.8,6.68,9.12,4,'edge')
    m.add(7.5,4.75,7.55,8.5,6.15,8.45,10,'stem')
    m.add(7.84,3.65,7.84,8.16,4.75,8.16,14,'needle')
    # side posts
    for x in [4.1,11.9]:
        m.add(x-.28,6.9,7.28,x+.28,11.7,8.72,9)
        m.add(x-.10,7.1,8.72,x+.10,11.4,8.96,10)
        m.add(x-.36,6.1,7.2,x+.36,6.9,8.8,10)
    # halo
    halo=[(4.8,11.8),(5.55,12.55),(6.4,13.1),(7.2,13.45),(8.0,13.58),(8.8,13.45),(9.6,13.1),(10.45,12.55),(11.2,11.8)]
    for x,y in halo:
        m.add(x-.35,y-.22,7.28,x+.35,y+.22,8.72,10)
        m.add(x-.18,y-.05,8.72,x+.18,y+.05,8.92,14)
    # inner black core and lower charm
    m.add(7.34,10.5,7.34,8.66,11.65,8.66,1)
    m.add(7.7,10.78,8.7,8.3,11.38,8.92,12)
    m.add(7.86,5.9,7.86,8.14,6.45,8.14,10)
    return m

def ink_cleaver():
    m=Model('form_1'); m.handle(top=12.8,r=.55,guard=False)
    m.add(7.48,4.7,7.38,8.52,13.0,8.62,8,'haft_core')
    # huge slab blade
    m.add(3.9,9.7,7.0,8.4,15.2,9.0,13,'blade_mass')
    m.add(4.15,9.95,8.96,8.16,14.95,9.14,7,'edge')
    m.add(3.7,10.25,7.2,4.35,14.85,8.8,4,'back_spine')
    # top notch and belly
    m.add(4.6,14.45,7.24,7.95,15.22,8.76,13,'tip_plate')
    m.add(5.35,10.35,9.02,5.7,14.35,9.28,10,'gold_inlay_1')
    m.add(6.0,11.1,9.02,6.3,13.7,9.28,10,'gold_inlay_2')
    m.add(6.7,11.6,9.02,7.0,12.95,9.28,10,'gold_inlay_3')
    # rear hook / shoulder
    m.add(7.9,9.7,7.16,8.55,10.6,8.84,15,'shoulder')
    return m


def ink_spike():
    m=Model('form_2'); m.handle(top=5.2,r=.5,guard=True)
    m.spine(5.25,8.6,1.55,13,7)
    m.spine(8.6,11.8,1.12,13,7)
    m.spine(11.8,13.75,.8,13,7)
    m.add(6.1,12.8,7.24,9.9,14.35,8.76,13,'head')
    m.add(6.95,13.78,7.56,9.05,15.48,8.44,7,'point')
    m.add(7.66,15.0,7.84,8.34,15.96,8.16,14,'tip')
    # side fins
    for x0,x1 in [(5.3,6.2),(9.8,10.7)]:
        m.add(x0,12.1,7.3,x1,13.0,8.7,4)
        m.add(x0+.15,12.75,7.42,x1-.15,13.45,8.58,15)
    # lower thorns
    for y in [7.0,9.0,10.9]:
        m.add(5.95,y,7.34,6.5,y+.55,8.66,4)
        m.add(9.5,y,7.34,10.05,y+.55,8.66,4)
    return m


def ink_greatsword(name='form_3', ultra=False):
    m=Model(name); top=4.0 if ultra else 4.7
    if not ultra:
        # Refined elegant greatsword: slimmer silhouette, layered fuller,
        # gilded ricasso and ink-thorn side ornaments.
        m.handle(top=top,r=.54,guard=False,gold=True,pommel=True)
        # pommel / grip refinements
        m.add(7.3,0.64,7.3,8.7,1.06,8.7,10,'pommel_cap')
        m.add(7.58,0.42,7.58,8.42,0.64,8.42,14,'pommel_tip')
        m.add(7.12,1.34,7.12,8.88,4.58,8.88,8,'grip_core')
        for y in [1.6,2.15,2.7,3.25,3.8,4.35]:
            m.add(7.18,y,8.86,8.82,y+.12,9.06,10,f'wrap_{int(y*100)}')
        # ornate guard + quillons
        m.add(5.15,4.48,7.28,10.85,4.96,8.72,10,'guard_bar')
        m.add(4.65,4.54,7.34,5.48,5.2,8.66,15,'guard_left_tip')
        m.add(10.52,4.54,7.34,11.35,5.2,8.66,15,'guard_right_tip')
        m.add(6.0,4.26,7.42,7.1,5.42,8.58,9,'guard_left_root')
        m.add(8.9,4.26,7.42,10.0,5.42,8.58,9,'guard_right_root')
        m.add(7.18,4.28,7.18,8.82,5.32,8.82,10,'ricasso_block')
        m.add(7.52,4.54,8.82,8.48,5.22,9.06,14,'ricasso_glint')
        # lower blade shoulders
        m.add(5.95,5.1,7.12,10.05,6.1,8.88,13,'shoulder_plate')
        m.add(6.18,5.18,8.88,9.82,5.96,9.06,7,'shoulder_edge')
        m.add(5.55,5.32,7.26,6.2,6.18,8.74,4,'left_shoulder_fang')
        m.add(9.8,5.32,7.26,10.45,6.18,8.74,4,'right_shoulder_fang')
        # main blade mass in layered sections
        sections=[(6.0,7.6,2.86),(7.6,9.55,2.52),(9.55,11.35,2.12),(11.35,12.95,1.68),(12.95,14.15,1.22)]
        for idx,(y0,y1,w) in enumerate(sections):
            m.add(8-w/2,y0,7.08,8+w/2,y1,8.92,13,f'blade_core_{idx}')
            m.add(8-w/2+.16,y0+.06,8.92,8+w/2-.16,y1-.06,9.08,7,f'edge_{idx}')
            m.add(8-w/2,y0+.1,7.16,8-w/2+.24,y1-.1,8.84,4,f'left_ridge_{idx}')
            m.add(8+w/2-.24,y0+.1,7.16,8+w/2,y1-.1,8.84,4,f'right_ridge_{idx}')
        # fuller / central gleam
        m.add(7.74,5.52,8.94,8.26,13.4,9.12,7,'central_fuller')
        m.add(7.86,5.58,7.82,8.14,13.26,8.18,14,'central_spine')
        # decorative mid-blade ornaments
        for y in [7.1,9.15,11.1]:
            m.add(6.08,y,7.3,6.72,y+.46,8.7,15,f'orn_l_{int(y*10)}')
            m.add(9.28,y,7.3,9.92,y+.46,8.7,15,f'orn_r_{int(y*10)}')
            m.add(6.68,y+.14,8.86,6.92,y+.34,9.06,10,f'orn_l_glint_{int(y*10)}')
            m.add(9.08,y+.14,8.86,9.32,y+.34,9.06,10,f'orn_r_glint_{int(y*10)}')
        # upper barbs and tip cluster
        m.add(6.62,13.66,7.28,7.22,14.46,8.72,4,'tip_left_barb')
        m.add(8.78,13.66,7.28,9.38,14.46,8.72,4,'tip_right_barb')
        m.add(7.28,13.98,7.34,8.72,15.56,8.66,13,'tip_body')
        m.add(7.56,14.3,8.88,8.44,15.4,9.08,7,'tip_edge')
        m.add(7.88,15.2,7.9,8.12,15.96,8.1,14,'tipline')
        return m
    # ultra greatsword remains heavier and more brutal
    m.handle(top=top,r=.66,guard=True)
    base_w=3.1
    sections=[(top+.35,6.1,1.0),(6.1,8.7,.95),(8.7,11.2,.86),(11.2,13.0,.72),(13.0,14.55,.58)]
    for y0,y1,k in sections:
        m.spine(y0,y1,base_w*k,13,7)
    m.add(7.36,13.92,7.42,8.64,15.68,8.58,7,'tip')
    m.add(7.82,14.94,7.82,8.18,15.96,8.18,14,'tipline')
    m.add(7.74,top+.48,8.96,8.26,13.84,9.14,7,'central_glint')
    thorn_y=[6.2,8.4,10.5,12.6]
    for y in thorn_y:
        span=1.1
        m.add(8-base_w/2-span,y,7.36,8-base_w/2+.05,y+.55,8.64,4)
        m.add(8+base_w/2-.05,y,7.36,8+base_w/2+span,y+.55,8.64,4)
    for y in [5.6,7.8,10.0,12.2]:
        m.add(4.15,y,7.28,5.0,y+.7,8.72,15)
        m.add(11.0,y,7.28,11.85,y+.7,8.72,15)
        m.add(4.85,y+.14,8.72,5.1,y+.54,9.02,7)
        m.add(10.9,y+.14,8.72,11.15,y+.54,9.02,7)
    return m


def needle_rapier():
    m=Model('form_4'); m.handle(top=5.35,r=.46,guard=False)
    m.add(7.88,5.32,7.88,8.12,15.45,8.12,7,'needle')
    m.add(7.94,14.7,7.94,8.06,15.96,8.06,14,'tip')
    # ornate rectangular cage
    m.add(4.95,4.55,7.3,11.05,5.05,8.7,10,'guard_front')
    m.add(5.2,4.3,7.44,5.55,8.05,8.56,10,'left_post')
    m.add(10.45,4.3,7.44,10.8,8.05,8.56,10,'right_post')
    m.add(5.35,7.75,7.44,10.65,8.1,8.56,10,'top_frame')
    m.add(5.35,4.55,7.44,10.65,4.82,8.56,10,'bottom_frame')
    m.add(5.55,6.55,7.52,10.45,6.82,8.48,15,'mid_bar')
    m.add(7.54,5.02,7.54,8.46,5.62,8.46,9,'hub')
    m.add(7.82,5.62,7.82,8.18,6.3,8.18,14,'bridge')
    return m


def ink_hammer():
    m=Model('form_5'); m.handle(top=12.0,r=.56,guard=False)
    m.add(3.0,10.7,5.8,13.0,14.85,10.2,13,'head')
    m.add(3.25,10.95,5.64,12.75,14.55,5.8,4,'top_front')
    m.add(3.25,10.95,10.2,12.75,14.55,10.36,7,'top_back')
    m.add(2.65,11.0,6.0,3.3,14.45,10.0,4,'left_cap')
    m.add(12.7,11.0,6.0,13.35,14.45,10.0,4,'right_cap')
    m.add(7.2,11.4,10.2,8.8,13.8,10.46,12,'rear_mark')
    # underfangs
    for x in [4.2,6.2,8.2,10.2]:
        m.add(x,10.05,7.2,x+.5,10.7,8.8,15)
    return m


def ink_spear():
    m=Model('form_7'); m.handle(top=3.2,r=.34,guard=False)
    m.rod(3.2,12.0,.32,8)
    # gold ring hilt / oracle circle
    m.add(5.7,11.5,7.46,10.3,11.92,8.54,10,'cross')
    m.add(7.48,11.0,7.48,8.52,12.25,8.52,10,'ring_hub')
    # long dark spear head
    m.add(6.7,11.95,7.18,9.3,13.65,8.82,13,'base_head')
    m.add(7.22,13.4,7.48,8.78,15.55,8.52,7,'point')
    m.add(7.82,15.0,7.82,8.18,15.96,8.18,14,'tip')
    # trailing barbs
    m.add(6.05,12.55,7.42,6.95,13.75,8.58,15)
    m.add(9.05,12.55,7.42,9.95,13.75,8.58,15)
    return m


def long_whip():
    """Eighth form: a continuous ink-black LONG WHIP, not a chain or flail.

    We use slim, individually oriented leather/ink segments, a tapered tip,
    and sparse gray edge highlights. All rotations use 1.21.1-compatible
    angles; a model validator is run before packaging.
    """
    import math
    m = Model('form_8')
    # Compact brass-ended leather grip. There is NO lock, weight or chain link.
    m.add(7.35, 1.2, 7.35, 8.65, 4.7, 8.65, 13, 'leather_grip')
    m.add(7.52, 1.42, 8.66, 8.48, 4.45, 8.87, 4, 'grip_highlight')
    for i, y in enumerate([1.55, 2.26, 2.97, 3.68]):
        m.add(7.29, y, 7.4, 8.71, y+.15, 8.60,
              9 if i in (0, 3) else 15, f'leather_band_{i}')
    m.add(7.20, .88, 7.20, 8.80, 1.34, 8.80, 9, 'pommel')
    m.add(7.65, .64, 7.65, 8.35, .9, 8.35, 10, 'pommel_rivet')
    m.add(7.25, 4.52, 7.22, 8.75, 5.09, 8.78, 9, 'gold_collar')
    m.add(7.65, 5.07, 7.65, 8.35, 5.54, 8.35, 2, 'lash_joint')

    # A single twisting continuous tapered lash. Unlike the old chain there
    # are no detached links and no heavy terminal block. Two offset render
    # planes add subtle volume rather than a flat dark ribbon.
    curve = [
        (8.0, 5.3, 8.0), (8.17, 6.05, 7.98), (8.52, 6.90, 7.90),
        (8.74, 7.75, 7.83), (8.68, 8.63, 7.77), (8.35, 9.46, 7.76),
        (7.83, 10.22, 7.82), (7.14, 10.91, 7.94), (6.44, 11.60, 8.10),
        (5.70, 12.32, 8.20), (4.91, 13.02, 8.28), (4.17, 13.62, 8.32),
        (3.39, 14.12, 8.36), (2.67, 14.07, 8.35), (2.18, 13.41, 8.27),
        (1.85, 12.66, 8.12), (1.65, 11.84, 8.04),
    ]

    def segment(a,b,width,material,name, offset_z=0):
        ax,ay,az=a; bx,by,bz=b
        cx=(ax+bx)/2; cy=(ay+by)/2; cz=(az+bz)/2 + offset_z
        dx=bx-ax; dy=by-ay
        dist=math.hypot(dx,dy)
        # Java block JSON accepts only these axis rotation angles.
        allowed=(-45, -22.5, 0, 22.5, 45)
        if abs(dy)>=abs(dx):
            angle=math.degrees(math.atan2(-dx,dy))
            rotation=min(allowed,key=lambda t:abs(t-angle))
            return m.add(cx-width/2,cy-dist*.57,cz-width*.52,
                         cx+width/2,cy+dist*.57,cz+width*.52,
                         material,name,rot=((cx,cy,cz),'z',rotation))
        angle=math.degrees(math.atan2(dy,dx))
        while angle>90: angle-=180
        while angle< -90: angle+=180
        rotation=min(allowed,key=lambda t:abs(t-angle))
        return m.add(cx-dist*.57,cy-width/2,cz-width*.52,
                     cx+dist*.57,cy+width/2,cz+width*.52,
                     material,name,rot=((cx,cy,cz),'z',rotation))

    last=len(curve)-2
    for i,(a,b) in enumerate(zip(curve, curve[1:])):
        taper=(1-i/(last+1))
        thickness=.60*taper+.17
        mat=13 if i%3 else 2
        segment(a,b,thickness,mat,f'continuous_lash_{i:02d}')
        # Very narrow reflected edge with NO chain-like ring textures.
        if i%3==1 and i<last-1:
            segment(a,b,thickness*.16,5 if i<9 else 6,
                    f'ink_edge_{i:02d}',offset_z=thickness*.68)
    # A ghostly silver-white hairline on the whip's taper.
    m.add(1.56,11.35,7.96,1.76,11.92,8.15,7,'silver_tip')
    return m


def abyss_scythe():
    m=Model('form_9')
    # oversized pole: taller than the wielder once display scale is applied
    m.add(7.26,0.72,7.26,8.74,5.65,8.74,8,'grip_core')
    for i,y in enumerate([1.08,1.76,2.44,3.12,3.80,4.48]):
        m.add(7.18,y,8.82,8.82,y+.13,9.05,10 if i%2==0 else 15,f'wrap_{i}')
    m.add(7.05,0.28,7.05,8.95,0.86,8.95,9,'pommel_main')
    m.add(7.52,0.06,7.52,8.48,0.28,8.48,14,'pommel_tip')
    m.add(7.42,5.55,7.42,8.58,15.85,8.58,8,'shaft_main')
    m.add(7.72,5.75,8.84,8.28,15.55,9.02,4,'shaft_glint')
    # collars and spine accents
    for y in [5.62,9.25,12.45,14.75]:
        m.add(7.18,y,7.18,8.82,y+.34,8.82,9,f'collar_{int(y*10)}')
        m.add(7.56,y+.08,8.82,8.44,y+.26,9.02,10,f'collar_glint_{int(y*10)}')
    # branching organic supports for the blade
    m.add(7.9,14.2,7.18,10.65,15.2,8.82,15,'root_branch_main')
    m.add(9.85,13.18,7.18,12.45,14.18,8.82,15,'root_branch_mid')
    m.add(11.95,11.9,7.2,13.75,12.78,8.8,15,'root_branch_upper')
    m.add(10.62,14.62,7.26,12.34,15.45,8.74,4,'thorn_lobe_low')
    m.add(12.58,13.36,7.26,14.06,14.18,8.74,4,'thorn_lobe_mid')
    m.add(13.75,12.05,7.26,14.95,12.82,8.74,4,'thorn_lobe_high')
    # immense crescent blade, layered and elegant
    segs=[
        (9.25,15.0,11.05,15.62,13),
        (10.6,14.5,12.45,15.18,13),
        (11.85,13.8,13.78,14.55,13),
        (12.95,12.95,14.82,13.78,13),
        (13.82,11.95,15.42,12.85,13),
        (14.45,10.88,15.82,11.78,7),
        (14.92,9.75,15.96,10.66,7),
        (15.14,8.72,15.96,9.42,14),
    ]
    for idx,(x0,y0,x1,y1,mat) in enumerate(segs):
        m.add(x0,y0,7.04,x1,y1,8.96,mat,f'blade_{idx}')
        m.add(x0+.10,y0+.08,8.96,x1-.08,y1-.08,9.12,7 if mat==13 else 14,f'blade_edge_{idx}')
    inner=[
        (10.05,14.32,11.52,14.82,15),
        (11.22,13.72,12.92,14.28,15),
        (12.36,12.95,13.98,13.58,15),
        (13.35,12.05,14.78,12.72,15),
        (14.06,11.02,15.22,11.68,6),
    ]
    for idx,(x0,y0,x1,y1,mat) in enumerate(inner):
        m.add(x0,y0,7.26,x1,y1,8.74,mat,f'inner_blade_{idx}')
    m.add(8.72,14.48,7.32,9.92,15.12,8.68,13,'heel_hook')
    m.add(9.0,14.58,8.68,9.98,15.0,8.9,7,'heel_hook_edge')
    m.add(5.42,14.55,7.36,8.05,15.02,8.64,11,'crimson_tail_main')
    m.add(4.72,13.98,7.42,6.18,14.46,8.58,12,'azure_tail_1')
    m.add(4.08,13.32,7.46,5.18,13.78,8.54,7,'silver_tail_2')
    m.add(6.78,14.36,7.26,7.34,15.06,8.74,4,'rear_talon')
    return m

MODELS_DEF=[
    ('twin_serpent_staff', twin_serpent_staff),
    ('form_1', ink_cleaver),
    ('form_2', ink_spike),
    ('form_3', lambda: ink_greatsword('form_3', False)),
    ('form_4', needle_rapier),
    ('form_5', ink_hammer),
    ('form_6', lambda: ink_greatsword('form_6', True)),
    ('form_7', ink_spear),
    ('form_8', long_whip),
    ('form_9', abyss_scythe),
]

built=[]
for name, factory in MODELS_DEF:
    m=factory() if callable(factory) else factory
    if not isinstance(m, Model):
        raise TypeError(name)
    # Historical generator: do not overwrite refined art or its morph overrides.
    # Use the individual build_* scripts to edit existing weapons.
    if not (MODELS / f'{name}.json').exists():
        m.export(overrides=(name=='twin_serpent_staff'))
    built.append(m)

# Preview renderer.
preview = Image.new('RGB', (1250, 980), '#0e1218')
d = ImageDraw.Draw(preview)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
except Exception:
    font = ImageFont.load_default()
labels=['神谕终端·双蛇杖','一式·手斧','二式·墨锥','三式·大剑','四式·刺剑','五式·重锤','六式·特大剑','七式·长枪','八式·长鞭','九式·镰刀']
for i,m in enumerate(built):
    col=i%5; row=i//5
    left=col*250; top=row*480
    d.rounded_rectangle((left+7, top+6, left+243, top+472), 17, fill='#1b2331', outline='#506074', width=2)
    d.text((left+12, top+12), labels[i], fill='#ece6db', font=font)
    parts=sorted(m.e, key=lambda e:(e['from'][2]+e['to'][2])/2, reverse=True)
    def iso(x,y,z):
        return (left+120 + (x-8)*10.5 + (z-8)*4.2, top+372 - (y-1)*16 - (z-8)*2.4)
    for e in parts:
        x0,y0,z0=e['from']; x1,y1,z1=e['to']
        uv=e['faces']['north']['uv']; mat=int(uv[0]//4)+4*int(uv[1]//4)
        base=rgb(PALETTE[mat]); hi=tuple(min(255,int(c*1.15)+10) for c in base); sh=tuple(max(0,int(c*0.66)) for c in base)
        a=iso(x0,y0,z1); b=iso(x1,y0,z1); c=iso(x1,y1,z1); ee=iso(x0,y1,z1)
        d.polygon([a,b,c,ee], fill=hi, outline='#11151a')
        d.polygon([b,iso(x1,y0,z0),iso(x1,y1,z0),c], fill=sh, outline='#101418')
        d.polygon([ee,c,iso(x1,y1,z0),iso(x0,y1,z0)], fill=base, outline='#12161b')
    d.text((left+12, top+440), f'{len(m.e)} parts · bbmodel exported', fill='#aab8c8', font=font)
preview.save(ROOT/'FINE_MODEL_PREVIEW.png')
# Single-weapon rendered preview for delivery after each refinement
focus = built[-1]
single = Image.new('RGB', (760, 920), '#0d1118')
sd = ImageDraw.Draw(single)
sd.rounded_rectangle((18, 18, 742, 902), 28, fill='#162131', outline='#6c7b90', width=3)
try:
    big_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 28)
    small_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
except Exception:
    big_font = font
    small_font = font
sd.text((36, 34), '九式·超巨大镰刀 预览', fill='#f0ebe4', font=big_font)
sd.text((36, 76), 'BBModel / JSON render preview · larger-than-player display tuning', fill='#aebccd', font=small_font)
parts=sorted(focus.e, key=lambda e:(e['from'][2]+e['to'][2])/2, reverse=True)
def iso2(x,y,z):
    return (382 + (x-8)*24 + (z-8)*7.5, 790 - (y-1)*30 - (z-8)*4.1)
for e in parts:
    x0,y0,z0=e['from']; x1,y1,z1=e['to']
    uv=e['faces']['north']['uv']; mat=int(uv[0]//4)+4*int(uv[1]//4)
    base=rgb(PALETTE[mat]); hi=tuple(min(255,int(c*1.16)+12) for c in base); sh=tuple(max(0,int(c*0.64)) for c in base)
    a=iso2(x0,y0,z1); b=iso2(x1,y0,z1); c=iso2(x1,y1,z1); ee=iso2(x0,y1,z1)
    sd.polygon([a,b,c,ee], fill=hi, outline='#11151a')
    sd.polygon([b,iso2(x1,y0,z0),iso2(x1,y1,z0),c], fill=sh, outline='#101418')
    sd.polygon([ee,c,iso2(x1,y1,z0),iso2(x0,y1,z0)], fill=base, outline='#12161b')
sd.text((36, 860), f'{len(focus.e)} parts · oversized display profile enabled', fill='#c5d0df', font=small_font)
single.save(ROOT/'FORM_9_GIANT_SCYTHE_PREVIEW.png')
print('Generated V0.9.0 ink arsenal models:', [m.name for m in built])

# V0.9.1: this art pass supersedes the legacy cuboid form_9 with the
# two-sided transparent scythe plane, so rerunning the full generator
# cannot silently restore the old staircase blade.
import runpy
runpy.run_path(str(Path(__file__).with_name('build_scythe_concept_v105.py')), run_name='__main__')

# v0.9.6: preserve the reference-authored translucent handaxe after general exports.
runpy.run_path(str(Path(__file__).with_name('build_handaxe_alpha.py')), run_name='__main__')

# Keep the hand-authored reference greatsword and flowing whip when regenerating the whole set.
runpy.run_path(str(Path(__file__).with_name('build_greatsword_alpha.py')),run_name='__main__')
runpy.run_path(str(Path(__file__).with_name('build_long_whip_alpha.py')),run_name='__main__')

# V0.10.5: restore the latest hand-authored forms after the generic legacy pass.
# Running this generator must not undo the reference-based swords/hammer/scythe.
runpy.run_path(str(Path(__file__).with_name('build_greatsword_colossal_v102.py')),run_name='__main__')
runpy.run_path(str(Path(__file__).with_name('build_form5_hammer_v104.py')),run_name='__main__')
runpy.run_path(str(Path(__file__).with_name('build_scythe_concept_v105.py')),run_name='__main__')
