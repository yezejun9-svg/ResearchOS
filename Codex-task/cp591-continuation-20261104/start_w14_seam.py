import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/w14-peer-auth-seam'
WT = ROOT / '.local/worktrees/w14-peer-auth-seam-20261104'
PRODUCTION = ['internal/host/host.go', 'internal/host/native.go', 'internal/host/native_pipe_windows.go', 'internal/domain/auth.go', 'internal/domain/client_protocol_auth.go', 'internal/api/v2.go']
TESTS = ['internal/host/native_peer_provenance_test.go', 'internal/domain/client_protocol_auth_context_test.go', 'internal/api/v2_auth_context_test.go']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(cwd, *args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '--no-optional-locks', *args], cwd=cwd, stderr=subprocess.STDOUT).decode('utf-8')


def put(path, value):
    tmp = path.with_name(path.name + '.new')
    assert not tmp.exists()
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, path)


p = argparse.ArgumentParser()
p.add_argument('--expected-head', required=True)
p.add_argument('--expected-revision', type=int, required=True)
p.add_argument('--expected-records', type=int, required=True)
a = p.parse_args()
cpfile = ROOT / 'execution/v2.4/checkpoint.json'
raw = cpfile.read_bytes()
cp = json.loads(raw)
assert cp['revision'] == a.expected_revision and len(cp['failure_counters']) == a.expected_records
assert git(ROOT, 'rev-parse', 'HEAD').strip() == a.expected_head
assert not OUT.exists() and not WT.exists(), 'Inspect uncertain prior worktree/scope creation; do not replay'
dirty = set(git(ROOT, 'diff', '--name-only').splitlines())
assert not dirty.intersection(PRODUCTION + TESTS)
protected = json.loads((ROOT / 'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json').read_bytes())['protected_preserved']
for path, digest in protected.items():
    assert (sha(ROOT / path) if (ROOT / path).is_file() else 'ABSENT_BEFORE') == digest
for path in TESTS:
    assert not (ROOT / path).exists()
base_sources = {path: sha(ROOT / path) for path in PRODUCTION}
OUT.mkdir()
for name in ('author', 'reviews', 'tools'):
    (OUT / name).mkdir()
(OUT / ('checkpoint.cp' + str(a.expected_revision) + '.before.json')).write_bytes(raw)
git(ROOT, 'worktree', 'add', '--no-checkout', '-b', 'codex/w14-peer-auth-seam-20261104', str(WT), a.expected_head)
git(WT, 'sparse-checkout', 'set', '--no-cone', '/AGENTS.md', '/go.mod', '/go.sum', '/internal/', '/adapters/', '/migrations/sqlite/', '/spec/v2.0/contracts/', '/ops/')
git(WT, 'checkout', 'HEAD')
evaluation = git(WT, 'ls-tree', '-r', '--name-only', 'HEAD', '--', 'evaluation/holdout/jev', 'evaluation/evolution', 'evaluation/skills').splitlines()
sources = [path for path in evaluation if path.endswith('.go') and not path.endswith('_test.go')]
git(WT, 'sparse-checkout', 'add', *['/' + path for path in sources])
assert not git(WT, 'status', '--porcelain=v1', '-uno').strip()
for path, digest in base_sources.items():
    assert sha(WT / path) == digest
