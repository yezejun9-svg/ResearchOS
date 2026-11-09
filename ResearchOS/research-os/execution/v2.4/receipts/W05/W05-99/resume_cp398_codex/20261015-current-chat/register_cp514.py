import datetime
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
O = B / 'continuation-cp514'
E = R / 'execution/v2.4/receipts/W05/W05-99'
S = E / 'owned_core_stop_anchor_revision02_source_codex/20261015-current-chat'
F = S / 'candidate-f5db4a96-final'
BASE = '4f4023c956f84d65743f39ce77d6c8899a21ada1'
CANDIDATE = 'f5db4a9639f1a50380eb5929ee6295887baeb756'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def ref(p):
    data = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def new(p, obj):
    with p.open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def replace(p, before, after):
    assert p.read_bytes() == before
    tmp = p.with_name(p.name + '.cp514.pending')
    with tmp.open('xb') as f:
        f.write(after)
    assert p.read_bytes() == before
    os.replace(tmp, p)


cp_p = R / 'execution/v2.4/checkpoint.json'
ow_p = R / 'execution/v2.4/path_ownership.json'
hp = R / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
sp = R / 'execution/v2.4/step_state.json'
raw = {p: p.read_bytes() for p in (cp_p, ow_p, hp, sp)}
cp, ow = read(cp_p), read(ow_p)
assert cp['revision'] == 513 and ow['revision'] == 299 and len(cp['failure_counters']) == 1645
assert ref(F / 'manifest.json')['sha256'] == '40ba49b8de7021a7ba3416f261436940ef3f5e24d31d62124a9f5f43a228482f'
manifest = read(F / 'manifest.json')
assert manifest['commit'] == CANDIDATE and manifest['tree'] == 'f6d44526df9f03abf1a5544cf4e7762be3d89208' and manifest['formal_increment'] == 0
O.mkdir(exist_ok=False)


def git(name, args, cwd=R):
    argv = ['git'] + args
    new(O / (name + '.command.json'), {'argv': argv, 'cwd': str(cwd), 'relevant_env': {'GIT_OPTIONAL_LOCKS': '0'}})
    p = subprocess.run(argv, cwd=cwd, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (O / (name + '.stdout.raw')).write_bytes(p.stdout)
    (O / (name + '.stderr.raw')).write_bytes(p.stderr)
    new(O / (name + '.result.json'), {'exit': p.returncode})
    p.check_returncode()
    return p.stdout.decode('utf8').strip()


assert git('head', ['rev-parse', 'HEAD']) == BASE
assert not git('index', ['diff', '--cached', '--name-only'])
assert len(git('status', ['status', '--short', '--untracked-files=no']).splitlines()) == 20
assert git('candidate-tree', ['rev-parse', CANDIDATE + '^{tree}']) == manifest['tree']
candidate_wt = Path(manifest['worktree'])
assert git('candidate-head', ['rev-parse', 'HEAD'], candidate_wt) == CANDIDATE
assert not git('candidate-status', ['status', '--porcelain'], candidate_wt)
allow = set(manifest['whole19_changed_from_main'])
assert len(allow) == 19 and set(git('whole19-diff-paths', ['diff', '--name-only', BASE, CANDIDATE]).splitlines()) == allow
assert set(git('repair-diff-paths', ['diff', '--name-only', manifest['repair_base'], CANDIDATE]).splitlines()) == set(manifest['changed_from_repair_base'])
tree_lines = git('source-blob-bindings', ['ls-tree', '-r', '--full-tree', CANDIDATE, '--'] + sorted(allow)).splitlines()
blobs = {line.split('\t', 1)[1]: line.split('\t', 1)[0].split()[2] for line in tree_lines}
assert len(blobs) == 19
for item in manifest['source_files']:
    path = Path(item['path'])
    assert path.resolve().is_relative_to(candidate_wt.resolve())
    data = path.read_bytes()
    assert len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256']
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert blob == item['git_blob'] == blobs[item['relative_path']]
assert set(item['relative_path'] for item in manifest['source_files']) == allow
verified = {}


def verify_refs(value):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str) and isinstance(value.get('bytes'), int):
            p = Path(value['path']).resolve()
            assert p.is_relative_to(R.resolve())
            key = str(p)
            expected = (value['sha256'], value['bytes'])
            if key in verified:
                assert verified[key] == expected
            else:
                data = p.read_bytes()
                assert (hashlib.sha256(data).hexdigest(), len(data)) == expected
                verified[key] = expected
        for v in value.values():
            verify_refs(v)
    elif isinstance(value, list):
        for v in value:
            verify_refs(v)


