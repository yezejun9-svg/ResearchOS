import ast
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
assert sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize


def ref(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


original = (OUT / 'seal.py').read_bytes()
assert hashlib.sha256(original).hexdigest() == '3575bb614b43990e6f5b924b94ad0694b2f3e6e92e660c4db2d245fe3eb73917'
old = "'runner_review_ref': prepared['pins']['runner_review'],"
new = "'go3_runner_review_ref': prepared['pins']['go3_review'],\n    'w09_source_review_ref': prepared['pins']['w09_review'],"
source = original.decode('utf-8')
assert source.count(old) == 1
revised = source.replace(old, new, 1)
ast.parse(revised)
prepared = json.loads((OUT / 'prepared_refs.json').read_bytes())
for key in ['go3_review', 'w09_review']:
    assert ref(ROOT / prepared['pins'][key]['path']) == prepared['pins'][key]
with (OUT / 'seal.v2.py').open('xb') as stream:
    stream.write(revised.encode('utf-8'))
binding = {'schema': 'researchos.root320-sealer-static-correction.v1',
    'old_unexecuted_sealer_ref': ref(OUT / 'seal.py'), 'executable_sealer_ref': ref(OUT / 'seal.v2.py'),
    'prepared_ref': ref(OUT / 'prepared_refs.json'), 'go3_review_ref': prepared['pins']['go3_review'],
    'w09_review_ref': prepared['pins']['w09_review'], 'exact_change': {'old': old, 'new': new},
    'reason': 'Independent static review found legacy runner_review key absent. Bind actual Go3 and W09 review keys; old draft never executed.',
    'actual_registration_executed': False, 'new_actual_failure_origins': 0, 'counter_reset': False,
    'source_acceptance': False, 'formal_increment': 0}
with (OUT / 'sealer-fix.binding.json').open('xb') as stream:
    stream.write((json.dumps(binding, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
assert (OUT / 'seal.py').read_bytes() == original
print(json.dumps({'new_sealer': ref(OUT / 'seal.v2.py'), 'binding': ref(OUT / 'sealer-fix.binding.json')}, ensure_ascii=True))
