"""Seal this independent read-only C20 review; no product execution."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
RUN='5402da3d-e835-42d6-8b5f-168b941158dc'
PACK=ROOT/'execution/receipts/W16'/RUN
DEST=ROOT/'execution/verifier/W16'/(RUN+'.json')

def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def relative(p):return p.relative_to(ROOT).as_posix()

summary=read(OUT/'global-audit-report.json')
private=read(OUT/'private-audit-report.json')
executor=read(PACK/'receipt.json')
case=read(PACK/'C20.json')
assert summary['status']=='PASS' and all(private['checks'].values())
assert executor['receipt_hash']==summary['executor_receipt_jcs_hash']

# Private data remains in memory. The output contains only aggregate checks.
directory=ROOT.parent/'verifier-evidence/W16/c20/b68d28b6-ed73-47a0-b15e-330b491abc04'
private_ids=[];tickets=[];sensitive_bodies=[]
for path in directory.glob('*.json'):
    descriptor=read(path);tickets.append(descriptor['ticket'].encode())
    body=path.with_suffix('.bin').read_bytes();obj=json.loads(body)
    if 'cases' in obj:
        private_ids.extend(c['id'].encode() for c in obj['cases']);sensitive_bodies.append(body)
    if 'labels' in obj:sensitive_bodies.append(body)
public_paths=[ROOT/x['path'] for x in read(PACK/'artifacts.json')['files']]+[PACK/'receipt.json']
public_paths += [p for p in OUT.iterdir() if p.is_file() and p.name not in ['evidence-index.json','privacy-check.json']]
public=b'\n'.join(p.read_bytes() for p in public_paths)
privacy={'status':'PASS','checked_public_files':len(public_paths),'private_case_count':len(private_ids),'protected_ticket_count':len(tickets),'private_case_ids_absent':all(x not in public for x in private_ids),'private_blob_tickets_absent':all(x not in public for x in tickets),'private_input_and_label_bodies_absent':all(x not in public for x in sensitive_bodies),'private_contents_exported':False}
assert all(privacy[k] for k in ['private_case_ids_absent','private_blob_tickets_absent','private_input_and_label_bodies_absent'])
save(OUT/'privacy-check.json',privacy)
index={'scope':'Independent complete C20 FIXTURE acceptance only','source_revision':summary['source_revision'],'executor_archive_commit':summary['archive_commit'],'executor_receipt_hash':executor['receipt_hash'],'files':{p.name:sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='evidence-index.json'}}
save(OUT/'evidence-index.json',index)
acceptance={
    'artifact_kind':'INDEPENDENT_LIMITED_CONSTRUCTION_ACCEPTANCE_WITH_OWNED_CASE_VERDICTS',
    'task_id':'W16','run_id':RUN,'project_id':executor['project_id'],
    'status':'PARTIAL_ACCEPTANCE','verdict':'PASS_IN_SCOPE','stage_accepted':False,
    'C20_accepted':True,'complete_C20_accepted':True,'whole_W16_accepted':False,'A16_accepted':False,
    'W16_G01_accepted':False,'W16_G03_accepted':False,'LIVE_qualified':False,
    'production_scheduler_upgrade_accepted':False,'independent_OS_service_accepted':False,'upstream_dependencies_cleared':False,
    'scope':'Complete frozen C20 case and all evidence requirements in FIXTURE mode only. Prior C09/C10/C12 and W16-G02 decisions remain unchanged.',
    'executor_identity':'codex:/root','verifier_identity':'codex:/root/evolution_verifier',
    'independence_basis':'Verifier did not implement the product, execute formal commands or assemble executor evidence. Independently reviewed frozen source, reconciled all three dispatcher chains and GLOBAL mappings, verified hashes, and recomputed public and protected raw objective results with separate read-only scripts. Shared OS-user agent labels are not treated as a protected isolation boundary.',
    'executed_code_revision':summary['source_revision'],'executor_archive_commit':summary['archive_commit'],
    'executor_receipt_reference':relative(PACK/'receipt.json'),'executor_receipt_sha256':sha(PACK/'receipt.json'),'executor_receipt_jcs_hash':executor['receipt_hash'],
    'artifact_manifest_reference':relative(PACK/'artifacts.json'),'artifact_manifest_sha256':sha(PACK/'artifacts.json'),'artifact_count_verified':summary['manifest_files'],
    'acceptance_baseline_reference':'spec/v2.0/contracts/acceptance.json','acceptance_baseline_sha256':sha(ROOT/'spec/v2.0/contracts/acceptance.json'),
    'task_baseline_sha256':sha(ROOT/'spec/v2.0/contracts/tasks.json'),
    'owned_case_verdicts':[{'case_id':'C20','verdict':'PASS','accepted':True,'mode':'FIXTURE',
        'actual_runtime_scope':'RECORDED_NATIVE_WINDOWS_APPCONTAINER_AND_TYPED_LOOPBACK_FIXTURE_WITH_RETAINED_PROTECTED_SYNTHETIC_HOLDOUT',
        'assertion_ids':['C20-01','C20-02','C20-03'],'assertion_verdicts':{k:'PASS' for k in ['C20-01','C20-02','C20-03']},
        'all_frozen_assertions_covered':True,'all_required_commands_executed':True,'all_case_evidence_requirements_satisfied':True,
        'required_command_keys':['test.jev.fixture','test.evolution','acceptance.audit'],
        'expected_actual_status_reference':relative(PACK/'C20.json'),'executor_global_evidence_sha256':sha(PACK/'C20.json'),
        'basis':'Frozen dual-rubric raw evidence and private input/label proof independently recompute to equal objective outcomes. Exact normal regression acceptance and candidate rejection are bound; benefit and closure reports retain NO_IMPROVEMENT and no real-world gain. Three required registered commands and all three formal assertions are completely reconciled.'}],
    'resolved_findings':[{'id':'W16-V-E01','resolution':'Closed for this new complete FIXTURE run: persistent protected inputs, labels and dual-rubric raw native proof are present and independently recomputed. Historical PARTIAL receipts are preserved.'}],
    'open_findings':[],
    'unaccepted_case_verdicts':[{'case_id':'A16','verdict':'PARTIAL_FIXTURE_ONLY','accepted':False,'basis':'This C20 fixture acceptance does not provide independent production supervisor, actual data cutover/recovery or required operating-window evidence.'}],
    'verification_summary':summary,'private_proof_sha256':private['protected_hashes']['dual_rubric_raw_proof_sha256'],
    'evidence_index_reference':relative(OUT/'evidence-index.json'),'evidence_index_sha256':sha(OUT/'evidence-index.json'),
    'semantic_audit_reference':relative(OUT/'global-audit-report.json'),'semantic_audit_sha256':sha(OUT/'global-audit-report.json'),
    'protected_recomputation_reference':relative(OUT/'private-audit-report.json'),'protected_recomputation_sha256':sha(OUT/'private-audit-report.json'),
    'review_reference':relative(OUT/'review.md'),'review_sha256':sha(OUT/'review.md'),
    'privacy_check_reference':relative(OUT/'privacy-check.json'),'privacy_check_sha256':sha(OUT/'privacy-check.json'),
    'resource_request_ids':executor['resource_request_ids'],
    'limits':[
        'Only complete C20 in its contract FIXTURE mode is accepted. Whole W16, A16, W16-G01/G03 dependencies and LIVE remain unaccepted.',
        'Two deterministic private questions and fixed loopback responses demonstrate the rubric-only scenario, not broad model quality, unseen-user generalization or real-world benefit. Model revision is NONE; no external model was invoked.',
        'Existing native output and receipt bytes were independently recomputed; zero new native/test executions were performed by this verifier. Temporary executable bytes were not independently rehashed.',
        'Private inputs, labels, rows, case IDs and protected tickets were kept out of ordinary review outputs; only hashes and aggregate results are exported.',
        'No production database, actual service activation, promotion, deployment, OS-service qualification or denied runtime/adversarial action was performed or authorized by this acceptance.',
        'Historical C20 PARTIAL records and the initial author loopback failure remain unchanged. Existing W16-G02/C09/C10/C12 decisions are not reissued or withdrawn.'
    ],
    'signed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
acceptance['receipt_hash']='sha256:'+hashlib.sha256(json.dumps(acceptance,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
encoded=json.dumps(acceptance,ensure_ascii=False).encode()
assert all(x not in encoded for x in private_ids+tickets+sensitive_bodies)
save(DEST,acceptance)
print(json.dumps({'verdict':'PASS_C20_FIXTURE','acceptance_reference':relative(DEST),'acceptance_sha256':sha(DEST),'acceptance_receipt_hash':acceptance['receipt_hash'],'evidence_index_sha256':sha(OUT/'evidence-index.json'),'review_sha256':sha(OUT/'review.md'),'private_contents_exported':False}))
