import datetime,hashlib,json,pathlib,subprocess
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT=pathlib.Path(__file__).resolve().parent
AUTHOR=ROOT/'execution/v2.4/receipts/W05/W05-99/public23_to24_candidate_integration_codex/candidate-20261012-01'
def ref(p):
    p=pathlib.Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def write(n,o):(OUT/n).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
old=read(OUT/'final-seal-checks.json');source=read(OUT/'source-checks.json')
old_decision_before=ref(OUT/'review-decision.json');old_seal_before=ref(OUT/'final-seal-checks.json')
p=AUTHOR/'main-mirror-manifest.json';raw=p.read_bytes();new=json.loads(raw.decode('utf-8-sig'))
new_ref=ref(p);assert new_ref['sha256']==hashlib.sha256(raw).hexdigest()
old_names={e['relative_path']:e for e in old['mirror_checks']};new_names={e['relative_path']:e for e in new['files']}
added=sorted(set(new_names)-set(old_names));removed=sorted(set(old_names)-set(new_names))
assert added==['SCOPE_AND_GAPS.md','candidate-product.patch'] and not removed
checks=[]
for name,e in new_names.items():
    main=ref(AUTHOR/name);worktree=ref(pathlib.Path(new['worktree_source'])/name)
    valid=main['sha256']==worktree['sha256']==e['sha256'] and main['bytes']==worktree['bytes']==e['bytes']
    old_equal=None
    if name in old_names:
        previous=old_names[name]['main'];old_equal=main['sha256']==previous['sha256'] and main['bytes']==previous['bytes']
        assert old_equal
    assert valid
    checks.append({'relative_path':name,'main':main,'worktree':worktree,'final_manifest_match':valid,'unchanged_from_previous_51':old_equal})
assert len(checks)==53==new['source_file_count']==new['verified_mirror_count']
main_head=git('rev-parse','HEAD').decode().strip();main_parent=git('rev-parse','HEAD^').decode().strip()
assert main_head=='549ad6924ad43d27bbe533f4ba020ef383a0888f' and main_parent==source['parent']
main_checks=[]
for e in source['files']:
    rel=e['relative_path'];actual=ref(ROOT/rel);committed=git('show',main_head+':'+rel)
    actual_match=actual['sha256']==e['expected']['sha256'] and actual['bytes']==e['expected']['bytes']
    candidate_blob=git('show',source['head']+':'+rel)
    committed_match=committed==candidate_blob
    assert actual_match and committed_match
    main_checks.append({'relative_path':rel,'main':actual,'matches_original_reviewed_source':actual_match,'main_commit_blob_matches_candidate_commit':committed_match})
changed=git('diff','--name-only',main_parent,main_head).decode().splitlines()
assert set(changed)=={e['relative_path'] for e in source['files']}
patch=(AUTHOR/'candidate-product.patch').read_text(encoding='utf-8-sig').replace('\r\n','\n')
patch_body=patch[patch.index('diff --git '):].strip()
expected_diff=git('diff','--no-ext-diff',source['parent'],source['head']).decode('utf-8-sig').replace('\r\n','\n').strip()
assert patch_body==expected_diff
assert ref(p)==new_ref and ref(OUT/'review-decision.json')==old_decision_before and ref(OUT/'final-seal-checks.json')==old_seal_before
archive=OUT/'author-final-53-manifest.raw.json';assert not archive.exists();archive.write_bytes(raw)
check_file='final-manifest-addendum-checks.json'
write(check_file,{'schema':'researchos.independent-main24-final-manifest-addendum-checks.v1','actor':'codex:/root/w05_migration_review','old_manifest_ref':old['manifest'],'old_manifest_path_no_longer_matches_hash':old['manifest']['sha256']!=new_ref['sha256'],'old_manifest_raw_archive_available':False,'old_manifest_not_reconstructed':True,'old_51_member_hash_inventory_preserved_in':old_seal_before,'final_manifest_ref':new_ref,'final_manifest_raw_archive_ref':ref(archive),'added':added,'removed':removed,'final_53_checks':checks,'main_head':main_head,'main_parent':main_parent,'main_source_checks':main_checks,'main_commit_changed_files':changed,'patch_body_equals_original_candidate_git_diff_after_newline_normalization':True,'old_decision_unchanged':old_decision_before,'source_and_product_calls_replayed':False})
decision={'schema':'researchos.independent-main24-candidate-review-addendum.v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/w05_migration_review','verdict':'ACCEPTED','evidence_scope':['SOURCE','ACTUAL_COMPONENT','MANIFEST_ADDENDUM'],'decision':'MAIN_40_FILE_DEVELOPMENT_INTEGRATION_REMAINS_ACCEPTABLE','previous_review_ref':old_decision_before,'previous_review_preserved':True,'previous_author_manifest_reference_status':'STALE_PATH_HASH_MISMATCH_DECLARED','previous_author_manifest_expected_sha256':old['manifest']['sha256'],'previous_author_manifest_raw_available':False,'previous_author_manifest_not_reconstructed':True,'final_author_manifest_ref':new_ref,'final_author_manifest_archive_ref':ref(archive),'addendum_checks_ref':ref(OUT/check_file),'delta_summary':{'old_member_count':51,'new_member_count':53,'all_51_prior_members_unchanged':True,'added_files':added,'added_patch_verification':'Candidate patch body exactly matches git diff adc460c..8dbfc952 after CRLF normalization.','added_scope_document_review':'Consistent with original component-only acceptance, build/raw limitations, no Native qualification and full20to24 OPEN. Statements about not integrating Main describe author actions at candidate production time; Root has now integrated separately.'},'main_commit':main_head,'main_40_working_files_match_original_source_hashes':True,'main_40_commit_blobs_match_candidate':True,'main_commit_has_only_reviewed_40_paths':True,'blocking_findings':[],'scope_boundary':'Repairs the current evidence reference by an explicit append-only addendum. Does not retroactively make the old manifest path valid; old review and 51-member records remain unchanged.','native_release_qualified':False,'native_revision_adoption_authorized_by_this_review':False,'original_build_raw_io_recovered':False,'populated_actual_workload_proven':False,'historical_product_or_native_prefix_replayed':False,'formal_acceptance':False,'parent_acceptance':False,'formal_case_accepted_delta':0,'full20to24':'OPEN','A04':'OPEN','W05_parent':'OPEN','product_or_canon_modified_by_reviewer':False}
write('review-decision-v2-addendum.json',decision)
print(json.dumps({'verdict':decision['verdict'],'decision_ref':ref(OUT/'review-decision-v2-addendum.json'),'final_manifest':new_ref,'previous_manifest_raw_available':False,'unchanged_prior_files':51,'verified_final_files':53,'main_source_files':len(main_checks)},ensure_ascii=True,indent=2))
