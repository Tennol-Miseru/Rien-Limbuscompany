#!/usr/bin/env python3
"""Rebuild form_3 greatsword as a broader, heavier alpha-plane ink greatsword.
Reference intent: huge black greatsword, broad and thick-looking, with root spike cluster.
Generates form_3.json, blockbench/form_3.bbmodel, texture, and preview.
"""
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
SIZE = 768
S = SIZE / 16


def P(x, y):
    return (round(x * S), round((16 - y) * S))


def poly(draw, pts, fill):
    draw.polygon([P(*xy) for xy in pts], fill=fill)


def line(draw, pts, fill, width):
    draw.line([P(*xy) for xy in pts], fill=fill, width=max(1, round(width * S)), joint='curve')


# ---------- Texture silhouette ----------
img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# A broader and more massive greatsword silhouette.
lower_edge = [
    (13.00, 6.15), (11.84, 7.10), (10.54, 8.26), (9.16, 9.58),
    (7.72, 11.00), (6.30, 12.30), (4.98, 13.42), (3.72, 14.34), (2.64, 15.08)
]
upper_edge = [
    (1.88, 14.20), (2.96, 13.30), (4.16, 12.20), (5.46, 10.92),
    (6.82, 9.56), (8.22, 8.12), (9.62, 6.82), (10.98, 5.62), (12.16, 4.68)
]
main = lower_edge + upper_edge
poly(d, main, (8, 10, 15, 255))

# Thicker inner mass near the root to create a heavy sword reading.
poly(d, [(11.24, 5.28), (12.72, 6.08), (12.24, 6.44), (10.88, 5.70)], (10, 12, 18, 220))

# Root spike cluster.
for spike in [
    [(10.84, 5.76), (13.30, 5.78), (12.18, 4.42)],
    [(10.00, 6.34), (12.12, 6.42), (11.14, 5.12)],
    [(9.10, 6.96), (10.98, 7.08), (10.06, 5.86)],
]:
    poly(d, spike, (11, 13, 18, 252))

# Top thorn / finial.
poly(d, [(12.46, 4.78), (12.92, 3.34), (13.38, 4.54)], (16, 18, 22, 248))

# Guard / root wedge accent.
poly(d, [(11.96, 5.68), (13.12, 5.80), (13.18, 5.30), (12.12, 5.18)], (48, 38, 23, 255))
poly(d, [(12.22, 5.58), (12.80, 5.64), (12.82, 5.38), (12.26, 5.30)], (148, 121, 76, 238))

# Highlights.
line(d, [(12.36, 5.92), (11.12, 6.98), (9.80, 8.18), (8.40, 9.52), (7.00, 10.92), (5.62, 12.18), (4.28, 13.30), (3.02, 14.20), (2.20, 14.76)],
     (183, 188, 194, 232), .058)
line(d, [(11.70, 5.26), (10.54, 6.24), (9.26, 7.46), (7.92, 8.80), (6.54, 10.16), (5.18, 11.48), (3.94, 12.58), (2.90, 13.38)],
     (71, 78, 86, 170), .054)
line(d, [(11.16, 5.86), (10.14, 6.84), (8.98, 7.98), (7.70, 9.28), (6.42, 10.52), (5.10, 11.78), (3.96, 12.80), (3.10, 13.48)],
     (102, 109, 118, 94), .030)
line(d, [(7.42, 10.74), (7.12, 10.42), (6.84, 10.12), (6.56, 9.84)], (0, 0, 0, 0), .018)
line(d, [(5.44, 12.36), (5.12, 12.06), (4.84, 11.78), (4.54, 11.54)], (0, 0, 0, 0), .016)

PATH = TEXTURES / 'greatsword_blade_alpha.png'
img.save(PATH)

