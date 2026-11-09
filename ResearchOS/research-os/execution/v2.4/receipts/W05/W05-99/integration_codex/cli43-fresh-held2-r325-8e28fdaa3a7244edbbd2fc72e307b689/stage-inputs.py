"""Root reversible metadata staging. No CAS, helper, product, compiler or model."""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
UID = '8e28fdaa3a7244edbbd2fc72e307b689'
V5 = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_root_binding_preparation_revision_codex/c16c5b73941e4e8a89b189594e53b4c5'
FULL = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-public-resources-15ccd02e325b4d0e9384d66bb2a9d924'
SELECTED = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-public-resources-selected-r324'
CANON = ['execution/v2.4/' + n + '.json' for n in ['checkpoint', 'path_ownership', 'step_state', 'commands']]

def need(ok, why):
    if not ok:
        raise RuntimeError(why)

def pin(p):
    p = Path(p).absolute()
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def raw(ref):
    p = Path(ref['path']); p = p if p.is_absolute() else ROOT / p
    b = p.read_bytes()
    need(len(b) == ref['bytes'] and hashlib.sha256(b).hexdigest() == ref['sha256'], 'Immutable reference mismatch')
    return b

def load(ref):
    return json.loads(raw(ref).decode('utf-8'))

def doc(p, sha=None):
    r = pin(p)
    need(sha is None or r['sha256'] == sha, 'Known completed hash mismatch')
    return load(r)

