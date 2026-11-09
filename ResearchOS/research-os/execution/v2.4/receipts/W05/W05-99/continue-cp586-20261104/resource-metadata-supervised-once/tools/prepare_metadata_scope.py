"""Prepare one exact Root metadata run; this file never starts a child."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
CBASE = HERE.parent / 'cp586-continuation'
SUPBASE = CBASE / 'owned-model-resource-supervisor-20261104'
SUP = SUPBASE / 'revision-02'
R4 = CBASE / 'owned-model-resource-stage-b/revision-04'
OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/resource-metadata-supervised-once'
REVIEW = SUP / 'reviews/independent-supervisor-review-02/source-review.json'
REVIEW_SHA = 'a1e562a307fdf7a7b0532df9773adab8c3dc8be3736b233c55f202aac00dee78'
MANIFEST_SHA = '8f7603011921d814e0cd3dd5c2c7d61c2ceea5a17b92b202901a461a130d96b4'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(path, value):
    temp = path.with_name(path.name + '.new')
    assert not temp.exists()
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temp, path)


p = argparse.ArgumentParser()
p.add_argument('--expected-head', required=True)
p.add_argument('--expected-revision', required=True, type=int)
p.add_argument('--expected-records', required=True, type=int)
a = p.parse_args()
assert sha(REVIEW) == REVIEW_SHA
report = json.loads(REVIEW.read_bytes())
assert report['root_scope_preparation_supported'] is True
assert sha(SUP / 'MANIFEST.json') == MANIFEST_SHA
manifest = json.loads((SUP / 'MANIFEST.json').read_bytes())
for item in manifest['files']:
    path = SUP / item['relative']
    assert path.resolve().is_relative_to(SUP.resolve())
    assert sha(path) == item['sha256'] and path.stat().st_size == item['bytes']
assert not (SUPBASE / 'attempt-01').exists() and not (R4 / 'run-01').exists()
free = shutil.disk_usage(CBASE).free
assert free >= 12 * 1024**3, 'C free space below existing R4 gate; no scope consumed'
cpfile = ROOT / 'execution/v2.4/checkpoint.json'
raw = cpfile.read_bytes()
cp = json.loads(raw)
assert cp['revision'] == a.expected_revision and len(cp['failure_counters']) == a.expected_records
assert cp['current_Main_HEAD'] == a.expected_head
actual = subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '--no-optional-locks', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert actual == a.expected_head
assert not OUT.exists(), 'Readback uncertain scope; do not replay'
protected = json.loads((ROOT / 'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json').read_bytes())['protected_preserved']
for path, digest in protected.items():
    assert (sha(ROOT / path) if (ROOT / path).is_file() else 'ABSENT_BEFORE') == digest
OUT.mkdir()
(OUT / 'evidence').mkdir()
(OUT / 'tools').mkdir()
(OUT / ('checkpoint.cp' + str(a.expected_revision) + '.before.json')).write_bytes(raw)
copies = [(SUP / 'MANIFEST.json', 'supervisor-v2/MANIFEST.json'), (REVIEW, 'supervisor-v2/source-review.json'),
          (R4 / 'reviews/independent-source-review-01/source-review.json', 'controller-r4/source-review.json')]
copies += [(SUP / item['relative'], 'supervisor-v2/' + item['relative']) for item in manifest['files']]
v1manifest = json.loads((SUPBASE / 'MANIFEST.json').read_bytes())
copies += [(SUPBASE / item['relative'], 'supervisor-v1/' + item['relative']) for item in v1manifest['files']]
copies += [(SUPBASE / 'MANIFEST.json', 'supervisor-v1/MANIFEST.json')]
v1review = SUPBASE / 'reviews/independent-supervisor-review-01'
for name in ('source-review.json', 'counterexample.json', 'offline-checks.json'):
    copies.append((v1review / name, 'supervisor-v1/reviews/' + name))
archive = []
for source, relative in copies:
    target = OUT / 'evidence' / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
    assert sha(target) == sha(source)
    archive.append({'path': relative, 'sha256': sha(target), 'bytes': target.stat().st_size})
put(OUT / 'evidence-manifest.json', archive)
now = datetime.now(timezone.utc).isoformat()
events = [
    ('20261104|supervisor|mock-default-temp-acl', 'AUTHOR_MOCK_FIXTURE_FAILURE_RETAINED', {'origin': 'SUPERVISOR-MOCKS-01-DEFAULT-TEMP-ACL', 'attempt_index': 1, 'exit_code': 1, 'fixture_errors': 3, 'raw_terminal': 'edb15c', 'repair': 'Pure-memory fixtures; original source/log retained.'}),
    ('20261104|supervisor|SUP-P1-001', 'INDEPENDENT_CANCELLATION_COUNTEREXAMPLE_REPAIRED_NOT_NATIVE_TEST', {'raw_terminal': 'e8d40e', 'old_review_sha256': 'bed62d14124fd98c90a52f3981f51fb556622a023b5170becec353baad0389b4', 'v2_review_sha256': REVIEW_SHA}),
    ('20261104|supervisor|review-v2-line-probe', 'REVIEWER_HARNESS_FAILURE_RETAINED', {'raw_terminal': '55a8cc', 'exit_code': 1, 'detail': 'Old hardcoded v1 line probe did not trigger in v2; original24mocks passed. Corrected dynamic line/opcode probe19b845 exit0; no source mutation.'}),
    ('20261104|supervisor|review-thread-limit', 'REVIEW_PREPARATION_TOOL_LIMIT_NOT_PRODUCT_FAILURE', {'detail': 'One completed cleanup_peer followup was blocked by agent thread limit; Root requested solo independent review, no retry.'}),
    ('20261104|supervisor|review-report-wrapper', 'REVIEW_REPORT_ORCHESTRATION_ERROR_NO_PARTIAL_WRITE', report['diagnostics']['report_assembly']),
]
r4review = json.loads((R4 / 'reviews/independent-source-review-01/source-review.json').read_bytes())
for event in r4review['diagnostics']['events']:
    events.append(('20261104|resource-r4-review|' + event['chunk'], 'READONLY_REVIEW_DIAGNOSTIC_PRESERVED', event))
initial = list(cp['failure_counters'])
existing = {entry.get('origin_key') for entry in initial}
for key, classification, detail in events:
    if key not in existing:
        cp['failure_counters'].append({'at': now, 'origin_key': key, 'classification': classification, 'detail': detail, 'attempts': 1, 'counter_reset': False})
assert cp['failure_counters'][:a.expected_records] == initial
revision = a.expected_revision + 1
scopefile = OUT / 'root-authorization.json'
resume = {'checkpoint_revision': revision, 'status': 'ROOT_AUTHORIZED_ONE_METADATA_DIAGNOSTIC_NOT_STARTED', 'main_head': a.expected_head,
          'root_authorization_ref': str(scopefile.relative_to(ROOT)), 'supervisor_review_sha256': REVIEW_SHA,
          'free_bytes_before_scope': free, 'failure_records': len(cp['failure_counters']), 'counter_reset': False,
          'formal_accepted': 0, 'formal_required': 42, 'formal_increment': 0, 'resource_ready': False,
          'limits': 'Exactly one private copied-server metadata diagnostic; version/tags each at most1, no inference/paid/old instance/old keys. No consumed or UNKNOWN native qualification replay.',
          'parallel_w14': 'Frozen9files pending independent QA under w14-peer-auth-seam; no writer handoff enabled.',
          'next': 'Execute this exact hash-bound supervisor once. After uncertain transport, read global attempt/run/results/process state before anything else; never automatically retry. Root must independently inspect cleanup/asset/request evidence before classifying metadata outcome.'}
put(OUT / 'RESUME.json', resume)
cp['revision'] = revision
cp['expected_previous_revision'] = a.expected_revision
cp['updated_at'] = now
cp['next_command'] = resume['next'] + ' Read ' + str((OUT / 'RESUME.json').relative_to(ROOT))
cp['current_implementation'] = {'status': resume['status'], 'at': now, 'resume_ref': str((OUT / 'RESUME.json').relative_to(ROOT)), 'active_construction_owners': [], 'formal_increment': 0}
cp['side_effects_pending'].append({'origin_key': 'OWNED_COPY_MODEL_METADATA_ONCE_20261104', 'state': 'ROOT_AUTHORIZED_NOT_STARTED', 'scope_ref': str(scopefile.relative_to(ROOT)), 'global_attempt_directory': str(SUPBASE / 'attempt-01'), 'inference_limit': 0, 'max_controller_launches': 1, 'automatic_retry': False})
assert cpfile.read_bytes() == raw
put(cpfile, cp)
handoff = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
before = handoff.read_bytes()
(OUT / ('handoff.cp' + str(a.expected_revision) + '.before.md')).write_bytes(before)
temp = handoff.with_name(handoff.name + '.cp' + str(revision) + '.new')
assert not temp.exists()
temp.write_bytes(('# Current resume CP' + str(revision) + '\n\nRead ' + str((OUT / 'RESUME.json').relative_to(ROOT)) + '. One Root-supervised private copied-server metadata diagnostic authorized after v2 source review; not yet started. No inference, paid call, old key/store/instance or formal acceptance. W14 seam remains pending independent QA. Never replay uncertain/consumed scopes.\n\n').encode() + before)
os.replace(temp, handoff)
grant = json.loads((SUP / 'ROOT-AUTHORIZATION-TEMPLATE.json').read_bytes())
grant.update(status='ROOT_AUTHORIZED_ONCE_AFTER_REVIEW', checkpoint_revision=revision, checkpoint_sha256=sha(cpfile),
             supervisor_manifest_sha256=MANIFEST_SHA, attempt_directory=str(SUPBASE / 'attempt-01'),
             independent_supervisor_review_sha256=REVIEW_SHA, at=now, purpose='METADATA_DIAGNOSTIC_ONLY_NOT_QUALIFICATION')
put(scopefile, grant)
args = ['-I', '-S', str(SUP / 'supervise.py'), '--execute', '--expected-manifest-sha256', MANIFEST_SHA, '--root-scope', str(scopefile), '--root-scope-sha256', sha(scopefile)]
put(OUT / 'RUN_COMMAND.json', {'exe': 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe', 'args': args, 'cwd': str(SUP), 'max_launches': 1, 'automatic_retry': False, 'not_executed_by_this_preparation': True})
(OUT / 'tools/prepare_metadata_scope.py').write_bytes(Path(__file__).read_bytes())
put(OUT / 'preparation-journal.json', {'status': 'ROOT_SCOPE_AND_CHECKPOINT_SAVED_NOT_STARTED', 'checkpoint_revision': revision, 'checkpoint_sha256': sha(cpfile), 'root_authorization_sha256': sha(scopefile), 'formal_increment': 0})
print(json.dumps({'checkpoint': revision, 'head': actual, 'failure_records': len(cp['failure_counters']), 'root_scope_sha256': sha(scopefile), 'free_gib': round(free / 1024**3, 2), 'not_started': True}))
