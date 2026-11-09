"""Construct literal Root current58 inputs using public immutable refs only.
No candidate import, native child, SQLite, network, or canonical writes.
"""
import copy
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
BASE = Path(__file__).resolve().parent
READS = {}

def need(ok, why):
    if not ok: raise RuntimeError(why)

def parse(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            need(k not in out, 'Duplicate key')
            out[k] = v
        return out
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))

def path(value):
    p = Path(value)
    p = p if p.is_absolute() else ROOT / p
    need(p.is_relative_to(ROOT) and p != ROOT and '..' not in p.parts, 'Repository ref boundary')
    need(p.resolve(strict=True) == p.absolute(), 'Alias')
    for cursor in [p, *p.parents]:
        if os.path.lexists(cursor):
            need(not cursor.is_symlink() and not (getattr(cursor.lstat(), 'st_file_attributes', 0) & 0x400), 'Reparse')
        if cursor == ROOT: break
    return p

def verify(ref):
    p = path(ref['path'])
    raw = p.read_bytes()
    need(len(raw) == ref['bytes'] and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'Frozen ref mismatch')
    key = str(p)
    if key in READS: need(READS[key] == raw, 'Immutable drift')
    READS[key] = raw
    return raw

def pin(p):
    raw = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    target = BASE / name
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with target.open('xb') as stream: stream.write(raw)
    return pin(target)

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Pinned -I -S -X utf8 required')
q = parse((BASE / 'root-construction.parameters.json').read_bytes())
need(q['actor'] == 'codex:/root' and q['source_acceptance'] is False and
     q['compile_or_case_execution_authorized'] is False and q['formal_increment'] == 0, 'Root metadata only')
need(q['after'] == [q['before'][0]+1, q['before'][1]+1,
                   q['before'][2]+len(q['pending_origin_refs'])], 'Explicit origin cut')
names = ['checkpoint', 'path_ownership', 'step_state', 'commands']
copies = [verify(x) for x in q['canonical_copies']]
need(all((ROOT / ('execution/v2.4/'+n+'.json')).read_bytes() == b for n, b in zip(names, copies)), 'Live four changed')
cp, ow = map(parse, copies[:2])
need([cp['revision'], ow['revision'], len(cp['failure_counters'])] == q['before'] and
     cp['head'] == q['source_commit'], 'Current Root tuple/head')
prefix = parse(verify(q['failure_prefix430_ref']))['failure_counters']
need(len(prefix) == 430 and cp['failure_counters'][:430] == prefix, '430 and full prior failure prefix')
origins, hashes = [], {x.get('evidence_ref', {}).get('sha256') for x in cp['failure_counters']}
for ref in q['pending_origin_refs']:
    payload = parse(verify(ref))
    need(ref['sha256'] not in hashes, 'Origin already registered or duplicated')
    hashes.add(ref['sha256'])
    origins.append({'origin_key': ref['sha256'], 'evidence_ref': ref,
                    'original_payload': payload, 'counter_reset': False,
                    'counted_once': True, 'automatic_retry': False})
cut_ref = save('failure-origins.cut.json', {'schema': 'researchos.root-failure-origin-cut.v1',
               'owner': 'codex:/root', 'before': q['before'], 'after': q['after'],
               'origins': origins, 'counter_reset': False})
catalog = parse(verify(q['catalog_ref']))
need(catalog['commit'] == q['source_commit'] and catalog['file_count'] == len(catalog['files']) == 639, 'Actual639 catalog')
source = []
for item in catalog['files']:
    ref = {'path': str(ROOT / item['path']), 'sha256': item['sha256'], 'bytes': item['bytes']}
    raw = verify(ref)
    need(hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() == item['git_blob'], 'Actual Git blob')
    source.append(ref)
source_ref = save('source-inputs.json', {'schema': 'researchos.current58-actual-public-source-inputs.v1',
                  'source_commit': q['source_commit'], 'catalog_ref': q['catalog_ref'],
                  'files': source, 'count': len(source), 'actual_compile_graph': None,
                  'source_acceptance': False, 'formal_increment': 0})
authority = parse(verify(q['authority_ref']))
need(authority['source_commit'] == q['source_commit'] and authority['unique_combined_source_paths'] == 58 and
     authority['fresh_compilation_or_cases_accepted'] is False, 'Current58 actual source authority only')
