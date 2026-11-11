import argparse
import hashlib
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description='Validate the Russian game/Together locale.')
parser.add_argument('--game-en', type=Path)
args = parser.parse_args()

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: '+key)
        result[key] = value
    return result

def leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, path+(key,))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from leaves(child, path+(i,))
    else:
        yield path, value

def tokens(text):
    return sorted(re.findall(r'\{\d+(?:[^{}]*)?\}|<>|</?(?:color|b|i|size|sprite|br|u)(?:=[^>]+|\s[^>]*)?>', text))

locale_file = root/'ru-RU.json'
data = json.loads(locale_file.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)
assert data['version'] == '1.0.1'
assert data['name'] == 'Русский'
expected = json.loads((root/'checks.json').read_text(encoding='utf-8'))
actual = hashlib.sha256(locale_file.read_bytes()).hexdigest()
assert actual == expected['sha256'], 'File differs from the checked release.'
mod = {k:v for k,v in data['other'].items() if k.startswith('casualtiestogether_')}
assert len(mod) == 525
assert len([k for k in mod if k.startswith('casualtiestogether_rule_name_')]) == 68
assert all(isinstance(v,str) and v and '\ufffd' not in v for v in mod.values())
for i in range(3):
    assert data['character'][i]['wwmrwrongway']
if args.game_en:
    source = json.loads(args.game_en.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)
    assert source['version'] == '1.0.1', 'Expected game EN.json version 1.0.1.'
    translated = dict(leaves(data))
    for path, value in leaves(source):
        assert path in translated, ('Missing',path)
        target = translated[path]
        assert type(target) is type(value), ('Type mismatch',path)
        if isinstance(value,str) and path not in [('description',),('pdaNotes',6,'Item1')]:
            assert tokens(value) == tokens(target), ('Placeholder mismatch',path)
print('OK: JSON, SHA256, game version, 457 Together strings, 68 rule names.')
