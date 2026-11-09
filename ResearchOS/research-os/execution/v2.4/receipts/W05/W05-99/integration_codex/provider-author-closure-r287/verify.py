import datetime
import gzip
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os').resolve()
WT = ROOT / '.local/worktrees/codex-w0599-provider-binding'
OUT = pathlib.Path(__file__).resolve().parent
NS = WT / 'execution/v2.4/receipts/W05/W05-99/provider_binding_executor_codex/typed-route-final-6c47a88a198349b4bd2a3d3d223510b1'
ALLOWED = [
    'execution/v2.4/receipts/W05/W05-99/provider_binding_executor_codex/typed-route-final-6c47a88a198349b4bd2a3d3d223510b1/',
    'execution/v2.4/receipts/W05/W05-99/provider_binding_executor_codex/typed-route-5188793d240a4f1197f92bbc510ad9e1/',
]
EXPECTED_HEAD = '6fb5263681c17f0e50920c354dc07ed440a23714'
errors = []


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(name, value):
    p = OUT / name
    assert not p.exists(), str(p)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return ref(p)


def ref(p):
    p = pathlib.Path(p)
    with p.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    return {'path': str(p), 'sha256': digest, 'bytes': p.stat().st_size}


def check_ref(item, label):
    p = pathlib.Path(item['path'])
    try:
        got = ref(p)
    except OSError as e:
        errors.append({'label': label, 'path': str(p), 'error': repr(e)})
        return
    if got['sha256'] != item['sha256'] or got['bytes'] != item['bytes']:
        errors.append({'label': label, 'expected': item, 'actual': got})


def git(label, args):
    argv = ['C:/Program Files/Git/cmd/git.exe', *args]
    started = now()
    p = subprocess.run(argv, cwd=WT, capture_output=True)
    stdout = OUT / (label + '.stdout.raw')
    stderr = OUT / (label + '.stderr.raw')
    assert not stdout.exists() and not stderr.exists()
    stdout.write_bytes(p.stdout)
    stderr.write_bytes(p.stderr)
    write(label + '.invocation.json', {'argv': argv, 'cwd': str(WT), 'started': started,
          'finished': now(), 'actual_exit': p.returncode, 'stdout': ref(stdout), 'stderr': ref(stderr)})
    if p.returncode != 0:
        errors.append({'label': label, 'actual_exit': p.returncode})
    return p.stdout


started = now()
head = git('candidate-head', ['rev-parse', 'HEAD']).decode('ascii').strip()
if head != EXPECTED_HEAD:
    errors.append({'label': 'candidate-head', 'expected': EXPECTED_HEAD, 'actual': head})
status = git('candidate-tracked-status', ['status', '--porcelain', '--untracked-files=no'])
if status.strip():
    errors.append({'label': 'candidate-tracked-status', 'status': status.decode('utf-8', errors='replace')})
delta = git('candidate-commit-paths', ['diff-tree', '--no-commit-id', '--name-only', '-r', '-z', 'HEAD'])
paths = [p.decode('utf-8') for p in delta.split(b'\0') if p]
source2 = ['internal/domain/runtime_model_verification.go', 'internal/domain/runtime_provider_binding_windows_test.go']
if sorted(p for p in paths if not p.startswith('execution/')) != sorted(source2):
    errors.append({'label': 'candidate-exact-source2', 'actual': [p for p in paths if not p.startswith('execution/')]})
if any(p not in source2 and not any(p.startswith(prefix) for prefix in ALLOWED) for p in paths):
    errors.append({'label': 'candidate-commit-outside-scope'})
write('candidate-commit-paths.json', {'paths': paths, 'count': len(paths)})
handoff = json.loads((NS / 'handoff.json').read_bytes())
manifest = json.loads((NS / 'manifest.json').read_bytes())
if ref(NS / 'manifest.json')['sha256'] != 'd72657266613d9f68f25f36cc2968cb231a161963d5040869d8cc12213403df3':
    errors.append({'label': 'manifest-exact-sha'})
manifest_rows = []
for row in manifest['files']:
    rel = row['path'].replace('\\', '/')
    p = (WT / rel).resolve()
    if not p.is_relative_to(WT.resolve()) or not any(rel.startswith(prefix) for prefix in ALLOWED):
        errors.append({'label': 'manifest-boundary', 'path': rel})
        continue
    item = {**row, 'path': str(p)}
    check_ref(item, 'manifest')
    manifest_rows.append(item)
if len(manifest_rows) != manifest['file_count'] or sum(x['bytes'] for x in manifest_rows) != manifest['total_bytes']:
    errors.append({'label': 'manifest-summary'})
write('manifest-verification.json', {'checked': len(manifest_rows), 'total_bytes': sum(x['bytes'] for x in manifest_rows),
      'manifest': ref(NS / 'manifest.json'), 'self_excluded': True, 'paths': manifest_rows})
for row in manifest['source2']:
    check_ref({**row, 'path': str(WT / row['path'])}, 'source2')
freeze = json.loads((NS / 'source9.freeze.json').read_bytes())
for rel, value in freeze.items():
    check_ref(value['current'], 'source9-current')
current = json.loads((NS / 'current-inputs.json').read_bytes())
before = json.loads((NS / 'before-first-case.json').read_bytes())
after = json.loads((NS / 'after-cases.json').read_bytes())
if current['files'] != before['files'] or current['files'] != after['files']:
    errors.append({'label': 'complete-frozen-vector-equality'})
vector_rows = []
for path, item in current['files'].items():
    if path != item['path']:
        errors.append({'label': 'vector-path-key', 'path': path})
    normalized = path.replace('\\', '/').lower()
    if '/.local/resources/' in normalized or '/evaluation/holdout/' in normalized:
        errors.append({'label': 'unexpected-private-input', 'path': path})
        continue
    check_ref(item, 'complete-current-vector')
    vector_rows.append(item)
