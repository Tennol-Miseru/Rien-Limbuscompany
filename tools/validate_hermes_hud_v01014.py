"""Standard-library-only static verification for Hermes HUD visuals.
Run: python tools/validate_hermes_hud_v01014.py
This is NOT a Gradle compilation or in-game rendering test.
"""
from pathlib import Path
import json
import struct

root = Path(__file__).resolve().parents[1]
assets = root / 'src/main/resources/assets/oraclearsenal'
client = root / 'src/client/java/io/github/oraclearsenal/client'
icon = assets / 'textures/gui/hermes_progress.png'
assert icon.is_file()
b = icon.read_bytes()
assert b[:8] == b'\x89PNG\r\n\x1a\n'
w, h = struct.unpack('>II', b[16:24])
assert (w, h) == (129, 125), (w, h)
assert b[25] == 6, 'Icon must be an RGBA PNG'

src = (client / 'HermesProgressHud.java').read_text(encoding='utf-8')
assert 'HudRenderCallback.EVENT.register' in src
assert 'progress <= 0' in src
assert 'progress > lastVisibleProgress' in src
assert 'PULSE_DURATION_MS = 420L' in src
assert 'getReplicaProgress' in src
assert 'textures/gui/hermes_progress_hud.png' in src
scaled=assets / 'textures/gui/hermes_progress_hud.png'
assert scaled.is_file()
assert struct.unpack('>II', scaled.read_bytes()[16:24]) == (28, 27)
assert 'HermesProgressHud.register();' in (client / 'OracleClient.java').read_text(encoding='utf-8')

combat = (root / 'src/main/java/io/github/oraclearsenal/OracleCombat.java').read_text(encoding='utf-8')
assert 'count + "/9 层"' not in combat
assert 'charge + "/9 层"' not in combat
assert 'addReplicaProgress(stack)' in combat
assert 'consumeReplica(stack)' in combat

sounds = json.loads((assets / 'sounds.json').read_text(encoding='utf-8'))
assert len(sounds) == 13
assert len(list((assets / 'sounds').rglob('*.ogg'))) == 25
assert 'mod_version=' in (root / 'gradle.properties').read_text(encoding='utf-8')
print('PASS: Hermes icon 129x125 original + 28x27 correct HUD sprite, zero-hide, increment pulse, 13/25 original audio intact')
