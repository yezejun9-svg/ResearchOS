import datetime
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os').resolve()
WT = ROOT / '.local/worktrees/codex-w0599-provider-binding'
OUT = pathlib.Path(__file__).resolve().parent
PRIOR = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/provider-author-closure-r287'
NS = WT / 'execution/v2.4/receipts/W05/W05-99/provider_binding_executor_codex/typed-route-final-6c47a88a198349b4bd2a3d3d223510b1'
GIT = 'C:/Program Files/Git/cmd/git.exe'
HEAD = '6fb5263681c17f0e50920c354dc07ed440a23714'
EXACT = ['README.md', 'generate_other.go', 'generate_windows.go', 'generator.go', 'generator_test.go', 'rubric.go', 'truth.go']


def ref(p):
    p = pathlib.Path(p)
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def save(name, value):
    p = OUT / name
    assert not p.exists(), str(p)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return ref(p)


old = json.loads((PRIOR / 'closure.json').read_bytes())
assert ref(PRIOR / 'closure.json')['sha256'] == 'cff73f4e3af4b6cafac5dd9c615e31e8e980cda8353abbecd9f612fa92c75482'
assert len(old['errors']) == 7 and {e['label'] for e in old['errors']} == {'unexpected-private-input'}
assert {pathlib.Path(e['path']).name for e in old['errors']} == set(EXACT)
assert json.loads((PRIOR / 'verify.invocation.json').read_bytes())['actual_exit'] == 1
current = json.loads((NS / 'current-inputs.json').read_bytes())
before = json.loads((NS / 'before-first-case.json').read_bytes())
after = json.loads((NS / 'after-cases.json').read_bytes())
assert current['files'] == before['files'] == after['files']
actual_head = subprocess.run([GIT, 'rev-parse', 'HEAD'], cwd=WT, capture_output=True, check=True).stdout.decode().strip()
assert actual_head == HEAD
rows = []
for name in EXACT:
    rel = 'evaluation/holdout/jev/' + name
    p = (WT / rel).resolve()
    assert p.is_relative_to(WT.resolve()) and p.name in EXACT
    expected = current['files'][str(p)]
    actual = ref(p)
    assert actual == expected
    argv = [GIT, 'cat-file', 'blob', HEAD + ':' + rel]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc = subprocess.run(argv, cwd=WT, capture_output=True)
    blob = OUT / (name + '.git-blob.raw')
    stderr = OUT / (name + '.git-stderr.raw')
    assert not blob.exists() and not stderr.exists()
    blob.write_bytes(proc.stdout)
    stderr.write_bytes(proc.stderr)
    invocation = {'argv': argv, 'cwd': str(WT), 'started': started,
                  'finished': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'actual_exit': proc.returncode, 'stdout': ref(blob), 'stderr': ref(stderr)}
    inv_ref = save(name + '.git-invocation.json', invocation)
    assert proc.returncode == 0 and proc.stdout == p.read_bytes()
    rows.append({'path': rel, 'declared_input': expected, 'actual_file': actual,
                 'immutable_candidate_git_blob': ref(blob), 'invocation': inv_ref,
                 'classification': 'IMMUTABLE_PUBLIC_REPOSITORY_GENERATOR_SOURCE; no generated holdout instance read'})
result = {'schema': 'researchos.root.public-input-classification-supplement.v1', 'actor': 'codex:/root',
          'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'candidate_head': HEAD,
          'prior_actual_exit': 1, 'prior_closure': ref(PRIOR / 'closure.json'),
          'correction': 'Overbroad path substring rejected seven public Git source files. Exact immutable tracked-source proof supplements only those omitted hashes; prior raw result remains unchanged.',
          'prior_complete_inputs_checked': old['complete_input_files'], 'supplemented_public_inputs': len(rows),
          'complete_inputs_checked': old['complete_input_files'] + len(rows),
          'declared_complete_input_count': current['count'], 'compiled_inputs_checked': old['compiled_input_files'],
          'author_public_files_checked': old['public_manifest_files'], 'author_case_records_checked': old['author_case_records'],
          'complete_frozen_vectors_equal': True, 'public_source7': rows,
          'status': 'AUTHOR_PUBLIC_CLOSURE_CORROBORATED_PENDING_NONAUTHOR_EXECUTION',
          'product_cases_run': 0, 'SQL_open': 0, 'model_calls': 0, 'worker_calls': 0, 'HTTP_calls': 0,
          'private_generated_holdout_reads': 0, 'private_resource_reads': 0,
          'source_changes': 0, 'canonical_mutations': 0, 'source_acceptance': False, 'formal_increment': 0,
          'old_case02_equivalence': old['old_case02_equivalence'], 'public_restore': old['public_restore']}
assert result['complete_inputs_checked'] == result['declared_complete_input_count'] == 20693
save('supplement.json', result)
files = [ref(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ['manifest.json', 'verify.invocation.json', 'verify.stdout.raw', 'verify.stderr.raw']]
save('manifest.json', {'schema': 'researchos.root.public-receipt-manifest.v1', 'files': files, 'file_count': len(files), 'self_excluded': True, 'source_acceptance': False})
print(json.dumps({'status': result['status'], 'complete_inputs_checked': result['complete_inputs_checked'], 'public_git_sources_supplemented': len(rows), 'supplement': ref(OUT / 'supplement.json')}, ensure_ascii=True))
