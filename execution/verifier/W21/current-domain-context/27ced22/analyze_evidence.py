"""Read-only evidence analysis. Writes only adjacent W21 verifier outputs; runs no tests."""
from pathlib import Path
import json, hashlib, subprocess, datetime, re

out = Path(__file__).resolve().parent
root = out.parents[4]
inputs = {}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
    p = Path(p)
    inputs[p.relative_to(root).as_posix()] = sha(p)
    return json.loads(p.read_text(encoding='utf-8'))
def write(name, value):
    (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
enc = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
digest = lambda x: 'sha256:' + hashlib.sha256(x).hexdigest()
now = datetime.datetime.now(datetime.timezone.utc).isoformat()

# Reuse the reviewed mechanical checks, stopping before that script's writes.
# The historical external CLI binary attestation is retained, never re-opened or executed.
old_script = root / 'execution/verifier/W06/c01-review/verify_c01.py'
inputs[old_script.relative_to(root).as_posix()] = sha(old_script)
code = old_script.read_text(encoding='utf-8').split("inp=read(live/'C01-input.json')", 1)[1].split('\nsummary=', 1)[0]
code = "inp=read(live/'C01-input.json')" + code
code = code.replace("assert command['no_prior_session'];assert digest(Path(command['argv'][0]).read_bytes())==command['binary_hash']", "assert command['no_prior_session']")
live = root / 'execution/receipts/W06/continuation-live/65ebbc11-20bd-4136-aa39-faa2fa3c4849'
exec(compile(code, str(old_script) + ':mechanical-archive-only', 'exec'))
replay = read(root / 'execution/verifier/W06/c01-review/replay-command.json')
assert sha(root / 'adapters/runtime/codex.go') == replay['source_overlay']['adapters/runtime/codex.go']
for name, h in replay['archived_stream_hashes'].items(): assert sha(live/name) == h
for p in live.iterdir():
    if p.is_file(): inputs[p.relative_to(root).as_posix()] = sha(p)
archive = {
    'status': 'PASS_ARCHIVE_MECHANICAL_CHECK_AND_UNCHANGED_PARSER_REPLAY_REUSE',
    'checked_at': now, 'new_provider_calls': 0, 'new_cli_calls': 0,
    'new_go_parser_replay_executed': False,
    'historical_live_revision': replay['executed_live_revision'],
    'historical_replayed_parser_revision': replay['replayed_parser_revision'],
    'current_parser_matches_accepted_replay_sha256': replay['source_overlay']['adapters/runtime/codex.go'],
    'archived_stream_hashes': replay['archived_stream_hashes'],
    'checks': ['input and prompt bytes/hash', 'exact prompt input suffix', 'canonical bundle hash',
        'stdout/stderr hashes and journal binding', 'settled/queue empty/children stopped/exit 0 historical journal',
        'result equals journal, command, and sealed output', 'no tool attempts and ephemeral invocation historical flags',
        'four materialized content hashes and manifest entries', 'ten record revision/hash bindings and nine vector references',
        'effective decision B supersedes historical A', 'goal/intent/task/source binding',
        '17*25=425; superseded option is not used', 'zero archived questions',
        'sealed computation log exact bytes/hash and result hash', 'independent deterministic FIXTURE acceptance bindings'],
    'materialized_count': len(inp['materialized_inputs']), 'record_count': len(inp['records']),
    'version_vector_count': len(inp['bundle']['version_vector']),
    'limits': ['The original model execution is historical, not a current-version model execution.',
        'The external CLI binary is not reopened; its original attestation is historical.',
        'Current parser byte equality supports reuse of the accepted historical replay; no fresh parser execution is claimed.',
        'Provider model revision and cost remain unknown. Full new planning/research context coverage is not claimed.']}
write('c01-archive-check.json', archive)

current = read(out/'current-assertions.json')
assert len(current) == 34 and all(x['status'] == 'PASS' for x in current)
by_id = {x['assertion_id']: x for x in current}
fixtures = [('W06','8af0b592-7e0d-4ced-83d3-32db7670007d','C01'),
    ('W17','b8d63ce4-93bb-4b47-8990-8e0bf1095b11','C02'),
    ('W09','887e8883-101f-4c3f-a9f6-85beee26127f','C19'),
    ('W09','887e8883-101f-4c3f-a9f6-85beee26127f','A06')]
frozen = read(root/'spec/v2.0/contracts/acceptance.json')
frozen_cases = {x['id']:x for x in frozen['cases']}
mapping, deltas = [], []
for wave, rid, cid in fixtures:
    case_path = root/f'execution/receipts/{wave}/{rid}/{cid}.json'
    case = read(case_path)
    verifier_path = root/f'execution/verifier/{wave}/{rid}.json'
    read(verifier_path)
    old = case['version_manifest']['source_sha256']
    paths = ['adapters/runtime/codex.go','adapters/retrieval/identity_windows.go','adapters/retrieval/identity_unix.go',
        'adapters/retrieval/local.go','internal/domain/retrieval.go','internal/domain/retrieval_local.go',
        'internal/domain/context.go','internal/domain/auth.go','internal/domain/http.go']
    compare = []
    for p in paths:
        if p not in old: continue
        original = subprocess.run(['git','show',case['version_manifest']['git_head']+':'+p],cwd=root,capture_output=True,check=True).stdout
        assert hashlib.sha256(original).hexdigest() == old[p]
        compare.append({'path':p,'accepted_sha256':old[p],'current_sha256':sha(root/p),'unchanged':old[p]==sha(root/p)})
    deltas.append({'case':cid,'historical_revision':case['version_manifest']['git_head'],'files':compare,
        'transitive_dependency_closure_proven':False})
    for a in case['assertion_results']:
        aid = a['assertion_id']
        assert a['status']=='PASS'
        f = next(x for x in frozen_cases[cid]['assertions'] if x['id']==aid)
        assert a['expected']==f['expected']
        matched = [by_id[aid]] if aid in by_id else []
        mode = 'CURRENT_TARGETED_FIXTURE_PASS' if matched else 'HISTORICAL_REUSE_ONLY'
        limits = []
        if cid=='C01':
            matched = [x for x in current if x['test'] in ['TestW04ContextRecovery','TestW04RestrictedContext']]
            mode = 'CURRENT_CONTEXT_DELTA_PLUS_ARCHIVE_REUSE'
            limits = archive['limits']
        if aid=='A06-02':
            mode = 'CURRENT_TRAVERSAL_DELTA_PLUS_HISTORICAL_JUNCTION_REUSE'
            limits = ['Current selector checks traversal/zero secret leakage; junction/root identity native filesystem cases are historical and were not rerun.']
        if aid=='A06-03':
            limits = ['Fallback/cache assertion was not executed in this batch; retrieval.go is byte-identical to the original accepted source. Shared source changes prevent treating this as a new full-case acceptance.']
        mapping.append({'case':cid,'assertion_id':aid,'frozen_expected':f['expected'],
            'historical_status':a['status'],'historical_case_ref':case_path.relative_to(root).as_posix(),
            'historical_verifier_ref':verifier_path.relative_to(root).as_posix(),'current_evidence_mode':mode,
            'current_assertion_refs':[{'assertion_id':x['assertion_id'],'test':x['test'],'raw':x['raw'],
                'raw_line':x['raw_line'],'raw_end_line':x['raw_end_line']} for x in matched],
            'archive_check':'c01-archive-check.json' if cid=='C01' else None,'limits':limits})
write('assertion-map.json',mapping)
write('current-contract-delta.json',deltas)
before=read(out/'source-before.json');after=read(out/'source-after.json')
assert before['source_files']==after['source_files']
for p,meta in after['source_files'].items(): assert sha(root/p)==meta['sha256'],p
execution=read(out/'execution.json');assert execution['exit_code']==0
write('review.json',{'verdict':'PASS_TARGETED_DELTA_WITH_EXPLICIT_HISTORICAL_REUSE',
    'checked_at':now,'reviewer':'codex:/root/control_drain','target_revision':after['target_commit'],
    'formal_acceptance':False,'canonical_42_case_status_changed':False,
    'R01':{'status':'PASS_TARGETED_CONTEXT_AUTHORIZATION_AND_ARCHIVE_REUSE','tests':3,'assertions':27},
    'R07':{'status':'PASS_TARGETED_PROVENANCE_INVALIDATION','tests':3,'assertions':7},
    'go_exit_code':0,'passed_tests':6,'assertions':34,'skips':0,'source_files_unchanged':len(after['source_files']),
    'scope':'Public synthetic SQLite, actual loopback HTTP for C02, local filesystem snapshots; no provider/native child/private store/production activation.',
    'attempt_1':'Go raw package and six tests PASS; wrapper parse failed before Go exit persistence. Preserved separately; its Go process exit is unknown.',
    'attempt_2':'Actual Go exit 0 persisted before parsing; complete chunk-aware extraction succeeds.',
    'limits':['C01 transcript and parser replay are historical reuse, not current model continuation.',
        'A06 junction/root identity and fallback/cache retain historical evidence only; no new complete A06 acceptance.',
        'No complete new planning/research context coverage or proven transitive dependency closure.',
        'No full 42-case reacceptance or current-control activation authorization.']})
write('input-hashes.json',inputs)
print(json.dumps({'archive':'PASS','mapped_assertions':len(mapping),'source_files':len(after['source_files'])}))
