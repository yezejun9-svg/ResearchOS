"""Root registration of one actual ordinary-GUI request; never execute it."""
import argparse
import copy
import datetime
import hashlib
import importlib.util
import json
import os
import pathlib
import sqlite3
import subprocess

ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT = pathlib.Path(__file__).parent
OBSERVER = ROOT / 'execution/v2.4/receipts/W05/W05-99/normal_qualification_actual_observer_v3_codex/20261012-current-chat/observe.py'
CPBASE = ROOT / 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def ref(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(raw), 'bytes': len(raw)}

def new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def replace(path, before, value):
    assert path.read_bytes() == before
    pending = path.with_name(path.name + '.request-registration.pending')
    with pending.open('xb') as stream:
        stream.write(value)
    assert path.read_bytes() == before
    os.replace(pending, path)

parser = argparse.ArgumentParser()
parser.add_argument('--request-id', required=True)
parser.add_argument('--expected-checkpoint', type=int, required=True)
parser.add_argument('--package-review', required=True)
parser.add_argument('--static-plan', required=True)
args = parser.parse_args()
spec = importlib.util.spec_from_file_location('approved_observer_v3', OBSERVER)
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)
observation = observer.observe(args.request_id)
request = observation['original_request']
assert not observation['consume_rows']
assert all(count == 0 for count in observation['counts'].values())
assert request['model_config_ref'] == 'mc-079c6ca85595aaac2dd17c2d0ed77b93'
assert request['authorize_purpose'] == 'mu_turn' and request['purpose_seconds'] == 600
assert observation['original_request_seconds_remaining_at_observation'] > 20
baseline = json.loads((OUT / '02-normal-session-baseline.observed.json').read_text(encoding='utf-8'))
assert observation['session'] == baseline['session'], 'SESSION_CHANGED_AFTER_BASELINE'
session = observation['session'][0]
assert datetime.datetime.fromisoformat(session['lease_expires_at'].replace('Z', '+00:00')) > datetime.datetime.now(datetime.timezone.utc)
assert session['sealed_at'] is None and session['archived_at'] is None
with sqlite3.connect(observer.DATABASE.as_uri() + '?mode=ro', uri=True) as db:
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    db.execute('BEGIN')
    run = db.execute('SELECT run_id FROM client_sessions WHERE id=? AND project_id=?', (observer.SESSION, observer.PROJECT)).fetchone()[0]
    assert not run
    witness = {'id': session['id'], 'project': session['project_id'], 'revision': session['revision'], 'writer_epoch': session['writer_epoch'], 'writer': session['writer_client_id'], 'run': run or ''}
    canonical = json.dumps(witness, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    assert 'sha256:' + digest(canonical) == request['session_hash']
    config = dict(db.execute('SELECT model_config_ref,owner_host_ref,principal,config_revision,canonical_config_json,config_hash,created_at FROM host_model_configurations WHERE model_config_ref=?', (request['model_config_ref'],)).fetchone())
    config_raw = config.pop('canonical_config_json')
    config_raw = config_raw.encode('utf-8') if isinstance(config_raw, str) else config_raw
    assert 'sha256:' + digest(config_raw) == config['config_hash'] == request['configuration_hash']
    assert config['owner_host_ref'] == request['owner_host'] and config['principal'] == request['owner_principal']
    config['canonical_config_bytes'] = len(config_raw)
    config['canonical_config_raw_sha256'] = digest(config_raw)
    payload = json.loads(config_raw)
    config['selected_nonsecret_configuration'] = {key: payload.get(key) for key in ['provider', 'model_id', 'base_url', 'api', 'revision']}
    db.execute('ROLLBACK')
planrow = [row for row in observation['plans'] if row['runtime'] == request['runtime_id'] and row['task'] == request['task_id']]
assert len(planrow) == 1 and planrow[0]['plan_hash'] == request['plan_hash']
plan = json.loads(planrow[0]['plan'])
assert 'sha256:' + digest(json.dumps(plan['profile_ref'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')) == request['profile_hash']
assert plan['model_qualification']['max_calls'] == 1
assert json.loads(observation['task'][0]['body'])['status'] == 'DRAFT'
observation['additional_readonly_binding'] = {'session_witness': witness, 'session_hash_validated': True, 'configuration_metadata': config, 'configuration_hash_validated': True, 'plan_profile_hash_validated': True, 'api_requests': 0, 'mutations': 0}
new(OUT / '03-original-prepared-confirmation.observed.json', observation)
cp_path = ROOT / 'execution/v2.4/checkpoint.json'
ow_path = ROOT / 'execution/v2.4/path_ownership.json'
hand_path = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
state_path = ROOT / 'execution/v2.4/step_state.json'
original = {path: path.read_bytes() for path in [cp_path, ow_path, hand_path, state_path]}
cp = json.loads(original[cp_path].decode('utf-8-sig'))
ow = json.loads(original[ow_path].decode('utf-8-sig'))
assert cp['revision'] == args.expected_checkpoint
next_cp = cp['revision'] + 1
next_ow = ow['revision'] + 1
CPDIR = CPBASE / ('continuation-cp' + str(next_cp))
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == cp['head'] == 'c465d1356480d6e6a90da84656724f9fc02b31c7'
assert digest((ROOT / 'execution/project_identity.json').read_bytes()) == '03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'
assert digest((ROOT / '.git/config').read_bytes()) == '1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
protected = json.loads((ROOT / 'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json').read_text(encoding='utf-8-sig'))
for member in protected['protected_source']:
    assert digest((ROOT / member['path']).read_bytes()) == member['sha256']
CPDIR.mkdir(exist_ok=False)
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
scope = {'schema': 'researchos.root-concrete-original-qualification-scope/1', 'at': now,
    'owner': 'codex:/root', 'checkpoint_revision': next_cp, 'request': request,
    'request_hash': observation['original_request_canonical_digest'],
    'request_evidence': ref(OUT / '03-original-prepared-confirmation.observed.json'),
    'baseline_ref': ref(OUT / '02-normal-session-baseline.observed.json'), 'launch_ref': ref(OUT / 'launch.json'),
    'static_plan_ref': ref(pathlib.Path(args.static_plan)), 'package_review_ref': ref(pathlib.Path(args.package_review)),
    'bounds': {'MODEL_max': 1, 'TOOL_max': 0, 'money_basis': 'UNKNOWN', 'money_amount': None, 'original_ref_only': True, 'purpose': 'mu_turn', 'seconds': 600},
    'allowed_action': 'same original request sole normal GUI explicit Chromium confirmation before expires_at; then original STATUS/read-only evidence only',
    'consumed_or_uncertain_retry_forbidden': True, 'Run_epoch_prompt': 'ONLY_ORIGINAL_PRODUCT_CLAIM_NO_PREALLOCATION',
    'ordinary_task_or_new_coding_ref_allowed': False, 'formal_increment': 0}
new(CPDIR / 'original-request-confirm-scope.json', scope)
failures = copy.deepcopy(cp['failure_counters'])
resume = {'schema':'researchos.current-chat-resume.v38','at':now,'checkpoint_revision':next_cp,
    'ownership_revision':next_ow,'head':cp['head'],'project_id':cp['project_id'],'current_step_id':'W05-99',
    'goal_status':'ACTIVE','accepted_formal_cases':0,'required_formal_cases':42,'required_parent_tasks':22,
    'failure_records_preserved':len(failures),'original_request_confirm_scope_ref':ref(CPDIR / 'original-request-confirm-scope.json'),
    'normal_session':'REACQUIRED_CURRENT_WRITER_PREPARED_UNCONSUMED_BOUND','phone_ready':False,
    'next_command':'Root sole normal GUI original-request CONFIRM before expiry then STATUS only; preserve all 22/42 requirements.'}
new(CPDIR / 'RESUME.current.json', resume)
resume_ref = ref(CPDIR / 'RESUME.current.json')
cp.update(revision=next_cp, expected_previous_revision=args.expected_checkpoint, updated_at=now, updated_by='codex:/root', next_command=resume['next_command'])
cp['work_in_progress'].update({'current_chat_continuation_cp'+str(next_cp):resume_ref,'original_request_confirm_scope_ref':resume['original_request_confirm_scope_ref'],'normal_qualification_prepare_status':resume['normal_session']})
cp['evidence_index'].append({'kind':'NORMAL_ORIGINAL_REQUEST_PREPARED_BOUND_SCOPE','ref':resume_ref,'formal_increment':0})
ow.update(revision=next_ow,expected_previous_revision=next_ow-1,updated_at=now,updated_by='codex:/root')
ow['special_paths']['normal_original_request_sole_confirmation']={'owner':'codex:/root','ref':resume['original_request_confirm_scope_ref'],'prior_scopes_and_owners_unchanged':True}
for path,name in [(cp_path,'checkpoint.before.raw.json'),(ow_path,'ownership.before.raw.json'),(hand_path,'handoff.before.raw.md')]:
    with (CPDIR/name).open('xb') as stream: stream.write(original[path])
assert datetime.datetime.fromisoformat(request['expires_at'].replace('Z','+00:00')) > datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(seconds=10)
assert cp['failure_counters']==failures
for path,raw in original.items(): assert path.read_bytes()==raw
replace(ow_path,original[ow_path],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode())
replace(cp_path,original[cp_path],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode())
prefix = '# Current verified continuation CP'+str(next_cp)+'\n\nRead `'+resume_ref['path']+'` first. Original unconsumed request bound, sole normal GUI confirmation before expiry; MODEL1 TOOL0 UNKNOWN/null. Formal0/42 all22 open.\n\n'
replace(hand_path,original[hand_path],prefix.encode()+original[hand_path])
assert state_path.read_bytes()==original[state_path]
print(json.dumps({'checkpoint_revision':next_cp,'ownership_revision':next_ow,'request_id':args.request_id,'request_hash':scope['request_hash'],'expires_at':request['expires_at'],'failures':len(failures),'formal_increment':0}))
