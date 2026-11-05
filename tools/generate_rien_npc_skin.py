"""Generate an ORIGINAL 64x64 player-model skin and simplified 2D preview, no ripped artwork."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'src/main/resources/assets/oraclearsenal/textures/entity'
P.mkdir(parents=True,exist_ok=True)
img=Image.new('RGBA',(64,64),(0,0,0,0))
d=ImageDraw.Draw(img)
INK='#18191b';DARK='#24262b';FAB='#34363c';SHADE='#101116';GOLD='#d2af68';GOLD2='#8e753f';WHITE='#eee9dd';SKIN='#dcc7b3';SKINDARK='#b99c89';HAIR='#1b2024';HIGHLIGHT='#636773'

def rect(box,c): d.rectangle(box,fill=c)
def surfaces(parts,c):
 for region in parts: rect(region,c)

# Fill the standard Steve-style UV islands, each face individually.
# head: right/left/front/back/top/bottom
surfaces([(0,8,7,15),(8,8,15,15),(16,8,23,15),(24,8,31,15),(8,0,15,7),(16,0,23,7)],SKIN)
# Hair wraps side and back; front hairline and separate bangs on hat overlay.
rect((0,8,7,11),HAIR);rect((16,8,23,11),HAIR);rect((24,8,31,14),HAIR)
rect((8,0,15,7),HAIR);rect((8,8,15,9),HAIR)
rect((8,10,8,13),SKINDARK)
# Face front left half skin, golden eye, right half mask under hair.
rect((9,12,10,12),'#b8a15c');rect((9,13,10,13),'#4b3622')
rect((12,10,15,15),WHITE)
rect((12,10,12,15),GOLD); rect((12,10,15,10),GOLD2)
rect((14,11,14,12),'#b2ada4');rect((13,12,13,13),'#9b9690');rect((15,14,15,15),GOLD)
rect((10,15,11,15),SKINDARK)
# Second layer hat: floating black bangs and side wisps.
rect((40,8,47,8),HAIR);rect((42,9,44,10),HAIR);rect((41,11,42,12),HAIR)
rect((32,8,33,13),HAIR);rect((55,8,55,11),HAIR)
# body (torso) UV: top 20..27,16..19; front 20..27,20..31
surfaces([(20,16,27,19),(28,16,35,19),(16,20,19,31),(20,20,27,31),(28,20,31,31),(32,20,39,31)],INK)
rect((21,20,26,25),WHITE) # collar
rect((22,20,25,22),'#ffffff');rect((23,22,24,30),INK)
rect((20,20,21,31),DARK);rect((26,20,27,31),DARK)
rect((20,24,22,26),SHADE);rect((25,24,27,26),SHADE)
rect((21,28,21,28),GOLD);rect((21,30,21,30),GOLD)
# back pockets / side creases
rect((32,25,39,25),FAB);rect((16,28,19,29),FAB)
# jacket overlay (mostly transparent except fine trims)
rect((20,36,21,47),'#31343b');rect((26,36,27,47),'#303238')
rect((20,36,22,38),GOLD2);rect((25,36,27,38),GOLD2)
rect((23,37,24,45),SHADE)
rect((21,41,21,41),GOLD);rect((21,44,21,44),GOLD)
# right arm base: top 44..47/40..43, front 44..47/20..31
surfaces([(44,16,47,19),(48,16,51,19),(40,20,43,31),(44,20,47,31),(48,20,51,31),(52,20,55,31)],INK)
rect((44,20,47,25),DARK);rect((44,28,47,31),WHITE) # glove
rect((45,24,45,25),GOLD2);rect((47,25,47,25),GOLD)
# left arm: second lower set front 36..39,52..63 etc
surfaces([(36,48,39,51),(40,48,43,51),(32,52,35,63),(36,52,39,63),(40,52,43,63),(44,52,47,63)],INK)
rect((36,52,39,57),DARK);rect((36,60,39,63),WHITE)
# pants right leg UV top4..7 and front4..7,20..31
surfaces([(4,16,7,19),(8,16,11,19),(0,20,3,31),(4,20,7,31),(8,20,11,31),(12,20,15,31)],INK)
rect((4,27,7,31),SHADE);rect((6,30,7,31),'#31271b');rect((4,24,4,26),FAB)
# left leg UV second lower part top20..23,front20..23,y52..63
surfaces([(20,48,23,51),(24,48,27,51),(16,52,19,63),(20,52,23,63),(24,52,27,63),(28,52,31,63)],INK)
rect((20,59,23,63),SHADE);rect((20,63,22,63),'#635336')
# arm overlay fine gold cuff and shoulder insignia
rect((44,36,47,37),GOLD2);rect((45,38,46,39),GOLD)
rect((48,52,51,53),GOLD2);rect((49,54,50,55),GOLD)
# leg overlay streaks
rect((4,36,4,44),FAB);rect((20,36,20,43),FAB)
# Hair overlay forehead kept partially asymmetric
# Fix no painted face to body disconnect; all islands use vanilla UV.
img.save(P/'rien.png')

# Second-phase skin: after the half-health removal animation, the previously
# masked side is bare skin with an eye and a faint red scar.
unmasked = img.copy()
ud = ImageDraw.Draw(unmasked)
ud.rectangle((12, 10, 15, 15), fill=SKIN)
ud.rectangle((12, 10, 15, 10), fill=HAIR)
ud.point((13, 12), fill='#51413b')
ud.point((14, 12), fill='#8d1d1c')
ud.line([(15,11), (14,12), (15,14)], fill='#b17067', width=1)
ud.point((12, 15), fill=SKINDARK)
unmasked.save(P/'rien_unmasked.png')

# Orthographic sprite preview assembled from actual UV fronts for reference, not in-game screenshot.
face=img.crop((8,8,16,16)).resize((128,128),Image.Resampling.NEAREST)
torso=img.crop((20,20,28,32)).resize((128,192),Image.Resampling.NEAREST)
leg_r=img.crop((4,20,8,32)).resize((64,192),Image.Resampling.NEAREST)
leg_l=img.crop((20,52,24,64)).resize((64,192),Image.Resampling.NEAREST)
arm_r=img.crop((44,20,48,32)).resize((64,192),Image.Resampling.NEAREST)
arm_l=img.crop((36,52,40,64)).resize((64,192),Image.Resampling.NEAREST)
can=Image.new('RGB',(740,735),'#151922');o=ImageDraw.Draw(can)
o.rounded_rectangle((40,35,700,690),25,fill='#222733',outline='#a88a54',width=3)
# Steve anatomical front arms + suit overlay cutouts
can.paste(face,(305,112),face)
can.paste(torso,(305,240),torso)
can.paste(leg_r,(305,432),leg_r);can.paste(leg_l,(369,432),leg_l)
can.paste(arm_r,(241,240),arm_r);can.paste(arm_l,(433,240),arm_l)
# Add neon-ish poster labels (regular font fallback)
try:
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
except OSError:
 font=ImageFont.load_default()
o.text((62,52),'RIEN NPC  /  PlayerModel 64 x 64',font=font,fill='#dfc68e')
o.text((62,650),'Original skin  |  Model preview (not a game screenshot)',font=font,fill='#a9abb1')
can.save(ROOT/'RIEN_NPC_PREVIEW.png')
print('Generated 64x64 skin and preview')
