import copy
import datetime
import hashlib
from http.client import HTTPResponse
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
MAIN = OUT.parents[3]
ROOT = MAIN / '.local/worktrees/c02-review'
AUTHOR = ROOT / 'execution/receipts/W17/c02/20260930T142902Z-f4f3ea0f54'
MODULE = ROOT / 'tests/security/c02_fixture.py'
spec = importlib.util.spec_from_file_location('c02_runner_readonly', MODULE)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]

def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

index = load(AUTHOR / 'evidence-index.json')
for name, expected in index['files'].items():
    assert Path(name).name == name
    assert digest(AUTHOR / name) == expected, name
manifest = load(AUTHOR / 'source-manifest.json')
for name, expected in manifest['files'].items():
    assert not Path(name).is_absolute() and '..' not in Path(name).parts and not name.startswith('.local/')
    assert digest(ROOT / name) == expected, name
assert digest(Path(manifest['go']['path'])) == manifest['go']['sha256']
inventory = load(ROOT / 'tests/security/c02_expected.json')
ids = runner.validate_inventory(inventory)
checks = []

for label, directory in [('author', AUTHOR), ('independent_native', OUT / 'native-rerun')]:
    events, records = lines(directory / 'go.stdout.jsonl'), lines(directory / 'audit.jsonl')
    checked = runner.validate_evidence(events, records, ids)
    http = [r for r in records if r.get('record_type') == 'http']
    assert [r['request_id'] for r in http] == list(range(1, len(http) + 1))
    for row in http:
        request_head, _, request_body = row['raw_request'].partition('\r\n\r\n')
        response_head, _, response_body = row['raw_response'].partition('\r\n\r\n')
        assert request_head.splitlines()[0] == f"{row['method']} {row['path']} HTTP/1.1"
        assert int(response_head.splitlines()[0].split()[1]) == row['status']
        # DumpResponse faithfully retains chunked transfer framing; decode it
        # through stdlib HTTP parsing before comparing the returned entity body.
        class WireSocket:
            def makefile(self, *args):
                return io.BytesIO(row['raw_response'].encode())
        parsed = HTTPResponse(WireSocket())
        parsed.begin()
        assert parsed.status == row['status']
        assert parsed.read().decode() == row['response_body']
        assert 'Authorization: Bearer [REDACTED]' in request_head
        assert datetime.datetime.fromisoformat(row['finished_at'].replace('Z', '+00:00')) >= datetime.datetime.fromisoformat(row['started_at'].replace('Z', '+00:00'))
    materials = [r for r in records if r.get('record_type') == 'materialized_file']
    for row in materials:
        assert row['sha256'] == 'sha256:' + hashlib.sha256(row['body'].encode()).hexdigest()
    for role in ['READER', 'PLANNER', 'EXECUTOR']:
        role_files = [r for r in materials if r['role'] == role]
        assert len(role_files) == 4
        public_shared = [json.loads(r['body']) for r in role_files if r['path'].endswith('.content') and 'fixture_explicit_shared_knowledge' in r['body']]
        assert len(public_shared) == 1
        shared = public_shared[0]
        assert shared['source'] == 'fixture://explicit-common-knowledge/shared-v1' and shared['source_version'] == '1'
        assert shared['shared_knowledge_scope'] == ['fixture_project_a', 'fixture_project_b']
        assert len(set(shared['authorized_project_ids'])) == 2
        # Successful reads use each role's still-valid A credential, not a 401.
        rows = [r for r in http if r.get('role') == role and r.get('audience') == 'A']
        assert not any(r['status'] == 401 for r in rows)
        assert any(r['status'] == 200 and 'fixture_a_authorized_material' in r['response_body'] for r in rows)
    scans = [r for r in records if r.get('record_type') == 'scan_report']
    assert len(scans) == 1
    assert scans[0]['total_HTTP_requests'] == len(http)
    assert scans[0]['A_response_leaks'] == scans[0]['A_material_leaks'] == scans[0]['service_log_leaks'] == 0
    assert scans[0]['A_http_responses_scanned'] == checked['scan']['A_http_responses']
    assert scans[0]['A_materialized_files_scanned'] == len(materials)
    checks.append({'source': label, 'assertions': len(checked['assertions']), 'http_count': len(http), 'scan': checked['scan'], 'wire_status_body_and_material_hashes_verified': True, 'shared_provenance_scope_version_present_in_all_roles_materials': True})