# ---------- Model geometry ----------
def face(idx):
    u = (idx % 4) * 4
    v = (idx // 4) * 4
    return {f: {'uv': [u + .15, v + .15, u + 3.85, v + 3.85], 'texture': '#palette'}
            for f in ('north', 'south', 'east', 'west', 'up', 'down')}


def box(name, frm, to, mat):
    return {'name': name, 'from': frm, 'to': to, 'faces': face(mat)}


parts = []


def add(name, a, b, mat):
    parts.append(box(name, a, b, mat))


# More substantial hilt to match heavier sword.
add('grip_core', [7.38, 0.26, 7.38], [8.62, 5.42, 8.62], 8)
for i, y in enumerate([0.60, 1.08, 1.56, 2.04, 2.52, 3.00, 3.48, 3.96, 4.44]):
    add(f'wrap_{i}', [7.22, y, 8.64], [8.78, y + 0.11, 8.84], 15 if i % 2 else 5)
add('pommel_block', [7.12, 0.00, 7.12], [8.88, 0.48, 8.88], 9)
add('pommel_cap', [7.50, 0.01, 7.50], [8.50, 0.20, 8.50], 14)
add('guard_core', [6.10, 4.96, 7.12], [9.96, 5.40, 8.88], 9)
add('guard_trim', [6.46, 5.14, 8.88], [9.60, 5.30, 9.12], 10)
add('socket_core', [7.16, 5.12, 7.16], [8.84, 6.10, 8.84], 1)
add('socket_trim', [7.40, 5.34, 8.84], [8.60, 5.94, 9.04], 10)
add('root_spike_a', [8.78, 5.54, 8.18], [12.02, 5.82, 8.96], 13)
add('root_spike_b', [8.60, 6.06, 8.14], [11.38, 6.32, 8.92], 13)
add('root_spike_c', [8.44, 6.60, 8.10], [10.70, 6.84, 8.88], 13)
add('finial', [8.76, 6.18, 8.12], [9.26, 7.38, 8.88], 13)
parts.append({
    'name': 'greatsword_alpha_plane',
    'from': [0.01, 0.01, 8.90], 'to': [15.99, 15.99, 8.92],
    'faces': {
        'north': {'uv': [0, 0, 16, 16], 'texture': '#ink_blade'},
        'south': {'uv': [0, 0, 16, 16], 'texture': '#ink_blade'},
    }
})

display = {
    'thirdperson_righthand': {'rotation': [0, 88, -34], 'translation': [1.0, 4.2, 0], 'scale': [1.78, 1.78, 1.78]},
    'thirdperson_lefthand': {'rotation': [0, -88, 34], 'translation': [1.0, 4.2, 0], 'scale': [1.78, 1.78, 1.78]},
    'firstperson_righthand': {'rotation': [0, -92, 26], 'translation': [1.3, 4.1, 1.0], 'scale': [2.00, 2.00, 2.00]},
    'firstperson_lefthand': {'rotation': [0, 92, -26], 'translation': [1.3, 4.1, 1.0], 'scale': [2.00, 2.00, 2.00]},
    'gui': {'rotation': [22, 228, 0], 'translation': [0, 0, 0], 'scale': [1.12, 1.12, 1.12]},
    'ground': {'rotation': [0, 0, 0], 'translation': [0, 3, 0], 'scale': [0.98, 0.98, 0.98]},
    'fixed': {'rotation': [0, 180, 0], 'translation': [0, 0, 0], 'scale': [1.08, 1.08, 1.08]},
}
model = {
    'parent': 'minecraft:block/block',
    'ambientocclusion': False,
    'gui_light': 'front',
    'textures': {
        'palette': 'oraclearsenal:item/palette',
        'ink_blade': 'oraclearsenal:item/greatsword_blade_alpha',
        'particle': 'oraclearsenal:item/palette'
    },
    'display': display,
    'elements': [{k: v for k, v in e.items() if k != 'name'} for e in parts]
}
(MODELS / 'form_3.json').write_text(json.dumps(model, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

bb = {
    'meta': {'format_version': '4.10', 'model_format': 'java_block'},
    'name': 'form_3',
    'resolution': {'width': 16, 'height': 16},
    'display': display,
    'textures': [
        {'name': 'palette.png', 'id': '0', 'particle': True, 'source': 'data:image/png;base64,' + base64.b64encode((TEXTURES / 'palette.png').read_bytes()).decode('ascii')},
        {'name': PATH.name, 'id': '1', 'source': 'data:image/png;base64,' + base64.b64encode(PATH.read_bytes()).decode('ascii')},
    ],
    'elements': []
}
for e in parts:
    item = {k: v for k, v in e.items() if k in ('name', 'from', 'to')}
    item['faces'] = {f: {'uv': v['uv'], 'texture': 1 if v['texture'] == '#ink_blade' else 0} for f, v in e['faces'].items()}
    bb['elements'].append(item)
(BB / 'form_3.bbmodel').write_text(json.dumps(bb, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

# ---------- Preview render ----------
obj = json.loads((MODELS / 'form_3.json').read_text(encoding='utf8'))
blade = Image.open(PATH).convert('RGBA')
W, H = 1180, 880
canvas = Image.new('RGBA', (W, H), (242, 239, 235, 255))
dr = ImageDraw.Draw(canvas)
for y in range(H):
    t = y / H
    dr.line((0, y, W, y), fill=(int(236 - 18 * t), int(233 - 14 * t), int(229 - 10 * t), 255))
dr.rounded_rectangle((20, 20, W - 20, H - 20), radius=24, outline=(70, 74, 78, 255), width=3)
try:
    f1 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 30)
    f2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
except OSError:
    f1 = f2 = ImageFont.load_default()
dr.text((42, 36), 'Rien  |  Form III Greatsword', fill=(20, 24, 30, 255), font=f1)
dr.text((42, 82), 'ALPHA-PLANE GREATSWORD / broader & heavier / actual model preview', fill=(74, 78, 84, 255), font=f2)
dr.line((42, 120, W - 42, 120), fill=(154, 153, 148), width=2)
unit = 34.0
ox = 420
oy = 790
solids = [e for e in obj['elements'] if e['faces'].get('north', {}).get('texture') == '#palette']
colors = {13: (17, 20, 26, 255), 1: (24, 28, 34, 255), 15: (79, 83, 89, 255), 5: (84, 90, 98, 255), 8: (36, 40, 47, 255), 9: (118, 94, 60, 255), 10: (163, 133, 84, 255), 14: (228, 232, 236, 255)}
for e in solids:
    x0, y0, _ = e['from']
    x1, y1, _ = e['to']
    uv = e['faces']['north']['uv']
    idx = int(uv[0] // 4) + 4 * int(uv[1] // 4)
    col = colors.get(idx, (46, 49, 54, 255))
    dr.rectangle((ox + (x0 - 8) * unit, oy - y1 * unit, ox + (x1 - 8) * unit, oy - y0 * unit), fill=col)
side = round(16 * unit)
canvas.alpha_composite(blade.resize((side, side), Image.Resampling.LANCZOS), (round(ox - 8 * unit), round(oy - 16 * unit)))
proxy_x = 940
bottom = oy
s_h = 16 * unit * 1.72 / 1.66
sx = s_h / 29
for rect, fill in [
    ((proxy_x - 5.2 * sx, bottom - 22 * sx, proxy_x + 5.2 * sx, bottom - 10 * sx), (97, 104, 114, 255)),
    ((proxy_x - 4 * sx, bottom - 29 * sx, proxy_x + 4 * sx, bottom - 22 * sx), (179, 179, 172, 255)),
    ((proxy_x - 5.2 * sx, bottom - 10 * sx, proxy_x - 0.4 * sx, bottom), (66, 71, 82, 255)),
    ((proxy_x + 0.4 * sx, bottom - 10 * sx, proxy_x + 5.2 * sx, bottom), (66, 71, 82, 255)),
    ((proxy_x - 8.2 * sx, bottom - 22 * sx, proxy_x - 5.4 * sx, bottom - 9 * sx), (130, 131, 124, 255)),
    ((proxy_x + 5.4 * sx, bottom - 22 * sx, proxy_x + 8.2 * sx, bottom - 9 * sx), (130, 131, 124, 255)),
]:
    dr.rectangle(rect, fill=fill)
dr.text((proxy_x - 84, bottom + 10), 'PLAYER / 1.8m', font=f2, fill=(57, 62, 67, 255))
dr.text((42, H - 48), 'CUTOUT PNG  |  768 x 768 RGBA  |  Form III Greatsword', font=f2, fill=(48, 52, 58, 255))
canvas.convert('RGB').save(ROOT / 'FORM_3_GREATSWORD_ALPHA_PREVIEW.png', quality=95)
print('Built form_3 alpha greatsword ->', PATH)
