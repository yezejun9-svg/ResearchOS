"""Finalize saved evidence only; never invokes a test or package fixture."""
import hashlib
import json
from collections import Counter
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]
INDEX=ROOT/'execution/verifier/W21/current-handoff-index/6374df3'
def sha(data):return hashlib.sha256(data).hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
r=load(OUT/'check-result.json')
assert r['actual_os_exit_code']==0 and r['reported']['status']=='PASS' and r['reported']['assertions']==28
assert r['source_tools_archives_sbom_unchanged'] and r['new_check_executions']==1
before,after=load(OUT/'before.json'),load(OUT/'after.json')
assert before==after
outcome=load(ROOT/'release/outcome_report.json')
acceptance=load(ROOT/'execution/acceptance_status.json')
ledger=load(ROOT/'execution/bootstrap_ledger.json')
assert outcome['historical_formal_status_counts']==dict(Counter(x['status'] for x in acceptance['cases'].values()))
closed=sum(v['status']=='CONSTRUCTION_ACCEPTED' for v in ledger['tasks'].values())
assert outcome['historical_wbs_counts']=={'CONSTRUCTION_ACCEPTED':closed,'NOT_CLOSED':len(ledger['tasks'])-closed}
assert outcome['current_full_case_acceptance_reissued'] is False and outcome['whole_goal_complete'] is False
assert outcome['observed_results']['existing_non_null_release_retention_in_C05']=='NOT_TESTED'
refs=['docs/handoff/current-construction.md','release/outcome_report.json',
      'execution/acceptance_status.json','execution/bootstrap_ledger.json',
      'execution/verifier/W08/manual-disposition/57ef089/review.md',
      'execution/verifier/W08/manual-disposition/57ef089/review.json',
      'execution/verifier/W16/current-control-admission/3695633/review.md',
      'execution/verifier/W16/recovery-context-fence/9253b99/review.md',
      'execution/verifier/W13/ui-recovery-c26/review.json',
      'execution/resource_requests/RQ-W05-CLI-POLICY-001.json',
      'execution/resource_requests/RQ-W17-LOCAL-CUTOVER-POLICY-001.json']
facts={'verdict':'PASS_FACTUAL_BOUNDED_HANDOFF_WITH_EXTERNAL_REFERENCES',
       'input_hashes':{p:sha((ROOT/p).read_bytes()) for p in refs},
       'historical_case_counts_match':True,'historical_wbs_counts_match':True,
       'null_outcome_baseline_not_current_live_success':True,'current_control_proof_does_not_bind_new_binary':True,
       'null_stable_release_limit_preserved':True,'work_only_predicate_source_review_limit_preserved':True,
       'old_five_r02_passes_not_fresh_final_source_runs':True,
       'handoff_is_source_checkout_document_not_bundled':True,'outcome_bundled_exact':True,
       'external_construction_refs_not_promised_in_zip':True,
       'formal_W21_G01_or_G02_accepted':False,'formal_A15_accepted':False}
save(OUT/'document-facts.json',facts)
review={'verdict':'PASS_BOUNDED_DEVELOPMENT_FIXTURE_ONLY','source_commit':before['git_head'],
        'new_fixture_check_runs':1,'actual_os_exit_code':0,'checks':28,'check_ids':r['reported']['assertion_ids'],
        'archive_sha256':r['reported']['archive_sha256'],'archive_entries':514,'manifest_files':513,
        'source_files_observed':r['source_files_observed'],'before_after_identical':True,
        'c05_binding':{'source_files':12,'raw_files':9,'new_tests':0,'report':'c05-package-binding.json'},
        'document_fact_review':'document-facts.json','clean_windows_A15':'NOT_RUN',
        'W20_whole_stage':'NOT_ACCEPTED','W21_G01':'NOT_ACCEPTED','W21_G02':'NOT_ACCEPTED',
        'whole_goal_complete':False,'license_gaps':2,'new_current_control_binary_proof':'NOT_ESTABLISHED',
        'old_matrix_or_provider_or_private_helper_reexecuted':False,
        'stdout_sha256':r['stdout_sha256'],'stderr_sha256':r['stderr_sha256']}
