"""Generate original half-mask assets for Minecraft 1.21.1's classic armor layer.
Pillow is a build-time only asset generator; no runtime dependencies.
The mask is a transparent helmet overlay (not a full face-covering skin).
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'src/main/resources/assets/oraclearsenal'
ARMOR = BASE / 'textures/models/armor'
ITEM_TEX = BASE / 'textures/item'
MODELS = BASE / 'models/item'
for d in (ARMOR, ITEM_TEX, MODELS): d.mkdir(parents=True, exist_ok=True)

# Use the 1.21.1 64x32 armor texture UV layout at 8x native resolution.
# HumanoidModel head front = (8,8)..(16,16).  X increases viewer-right.
# Face left (wearer's left) is viewer-right; only draw into that half.
K = 8
atlas = Image.new('RGBA',(64*K,32*K))

WHITE = '#e5e7dc'
LIGHT = '#fff9e9'
SHADE = '#b9c3c4'
GOLD = '#c89a48'
GOLD_LIGHT = '#ffe3a0'
GOLD_DARK = '#705431'
CRACK = '#667278'


def mask_front(x0: float, y0: float, scale: float):
    """Paint a mask on armor atlas using the front UV origin and UV-pixel units."""
    P=lambda xy: (round((x0+xy[0])*scale), round((y0+xy[1])*scale))
    dr=ImageDraw.Draw(atlas)
    shape=[(3.72,0.15),(7.85,0.15),(7.92,6.05),(7.48,6.53),
           (6.48,6.46),(5.88,6.02),(4.80,5.30),(3.92,4.50),
           (3.38,4.05),(3.58,2.75),(3.47,1.65)]
    dr.polygon([P(pt) for pt in shape],fill=WHITE)
    # softly tinted vertical porcelain facets
    dr.polygon([P(q) for q in [(4,0.27),(5.4,0.25),(5.08,4.86),(4.32,4.26),(3.72,3.8)]],fill=LIGHT)
    dr.polygon([P(q) for q in [(7.24,.33),(7.82,.33),(7.82,5.88),(7.36,6.37),(6.7,6.25)]],fill=SHADE)
    # Gold rim makes the angular, open-bottom half-mask distinct.
    rim=[(3.69,.20),(3.50,1.68),(3.61,2.78),(3.42,4.02),
         (4.08,4.64),(4.91,5.37),(5.98,6.10),(6.48,6.46),(7.46,6.50)]
    dr.line([P(q) for q in rim], fill=GOLD_DARK,width=round(scale*.35),joint='curve')
    dr.line([P(q) for q in rim], fill=GOLD,width=max(1,round(scale*.22)),joint='curve')
    dr.line([P(q) for q in rim], fill=GOLD_LIGHT,width=max(1,round(scale*.08)),joint='curve')
    # Segmented black cracks in the ceramic, branching near temple.
    fracture=[(5.37,.18),(5.46,.83),(5.19,1.38),(5.48,1.98),(5.16,2.55),
              (5.42,3.06),(5.19,3.65),(5.72,4.14)]
    dr.line([P(q) for q in fracture], fill=CRACK,width=max(1,round(scale*.14)),joint='curve')
    dr.line([P(q) for q in [(5.48,1.98),(6.05,2.21),(6.18,2.84)]],fill=CRACK,width=max(1,round(scale*.10)))
    dr.line([P(q) for q in [(5.19,3.65),(4.97,4.07)]],fill=CRACK,width=max(1,round(scale*.09)))
    dr.line([P(q) for q in [(6.2,.22),(6.6,.35)]],fill=GOLD_LIGHT,width=max(1,round(scale*.1)))

mask_front(8,8,K)
# Texture-layout fallback for the spare 'hat' geometry, in case renderers use it.
# In vanilla 1.21.1 armor heads use texOffs(0,0), but these coordinates
# keep custom player-model replacements visually compatible.
mask_front(40,8,K)

d=ImageDraw.Draw(atlas)
# Wearer's left-side temple wrap: right side of standard head UV.
# This is opaque only near the face, not a full white helmet side.
for px in range(17,20):
    for py in range(9,15):
        x1,y1=(px*K,py*K)
        d.rectangle((x1,y1,x1+K-1,y1+K-1),fill=SHADE if px>18 else WHITE)
# Gold stroke at the rear edge of temple strip.
d.line([(19*K,9*K),(19*K,14*K)],fill=GOLD,width=2)

atlas.save(ARMOR / 'rien_mask_layer_1.png')
# Armor layer 2 isn't needed for a standalone helmet, but include an empty
# transparent texture for resource-pack compatibility.
Image.new('RGBA',atlas.size).save(ARMOR / 'rien_mask_layer_2.png')

# The same basic geometry in a more legible inventory pixel icon.
S=10
icon=Image.new('RGBA',(64,64))
pix=ImageDraw.Draw(icon)
poly=[(25,5),(49,5),(54,12),(54,36),(48,45),(42,48),(35,45),
      (30,40),(23,35),(19,30),(21,17)]
pix.polygon(poly,fill='#333840')
pix.polygon([(25,7),(49,7),(52,12),(52,34),(47,42),(41,45),(34,42),
             (28,37),(22,31),(23,17)],fill=WHITE)
pix.polygon([(28,8),(37,8),(34,32),(28,35),(24,29),(25,17)],fill=LIGHT)
pix.polygon([(46,8),(50,10),(50,33),(46,40),(44,39)],fill=SHADE)
pix.line([(26,7),(24,17),(23,29),(29,37),(36,42),(42,46),(48,44)],fill=GOLD_DARK,width=5,joint='curve')
pix.line([(26,7),(24,17),(23,29),(29,37),(36,42),(42,46),(48,44)],fill=GOLD,width=3,joint='curve')
pix.line([(31,9),(32,15),(29,19),(34,26),(32,31),(37,35)],fill=CRACK,width=2,joint='curve')
pix.line([(34,26),(40,29),(42,33)],fill=CRACK,width=1)
pix.line([(44,10),(46,14)],fill=GOLD_LIGHT,width=2)
icon.save(ITEM_TEX/'rien_mask.png')

# Item model: vanilla extruded sprite; helmet's actual third-person head mesh
# comes from Minecraft's HumanoidArmorLayer and the texture above.
(MODELS/'rien_mask.json').write_text(json.dumps({
    'parent':'minecraft:item/generated',
    'textures':{'layer0':'oraclearsenal:item/rien_mask'},
    'display': {
        'gui':{'rotation':[0,0,0], 'translation':[0,0,0], 'scale':[1,1,1]},
        'ground':{'scale':[.65,.65,.65]}
    }
},indent=2)+'\n',encoding='utf8')

# Illustrated mockup only, not a screenshot or Minecraft renderer output.
preview=Image.new('RGB',(1024,560),'#121822')
draw=ImageDraw.Draw(preview)
try:
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',25)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
except OSError:
    font=ImageFont.load_default(); small=font
# Stylised avatar front to demonstrate what the transparent armor layer does.
draw.rounded_rectangle((45,40,500,516),radius=20,fill='#1f2b3b',outline='#526174',width=2)
draw.rounded_rectangle((520,40,979,516),radius=20,fill='#1f2b3b',outline='#526174',width=2)

# Pixelated avatar: black hair, pale skin, exposed gold eye.
head=Image.new('RGBA',(16,16))
hd=ImageDraw.Draw(head)
hd.rectangle((2,2,13,14),fill='#d1b9a7')
hd.rectangle((1,0,14,4),fill='#171b20')
hd.rectangle((2,3,4,8),fill='#191b20')
hd.rectangle((5,4,8,5),fill='#272b31')
hd.rectangle((5,8,7,9),fill='#c49b34')
hd.point((6,8),fill='#181b20')
hd.rectangle((7,13,9,13),fill='#926f65')
# render the frontal UV (scale 8x to 16px face) over the corresponding avatar pixels
front=atlas.crop((8*K,8*K,16*K,16*K))
# use 8px texture region -> interpolate nearest into 16px pixel head position x=2..14, y=2..14
front=front.resize((12,12),Image.Resampling.NEAREST)
head.alpha_composite(front,(2,2))
head=head.resize((272,272),Image.Resampling.NEAREST)
preview.paste(head,(130,142),head)

draw.text((70,67),'MASK / EQUIPPED VIEW',fill='#f2eee4',font=font)
draw.text((70,460),'Transparent outside the left facial half',fill='#bfcbd6',font=small)

draw.text((555,67),'ITEM / INVENTORY ICON',fill='#f2eee4',font=font)
large=icon.resize((250,250),Image.Resampling.NEAREST)
preview.paste(large,(615,140),large)
draw.text((545,455),'Porcelain / gold trim / hairline fracture',fill='#bfcbd6',font=small)
draw.text((45,532),'Schematic art preview - not an in-game screenshot',fill='#8fa0b5',font=small)
preview.save(ROOT/'RIEN_MASK_PREVIEW.png')
print('Generated 1 mask item icon/model + 2 armor layers + conceptual preview')
