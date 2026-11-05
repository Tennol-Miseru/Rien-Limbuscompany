"""Validate Minecraft 1.21.1 JSON item models before packaging.

The v0.8.5 generator accidentally serialized strings like 'blade_mass' as
rotations. JSON syntax checks alone did not detect this, and the game rendered
the missing-model magenta/black cube. This check validates actual model fields.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/oraclearsenal'
MODEL_DIR = ASSETS / 'models/item'
TEXTURE_ROOT = ASSETS / 'textures'
MAIN = 'twin_serpent_staff'
FORMS = [f'form_{i}' for i in range(1, 11)]


def check_num(v, label):
    assert isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v), label


def validate():
    for name in [MAIN, *FORMS, 'prescript_pager']:
        file = MODEL_DIR / f'{name}.json'
        assert file.exists(), f'model missing: {file}'
        d = json.loads(file.read_text(encoding='utf8'))
        assert d.get('parent') == 'minecraft:block/block', f'{name}: unexpected model parent'
        textures = d.get('textures', {})
        if name == MAIN:
            assert textures.get('staff') == 'oraclearsenal:item/twin_serpent_staff', (name, textures)
            assert (TEXTURE_ROOT / 'item/twin_serpent_staff.png').is_file()
        else:
            assert isinstance(textures.get('particle'), str) and textures['particle'].startswith('oraclearsenal:item/'), (name, textures)
            if name not in ('form_6', 'form_7'):
                assert textures.get('palette') == 'oraclearsenal:item/palette', (name, textures)
        assert (TEXTURE_ROOT / 'item/palette.png').is_file()
        assert len(d['elements']) > 0, name
        for i, el in enumerate(d['elements']):
            prefix = f'{name}: element {i}'
            for key in ('from', 'to'):
                v = el.get(key)
                assert isinstance(v, list) and len(v) == 3, (prefix, key)
                for a in v:
                    check_num(a, (prefix,key,a))
            for lo, hi in zip(el['from'], el['to']):
                assert -16 <= lo < hi <= 32, (prefix, 'invalid cuboid bounds for Minecraft 1.21.1', lo, hi)
            rotation = el.get('rotation')
            if rotation is not None:
                assert isinstance(rotation, dict), (prefix, rotation)
                assert rotation.get('axis') in ('x', 'y', 'z'), (prefix, rotation)
                check_num(rotation.get('angle'), (prefix, rotation))
                assert rotation.get('angle') in (-45, -22.5, 0, 22.5, 45), (prefix, rotation)
                origin = rotation.get('origin')
                assert isinstance(origin, list) and len(origin) == 3, (prefix, rotation)
                for a in origin: check_num(a, (prefix, rotation))
            faces = el.get('faces')
            assert isinstance(faces, dict) and faces, (prefix, 'no faces')
            for side, fc in faces.items():
                assert side in ('north','south','east','west','up','down'), (prefix, side)
                ref = fc.get('texture')
                assert isinstance(ref, str) and ref.startswith('#') and ref[1:] in textures, (prefix, ref)
                uv = fc.get('uv')
                if uv is not None:
                    assert isinstance(uv,list) and len(uv) == 4, (prefix, 'uv')
                    for v in uv:
                        check_num(v, (prefix,'uv',v))
                        assert 0 <= v <= 16, (prefix,'uv',v)
        for hand in ('firstperson_righthand','thirdperson_righthand','gui'):
            assert hand in d.get('display',{}), (name,hand)
        if name == MAIN:
            overrides = d.get('overrides')
            assert isinstance(overrides, list) and len(overrides) == 10
            for i, ov in enumerate(overrides, 1):
                assert ov.get('predicate',{}).get('custom_model_data') == i, (name, i, ov)
                assert ov.get('model') == f'oraclearsenal:item/form_{i}', (name, i, ov)
    assert Image.open(TEXTURE_ROOT/'item/palette.png').size == (64,64)
    for name in [MAIN, *FORMS]:
        bb=ROOT / 'blockbench' / f'{name}.bbmodel'
        assert bb.is_file(), bb
        data=json.loads(bb.read_text(encoding='utf8'))
        assert len(data.get('elements', [])) == len(json.loads((MODEL_DIR/f'{name}.json').read_text())['elements']), name
        for element in data['elements']:
            assert isinstance(element.get('name'), str), (name, element)
            rotation=element.get('rotation')
            if rotation is not None:
                # BBModel remains the artist's *original* high-fidelity source;
                # unsupported rotations are baked/quantized in the game JSON.
                assert ((isinstance(rotation, dict) and
                    (('axis' in rotation and isinstance(rotation.get('angle'), (float, int))) or
                     any(isinstance(rotation.get(axis), (float, int)) for axis in ('x','y','z')))) or
                     (isinstance(rotation, list) and len(rotation)==3 and
                      all(isinstance(x, (int,float)) for x in rotation))), (name,rotation)
    print('PASS: 11 Minecraft 1.21.1-compatible weapon models, 11 editable bbmodels,')
    print('      10 variant references, pager, palette texture and display transforms.')


if __name__ == '__main__':
    validate()
