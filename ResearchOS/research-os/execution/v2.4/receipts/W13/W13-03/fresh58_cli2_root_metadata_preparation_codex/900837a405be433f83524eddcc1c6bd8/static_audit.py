"""Root source-only byte inverse and AST audit. No candidate import or process API."""
import ast
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent

def raw_ref(ref):
    raw = Path(ref['path']).read_bytes()
    if len(raw) != ref['bytes'] or hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise RuntimeError('Frozen original mismatch: ' + ref['path'])
    return raw

def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def parse(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out: raise RuntimeError('Duplicate key')
            out[k] = v
        return out
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs)

if not (sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode):
    raise RuntimeError('Pinned Python -I -S -X utf8 required')
rows = []
for proof_name in ['source-delta.json', 'wrapper-source-delta.json']:
    proof = parse((BASE / proof_name).read_bytes())
    for item in proof['changes']:
        old = raw_ref(item['original_ref'])
        candidate = BASE / item['name']
        new = candidate.read_bytes()
        restored = new.decode('utf-8')
        for change in reversed(item['exact_replacements']):
            if restored.count(change['after']) != 1:
                raise RuntimeError('Nonunique inverse literal')
            restored = restored.replace(change['after'], change['before'], 1)
        if restored.encode('utf-8') != old:
            raise RuntimeError('Whole byte inverse failed: ' + item['name'])
        a = ast.parse(old.decode('utf-8'))
        b = ast.parse(new.decode('utf-8'))
        definition_count = 0
        if item['name'] in ['build_binding.current58.proposed.py', 'metadata_pipeline.current58.proposed.py']:
            aa = [ast.dump(x, include_attributes=False) for x in a.body if isinstance(x, (ast.FunctionDef, ast.ClassDef))]
            bb = [ast.dump(x, include_attributes=False) for x in b.body if isinstance(x, (ast.FunctionDef, ast.ClassDef))]
            if aa != bb: raise RuntimeError('Existing definitions changed')
            definition_count = len(aa)
        rows.append({'original_ref': item['original_ref'], 'candidate_ref': pin(candidate),
                     'whole_byte_inverse': True, 'AST_parsed_only': True,
                     'unchanged_definition_count': definition_count})
result = {'schema': 'researchos.current58-root-metadata-source-static-audit.v1',
          'actor': 'codex:/root', 'files': rows, 'inverse_count': len(rows),
          'actual_candidate_imports': 0, 'actual_candidate_runs': 0,
          'actual_canonical_writes': 0, 'formal_increment': 0,
          'source_acceptance': False, 'execution_authorized': False}
with (BASE / 'static-audit.json').open('xb') as stream:
    stream.write((json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'status': 'SOURCE_PREPARATION_STATIC_AUDIT_REPORTED',
                  'whole_byte_inverse_count': len(rows), 'candidate_runs': 0,
                  'canonical_writes': 0, 'formal_increment': 0}))
