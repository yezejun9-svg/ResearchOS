"""Root metadata binding and scope emission only. No CAS/grant/product launcher."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
PYTHON = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
V5 = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_root_binding_preparation_revision_codex/c16c5b73941e4e8a89b189594e53b4c5'
RUNTIME = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli43_windows_recursive_resource_catalog_codex/ca31885a78a74dff8ac108e20542331e/runtime-v3.json'

def need(ok, why):
    if not ok:
        raise RuntimeError(why)

def pin(p):
    p = Path(p).absolute()
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def verified(p, sha):
    b = Path(p).read_bytes()
    need(hashlib.sha256(b).hexdigest() == sha, 'Input document changed')
    return json.loads(b.decode('utf-8'))

def save(name, obj):
    with (OUT / name).open('xb') as f:
        f.write((json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use -I -S -X utf8')
sys.dont_write_bytecode = True
inputs = verified(OUT / 'root-inputs.json', '7410770d6e75e9ba518b7daffb4b8dc0edd2916c9a9ac06e93a8eaaba4e6c0ca')
rt = verified(RUNTIME, '98b5efb1e3bfa8ab5c64a7ed3280b62ca6c856cc562e1d5ea59f89caca28d6cf')
need(len(rt['files']) == 1242, 'Actual bounded public runtime rows')
inputs['runtime_resources_ref'] = pin(RUNTIME)
inputs['resource_final_binding'] = 'Actual declared runtime-v3 bytes; independent candidate-resource review and actual bound-scope review remain required before registration or product execution.'
save('root-inputs.runtime-bound.json', inputs)
builder = V5 / 'build_binding.v5.proposed.py'
need(pin(builder)['sha256'] == '179de3dc1763cdf956b08327cb8727e231a3a227b9067ee84c4fc8158c88ad5a', 'Reviewed binding builder SHA')
flags = ['-I', '-S', '-X', 'utf8']
argv = [PYTHON, *flags, str(builder)]
refkeys = ['scope_template_ref', 'runtime_resources_ref', 'compiler_resources_ref', 'current43_authority_ref',
           'origin_cut_ref', 'canonical_before_ref', 'source_inputs_ref', 'metadata_code_refs_ref', 'failure_prefix430_ref']
for k in refkeys:
    argv += ['--' + k.replace('_', '-'), json.dumps(inputs[k], ensure_ascii=False)]
argv += ['--controller-review-ref', 'null']
for k in ['before', 'after', 'main_git', 'public_environment']:
    argv += ['--' + k.replace('_', '-'), json.dumps(inputs[k], ensure_ascii=False)]
for k in ['run_uuid', 'registration_namespace', 'controller_review_path', 'new_output_root', 'new_wrapper_root',
          'new_export_root', 'new_authorization_root', 'new_grant_preflight_root']:
    argv += ['--' + k.replace('_', '-'), inputs[k]]
argv += ['--output', str(OUT / 'binding.pre-review.json')]

def run_metadata(label, args, limit):
    save(label + '.request.json', {'argv': args, 'cwd': str(ROOT), 'timeout_seconds': limit,
         'purpose': 'Metadata preparation only', 'automatic_retry': False,
         'Windows_Job_or_OS_lifecycle_qualification': False})
    with (OUT / (label + '.stdout.raw')).open('xb') as stdout, (OUT / (label + '.stderr.raw')).open('xb') as stderr:
        r = subprocess.run(args, cwd=ROOT, stdout=stdout, stderr=stderr, timeout=limit, check=False)
    save(label + '.invocation.json', {'actual_native_exit': r.returncode,
         'stdout_ref': pin(OUT / (label + '.stdout.raw')), 'stderr_ref': pin(OUT / (label + '.stderr.raw')),
         'automatic_retry': False, 'counter_reset': False, 'product_executed': False})
    need(r.returncode == 0, 'Metadata phase failed: ' + label)

run_metadata('binding-build', argv, 60)
binding_ref = pin(OUT / 'binding.pre-review.json')
run_metadata('scope-build', [PYTHON, *flags, str(OUT / 'scope_builder.py'),
    '--binding-ref', json.dumps(binding_ref, ensure_ascii=False), '--output', str(OUT),
    '--scope-template-ref', json.dumps(inputs['scope_template_ref'], ensure_ascii=False)], 900)
scope_ref = pin(OUT / 'scope_registration.json')
save('bound-scope-audit.json', {'actor': 'codex:/root', 'binding_ref': binding_ref, 'scope_ref': scope_ref,
    'actual_metadata_native_exits': [0, 0], 'current_canonical_before': inputs['before'],
    'proposed_after': inputs['after'], 'current_source_commit': inputs['main_git']['head'],
    'controller_review_path': inputs['controller_review_path'], 'controller_review_ref': None,
    'actual_registration_run_seal_grant_launcher': 0, 'actual_compile_graph': None,
    'actual_product_cases': 'NOT_RUN', 'formal_increment': 0,
    'standalone_scope_not_a_grant': True, 'actual_execution_authority': 'NOT_REGISTERED_NOT_GRANTED'})
members = [pin(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'bound-scope.manifest.json']
save('bound-scope.manifest.json', {'actor': 'codex:/root', 'entries': members, 'count': len(members), 'self_excluded': True,
    'canonical_source_writes': 0, 'formal_increment': 0})
print(json.dumps({'scope_ref': scope_ref, 'audit_ref': pin(OUT / 'bound-scope-audit.json'),
                 'manifest_ref': pin(OUT / 'bound-scope.manifest.json')}, ensure_ascii=False))
