"""Read fresh delivery and native receipts; no product acceptance evaluation."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

out = Path(__file__).resolve().parent
repo = next(p for p in out.parents if (p / 'execution/project_identity.json').is_file())
prefix = 'execution/v2.4/receipts/W07/W07-99/'
proof_path = prefix + 'source_executor_codex/run-c495292dee2d4e4fba7bb11a06979907/proof.json'
native_path = prefix + 'integration_codex/native-runs/20261006T094133Z-84f33c70d7/result.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p): return {'path':p.relative_to(repo).as_posix(), 'sha256':sha(p)}
proof = read(repo/proof_path)
native = read(repo/native_path)
checks = []
for r in native['registered_commands']:
    p = repo/r['receipt_ref']['path']
    row = read(p)
    checks.append({'id':r['id'],'receipt_ref':ref(p),'reference_hash_matches':sha(p)==r['receipt_ref']['sha256'],
        'status':row['status'],'exit_code':row['exit_code'],'child_exit_code':row['child_exit_code'],
        'invocation_id':row['invocation_id'],'selectors':row['selectors'],
        'raw_hash_matches':{k:sha(repo/row[k]['path'])==row[k]['sha256'] for k in ['stdout','stderr']}})
before = read(repo/proof['source_before_ref']['path'])
after = read(repo/proof['source_after_ref']['path'])
drift = [name for name, digest in before.items() if not (repo/name).is_file() or sha(repo/name)!=digest.removeprefix('sha256:')]
state = read(repo/'execution/v2.4/step_state.json')
result = {'schema':'researchos.w07.preflight-fresh-arrival.v1','actor':'codex:/root/queue_upgrade_impl','observed_at':datetime.now(timezone.utc).isoformat(),
 'formal_acceptances':0,'product_qualification_runs':0,'live_invocations':0,
 'supersedes_only':'README.md final pending list fresh proof/native4 absence; historical snapshot remains unchanged',
 'proof_ref':ref(repo/proof_path),'matches_root_proof_sha':sha(repo/proof_path)=='fbd3f8ec8a241b011f99134f4100c2ff47b56def775eb9ddb6be3df0e83fa6b3',
 'native_result_ref':ref(repo/native_path),'matches_root_native_sha':sha(repo/native_path)=='e7be7b52ba09b2d85fde4514bf64f77cf4fd1eb056ab01c81cd45a4c302d7425',
 'native_receipt_checks':checks,'source_capture_paths':len(before),'capture_before_equals_after':before==after,'current_capture_drift':drift,
 'owner':next(r for r in state['steps'] if r['id']=='W07-99'),'state_ref':ref(repo/'execution/v2.4/step_state.json'),
 'remaining':['complete formal vector/context/GLOBAL4 with native receipt copies','independent full product review (not this preflight)',
 'actual reviewer-to-Root message carrying review+proof SHA','Root observation/issuance','canonical owner registration after actual review','current full derive and parent process'],
 'no_repeat_required':'Use delivered fresh proof/native receipts if full current qualification succeeds; do not repeat LIVE solely because old preflight list preceded delivery',
 'field_map_path_note':'frozen_baselines diagnostic refs use absolute filesystem paths; convert repository_copy.path to repository-relative slash path when forming context/vector refs',
 'snapshot_tool_check_note':'snapshot.py independently reads actual python/go/browser_act binaries and records actual_sha256; initial shell hash comparison was a no-op and is not qualification evidence',
 'artifacts':{name:ref(out/name) for name in ['README.md','field_map.json','snapshot.json','snapshot.command.json','snapshot.py']}}
(out/'fresh_arrival.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'FRESH_DELIVERY_READONLY_CHECKED','formal_acceptances':0,'native_receipts':len(checks),
 'source_capture_paths':len(before),'source_capture_drift_count':len(drift),'canonical_owner_status':result['owner']['status'],
 'fresh_arrival_sha256':sha(out/'fresh_arrival.json')},ensure_ascii=False))
assert result['matches_root_proof_sha'] and result['matches_root_native_sha']
assert before==after and not drift
assert all(r['reference_hash_matches'] and all(r['raw_hash_matches'].values()) and r['status']=='PASS' and r['exit_code']==r['child_exit_code']==0 for r in checks)