compiled = json.loads((NS / 'compiled-inputs.before.json').read_bytes())
if any(current['files'].get(p) != item for p, item in compiled['files'].items()):
    errors.append({'label': 'compiled-not-in-complete-vector'})
check_ref(handoff['test_executable'], 'test-executable')
if current['files'].get(handoff['test_executable']['path']) != handoff['test_executable']:
    errors.append({'label': 'executable-not-in-complete-vector'})
write('complete-vector-verification.json', {'at': now(), 'before': ref(NS / 'before-first-case.json'),
      'after': ref(NS / 'after-cases.json'), 'current': ref(NS / 'current-inputs.json'),
      'current_count': len(vector_rows), 'compiled_count': len(compiled['files']),
      'equality': current['files'] == before['files'] == after['files'],
      'test_executable': handoff['test_executable'], 'checked_every_current_file': True,
      'private_inputs_read': 0})
original_before = json.loads((NS / 'original-inputs.before.json').read_bytes())
original_after = json.loads((NS / 'original-inputs.after.json').read_bytes())
if original_before != original_after:
    errors.append({'label': 'original-seven-before-after-equality'})
for key, value in original_before.items():
    for name, item in value.items():
        check_ref(item, 'original-seven-' + key + '-' + name)
write('original-seven-verification.json', {'before': ref(NS / 'original-inputs.before.json'),
      'after': ref(NS / 'original-inputs.after.json'), 'count': len(original_before),
      'all_current_refs_checked': True, 'before_after_equal': original_before == original_after,
      'no_sqlite_open': True})
audit = json.loads((NS / 'case-audit.json').read_bytes())
case_records = []
for row in audit['cases']:
    result = json.loads(pathlib.Path(row['result']['path']).read_bytes())
    actual = json.loads(pathlib.Path(row['actual']['path']).read_bytes())
    check_ref(row['result'], 'case-result')
    check_ref(row['actual'], 'case-actual')
    if result['exit'] != row['exit'] or result['exit'] != 0 or row['skip'] != 0:
        errors.append({'label': 'case-actual-exit', 'case': row['name']})
    for k in ['stdout', 'stderr']:
        check_ref(result[k], 'case-' + k)
    info = {'case': row['name'], 'actual_exit': result['exit'], 'test': row['test'], 'skip': row['skip']}
    if 'semantic_before' in row:
        for k in ['semantic_before', 'semantic_after', 'closed_db']:
            check_ref(row[k], 'case-' + k)
        a = json.loads(gzip.decompress(pathlib.Path(row['semantic_before']['path']).read_bytes()))
        b = json.loads(gzip.decompress(pathlib.Path(row['semantic_after']['path']).read_bytes()))
        info.update({'paired_stored_semantic_equal': a == b, 'semantic_equal_declared': row['semantic_equal'],
                     'semantic_before': row['semantic_before'], 'semantic_after': row['semantic_after'],
                     'closed_db': row['closed_db']})
        if (a == b) != row['semantic_equal']:
            errors.append({'label': 'case-paired-semantic-declaration', 'case': row['name']})
    case_records.append(info)
if len(case_records) != 64 or handoff['pass'] != 64 or handoff['fail'] != 0 or handoff['skip'] != 0:
    errors.append({'label': 'case-count'})
write('author-case-record-verification.json', {'actual_author_case_count': len(case_records), 'cases': case_records,
      'root_product_cases_run': 0, 'root_sqlite_open': 0,
      'scope': 'Existing author sealed bytes only; stored paired vectors corroborated, not independently derived from SQLite.'})
result = {'schema': 'researchos.root.public-provider-author-closure.v1', 'actor': 'codex:/root',
          'started': started, 'finished': now(), 'candidate_head': head, 'author_handoff': ref(NS / 'handoff.json'),
          'public_manifest_files': len(manifest_rows), 'source9_checked': len(freeze), 'source2': manifest['source2'],
          'complete_input_files': len(vector_rows), 'compiled_input_files': len(compiled['files']),
          'author_case_records': len(case_records), 'errors': errors,
          'status': 'AUTHOR_PUBLIC_CLOSURE_CORROBORATED_PENDING_NONAUTHOR_EXECUTION' if not errors else 'NEEDS_RECONCILIATION',
          'root_product_cases': 0, 'root_sql': 0, 'model_calls': 0, 'worker_calls': 0, 'HTTP_calls': 0,
          'private_resource_reads': 0, 'canonical_mutations': 0, 'formal_increment': 0,
          'public_restore': 'AUTHOR_NOT_RUN_OPTIONAL; no public restore credit',
          'old_case02_equivalence': 'UNPROVEN; newly stored equal pairs do not amend old 5a4-to-c687 limitation',
          'source_acceptance': False}
write('closure.json', result)
files = [ref(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ['manifest.json', 'verify.stdout.raw', 'verify.stderr.raw', 'verify.invocation.json']]
write('manifest.json', {'schema': 'researchos.root.public-receipt-manifest.v1', 'actor': 'codex:/root',
      'files': files, 'file_count': len(files), 'self_excluded': True, 'source_acceptance': False})
print(json.dumps({'status': result['status'], 'errors': len(errors), 'public_files': len(manifest_rows),
      'complete_inputs': len(vector_rows), 'compiled_inputs': len(compiled['files']),
      'author_case_records': len(case_records), 'closure': ref(OUT / 'closure.json')}, ensure_ascii=True))
raise SystemExit(0 if not errors else 1)