save(OUT/'review.json',review)
files=[{'path':p.name,'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
       for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']
save(OUT/'manifest.json',{'verdict':review['verdict'],'source_commit':before['git_head'],'files':files})
assert all(sha((OUT/x['path']).read_bytes())==x['sha256'] for x in files)
base_manifest=INDEX/'manifest.json'
assert sha(base_manifest.read_bytes())=='99a5ac98b87fb8da8c9b6dfe59a3426a5fe61a8866a1693c19c6ba2b1f9768d4'
old=load(base_manifest)
assert len(old['files'])==8
assert all(sha((INDEX/x['path']).read_bytes())==x['sha256'] for x in old['files'])
assert not (INDEX/'final-supplement.json').exists() and not (INDEX/'supplement-manifest.json').exists()
supplement={'kind':'FINAL_LOCATIONS_ONLY_NO_REISSUE_OF_42_CASE_INDEX','basis_source':'6374df33e95b5f64a53fab8c656d2486298cf57d',
 'original_snapshot_files_unchanged':8,'original_manifest_sha256':sha(base_manifest.read_bytes()),
 'C05':{'status':'BOUNDED_COMPATIBILITY_REPAIR_INDEPENDENTLY_REVIEWED',
        'production_source':'78d4de057ca9f0810d8bfe4f5aac5c4c856c44ba','final_source':'57ef0892e60c9fdf9a57aad2dd62f82e002ff337',
        'root_integration':'1f934c424c4f5cca4a19fa50098013ff7756e361',
        'review':'execution/verifier/W08/manual-disposition/57ef089/review.md',
        'review_sha256':'84f6c7532d14e22923be37b45c3442fae07b6d3dad416661cff5b6560e5bc5a0',
        'package_source_commit_preserves_12_files':True,'raw_files_preserved':9,
        'c05_original_assertions_pass':8,'final_matrix_subtests_pass':21,'new_test_execution':False,
        'full_current_C05_accepted':False,'limits':['null==null stable Release','work-only predicate not isolated dynamically','five older R02 passes retain source drift limits']},
 'package':{'status':'PASS_BOUNDED_DEVELOPMENT_FIXTURE_ONLY','source_commit':before['git_head'],
        'archives':list(before['archives']),'archive_sha256':r['reported']['archive_sha256'],
        'review':'execution/verifier/W20/final-bundle/a418d50/review.md',
        'review_sha256':sha((OUT/'review.md').read_bytes()),
        'manifest':'execution/verifier/W20/final-bundle/a418d50/manifest.json',
        'manifest_sha256':sha((OUT/'manifest.json').read_bytes()),
        'existing_fixture_executed_once':True,'actual_exit_code':0,'checks':28,
        'license_gaps':2,'clean_Windows_A15':'NOT_RUN','fresh_current_control_proof':'NOT_ESTABLISHED'},
 'formal_case_states_changed':False,'W21_G01':'NOT_ACCEPTED','W21_G02':'NOT_ACCEPTED','whole_goal_complete':False}
save(INDEX/'final-supplement.json',supplement)
save(INDEX/'supplement-manifest.json',{'original_manifest_sha256':sha(base_manifest.read_bytes()),
    'files':[{'path':'final-supplement.json','sha256':sha((INDEX/'final-supplement.json').read_bytes()),
              'bytes':(INDEX/'final-supplement.json').stat().st_size}]})
assert all(sha((INDEX/x['path']).read_bytes())==x['sha256'] for x in old['files'])
print(json.dumps({'review_sha256':sha((OUT/'review.md').read_bytes()),'review_json_sha256':sha((OUT/'review.json').read_bytes()),
 'manifest_sha256':sha((OUT/'manifest.json').read_bytes()),'output_files':len(files),
 'supplement_sha256':sha((INDEX/'final-supplement.json').read_bytes()),
 'supplement_manifest_sha256':sha((INDEX/'supplement-manifest.json').read_bytes()),'original_snapshot_unchanged':True},ensure_ascii=False))