events, records = lines(AUTHOR / 'go.stdout.jsonl'), lines(AUTHOR / 'audit.jsonl')
negative = []
env = dict(os.environ, RESEARCHOS_TASK_ID='W17', RESEARCHOS_CASE_ID='C02', RESEARCHOS_CHECK_ID='', RESEARCHOS_MODE='FIXTURE', RESEARCHOS_MEASUREMENT_MODE='FIXTURE')
for name, change, arguments in [
    ('wrong-task', {'RESEARCHOS_TASK_ID': 'W04'}, []),
    ('wrong-case', {'RESEARCHOS_CASE_ID': 'C22'}, []),
    ('whole-gate', {'RESEARCHOS_CHECK_ID': 'W17-G01'}, []),
    ('invented-check', {'RESEARCHOS_CHECK_ID': 'C02'}, []),
    ('live-mode', {'RESEARCHOS_MODE': 'LIVE'}, []),
    ('unknown-argument', {}, ['--case=C22']),
]:
    result = subprocess.run([sys.executable, '-B', str(MODULE), *arguments], cwd=ROOT, env=env | change, capture_output=True, text=True, encoding='utf-8')
    response = json.loads(result.stdout)
    assert result.returncode == 1 and response['status'] == 'FAIL' and response['assertions'] == 0 and response['receipt'] is None
    negative.append({'name': name, 'exit_code': result.returncode, 'stdout': response, 'stderr': result.stderr, 'status': 'PASS'})

def reject(name, fn):
    try:
        fn()
    except (ValueError, KeyError) as error:
        negative.append({'name': name, 'error': str(error), 'status': 'PASS'})
    else:
        raise AssertionError('runner unexpectedly accepted: ' + name)

reject('empty-inventory', lambda: runner.validate_inventory(inventory | {'required_assertions': []}))
reject('duplicate-inventory', lambda: runner.validate_inventory(inventory | {'required_assertions': [*ids[:-1], ids[0]]}))
reject('missing-test', lambda: runner.validate_evidence([e for e in events if not (e.get('Action') == 'pass' and e.get('Test'))], records, ids))
reject('zero-assertions', lambda: runner.validate_evidence(events, [r for r in records if r.get('record_type') != 'assertion'], ids))
reject('duplicate-assertion', lambda: runner.validate_evidence(events, records + [next(r for r in records if r.get('record_type') == 'assertion')], ids))
changed = copy.deepcopy(records)
next(r for r in changed if r.get('record_type') == 'http' and r.get('audience') == 'A')['raw_response'] += 'fixture_b_private_marker'
reject('private-marker-leak', lambda: runner.validate_evidence(events, changed, ids))
changed = copy.deepcopy(records)
next(r for r in changed if r.get('record_type') == 'http' and r.get('role') == 'READER')['status'] = 401
reject('expired-credential', lambda: runner.validate_evidence(events, changed, ids))

# Independent evidence corruption probes beyond the author's original 13.
changed = copy.deepcopy(records)
next(r for r in changed if r.get('record_type') == 'materialized_file')['body'] += 'fixture_b_private_marker'
reject('materialized-body-leak', lambda: runner.validate_evidence(events, changed, ids))
changed = copy.deepcopy(records)
next(r for r in changed if r.get('record_type') == 'assertion')['actual'] = 'forged'
reject('persisted-stdout-divergence', lambda: runner.validate_evidence(events, changed, ids))
changed = [r for r in records if not (r.get('record_type') == 'http' and r.get('audience') == 'B_CONTROL' and 'fixture_b_private_marker' in r.get('response_body', ''))]
reject('missing-B-exists-positive', lambda: runner.validate_evidence(events, changed, ids))

save('validation.json', {'status': 'PASS', 'source_revision': 'c3991c0775f79382617459b369e1f369e9e3b960', 'author_file_hashes_verified': len(index['files']), 'author_source_hashes_verified': len(manifest['files']), 'native_and_author': checks, 'negative_count': len(negative), 'negative_probes': negative, 'production_or_provider_accessed': False})
print(json.dumps({'status': 'PASS', 'native_assertions': 22, 'native_http_count': checks[1]['http_count'], 'negative_probes': len(negative), 'verified_source_files': len(manifest['files'])}))
