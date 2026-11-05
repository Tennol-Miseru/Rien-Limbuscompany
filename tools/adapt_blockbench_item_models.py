#!/usr/bin/env python3
"""Adapt supplied Blockbench item-model exports to vanilla Java block-model rotations.

Keeps original vendor assets under art_sources for faithful editing. The runtime JSON
uses mathematically exact quarter turns baked into cuboid bounds, and quantizes
only the small remaining single-axis rotation to Minecraft-supported angles.
"""
import json,math,collections
from pathlib import Path
ALLOWED=(-45.,-22.5,0.,22.5,45.)
NORMALS={"east":(1,0,0),"west":(-1,0,0),"up":(0,1,0),"down":(0,-1,0),"north":(0,0,-1),"south":(0,0,1)}
INVERSE={v:k for k,v in NORMALS.items()}

def rotated(v, axis, k):
 x,y,z=v
 for _ in range(k%4):
  if axis == 'z': x,y=-y,x
  elif axis == 'y': x,z=z,-x
  elif axis == 'x': y,z=-z,y
  else:raise ValueError(axis)
 return x,y,z

def adapt_element(e, stats):
 r=e.get('rotation')
 if not isinstance(r,dict):return
 if 'axis' in r:
  axis=r['axis']; theta=float(r['angle']); origin=r['origin']
 else:
  origin=r.get('origin')
  if not isinstance(origin,list) or len(origin)!=3:raise ValueError('Invalid origin')
  a={k:float(r.get(k,0)) for k in 'xyz'}
  active=[k for k,v in a.items() if abs(v)>1e-6]
  if len(active)>1:raise ValueError('Multi-axis rotation not supported')
  axis=active[0] if active else 'z'; theta=a[axis] if active else 0.
  stats['converted_euler']+=1
 if len(origin)==2 and axis=='z':
  # Some cross-rapier elements store an XY pivot only; infer Z from cuboid center.
  origin=list(origin)+[round((e['from'][2]+e['to'][2])*0.5,6)]
  stats['expanded_2d_origins']+=1
 if len(origin)!=3 or not all(isinstance(x,(float,int)) for x in origin):raise ValueError('bad origin')
 if axis not in 'xyz':raise ValueError('wrong axis')
 if any(abs(theta-a)<0.00001 for a in ALLOWED):
  e['rotation']={'angle':int(theta) if theta.is_integer() else theta,'axis':axis,'origin':origin}
  return
 # Full quarter-turn rotation baked exactly into cuboid, so remainder only <=45.
 quarters=int(math.floor((theta+45.)/90.))
 residual=theta-90*quarters
 while residual>45: quarters+=1;residual-=90
 while residual< -45: quarters-=1;residual+=90
 legal=min(ALLOWED,key=lambda x:abs(x-residual))
 if quarters%4:
  pts=[]
  for x in (e['from'][0], e['to'][0]):
   for y in (e['from'][1], e['to'][1]):
    for z in (e['from'][2], e['to'][2]):
     local=tuple(a-b for a,b in zip((x,y,z),origin))
     rotated_pt=rotated(local,axis,quarters)
     pts.append([a+b for a,b in zip(rotated_pt,origin)])
  e['from']=[round(min(p[i] for p in pts),6) for i in range(3)]
  e['to']=[round(max(p[i] for p in pts),6) for i in range(3)]
  # Remap surface normals so colored face materials do not migrate.
  new_faces={}
  for direction,face in e['faces'].items():
   k=INVERSE[rotated(NORMALS[direction],axis,quarters)]
   new_faces[k]=face
  e['faces']=new_faces
  stats['quarter_turns']+=1
 if abs(legal-residual)>0.00001:stats['quantized']+=1
 e['rotation']={'angle':int(legal) if float(legal).is_integer() else legal,'axis':axis,'origin':origin}
 stats['adapted']+=1
 stats['largest_residual_error']=max(stats['largest_residual_error'],abs(legal-residual))

if __name__=='__main__':
 import sys
 root=Path(sys.argv[1]); output=Path(sys.argv[2]);output.mkdir(parents=True,exist_ok=True)
 allstats={}
 for p in sorted(root.glob('*.json')):
  data=json.loads(p.read_text())
  stats=collections.defaultdict(int)
  for el in data.get('elements',[]):adapt_element(el,stats)
  (output/p.name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  allstats[p.stem]=dict(stats)
 print(json.dumps(allstats,indent=2))
