"""Read-only independent evidence verification; no provider/network calls."""
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[7]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'execution/v2.4/receipts/W05/W05-99/local_model_product_live_codex/20261012-current-chat'
WT = ROOT / '.local/worktrees/w05-local-product-live-20261012'
HEAD = '292ad860f9e76cf2795d5a3010da1d114d01ff56'
checks = []
def check(name, value):
    checks.append({'check': name, 'passed': bool(value)})
def digest(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()
def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'), sort_keys=True).encode()
def read(name):
    return json.loads((SOURCE / name).read_text(encoding='utf-8-sig'))
def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

manifest = read('probe_manifest.json')
check('frozen_manifest_sha256', digest((SOURCE/'probe_manifest.json').read_bytes()) == 'sha256:2093394e61c0a42c11848a69952826dd14945fbc7fee776bbe7718b814348175')
for entry in manifest['files']:
    raw = (SOURCE/entry['file']).read_bytes()
    check('member:'+entry['file'], len(raw)==entry['bytes'] and digest(raw)=='sha256:'+entry['sha256'])
fact, request, result, obs, run = [read(n) for n in ['effect_fact.json','model_request.json','worker_result.json','runtime_observation.json','run.json']]
frames = [json.loads(line) for line in (SOURCE/'worker_stdout.ndjson').read_text().splitlines()]
response = (SOURCE/'model_response.sse').read_bytes()
check('effect_request_body_matches_worker_frame', frames[1]['payload']['body']==request)
check('three_worker_frames_one_model_zero_tools', [f['sequence'] for f in frames]==[1,2,3] and frames[2]['payload']=={'model_calls':1,'tool_calls':0})
check('response_exact_bytes_and_digest', fact['receipt']['payload']['body'].encode()==response and digest(response)==fact['provider_response_hash']==manifest['provider_response_hash'])
check('shared_project_run_dispatch', fact['project_id']==run['project_id']==manifest['project_id'] and fact['run_id']==run['id']==result['run_id']==obs['spec']['run_id']==manifest['run_id'] and fact['dispatch_key']==obs['dispatch_key']==run['external_run_id']==manifest['dispatch_key'])
check('native_observation_log_object_equal', obs==read('log_artifact.json'))
check('native_observation_raw_files_hashes', obs['stdout_hash']==digest((SOURCE/'worker_stdout.ndjson').read_bytes()) and obs['stderr_hash']==digest((SOURCE/'worker_stderr.raw').read_bytes()) and obs['artifacts'][0]['content_hash']==digest((SOURCE/'worker_result.json').read_bytes()))
check('native_settlement_flags', obs['state']==run['status']=='SETTLED' and obs['exit_code']==run['exit_code']==0 and all(obs[k] is True for k in ['children_stopped','cleanup_complete','queue_empty','streams_drained']) and obs['protocol']=={'acknowledged':3,'frames':3,'settled':True})
chunks = [json.loads(line[6:]) for line in response.decode().splitlines() if line.startswith('data: ') and line!='data: [DONE]']
text = ''.join(c.get('delta',{}).get('content','') for p in chunks for c in p.get('choices',[]))
check('SSE_answer_and_usage_match_result', text==result['messages'][-1]['content'][0]['text']=='I received this task.' and chunks[-1]['usage']=={'prompt_tokens':1402,'completion_tokens':6,'total_tokens':1408})
check('actual_cost_remains_unknown', result['actual_cost'] is None and fact['receipt']['actual_cost'] is None and result['sdk_cost_is_placeholder'] is True)
check('local_credential_free_manifest', manifest['credential_ref'] is None and manifest['provider_authorization_header'] is None and obs['spec']['credential_revision']=='none')

db_summary = {}
for suffix in ['', '-v2']:
    root = WT/'.local'/('w05-local-model-data'+suffix)
    db = sqlite3.connect((root/'researchos.sqlite').resolve().as_uri()+'?mode=ro', uri=True)
    counts = dict(db.execute('select kind,count(*) from domain_objects group by kind'))
    effects = [json.loads(row[0]) for row in db.execute('select body from resource_effects order by sequence')]
    registrations = [json.loads(row[0]) for row in db.execute("select body from domain_objects where kind='RuntimeRegistration'")]
    db_summary[suffix or 'v1'] = {'domain_object_counts':counts,'effect_states':[e['state'] for e in effects], 'registrations':[{k:r.get(k) for k in ['id','status','credential_ref','qualification_ids']} for r in registrations]}
    check('no_acceptance_receipt:'+suffix, counts.get('AcceptanceReceipt',0)==0)
    check('no_qualified_runtime:'+suffix, all(r['status']=='REGISTERED' and not r['qualification_ids'] for r in registrations))
    if not suffix:
        check('v1_no_Run_no_effect', counts.get('Run',0)==0 and not effects)
    else:
        check('v2_single_run_no_UNKNOWN_retry', counts.get('Run',0)==1 and [e['state'] for e in effects]==['PREPARED','STARTED','CONFIRMED'])
        ledger = [json.loads(r[0]) for r in db.execute("select body from domain_objects where kind='BudgetLedgerEntry'")]
        reservation = next(x for x in ledger if x['id']==fact['reservation_id'])
        effect = effects[-1]
        cost = {'policy_id':reservation['policy_id'],'run_id':run['id'],'operation':'RESERVE','money':reservation['money'],'provider_request_id':effect['key'],'provider_event_id':'prepare/'+effect['key'],'reservation_id':None,'cost_basis':'UPPER_BOUND','occurred_at':run['created_at']}
        check('recomputed_request_hash_with_reserved_cost', digest(canonical([effect['payload'],cost]))==fact['request_hash'])
        check('DB_effect_payload_same_as_raw_frame', effect['payload']['payload']==frames[1]['payload'])
        check('model_reservation_not_released', reservation['money']=={'amount':'0.01','currency':'USD'} and not any(x['provider_request_id']==effect['key'] and x['operation'] in ['RELEASE','RECONCILE'] for x in ledger))
        save('request_hash_inputs.json', {'provenance':'Independent read-only extraction from retained v2 database; supplemental, outside original frozen package','request':effect['payload'],'reservation_input':cost})
        dispatch = db.execute('select manifest,manifest_hash,state,identity,observation_sequence from runtime_dispatches').fetchall()
        check('one_dispatch_bound_to_observation', len(dispatch)==1 and dispatch[0][1]==obs['manifest_hash'] and dispatch[0][2]=='SETTLED' and json.loads(dispatch[0][3])==obs['identity'] and dispatch[0][4]==7)
        admission = json.loads(dispatch[0][0])
        check('dispatch_manifest_canonical_hash', digest(canonical(admission))==obs['manifest_hash'])
        profile = admission['admission']['profile']
        staged = root/'runtime-dispatches'/manifest['dispatch_key']/'input'
        check('staged_program_and_bundle_frozen_hash', digest((staged/'worker.exe').read_bytes())==obs['spec']['build_hash'] and digest((staged/'mu-worker.mjs').read_bytes())==profile['bundle_hash'])
        check('profile_digest_no_model_credential', digest(canonical(profile))==obs['spec']['profile_hash'] and profile['credential_revision']=='none')
        db_summary['-v2']['program_hashes']={'worker_executable':obs['spec']['build_hash'],'mu_bundle':profile['bundle_hash']}
    db.close()
save('readonly_database_checks.json', db_summary)

check('candidate_head_matches_report', subprocess.check_output(['git','-C',str(WT),'rev-parse','HEAD'],text=True).strip()==HEAD)
production = {}
for name in ['internal/domain/runtime_model_windows.go','internal/domain/runtime_broker_windows.go','internal/domain/runtime_effect_wire_windows.go','internal/domain/runtime_model_verification.go','internal/domain/runtime_coordinator_windows.go','apps/control/main.go']:
    raw = (WT/name).read_bytes()
    pinned = subprocess.check_output(['git','-C',str(WT),'show',HEAD+':'+name])
    check('candidate_source:'+name, raw.replace(b'\r\n',b'\n')==pinned.replace(b'\r\n',b'\n'))
    production[name] = digest(raw)
with zipfile.ZipFile(SOURCE/'harness_source.zip') as archive:
    for name in archive.namelist():
        check('harness_zip_matches_retained_source:'+name, archive.read(name)==(WT/'.local/w05-local-model-harness'/name).read_bytes())
save('source_checks.json', {'head':HEAD,'production_source_hashes':production,'note':'Checks bind retained source, not a reproducible Go binary build attestation.'})
save('verification_results.json', {'scope':'READ_ONLY_STATIC_AND_RETAINED_LOCAL_EVIDENCE','model_calls_issued_by_reviewer':0,'checks':checks,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks)})
print(json.dumps({'checks':len(checks),'passed':sum(c['passed'] for c in checks),'failed':[c['check'] for c in checks if not c['passed']]},ensure_ascii=False))
