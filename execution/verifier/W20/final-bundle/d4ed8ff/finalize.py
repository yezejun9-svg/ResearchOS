"""Read saved output and finalize independent evidence; never executes product/check code."""
import hashlib
import json
import zipfile
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]
INDEX=ROOT/'execution/verifier/W21/current-handoff-index/6374df3'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def record(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
assert not (OUT/'manifest.json').exists(), 'Finalized output is immutable'
r=load(OUT/'check-result.json'); before=load(OUT/'before.json'); after=load(OUT/'after.json')
assert r['actual_os_exit_code']==0 and r['reported']['assertions']==16 and r['reported']['status']=='PASS'
assert r['before_after_identical'] and before==after
assert '--run-fixture' not in load(OUT/'command.json')['argv']
old=load(OUT.parent/'a418d50/check-result.json')
assert old['actual_os_exit_code']==0 and old['reported']['assertions']==28
assert before['check_sha256']==load(OUT.parent/'a418d50/before.json')['check_sha256']
preserved=load(OUT/'preservation-before.json')
assert all(record(ROOT/x['path'])==x for x in preserved)
gr=load(ROOT/'execution/verifier/W20/user-guide/8d8c0db/report.json')
source_checks=[]
for x in gr['facts_source_files']:
    p=ROOT/x['path']; current=record(p)
    assert current['sha256']==x['sha256']
    source_checks.append(current)
assert len(source_checks)==21
build=ROOT/'execution/receipts/W20/final-bundle/d4ed8ff'
raw_builds=[]
with zipfile.ZipFile(ROOT/'.local/researchos-development-d4ed8ff-a.zip') as z:
    m=json.loads(z.read('release-manifest.json'))
    tree={n:sha(z.read(n)) for n in sorted(z.namelist()) if n!='release-manifest.json' and not n.startswith(('bin/','web/dist/','licenses/'))}
    derived=sha((json.dumps(tree,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode())
    assert derived==m['source_tree_sha256'] and m['build_id']==derived[:20]
    for label in 'ab':
        c=load(build/f'build-{label}.command.json')
        raw=load(build/f'build-{label}.stdout.raw.json')
        assert c['exit_code']==0 and raw['archive_sha256']==r['reported']['archive_sha256']
        assert raw['source_commit']==before['git_head'] and raw['manifest_sha256']==sha(z.read('release-manifest.json'))
        raw_builds.append({'label':label,'actual_recorded_exit_code':c['exit_code'],'command':record(build/f'build-{label}.command.json'),'stdout':record(build/f'build-{label}.stdout.raw.json'),'stderr':record(build/f'build-{label}.stderr.raw.txt')})
audit=load(OUT/'archive-audit.json')
groups={
 'four_executables':lambda p:p.startswith('bin/'),
 'web_dist':lambda p:p.startswith('web/dist/'),
 'fixture_scripts':lambda p:p.startswith('scripts/'),
 'frozen_spec_contracts':lambda p:p.startswith('spec/'),
 'migrations':lambda p:'migrations/' in p,
 'configs_and_locks':lambda p:p.startswith('config/') or 'lock' in Path(p).name or p=='go.sum',
 'command_registry_dispatcher':lambda p:p=='execution/commands.json' or p.startswith('execution/command_dispatcher/'),
}
grouped={name:[x for x in audit['unchanged_payload'] if predicate(x['path'])] for name,predicate in groups.items()}
assert len(grouped['four_executables'])==4 and all(grouped.values())
save(OUT/'reuse-binding.json',{'guide_fact_sources_current_exact':source_checks,'guide_fact_source_count':21,'groups':grouped,'existing_check_unchanged_sha256':before['check_sha256'],'source_tree_hash_independently_derived':derived,'build_id':m['build_id'],'recorded_build_commands':raw_builds,'new_manifest_reverified_by_current_static_check':True,'historical_native_reuse_scope':'Unchanged bounded fixture mechanisms only; no current archive launch or future environment claim','changed_manifest_is_start_precondition':True,'stop_path_and_runtime_inputs_are_not_all_identical_because_package_identity_and_path_change':True})
review={'verdict':'PASS_BOUNDED_STATIC_DOCUMENT_PACKAGE_WITH_HISTORICAL_NATIVE_REUSE','source_commit':before['git_head'],'archive_sha256':r['reported']['archive_sha256'],'archive_entries':515,'manifest_files':514,'current_static':{'actual_os_exit_code':0,'check_executions':1,'assertions':16,'assertion_ids':r['reported']['assertion_ids'],'stdout_sha256':r['stdout_sha256'],'stderr_sha256':r['stderr_sha256']},'current_product_native_executions':0,'historical_a418':{'source_commit':'a418d503f29646f62010905f9dc9338630aa0108','archive_sha256':'dc90caedd5287bcd718c76bc8e0e2189cf3b33c92a547b6d9fe71d3564f8a193','actual_os_exit_code':0,'assertions':28,'report':'execution/verifier/W20/final-bundle/a418d50/review.json','manifest_sha256':'d963c5e8d9da41c81a30f7e18b36c497c289615fecdecc621d9badaa2c5cc0a9','rerun':False},'exact_unchanged_payloads':511,'changed_manifest_fields':audit['manifest_semantic_delta'],'source_files_observed':461,'before_after_identical':True,'original_evidence_preserved':True,'guide_pages':11,'guide_relative_links':51,'historical_screenshots':45,'missing_screenshot_cells':5,'screenshots_bundled':False,'license_gaps':2,'clean_Windows_A15':'NOT_RUN','W20_whole_stage':'NOT_ACCEPTED','W21_G01':'NOT_ACCEPTED','W21_G02':'NOT_ACCEPTED','whole_goal_complete':False,'new_current_control_binary_proof':'NOT_ESTABLISHED','new_browser_provider_private_or_blocked_branch_execution':False}
save(OUT/'review.json',review)
files=[{'path':p.name,'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']
save(OUT/'manifest.json',{'verdict':review['verdict'],'source_commit':before['git_head'],'files':files})
assert all(sha((OUT/x['path']).read_bytes())==x['sha256'] for x in files)
supplement_path=INDEX/'doc-package-supplement.json'
supp_manifest=INDEX/'doc-package-supplement-manifest.json'
assert not supplement_path.exists() and not supp_manifest.exists()
supplement={'kind':'DOCUMENT_PACKAGE_LOCATIONS_ONLY_NO_REISSUE_OF_ORIGINAL_INDEX','original_snapshot_manifest_sha256':sha((INDEX/'manifest.json').read_bytes()),'prior_a418_supplement_sha256':sha((INDEX/'final-supplement.json').read_bytes()),'prior_a418_supplement_manifest_sha256':sha((INDEX/'supplement-manifest.json').read_bytes()),'source_commit':before['git_head'],'archive_sha256':r['reported']['archive_sha256'],'archive':'.local/researchos-development-d4ed8ff-a.zip','review':record(OUT/'review.md'),'review_json':record(OUT/'review.json'),'review_manifest':record(OUT/'manifest.json'),'static_check':review['current_static'],'current_product_native_executions':0,'historical_a418':review['historical_a418'],'exact_unchanged_payloads':511,'guide_pages':11,'historical_screenshots':45,'missing_screenshot_cells':5,'screenshots_bundled':False,'formal_case_states_changed':False,'clean_Windows_A15':'NOT_RUN','W20_whole_stage':'NOT_ACCEPTED','W21_G01':'NOT_ACCEPTED','W21_G02':'NOT_ACCEPTED','whole_goal_complete':False}
save(supplement_path,supplement)
save(supp_manifest,{'original_snapshot_manifest_sha256':supplement['original_snapshot_manifest_sha256'],'prior_supplement_manifest_sha256':supplement['prior_a418_supplement_manifest_sha256'],'files':[{'path':supplement_path.name,'sha256':sha(supplement_path.read_bytes()),'bytes':supplement_path.stat().st_size}]})
assert all(record(ROOT/x['path'])==x for x in preserved)
print(json.dumps({'review':record(OUT/'review.md'),'review_json':record(OUT/'review.json'),'manifest':record(OUT/'manifest.json'),'output_files':len(files),'doc_package_supplement':record(supplement_path),'doc_package_supplement_manifest':record(supp_manifest),'old_files_preserved':True},ensure_ascii=False))
