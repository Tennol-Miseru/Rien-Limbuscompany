from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
client=(root/'src/client/java/io/github/oraclearsenal/client/HermesProgressHud.java').read_text(encoding='utf-8')
assert 'String count = Integer.toString(progress);' in client
assert 'String count = progress + "/9";' not in client
assert 'progress <= 0' in client
assert 'progress > lastVisibleProgress' in client
assert 'PULSE_DURATION_MS = 420L' in client
assert 'progress == 9 ?' in client
assets=root/'src/main/resources/assets/oraclearsenal'
assert len(json.loads((assets/'sounds.json').read_text(encoding='utf-8'))) == 13
assert len(list((assets/'sounds').rglob('*.ogg'))) == 25
print('PASS: Hermes counter 1-9 only, zero hidden, pulse and 9th highlight preserved')
