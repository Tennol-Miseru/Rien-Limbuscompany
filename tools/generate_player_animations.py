"""Generate GeckoLib-style PlayerAnimator keyframe JSON clips.
Axes are degrees; all clips use vanilla player bones and are authored as separate clips.
"""
import json
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'src/main/resources/assets/oraclearsenal/player_animations'
OUT.mkdir(parents=True,exist_ok=True)

def clip(name,duration,pose):
    # pose mapping bone -> rotation triples at normalized [0, 0.2, 0.52, 0.78, 1] times
    times=[0,.2,.52,.78,1]
    bones={}
    for bone,arr in pose.items():
        assert len(arr)==5,(name,bone)
        bones[bone]={'rotation':{str(round(duration*t,3)):v for t,v in zip(times,arr)}}
    return {'loop':False,'animation_length':duration,'bones':bones}

z=[0,0,0]
base={
'slash_left':clip('slash_left',.4,{
    'right_arm':[[ -35,25,45],[-95,65,45],[-130,-40,-40],[-70,-25,-22],[-15,0,0]],
    'left_arm': [[-25,5,-15],[-50,-5,-25],[-40,10,5],[-20,0,0],z],
    'torso':[[0,25,0],[0,35,3],[0,-25,-5],[0,-8,0],z],
    'head':[[0,-12,0],[0,-12,0],[0,10,0],z,z],
}),
'slash_right':clip('slash_right',.4,{
    'right_arm':[[-38,-45,-32],[-95,-65,-50],[-132,38,44],[-70,30,18],[-15,0,0]],
    'left_arm':[[-25,-5,20],[-50,5,10],[-38,-5,-12],[-20,0,0],z],
    'torso':[[0,-25,0],[0,-35,-3],[0,28,6],[0,8,0],z]
}),
'rapid_thrust':clip('rapid_thrust',.35,{
    'right_arm':[[-85,5,8],[-155,2,0],[-62,0,4],[-155,0,0],[-65,0,5]],
    'left_arm':[[-60,0,-8],[-80,0,-12],[-65,0,-4],[-55,0,-8],z],
    'torso':[[12,-8,0],[24,-10,0],[5,10,0],[22,4,0],z],
    'head':[[-6,0,0],[-14,0,0],[0,0,0],[-12,0,0],z]
}),
'heavy_down':clip('heavy_down',.6,{
    'right_arm':[[-50,-18,35],[-175,-10,20],[-195,4,5],[-5,0,12],[-15,0,0]],
    'left_arm':[[-35,10,-35],[-150,20,-22],[-170,5,-8],[-20,0,5],z],
    'torso':[[0,8,0],[-20,0,0],[-35,0,0],[38,0,0],z],
    'head':[[0,0,0],[10,0,0],[10,0,0],[-12,0,0],z]
}),
'long_whip':clip('long_whip',.55,{
    'right_arm':[[-35,40,35],[-160,55,55],[-115,-70,-65],[-60,0,15],z],
    'left_arm':[[-25,-10,-5],[-20,-35,-15],[-52,0,20],[-20,0,0],z],
    'torso':[[0,6,0],[0,16,0],[0,-16,0],[0,-8,0],z]
}),
'scythe_reap':clip('scythe_reap',.6,{
    'right_arm':[[-55,45,25],[-125,70,55],[-140,-65,-45],[-75,-30,-12],z],
    'left_arm':[[-45,40,-35],[-130,60,-25],[-105,-35,20],[-50,0,0],z],
    'torso':[[0,50,-5],[0,65,-8],[0,-65,9],[0,-25,0],z],
    'head':[[0,-15,0],[0,-20,0],[0,15,0],[0,5,0],z]
}),
'blink_draw':clip('blink_draw',.55,{
    'right_arm':[[-30,-20,20],[-120,-30,35],[-165,5,-15],[-75,0,0],z],
    'left_arm':[[-15,0,-10],[-75,0,-30],[-85,0,10],[-25,0,0],z],
    'torso':[[18,0,0],[32,-15,0],[0,20,0],[0,0,0],z],
    'head':[[10,0,0],[15,-15,0],[-10,10,0],z,z]
})}
for name,dat in base.items():
    out={'format_version':'1.8.0','animations':{name:dat}}
    (OUT/f'{name}.animation.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print('Generated',len(base),'keyframe animation clips in',OUT)
