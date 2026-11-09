import hashlib,json,pathlib,sys
E=pathlib.Path(__file__).parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def put(name,v):
    with (E/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
denial=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/Desktop-temp-index-policy-denial.json')
if denial.is_file():
    raw=denial.read_bytes()
    with (E/'author-diagnostic-inputs/Desktop-temp-index-policy-denial.json').open('xb') as f:f.write(raw)
    denial_ref={'path':str(denial),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
else:denial_ref={'path':str(denial),'status':'ROOT_REPORTED_NOT_PRESENT_AT_SEAL'}
put('LATE-CONTEXT-NOTICE.json',{'root_reported_author_temp_index_cleanup_policy_denial':denial_ref,'denied_action_execution':'No native execution record; original temporary index retained; no retry by reviewer','source_blocking':False,'administrator_session':'USER_PREPARING_NOT_VERIFIED per root; not C57 resource readiness or acceptance','formal_increment':0})
put('R3-final-seal.recipe.json',{'argv':[sys.executable,'-B','-Xutf8',str(E/'seal_r3_review.py')],'writes':'Review manifest and seal only plus copied late diagnostic notice','mode':'READ_EXISTING_REVIEW_BYTES_NO_TEST_NO_GUI_CORE'})
for name in ['r2-test-temp','r2-actual-test-temp','r3-test-temp','r3-direct-probe-temp','never-created-r2-dryrun-state','never-created-r3-dryrun-state']:
    assert not (E/name).exists(),name
exclude={'R3-REVIEW-MANIFEST.json','R3-REVIEW-SEAL.json'}
rows=[]
for p in sorted(E.rglob('*')):
    if p.is_file() and p.name not in exclude:
        rows.append({'path':p.relative_to(E).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
put('R3-REVIEW-MANIFEST.json',{'schema':'researchos.desktop-complete-tree-independent-review-manifest.v1','root':str(E),'candidate_commit':'ecc28dd3c91a0f68dcddb41b53325aa7f0e81419','candidate_tree':'1d44a02c9483fc529b08ffe81895ec443920bdd1','bundle_manifest_sha256':'e1d61b68d12c61e2dda341df3541d2b4b541b9c2331af5da26ca56dff759b620','files':rows,'excludes':'This manifest and its seal avoid self-reference; all pre-seal files are included.'})
for r in rows:assert sha(E/r['path'])==r['sha256']
seal={'schema':'researchos.desktop-complete-tree-independent-review-seal.v1','verdict':'SOURCE_BUILD_REVIEW_PASS_NOT_NATIVE_ACCEPTED','candidate_commit':'ecc28dd3c91a0f68dcddb41b53325aa7f0e81419','candidate_tree':'1d44a02c9483fc529b08ffe81895ec443920bdd1','parent_commit':'7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e','source_freeze_sha256':'c6ac8745f27d91a7d74aa804acdc05f3a50932b0d414a91f63daefe75c00c113','bundle_manifest_sha256':'e1d61b68d12c61e2dda341df3541d2b4b541b9c2331af5da26ca56dff759b620','report_sha256':sha(E/'R3-INDEPENDENT-REVIEW.md'),'diagnostics_sha256':sha(E/'REVIEW-DIAGNOSTICS.json'),'late_diagnostic_notice_sha256':sha(E/'LATE-CONTEXT-NOTICE.json'),'review_manifest_sha256':sha(E/'R3-REVIEW-MANIFEST.json'),'review_file_count':len(rows),'blocking_findings':0,'nonblocking_findings':['R2-N01 long-path mock cleanup'],'reviewer_nonzero_attempts_retained':['011','018','029','031'],'native_gui_core_starts':0,'provider_calls':0,'formal_increment':0,'C57_recovery_or_acceptance':False,'source_mutations_by_reviewer':0}
put('R3-REVIEW-SEAL.json',seal)
print(json.dumps({'verdict':seal['verdict'],'report_sha256':seal['report_sha256'],'manifest_sha256':seal['review_manifest_sha256'],'seal_sha256':sha(E/'R3-REVIEW-SEAL.json'),'file_count':len(rows),'native_gui_core_starts':0,'formal_increment':0}))
