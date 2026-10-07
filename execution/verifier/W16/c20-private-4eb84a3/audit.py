"""Read existing C20 fixtures only; never execute a candidate or export private rows."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SOURCE = '4eb84a3a4ae41ae9acd6d9bc21582c478fa855c6'
RAW = '0503ede60acc606caef4f645a6e83d038cb3ab83'
PREFIX = 'execution/receipts/W16/c20-private/f10ca600-0adb-4775-9091-da5c2752f85a/'
PRIVATE = Path('D:/作品集/ResearchOS/verifier-evidence/W16/c20/f10ca600-0adb-4775-9091-da5c2752f85a')

def digest(b):
    return 'sha256:' + hashlib.sha256(b).hexdigest()

def encode(obj, sort=False):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'), sort_keys=sort).encode()

def git(commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)

checks = {}
def check(name, value):
    checks[name] = bool(value)

public = {}
paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', RAW, '--', PREFIX], cwd=ROOT).decode().splitlines()
for path in paths:
    raw = git(RAW, path)
    public[path[len(PREFIX):]] = raw
before = json.loads(public['before.json'])
report = json.loads(public['report.json'])
locator = json.loads(next(v for k, v in public.items() if k.endswith('-C20-protected-locator.json')))
benefit = json.loads(next(v for k, v in public.items() if k.endswith('-C20-private-benefit.json')))
record = json.loads(public['c87eaeeec916408aec925607f5a6fb34-REGRESSION.json'])
source_hashes = {k: digest(git(SOURCE, k.replace('\\', '/'))) == v for k, v in before['version_manifest']['files'].items()}
check('all_frozen_source_hashes', all(source_hashes.values()))
check('raw_source_commit', before['version_manifest']['code_commit'] == SOURCE)
check('all_public_report_hashes', all(digest(public[k]) == v for k, v in report['hashes'].items()))
check('fixture_scope_retained', report['status'] == 'PARTIAL' and report['scope'] == 'W16_G02_FIXTURE_ONLY' and report['independent_acceptance'] == 'NONE')
lines = public['stdout.txt'].decode().splitlines()
check('seven_assertions_bound_to_raw_lines', len(report['assertions']) == 7 and all(json.loads(lines[a['raw']['line']-1].split(' ', 1)[1]) == {k:v for k,v in a.items() if k != 'raw'} for a in report['assertions']))
check('five_author_test_passes_no_skip', sum(x.startswith('--- PASS:') for x in lines) == 5 and not any('--- FAIL:' in x or '--- SKIP:' in x for x in lines))
gainlog = public['objective-gain-stdout.txt'].decode()
check('objective_gain_cases_in_existing_log', all('--- PASS: TestObjectiveHoldoutGain/' + name in gainlog for name in ['newly-correct-with-stable-win-preserved', 'score-only-inflation', 'new-win-with-regression']))

private_data = {}
descriptors = []
descriptor_hashes = []
for path in PRIVATE.glob('*.json'):
    desc_raw = path.read_bytes()
    desc = json.loads(desc_raw)
    raw = path.with_suffix('.bin').read_bytes()
    desc_ok = digest(raw) == desc['hash'] and len(raw) == desc['size'] and desc['measurement_mode'] == 'FIXTURE' and desc['media_type'] == 'application/json'
    descriptors.append((desc, desc_ok))
    descriptor_hashes.append(digest(desc_raw))
    private_data[digest(raw)] = (raw, json.loads(raw))
check('three_protected_blobs_descriptors_valid', len(descriptors) == 3 and all(ok for _, ok in descriptors))
check('protected_project_bound', all(d['project'] == record['candidate']['project_id'] for d, _ in descriptors))
check('protected_locator_matches_existing_directory', Path(locator['protected_store']).resolve() == PRIVATE.resolve())
inputs_raw, inputs = private_data[locator['input_sha256']]
labels_raw, labels = private_data[locator['label_sha256']]
proof_raw, proof = private_data[locator['dual_rubric_raw_proof_sha256']]
check('stored_input_label_serialization', encode(inputs) == inputs_raw and encode(labels) == labels_raw)
check('input_label_proof_version', inputs['revision'] == labels['revision'] == proof['revision'] == 'private-c20-fixture-v1' and proof['model_revision'] == 'NONE')
check('proof_input_label_binding', proof['inputs_hash'] == digest(inputs_raw) and proof['labels_hash'] == digest(labels_raw))
x = record['candidate']
plan = {k:x[k] for k in ['scope','candidate_artifact_ref','stable_artifact_ref','isolated_workspace_id','baseline_suite_ref','baseline_policy_hash','changed_paths_manifest_ref','experiment_id','migration_plan_ref','rollback_plan_ref','independent_supervisor_id']}
check('proof_plan_binding', proof['plan_hash'] == digest(encode(plan, True)) == record['execution']['plan_hash'])
check('proof_build_binding', proof['stable_hash'] == locator['stable_build_sha256'] == x['stable_artifact_ref']['content_hash'] == record['execution']['baseline_hash'] and proof['candidate_hash'] == locator['candidate_build_sha256'] == x['candidate_artifact_ref']['content_hash'] == record['execution']['candidate_hash'])
check('proof_suite_policy_binding', proof['public_suite_hash'] == record['execution']['suite_hash'] and proof['policy_hash'] == record['execution']['policy_hash'] == x['baseline_policy_hash'])
check('proof_public_observation_binding', digest(proof_raw) == record['execution']['holdout_proof_hash'] == benefit['private_proof_sha256'])
cases = inputs['cases']
check('private_case_count_identity', len(cases) == len(labels['labels']) == len(proof['pairs']) == 2 and len({c['id'] for c in cases}) == 2 and all(c['id'] not in ['existing-add','negative-input','instruction-injection','optional-product'] for c in cases))
check('labels_independently_recomputed', all(c['operation'] == 'add' and not c['text'] and c['id'] == l['id'] and l['expected'] == c['a'] + c['b'] for c,l in zip(cases, labels['labels'])))
baseline_correct = candidate_correct = 0
equal = inflation = True
sids = set()
per_invocation = []
for c,l,pair in zip(cases, labels['labels'], proof['pairs']):
    responses = []
    for side, build in [('baseline', proof['stable_hash']), ('candidate', proof['candidate_hash'])]:
        inv = pair[side]
        r = inv['receipt']
        request = inv['request']
        row = json.loads(inv['raw'])
        ok = inv['build_hash'] == build and request['phase'] == 'REGRESSION' and request['cases'] == [c] and not request['protected_paths']
        ok = ok and inv['input_hash'] == digest(encode(request)) and inv['raw_hash'] == digest(inv['raw'].encode()) and base64.b64decode(r['stdout']) == inv['raw'].encode()
        ok = ok and r['exit_code'] == 0 and r['children_stopped'] and not r['timed_out'] and not r['capabilities'] and r['pid'] > 0 and bool(r['appcontainer_sid'])
        ok = ok and len(row) == 1 and row[0]['id'] == c['id'] and bool(row[0]['rubric']) and set(row[0]) == {'id','value','self_score','rubric','write_denied'}
        per_invocation.append(bool(ok))
        sids.add(r['appcontainer_sid'])
        responses.append(row[0])
    a,b = responses
    baseline_correct += a['value'] == l['expected']
    candidate_correct += b['value'] == l['expected']
    equal = equal and a['value'] == b['value']
    inflation = inflation and b['self_score'] > a['self_score'] and b['rubric'] != a['rubric']
check('four_existing_invocations_bound', len(per_invocation) == 4 and all(per_invocation))
check('four_distinct_appcontainer_sids', len(sids) == 4)
check('same_question_for_both_builds', all(p['baseline']['input_hash'] == p['candidate']['input_hash'] for p in proof['pairs']))
check('objective_outcomes_equal_scores_inflated', baseline_correct == candidate_correct == 2 and equal and inflation)
summary = record['execution']['holdout_summary']
check('summary_matches_recomputed_outcomes', summary == {'revision':'private-c20-fixture-v1','measurement_mode':'FIXTURE','model_revision':'NONE','total':2,'baseline_correct':2,'candidate_correct':2,'outcomes_equal':True,'gain':False})
check('benefit_and_closed_state_match', benefit['baseline_correct'] == baseline_correct and benefit['candidate_correct'] == candidate_correct and not benefit['outcome_gain'] and benefit['experiment_outcome'] == 'NO_IMPROVEMENT' and not benefit['project_closed'] and record['experiment']['outcome'] == 'NO_IMPROVEMENT')
public_bytes = b'\n'.join(public.values())
check('no_private_case_ids_or_blob_tickets_in_public_receipts', all(c['id'].encode() not in public_bytes for c in cases) and all(d['ticket'].encode() not in public_bytes for d,_ in descriptors))

audit = {'verdict':'PASS_READONLY_EXISTING_FIXTURE_EVIDENCE' if all(checks.values()) else 'NEEDS_REVIEW', 'source_commit':SOURCE, 'raw_commit':RAW, 'source_hash_count':len(source_hashes), 'public_file_count':len(public), 'protected_blob_count':len(descriptors), 'private_descriptor_hashes':sorted(descriptor_hashes), 'protected_hashes':{k:locator[k] for k in ['input_sha256','label_sha256','dual_rubric_raw_proof_sha256']}, 'checks':checks, 'aggregate':{'cases':2,'baseline_correct':baseline_correct,'candidate_correct':candidate_correct,'outcomes_equal':equal,'scores_increased':inflation,'objective_gain':False}, 'limits':['No new Go/native/adversarial execution.', 'Existing executable byte hashes are cross-bound, not rehashed from retained binaries.', 'No LIVE, formal private holdout, global evidence or production promotion acceptance.']}
(OUT/'audit.json').write_text(json.dumps(audit, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'verdict':audit['verdict'],'checks':len(checks),'failed':[k for k,v in checks.items() if not v],'source_hash_count':len(source_hashes),'public_file_count':len(public)}))