now = datetime.now(timezone.utc).isoformat()
scope = {
    'scope_id': 'W14_VERIFIED_NATIVE_PEER_AND_COMMAND_AUTH_SEAM_V1', 'parent': 'W14-01 prerequisite under current W05-99 blocker',
    'at': now, 'base_head': a.expected_head, 'worktree': str(WT), 'owner': 'codex:/root/workbench_builder', 'integrator': 'codex:/root',
    'existing_root_lease': 'path_ownership active_integrator codex:/root; W14-01 owner codex:/root. Historical subleases retained, no live source overlap; exact child scope here.',
    'production_paths': PRODUCTION, 'test_paths': TESTS, 'base_source_sha256': base_sources,
    'allowed': [
        'Preserve OS-produced native peer facts across private typed Host dispatch seam; legacy bool must never mint such facts.',
        'Fresh per-Host.New private random boot generation; entropy failure before filesystem/database effects; no stable-InstanceID substitute.',
        'Resolve actual credential within the same v2 command transaction via existing auth/RBAC/remote rules; store only opaque private context facts, no raw token and no native/client/sameOS claim.',
        'Preserve ordinary AuthenticateToken/HandleNative compatibility and public v2 request/error semantics. Use current Service contracts and normal domain primitives.',
        'Focused injected peer/entropy tests and fresh-SQLite/HTTP fixtures. No actual Native/model/backend execution.',
    ],
    'forbidden': [
        'No native wire method, new table, numbered migration, public schema or registry change',
        'No writer grant/lease expiry bypass, attach settlement/control/ACK rewrite, new journal or queue clear',
        'No bootstrap credential issue/rotation beyond existing behavior; no model/renderer receives credential facts',
        'No old database/runtime/model/qualification scope access or replay; no formal acceptance assertion',
        'No actual native backend, model, GPU, network service, paid call or external message',
    ],
    'limits': 'Prerequisite seam only. Durable native client/writer proof, request attestation, ACK/replay/full settlement/CAS and active pause remain unimplemented; ordinary bearer never proves native identity.',
    'formal_increment': 0, 'counter_reset': False,
}
put(OUT / 'scope.json', scope)
revision = a.expected_revision + 1
resume = {'checkpoint_revision': revision, 'status': 'IMPLEMENTING_W14_PEER_AUTH_SEAM_NO_WRITER_TAKEOVER', 'main_head': a.expected_head, 'scope_ref': str((OUT / 'scope.json').relative_to(ROOT)), 'worktree': str(WT), 'formal_accepted': 0, 'formal_required': 42, 'formal_increment': 0, 'failure_records': len(cp['failure_counters']), 'next': 'Implement exact9files then focused checks and independent review. Finish supervisor offline review before a separately consumed Root metadata-only resource scope; keep writer/LIVE/SDK gates.'}
put(OUT / 'RESUME.json', resume)
cp['revision'] = revision
cp['expected_previous_revision'] = a.expected_revision
cp['updated_at'] = now
cp['next_command'] = resume['next'] + ' Read ' + str((OUT / 'RESUME.json').relative_to(ROOT))
cp['current_implementation'] = {'status': resume['status'], 'at': now, 'resume_ref': str((OUT / 'RESUME.json').relative_to(ROOT)), 'active_construction_owners': [scope['owner'], 'codex:/root/runtime_readiness controller supervisor'], 'formal_increment': 0}
cp['workers'].append({'step_id': 'W14-01', 'slice_id': scope['scope_id'], 'owner': scope['owner'], 'worktree': str(WT), 'state': 'SCOPED_SOURCE_IMPLEMENTATION_ONLY', 'scope_ref': resume['scope_ref']})
assert cpfile.read_bytes() == raw
put(cpfile, cp)
handoff = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
before = handoff.read_bytes()
(OUT / ('handoff.cp' + str(a.expected_revision) + '.before.md')).write_bytes(before)
temp = handoff.with_name(handoff.name + '.cp' + str(revision) + '.new')
assert not temp.exists()
temp.write_bytes(('# Current resume CP' + str(revision) + '\n\nRead ' + str((OUT / 'RESUME.json').relative_to(ROOT)) + '. Exact9file W14 native-peer/auth-command prerequisite seam scoped; no writer transfer, native wire, table or old DB change. Supervisor remains offline-only pending independent review. Formal0/42; historical counters retained.\n\n').encode() + before)
os.replace(temp, handoff)
(OUT / 'tools/start_w14_seam.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'checkpoint': revision, 'head': a.expected_head, 'worktree': str(WT), 'files': 9, 'failure_records': len(cp['failure_counters']), 'formal_increment': 0}))