def write(name, obj):
    with (OUT / name).open('xb') as f:
        f.write((json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(OUT / name)

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use -I -S -X utf8')
sys.dont_write_bytecode = True
audit = doc(FULL / 'audit.json', '02e5f29ca636b5ac468badc24aa0e5fce27f1a9c3b0b9bee2ca2a24dbabe3823')
need(all(pin(x['path']) == x for x in audit['before_refs'][:4]), 'Canonical bytes changed')
cp = doc(ROOT / CANON[0]); ow = doc(ROOT / CANON[1])
need([cp['revision'], ow['revision'], len(cp['failure_counters'])] == [324, 152, 430], 'Actual before tuple')
need(cp['head'] == 'a510dbef4a7e08fb5c428df44c39b133f3ffa856', 'Actual source identity')
root_origin = write('failure-origin.11225f.json', {
    'schema': 'researchos.original-root-tool-failure-origin.v1', 'actor': 'codex:/root',
    'tool_chunk_id': '11225f', 'actual_outer_exit': 1, 'actual_native_exit': None,
    'native_kind': None, 'target_execution': 0,
    'command': "Get-Content -LiteralPath 'execution/v2.4/receipts/W05/W05-99/cli43_root_binding_static_independent_review_codex/24e45e3f33844e759faa662405e3d665/failure-origin.1cd225.json' -ErrorAction SilentlyContinue",
    'reason': 'Root incorrectly located the original failure receipt under the final review namespace. The actual original is in bc206741b04744428ba32e4e126093a9; no target rerun.',
    'original_tool_result_known_fields': {'chunk_id': '11225f', 'wall_time_seconds': 0.5732323,
        'exit_code': 1, 'original_token_count': 0, 'output': ''},
    'original_native_stdout_stderr_files': None, 'raw_limitation': 'Known tool fields only; stderr was suppressed in the original locator, not reconstructed.',
    'counter_reset': False, 'automatic_same_input_retry': False})
pending = doc(FULL / 'postcut-pending5.json', 'e71481d8a0c5a7b848a950cb1a9fc495c4589731a003853e8382fd3ba7ad80f1')['pending_refs']
w05_origin = pin(ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_root_binding_static_independent_review_codex/bc206741b04744428ba32e4e126093a9/failure-origin.1cd225.json')
need(w05_origin['sha256'] == '00f7ebe34c21401fad9d40ce175cd702003e8187b6cd1be61de378db5af1e7ec', 'W05 original receipt SHA')
origins = []
for r in pending + [w05_origin, root_origin]:
    payload = load(r)
    origins.append({'evidence_ref': r, 'original_payload': payload, 'counter_reset': False,
                    'automatic_same_input_retry': False, 'classification': 'ACTUAL_TOOL_OR_METADATA_FAILURE_NOT_PRODUCT_CASE'})
cut = write('failure-origins.cut.json', {'before': [324, 152, 430], 'after': [325, 153, 437],
    'origins': origins, 'counter_reset': False, 'actual_registration_executed': False,
    'no_inferred_native_exits': True})
prefix = write('failure-prefix430.json', {'failure_counters': cp['failure_counters'],
    'actual_origin_count': 430, 'source_checkpoint_ref': audit['before_refs'][0]})
archive = OUT / 'canonical-before'
archive.mkdir(exist_ok=False)
copies = []
for name, r in zip(CANON, audit['before_refs'][:4]):
    p = archive / (Path(name).stem + '.raw')
    with p.open('xb') as f: f.write(raw(r))
    copies.append({'canonical_path': name, 'ref': pin(p), 'live_original_ref': r})
before = write('canonical-before.json', {'entries': copies, 'before': [324, 152, 430]})
scope_template = doc(V5 / 'scope.v5.proposed.json', '8b458fd73a41756272741b7580a2fecb6a93611dbce5e92f2a502126358409f4')
catalog = load(scope_template['catalog_ref'])
need(catalog['commit'] == cp['head'] and len(catalog['files']) == 597, 'Fresh current public source catalogue')
source_rows = []
for r in catalog['files']:
    current = pin(ROOT / r['path'])
    need(current['sha256'] == r['sha256'] and current['bytes'] == r['bytes'], 'Actual Main public source mismatch')
    source_rows.append(current)
source_ref = write('source-inputs.json', {'files': source_rows, 'source_commit': cp['head'],
    'catalog_ref': scope_template['catalog_ref'], 'resource_role': 'Current public source only; no historical graph or compiled output'})
handoff = doc(V5 / 'handoff.json', 'a0bbb49f7250d8d4d9abaea9d2073ce8bd4fe8f84388a5b701b53299cd388eb6')
code = []
for r in handoff['wrapper_refs']:
    p = OUT / Path(r['path']).name
    with p.open('xb') as f: f.write(raw(r))
    actual = pin(p)
    need(actual['sha256'] == r['sha256'] and actual['bytes'] == r['bytes'], 'Staged wrapper byte drift')
    code.append(actual)
code += [handoff['metadata_pipeline_ref'], handoff['binding_builder_ref']]
code_ref = write('metadata-code-refs.json', {'entries': code, 'source_preparation_handoff_ref': pin(V5 / 'handoff.json'),
    'templates_executed': 0, 'register_run_seal_grant_executed': 0})
review_path = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_current_bound_scope_independent_review_codex/1bcae38e2c3a483d8a1a37602b4e6dcb/review.json'
parents = {
    'output': ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_fresh_compiler_executor_codex',
    'wrapper': ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_fresh_compiler_launcher_codex',
    'authorization': ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_fresh_compiler_authorization_codex',
    'preflight': ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_fresh_compiler_grant_preflight_codex',
    'export': ROOT / '.local',
}
for p in parents.values():
    need(p.resolve(strict=False) == p.absolute() and p.is_relative_to(ROOT), 'Owned parent boundary')
    p.mkdir(parents=True, exist_ok=True)
leaves = {k: str(p / (('cli43-export-' if k == 'export' else '') + UID)) for k, p in parents.items()}
need(all(not Path(p).exists() for p in leaves.values()), 'Fresh finite leaf already exists')
request = write('root-inputs.json', {'owner': 'codex:/root', 'run_uuid': UID,
    'before': [324, 152, 430], 'after': [325, 153, 437], 'main_git': audit['main_git'],
    'public_environment': audit['public_environment'], 'registration_namespace': OUT.relative_to(ROOT).as_posix(),
    'controller_review_path': str(review_path), 'controller_review_ref': None,
    'scope_template_ref': pin(V5 / 'scope.v5.proposed.json'),
    'compiler_resources_ref': pin(SELECTED / 'compiler-resources.json'),
    'current43_authority_ref': pin(FULL / 'current43-authority.json'),
    'canonical_before_ref': before, 'source_inputs_ref': source_ref, 'metadata_code_refs_ref': code_ref,
    'failure_prefix430_ref': prefix, 'origin_cut_ref': cut,
    'runtime_resources_ref': None,
    'new_output_root': leaves['output'], 'new_wrapper_root': leaves['wrapper'], 'new_export_root': leaves['export'],
    'new_authorization_root': leaves['authorization'], 'new_grant_preflight_root': leaves['preflight'],
    'resource_final_binding': 'Root explicitly supplies sealed runtime-v3 after independent resource review; no default.',
    'scope_binding_or_candidate_executed': False, 'actual_case_acceptance': False, 'formal_increment': 0})
write('staging-audit.json', {'actor': 'codex:/root', 'actual_before': [324, 152, 430],
    'explicit_proposed_after': [325, 153, 437], 'source_commit': cp['head'],
    'root_inputs_ref': request, 'pending_origins': 7, 'counter_reset': False,
    'current_canonical_refs': audit['before_refs'][:4], 'source_rows_verified': len(source_rows),
    'staged_wrapper_count': 6, 'actual_source_or_canonical_index_writes': 0,
    'actual_compiler_SQL_HTTP_DLL_MODEL_calls': 0, 'actual_binding_builder_or_template_calls': 0,
    'runtime_unresolved': True, 'goal_status': 'ACTIVE', 'formal_increment': 0})
members = [pin(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
write('staging.manifest.json', {'actor': 'codex:/root', 'entries': members, 'count': len(members), 'self_excluded': True})
print(json.dumps({'root_inputs_ref': request, 'staging_audit_ref': pin(OUT / 'staging-audit.json'),
    'staging_manifest_ref': pin(OUT / 'staging.manifest.json')}, ensure_ascii=False))
