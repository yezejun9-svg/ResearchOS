import datetime as dt,hashlib,json
from pathlib import Path
E=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
P=R/'execution/v2.4/receipts/W17/W17-03/native25_actual_root_codex/20261014-current-chat/positive-replay-01'
def ref(p):
 raw=Path(p).read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,v):
 with (E/name).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
report=json.loads((E/'revision02/RELEASE-report.json').read_bytes())
assert report['state']=='EXACT_RELEASE_PAYLOAD_CHECKED_READY_FOR_SEPARATE_ROOT_SIGN_DECISION'
write('FINAL-report.json',{
 'schema':'researchos.native25-positive-release-independent-final/1','state':report['state'],'reviewer':report['reviewer'],
 'at':dt.datetime.now(dt.timezone.utc).isoformat(),'detail_report_ref':ref(E/'revision02/RELEASE-report.json'),
 'payload_ref':report['payload_ref'],'snapshot_ref':report['snapshot_ref'],'config_ref':report['config_ref'],
 'signed_destination':report['signed_destination'],'sign_kind':'release','source_pins':648,'all_frozen_public_inputs':4373,
 'fresh_sql_read':{'scope':'two actual synthetic fixture databases only','source24_whole_typed_rows_and_schema':'MATCH','restored25_whole_typed_rows':'MATCH_REHEARSAL_RECEIPT','query_only':True,'raw_rows_or_credentials_saved':False,'database_file_hash_unchanged_by_read':True},
 'root_operation_wrapper_ref':ref(P/'root_concrete_operation.py'),
 'root_operation_wrapper_review':'Reads an existing concrete Root approval, checks frozen controller hash, dispatches only sign_reviewed/publish_signed/release_fixture. Does not generate approval, print private runtime path, or select signing policy. Reviewer did not invoke it.',
 'decision':report['decision'],'scope':report['scope'],'limitations':[report['limitation'],'This report is a source/evidence review artifact, not a Root approval. Root must still make its own one-payload decision and later separately review actual signed bytes before publication.','The original snapshot and payload were verified while the case was paused; if Root has since moved phases, this remains historical evidence and grants no fresh authority.'],
 'diagnostic_history':{'first_checker_exit':1,'first_checker_report_ref':ref(E/'RELEASE-report.json'),'first_checker_stderr_ref':ref(E/'check.stderr.raw.txt'),'cause':'Reviewer canonical hash helper incorrectly retained Go Marshal HTML escaping. Exact row-by-row typed digests already matched; project Hash canonicalizes via RFC8785 JCS. Corrected only independent helper to JCS-compatible string/array/map encoding; original source/data untouched.','corrected_checker_exit':0,'corrected_checker_report_ref':ref(E/'revision02/RELEASE-report.json'),'failures_retained':True},
 'signatures_created':0,'harness_approvals_created':0,'root_approvals_created':0,'fixture_release_requested':False,'private_key_reads':0,'original_product_db_reads':0,'formal_increment':0,'formal_accepted_cases':'0/42','parent_tasks_open':22})
members=[ref(p) for p in sorted(E.rglob('*')) if p.is_file() and p!=E/'manifest.json']
write('manifest.json',{'schema':'researchos.native25-positive-release-review-evidence-manifest/1','state':report['state'],'reviewer':report['reviewer'],'report_ref':ref(E/'FINAL-report.json'),'members':members,'formal_increment':0})
for member in members:
 actual=ref(member['path']);assert actual['sha256']==member['sha256'] and actual['bytes']==member['bytes']
print(json.dumps({'report_ref':ref(E/'FINAL-report.json'),'manifest_ref':ref(E/'manifest.json'),'members':len(members)},ensure_ascii=True))
