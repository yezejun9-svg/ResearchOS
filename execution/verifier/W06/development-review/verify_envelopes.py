from pathlib import Path
import json,hashlib,datetime
root=Path(__file__).resolve().parents[4];out=Path(__file__).parent;base=root/'execution/receipts/W06/524048b0-de1b-402b-9da3-ba71d7c5cfe6'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
receipt=read(base/'receipt.json');manifest=read(base/'artifacts.json');catalog=read(root/'spec/v2.0/contracts/acceptance.json');preflight=read(base/'environment-before.json');frozen={c['id']:c for c in catalog['cases']};checked={}
def verify_ref(ref):
 path=ref.get('path',ref.get('reference'));expected=ref['sha256'].removeprefix('sha256:');assert sha(root/path)==expected,path;checked[path]=expected
assert receipt['artifact_manifest_hash']==sha(base/'artifacts.json')
for row in manifest:verify_ref(row)
body=dict(receipt);expected=body.pop('receipt_hash');actual='sha256:'+hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert actual==expected,(actual,expected)
assert receipt['input_manifest_hash']==sha(root/'spec/v2.0/PACKAGE_MANIFEST.json')
assert receipt['route_revision']==sha(root/'execution/route.json')
assert receipt['code_revision']=='98468b525d7b88e49d23d434a1d39fcdd403b725'
checks=[]
for case in ['A02','A03']:
 d=read(base/(case+'.json'));run=d['run_receipt'];vm=d['version_manifest'];rows=d['assertion_results'];assert d['global_evidence_id']=='GLOBAL_EVIDENCE_V1'
 assert run['case_id']==case and run['environment_mode']==frozen[case]['mode'];assert run['executor_identity']!=run['independent_verifier_identity']=='codex:/root/orchestration_verifier'
 assert vm['git_head']==receipt['code_revision'];assert vm['source_sha256']==preflight['source_sha256'];verify_ref(vm['preflight_reference'])
 assert vm['sampled_at']<run['started_at'];assert vm['model_runtime']['status']=='NOT_APPLICABLE' and vm['model_runtime']['reason'];assert vm['working_tree_clean']==False and vm['tracked_source_clean']==True
 for v in vm['policy_versions']:verify_ref(v)
 for path,h in vm['lock_files'].items():verify_ref({'path':path,'sha256':h})
 assert vm['rubric']['acceptance_sha256']==sha(root/'spec/v2.0/contracts/acceptance.json') and vm['task_gates_sha256']==sha(root/'spec/v2.0/contracts/tasks.json')
 supported=[]
 for command in d['command_receipt']:
  verify_ref(command);inv=read(root/command['reference'])
  for k in ['command_key','argv','cwd','environment_names','exit_code','stdout','stderr','registered_command_revision']:assert command[k]==inv[k],(case,k)
  verify_ref(command['stdout']);verify_ref(command['stderr'])
  stdout=read(root/command['stdout']['path']);inner=read(stdout['receipt']);supported.extend(inner['assertions'])
 byid={r['id']:r for r in frozen[case]['assertions']};assert [r['assertion_id'] for r in rows]==list(byid)
 mapping=[]
 for row in rows:
  rid=row['assertion_id'];assert row['expected']==byid[rid]['expected'] and row['status']=='PASS';assert row['actual']
  for v in row['raw_evidence']:verify_ref(v)
  for v in row['actual']:assert v in supported,(case,rid,v['assertion_id']);assert v['status']=='PASS'
  mapping.append({'assertion_id':rid,'supporting_ids':sorted(set(v['assertion_id'] for v in row['actual']))})
 for v in d['supplemental_assertions']:assert v in supported
 for v in d.get('historical_route_evidence',[]):verify_ref(v)
 assert d['acceptance_receipt']['reference']=='execution/verifier/W06/524048b0-de1b-402b-9da3-ba71d7c5cfe6.json'
 checks.append({'case_id':case,'mode':run['environment_mode'],'formal_ids':[r['assertion_id'] for r in rows],'mapping':mapping,'case_sha256':sha(base/(case+'.json'))})
result={'status':'PASS','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'executor_receipt_sha256':sha(base/'receipt.json'),'executor_receipt_jcs_hash':expected,'artifact_manifest_sha256':sha(base/'artifacts.json'),'artifact_count':len(manifest),'all_reference_hashes_checked':len(checked),'case_checks':checks,'checked_references':checked}
(out/'envelope-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='checked_references'},ensure_ascii=False,indent=2))