verify_refs(manifest)
index = read(Path(manifest['command_capture_index']['path']))
verify_refs(index)
assert len(index['captures']) == 275
ledger = read(Path(manifest['failure_ledger']['path']))
assert len(ledger['raw_nonzero_command_captures']) == 63
capture_by_dir = {str(Path(v['directory']).resolve()): v for v in index['captures']}
for item in ledger['raw_nonzero_command_captures']:
    captured = capture_by_dir[str(Path(item['capture']).resolve())]
    assert captured['native_exit'] == item['native_exit'] and captured['stderr']['sha256'] == item['stderr_sha256']
patch = Path(manifest['whole19_patch']['path']).read_bytes()
patch_paths = set(re.findall(rb'^diff --git a/(.*?) b/', patch, re.MULTILINE))
assert {p.decode('utf8') for p in patch_paths} == allow
guards = read(E / 'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']
for item in guards:
    assert ref(R / item['path'])['sha256'] == item['sha256']
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O / 'source-artifact-verification.json', {'at': now, 'manifest': ref(F / 'manifest.json'), 'nested_unique_file_refs_verified': len(verified), 'command_captures': len(index['captures']), 'native_nonzero_unclassified_records': 63, 'source_paths_and_candidate_blobs': 19, 'whole_patch_path_count': 19, 'fixture_case_count': len(manifest['fixture_cases']), 'protected_source_unchanged': True, 'semantic_acceptance': False, 'actual_authority': False})
scope = {
    'schema': 'researchos.owned-core-stop-source-r2-independent-review.v1', 'at': now,
    'owner': 'codex:/root/owned_core_stop_source_review', 'model': 'gpt-6-astra', 'reasoning_effort': 'high',
    'model_choice_reason': 'Independent security and architecture review of exact19 Windows native stop/SQLite/compiled operation grants and cross-phase durable authority',
    'candidate': CANDIDATE, 'candidate_tree': manifest['tree'], 'main_base': BASE, 'repair_base': manifest['repair_base'],
    'read_only_worktree': str(candidate_wt), 'source_allowlist': sorted(allow),
    'own_receipts': str(E / 'owned_core_stop_anchor_revision02_independent_review_codex/20261015-current-chat'),
    'own_temporary_root': str(R / '.local/owned-core-stop-r2-independent-review-20261015'),
    'inputs': [ref(F / 'manifest.json'), ref(B / 'continuation-cp508/owned-stop-anchor-revision02-source-scope.json'), ref(O / 'source-artifact-verification.json'), ref(S / 'fixture_e2e_r2.py'), ref(S / 'run_logged.py')],
    'requirements': [
        'Review complete19path diff from Main4f, including8 inherited56e paths, plus11path repair diff. CandidateRootFrozenNotAccepted status is not operation authority. Independently verify Source/blob/tree/patch/command/fixture lineage and frozen capture completeness. Main4f/current Core54076/Desktop69996/Ollama/original DB/oldf3Run/profiles/private authority/spec/Source25 untouched.',
        'Review complete CP508 mandatory SA-D01..05 and original S201..S216/SA01..15 intent. Acyclic real two-grant builds, preexisting operation-directory native pin and ACL; exact bound documents read/decoded through same retained deny-write/delete handles; ancestor/parent image/native identity lifetimes and alias/reparse/hardlink/race boundaries. A hash match cannot replace semantic review/scope/acceptance binding.',
        'Check strict argument/action and pure compiled-grant validation before any side effect, duplicate JSON/unknown/action fields/bounds, default/expired grant zero action, exact phase successor only, shared exclusive op lock, immutable preflight completion, durable STOP attempt/BEGIN/INTENT permanent consumption, no retry after any uncertain/torn state. Expired inspect reads immutable authorized outcome only without new lock/DB/process probes or writes.',
        'Review retained exact Core and parent native process handles/creation/image/SID/root and original-handle Wait numeric exit, finite wall+monotonic deadline at final intent/native call, zero native call if expiry between flush/call, at most one native terminate across concurrent phases/binaries/replay. Preserve consumed permission after expiry/failure. SQLite read-only fixed census catalogue, online backup/durable nonempty WAL rows, exclusive barrier/lease and postflight drift blocks maintenance; never infer closure from status text or returned synthetic bool.',
        'Original accepted proof classes remain strict. Historical fixture seven proof receipts are synthetic and do not establish actual original current-process/UNKNOWN Run proof. Do not weaken verifier-native Wait/isolation classes or add an operational substitute in this review. Readonly CP511 startup audit may conclude NOT_PROVABLE separately; current actual STOP remains unavailable regardless fixture Source verdict.',
        'Fresh focused checks proportional to review findings, including a fresh own-E real two-compiled-grant/nonempty SQLite CLI positive. May copy fixture_e2e_r2.py and run_logged.py into own E, record original and derived hashes/diff, replace only copied go_env temp/cache constants with unique own D paths; WORKTREE remains frozen f5 read-only. Build own fixture-r2.exe from frozen ops/owned_core_stop/fixture into own E. MODE positive and a small set of new targeted negatives needed for suspected gaps are allowed. No edits to author frozen files/candidate Source and no actual product/private signers/models. Do not rerun all old cases mechanically if no new concern.',
        'Manifest has275 captures,63 nonzero records uniformly tagged REVIEW_RAW_EXPECTED_DENY_OR_FAILURE and one initial capture-gap description. Root preserves these as mixed unclassified records, not63 product failures. Independently classify the63 raw native nonzero cases as expected denial vs implementation/test/tool error, separate three harness-correction summaries without duplicating underlying failures, and report any further missing/skipped/capture issues. Capture all own recipes BEFORE execution with raw stdout/stderr/native exit/relevantenv and failed attempts preserved.',
        'Use existing project Go1.27.1/Python3.14 and D task-owned GOTMPDIR/GOCACHE/TMP/TEMP. No dependency install, Git mutation, original process/DB probes, actor messages or original data operation. Do not retry previous policy-denied cleanup paths. Freeze review.md/review.json/diagnostic-audit.json/classified-author-nonzero.json/evidence-manifest.json including all evidence. Verdict LIMITED_SOURCE_ACCEPTED only if meaningful cuts support all required semantics; otherwise exact actionable findings and minimal repair. Formal increment0, all22open, no Main/package/actual acceptance.',
    ], 'formal_increment': 0, 'source_write_authority': False, 'actual_authority': False,
}
new(O / 'owned-core-stop-source-r2-independent-review-scope.json', scope)
old = list(cp['failure_counters'])
for i, item in enumerate(ledger['raw_nonzero_command_captures'], 1):
    origin = '20261015|owned-stop-r2-author-nonzero-record-' + str(i)
    assert not any(v.get('origin_key') == origin for v in old)
    cp['failure_counters'].append({'origin_key': origin, 'attempts': 1, 'status': 'AUTHOR_NONZERO_COMMAND_RECORD_EXPECTED_DENIAL_OR_FAILURE_UNCLASSIFIED', 'detail': {'capture': item['capture'], 'native_exit': item['native_exit'], 'author_classification': item['classification'], 'not_counted_as_product_failure_claim': True}, 'evidence_ref': ref(F / 'failure-ledger.json'), 'counter_reset': False})
