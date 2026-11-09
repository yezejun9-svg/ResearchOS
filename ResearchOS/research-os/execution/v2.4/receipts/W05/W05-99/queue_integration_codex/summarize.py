from pathlib import Path
import hashlib,json,subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
runs=read(HERE/'results.json')['runs']
source_before=read(ROOT/'execution/v2.4/receipts/W05/W05-99/queue_executor_codex/source_after.json')['files']
source_after=[ref(ROOT/f['path']) for f in source_before]
assert source_before==source_after
write(HERE/'integrated-source33.json',source_after)
index=[]
for r in runs:
    d=HERE/r['name'];command=read(d/'command.json')
    for key in ('stdout','stderr'):assert sha(ROOT/r[key]['path'])==r[key]['sha256']
    before=read(d/'inputs-before.json');after=read(d/'inputs-after.json')
    assert r['source_vector_equal']==(before==after)
    index.append({'name':r['name'],'command':ref(d/'command.json'),'result':ref(d/'result.json'),'head':command['head'],'head_after':r['head_after'],'exit_code':r['exit_code'],'pass_events':len(r['test_events']['pass']),'top_level_passes':sum('/' not in t for t in r['test_events']['pass']),'fail':r['test_events']['fail'],'skip':r['test_events']['skip'],'node_counts':r['node_counts'],'input_count':len(before),'vector_equal':before==after,'input_before':ref(d/'inputs-before.json'),'input_after':ref(d/'inputs-after.json'),'stdout':r['stdout'],'stderr':r['stderr']})
review=ROOT/'execution/v2.4/receipts/W05/W05-99/resume_review_codex/s6_final_source_review.json'
prior=read(ROOT/'execution/v2.4/receipts/W05/W05-99/queue_executor_codex/execution_report.json')
all_pass=len(runs)==6 and all(r['exit_code']==0 and r['source_vector_equal'] and not r['test_events']['fail'] and not r['test_events']['skip'] for r in runs)
report={'schema':'researchos.w05.s6-current-main-integration.v1','classification':'CURRENT_MAIN_LOCAL_INTEGRATION_NOT_FORMAL_ACCEPTANCE','status':'PASS_CURRENT_SCOPED_INTEGRATION' if all_pass else 'FAILED_OR_INCOMPLETE','product_source_read_only':True,'source33_matches_independently_reviewed_candidate':True,'independent_review':ref(review),'independent_verdict':read(review)['verdict'],'runs':index,'sdk_build':read(HERE/'sdk-build/stdout.raw'),'final_source33':ref(HERE/'integrated-source33.json'),'no_counter_reset':True,'prior_failure_history':ref(ROOT/'execution/v2.4/receipts/W05/W05-99/queue_executor_codex/run_index.json'),'historical_blockers_unchanged':prior['broad_regression']['remaining_failures'],'coverage_limits':['Q10 historical gates remain open; current matrix PASS is not all-repository or all-Q01..Q10 acceptance.','Q06 remains persisted-state/transaction and original receipt replay evidence, not instruction-by-instruction OS crash injection.','Actual SDK uses bounded loopback fixture model, not external provider LIVE.','W07 health tests here are product regression fixtures, not source LIVE or independent formal H07 acceptance.','WindowsDesktop UI interaction, W05/A04 parent acceptance, protected holdout and privileged owner gates are not claimed.','Existing checkpoint, command/ownership indexes and prior raw receipts were not edited.'],'formal_case_count_delta':0,'parent_acceptance':False,'external_provider_live':False,'frozen_package':{'path':'execution/v2.4/receipts/W05/W05-99/queue_executor_codex/frozen-package-input','manifest_sha256':'4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964','exact_files':147,'external_package_used':False},'artifact_locations':{'bundle':'.local/w0599-queue-integration/mu-worker.mjs','control':'.local/w0599-queue-integration/control.exe'},'invocation':{'argv':['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe','execution/v2.4/receipts/W05/W05-99/queue_integration_codex/run.py'],'cwd':str(ROOT),'runner':ref(HERE/'run.py')}}
write(HERE/'integration_report.json',report)
write(HERE/'receipt_manifest.json',{'files':[ref(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='receipt_manifest.json']})
print(json.dumps({'status':report['status'],'runs':[{k:r[k] for k in ('name','exit_code','pass_events','top_level_passes','fail','skip','node_counts','vector_equal')} for r in index],'report_sha256':sha(HERE/'integration_report.json')},indent=2))
