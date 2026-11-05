"""Produce PlayerAnimator 1.21.1 animations for the nine phantom strikes and finishing stance."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
out = root / 'src/main/resources/assets/oraclearsenal/player_animations'

# All clip lengths expressed in seconds, and strictly aligned with server tick schedule.
def save(name, seconds, poses):
    fractions=(0., .15, .34, .60, 1.)
    bones={}
    for bone, seq in poses.items():
        assert len(seq) == 5
        bones[bone]={ 'rotation': {str(round(t * seconds, 3)): value
                                     for t,value in zip(fractions, seq)}}
    value={'format_version':'1.8.0','animations':{
        name:{'loop':False, 'animation_length':seconds,'bones':bones}
    }}
    (out / f'{name}.animation.json').write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf8')

Z=[0,0,0]
# Intro: hunched, spectral tension, raises both arms, head sharply tilts.
save('crescendo_intro', .5, {
    'right_arm': [[-10,0,0],[-40,-40,20],[-105,30,45],[-150,12,35],[-100,0,15]],
    'left_arm': [[-10,0,0],[-45,40,-15],[-105,-30,-40],[-145,-12,-22],[-100,0,-10]],
    'torso': [[0,0,0],[12,-22,0],[28,-32,12],[42,6,-9],[35,0,0]],
    'head': [[0,0,0],[10,10,0],[26,-16,6],[-10,13,0],Z],
})

base = {
    'slash_left': 'slash_left',
    'rapid_thrust':'rapid_thrust',
    'slash_right':'slash_right',
    'heavy_down':'heavy_down',
    'long_whip':'long_whip',
    'scythe_reap':'scythe_reap'
}
form_names=['slash_left','rapid_thrust','slash_right','rapid_thrust','heavy_down',
            'heavy_down','rapid_thrust','long_whip','scythe_reap']
for i,name in enumerate(form_names,1):
    src=json.loads((out/f'{name}.animation.json').read_text())['animations'][name]
    bones={}
    for bone,record in src['bones'].items():
        values=list(record['rotation'].values())
        # Clip starts with aggressive offset on first frame, fast anticipation and recovery.
        transformed=[]
        for j, v in enumerate(values):
            arr=list(v)
            if bone=='torso':
                arr[1] += (17 if i % 2 else -18) * (1-j/4)
                arr[0] += 9 * (1-j/4)
            if bone=='right_arm':
                arr[0] -= 12 * (1-j/4)
                arr[2] += (14 if i % 2 else -14) * (1-j/4)
            if bone=='head':
                arr[1] += (-12 if i%2 else 12) * (1-j/4)
            transformed.append([round(float(x),2) for x in arr])
        bones[bone]=transformed
    # Finishing scythe uses pronounced upper-body involvement and two arm follow-through.
    if i==9:
        bones['torso']=[[5,48,-8],[0,73,-11],[-10,-82,15],[-22,-24,2],Z]
        bones['right_arm']=[[-55,45,35],[-140,70,64],[-175,-90,-50],[-80,-25,-18],Z]
        bones['left_arm']=[[-40,15,-30],[-125,30,-38],[-140,-60,30],[-50,0,0],Z]
    save('crescendo_'+name,.4,bones)

save('crescendo_finish', .6, {
    'right_arm': [[-165,-60,-30],[-155,-45,-23],[-110,-15,-17],[-65,0,-10],Z],
    'left_arm': [[-105,20,20],[-110,22,14],[-65,5,4],[-20,0,0],Z],
    'torso': [[-18,-65,12],[-30,-37,8],[-12,-17,3],[0,-5,0],Z],
    'head': [[8,30,-5],[12,13,0],[5,8,0],[0,0,0],Z],
})
print('Generated Crescendo intro, 6 unique attack types and finishing recovery clips.')