cp['failure_counters'].append({'origin_key': '20261015|owned-stop-r2-initial-command-capture-gap', 'attempts': 1, 'status': 'AUTHOR_CAPTURE_GAP_PRESERVED', 'detail': ledger['capture_gap'], 'evidence_ref': ref(F / 'failure-ledger.json'), 'counter_reset': False})
assert cp['failure_counters'][:1645] == old and len(cp['failure_counters']) == 1709
resume = read(B / 'continuation-cp513/RESUME.current.json')
resume.update(schema='researchos.current-chat-resume.v92', at=now, checkpoint_revision=514, ownership_revision=300, failure_records_preserved=len(cp['failure_counters']), owned_stop_r2_candidate_ref=ref(F / 'manifest.json'), owned_stop_r2_artifact_verification_ref=ref(O / 'source-artifact-verification.json'), owned_stop_r2_independent_review_scope_ref=ref(O / 'owned-core-stop-source-r2-independent-review-scope.json'), active_source_cards=['CP512 B onlinefirstgate/drain/FAILEDprivateconsumer exact9 paths fromacceptedA-r2f48'])
resume['next_command'] = 'STOP-r2f5 frozen exact19 nowindependent review; B Source CP512 active. Readonly startup audit final pending NOT_PROVABLE historical native closure. Stop artifact19blobs/275captures/16caseRefs verified only resource provenance,63mixednonzero+initialgap preserved pending reviewclassification, no63productfailure claim. No SourceC/D/newproof/Main integration/actual authority. Main4f/protected9/dirty20/indexempty/originalCore+f3UNKNOWN unchanged. Formal0/42/all22open.'
new(O / 'RESUME.current.json', resume)
rr = ref(O / 'RESUME.current.json')
cp.update(revision=514, expected_previous_revision=513, updated_at=now, updated_by='codex:/root', next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp514=rr, owned_stop_r2_candidate_ref=ref(F / 'manifest.json'), owned_stop_r2_independent_review_scope_ref=ref(O / 'owned-core-stop-source-r2-independent-review-scope.json'))
cp['evidence_index'].append({'kind': 'STOP_R2_EXACT19_FROZEN_INDEPENDENT_SOURCE_REVIEW_REGISTERED', 'ref': rr, 'formal_increment': 0})
ow.update(revision=300, expected_previous_revision=299, updated_at=now, updated_by='codex:/root')
ow['special_paths']['owned_stop_r2_independent_review'] = {'owner': scope['owner'], 'mode': 'READ_ONLY_INDEPENDENT_SOURCE_REVIEW', 'state': 'REGISTERED', 'scope_ref': ref(O / 'owned-core-stop-source-r2-independent-review-scope.json'), 'write_scope': [scope['own_receipts'], scope['own_temporary_root']], 'source_write_authority': False, 'actual_authority': False}
for p, name in ((cp_p, 'checkpoint.before.raw.json'), (ow_p, 'ownership.before.raw.json'), (hp, 'handoff.before.raw.md')):
    (O / name).write_bytes(raw[p])
for p, data in raw.items():
    assert p.read_bytes() == data
replace(ow_p, raw[ow_p], (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode())
replace(cp_p, raw[cp_p], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode())
replace(hp, raw[hp], ('# Current verified continuation CP514\n\nRead `' + rr['path'] + '` first. STOP-r2f5 exact19 frozen and independent review registered; B is sole active Source card. Original maintenance unavailable; no actual authority. Formal0/42/all22open; preserved mixed records' + str(len(cp['failure_counters'])) + '.\n\n').encode() + raw[hp])
assert sp.read_bytes() == raw[sp]
print(json.dumps({'checkpoint': 514, 'ownership': 300, 'preserved_mixed_records': len(cp['failure_counters']), 'resume': rr, 'scope': ref(O / 'owned-core-stop-source-r2-independent-review-scope.json'), 'artifact_refs_verified': len(verified)}))