for ref in [q['publication_manifest_ref'], q['publication_tool_observation_ref'],
            q['publisher_preparation_review_ref'], q['compiler_resources_ref']]: verify(ref)
template = parse(verify(q['scope_template_ref']))
need(template['preparation_only'] is True and template['execution_authorized'] is False, 'Original preparation template')
template['catalog_ref'] = q['catalog_ref']
template['not_run_reason'] = 'Actual Root scope/grant and current58 fresh compilation/held2 execution remain pending.'
template_ref = save('scope.template.current58.actual-catalog.json', template)
runtime = copy.deepcopy(parse(verify(q['runtime_base_ref'])))
rows = {}
for ref in runtime['files']:
    normalized = os.path.normcase(str(Path(ref['path']).absolute()))
    need(normalized not in rows or rows[normalized] == ref, 'Conflicting runtime base')
    rows[normalized] = ref
for ref in q['metadata_code_refs']:
    verify(ref)
    actual = dict(ref, path=str(path(ref['path'])))
    normalized = os.path.normcase(actual['path'])
    need(normalized not in rows or rows[normalized] == actual, 'Conflicting actual metadata overlay')
    rows[normalized] = actual
runtime['files'] = sorted(rows.values(), key=lambda x: os.path.normcase(x['path']))
runtime['current58_metadata_overlay'] = {'base_ref': q['runtime_base_ref'],
       'exact_metadata_refs': [dict(x, path=str(path(x['path']))) for x in q['metadata_code_refs']],
       'immutable_catalog_is_not_execution_qualification': True,
       'full_runtime_and_compiler_bytes_membership_required_in_actual_scope_and_execution': True}
runtime_ref = save('runtime-with-current58-root-metadata.json', runtime)
b = {'owner': 'codex:/root', 'run_uuid': q['allocation']['run_uuid'],
     'before': q['before'], 'after': q['after'], 'main_git': q['main_git'],
     'public_environment': q['public_environment'],
     'registration_namespace': BASE.relative_to(ROOT).as_posix(),
     'controller_review_path': q['controller_review_path'], 'controller_review_ref': None,
     'scope_template_ref': template_ref, 'compiler_resources_ref': q['compiler_resources_ref'],
     'current43_authority_ref': q['authority_ref'],
     'canonical_before_ref': pin(BASE / 'canonical-before.json'), 'source_inputs_ref': source_ref,
     'metadata_code_refs_ref': pin(BASE / 'metadata-code-refs.json'),
     'failure_prefix430_ref': q['failure_prefix430_ref'], 'origin_cut_ref': cut_ref,
     'runtime_resources_ref': runtime_ref, 'formal_increment': 0,
     'scope_binding_or_candidate_executed': False, 'actual_case_acceptance': False}
for key in ['new_output_root', 'new_wrapper_root', 'new_export_root', 'new_authorization_root', 'new_grant_preflight_root']:
    b[key] = q['allocation'][key]
    need(not os.path.lexists(Path(b[key])), 'Execution leaf appeared')
need(all(path(p).read_bytes() == raw for p, raw in READS.items()), 'Final immutable input drift')
need(all((ROOT / ('execution/v2.4/'+n+'.json')).read_bytes() == raw for n, raw in zip(names, copies)), 'Final live four changed')
root_ref = save('root-inputs.current58.pre-review.json', b)
audit_ref = save('root-construction.audit.json', {'actor': 'codex:/root', 'root_inputs_ref': root_ref,
        'before': q['before'], 'after': q['after'], 'new_origins': len(origins),
        'source_files': len(source), 'runtime_files': len(runtime['files']),
        'actual_candidate_runs': 0, 'canonical_writes': 0, 'formal_increment': 0,
        'source_acceptance': False, 'full_runtime_or_compiler_membership_remeasured': False,
        'actual_compilation_or_cases': 0, 'created_execution_leaves': 0})
print(json.dumps({'status': 'ACTUAL_ROOT_INPUTS_CONSTRUCTED_NO_EXECUTION_AUTHORITY',
                  'root_inputs_ref': root_ref, 'audit_ref': audit_ref,
                  'before': q['before'], 'after': q['after'], 'source_files': len(source),
                  'runtime_files': len(runtime['files']), 'formal_increment': 0}))
