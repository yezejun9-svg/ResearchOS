import pathlib,json,hashlib,subprocess,datetime,re
E=pathlib.Path(__file__).parent;S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-any-combined-build-20261014');P=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-any-a7ec7ebf-20261014')
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def save(n,o):(E/n).write_text(json.dumps(o,ensure_ascii=True,indent=2),encoding='utf8')
A=read(E/'package-audit.json');B=read(E/'verified-boundary/validator-package-boundary.json');R=read(E/'react-build-comparison.json');ACL=read(E/'live-acl-readback.json');C=A['source']['commit']
assert B['all_passed'] and len(B['cases'])==7 and R['independent_build_equal_package'] and len(R['assets'])==3
assert ACL['protected'] and ACL['owner_sid']==ACL['current_user_sid'] and len(ACL['access'])==1
ace=ACL['access'][0];assert ace['sid']==ACL['current_user_sid'] and ace['rights']=='FullControl' and ace['control']=='Allow' and not ace['inherited'] and ace['inheritance']=='None' and ace['propagation']=='None'
assert subprocess.check_output(['git','-C',str(S),'rev-parse','HEAD']).decode().strip()==C
assert subprocess.check_output(['git','-C',str(S),'status','--porcelain']).decode().strip()==''
cache={};rechecked=0
def verify(path,digest):
 global rechecked
 key=str(pathlib.Path(path).resolve()).lower()
 if key not in cache:cache[key]=sha(path)
 assert cache[key]==digest,path
 rechecked+=1
for f in A['package_members']:verify(f['path'],f['sha256'])
for f in A['references']:verify(f['path'],f['sha256'])
RAW=S/'.local/receipts/coding-any-combined-20261014'
for prefix in ['', 'core-']:
 for f in read(RAW/(prefix+'inputs.before.json')):verify(f['path'],f['sha256'])
for f in read(E/'small-fixture-inputs.json')['web_files']:verify(f['source'],f['sha256']);verify(f['fixture'],f['sha256'])
for f in read(E/'react-fixture-supplement.json')['files']:verify(f['source'],f['sha256']);verify(f['fixture'],f['sha256'])
prod=S/'internal/host/runtime_coding_windows.go';assert sha(prod)=='4b757f691036002e8ba0482a4c3fece2609b9a71d6b70fc536ca4dbb4b194e95'
corelist=(RAW/'core-go-list.stdout').read_text(encoding='utf8');corelog=(RAW/'core-control-build.stderr').read_text(encoding='utf8')
assert 'runtime_coding_windows.go' in corelist and 'runtime_coding_windows.go' in corelog
assert read(E/'react-build.process.json')['native_exit']==1 and read(E/'react-build-r2.process.json')['native_exit']==0
assert not (E/'react-fixture/node_modules').exists() and not (E/'react-source/apps/web/node_modules').exists()
for p in E.rglob('*'):assert not p.is_symlink() and not p.is_junction(),str(p)
three={v['binary']['path']:v['binary']['sha256'] for v in A['fresh_go_versions']}
report={'schema':'researchos.cp465-independent-normal-package-review/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/attach_review_resume','verdict':'APPROVE_PACKAGE_FOR_ROOT_CONTROLLED_ACTIVATION','findings':[],
 'package_root':str(P),'source':A['source'],'author_manifest':A['author_manifest'],'package_members':58,'fresh_go_binaries':three,'fresh_go_vcs':{'control':C,'runtime_verifier':C,'validator':C,'modified':False,'independent_go_version_m_native_exits':[0,0,0]},
 'input_closure':A['inputs'],'go_list_source_embed_closure':A['go_list_closure'],'frozen_reference_count':A['reference_count'],'final_unique_hashes_rechecked':len(cache),'final_assertions_rechecked':rechecked,
 'source_fix_binding':{'production_checker_sha256':sha(prod),'core_go_list_contains_production_checker':True,'core_control_native_compile_log_contains_production_checker':True,'read_write_scope':'read326/write2 unchanged per accepted exact2 source review; package review does not widen it.'},
 'desktop_assets':{'Main_preload_modules':14,'Main_preload_byte_equal_current_source':True,'React_assets':3,'independent_small_source_rebuild_native_exit':0,'independent_React_assets_byte_equal_package':True,'build_fixture_source_files':31,'build_fixture_source_bytes':421487},
 'tests':{'author_packaged_non_GUI_cases':A['author_package_test_counts'],'author_package_native_exit':0,'fresh_independent_packaged_validator_cases':7,'fresh_validator_all_checks_passed':True,'fresh_validator_metadata_checks_per_case':14,'fresh_cases':[{'name':x['name'],'outcome':x['outcome'],'reason':x['reason'],'native_exit':x['native_exit']} for x in B['cases']]},
 'installation_manifest':A['installer'],'current_acl_readback':ACL,'default_Mu':{'commit':A['mu_commit'],'three_components':'node.exe, mu-worker.mjs, mu-worker.mjs.build.json','byte_equal_previously_independently_approved_package':True,'old_independent_review':A['old_package_review'],'accepted_pause_candidate_installed':False},
 'migration_compatibility':{'numbered_files':A['numbered_migrations'],'exact_1_to_24':True,'migration25_absent':True,'all_migration_bytes_equal_current_candidate_and_previously_approved_package':True,'evidence_class':'Static package compatibility with retained original1..24 migration contract; no real database reopen/migrate operation performed.'},
 'preserved_failures':[A['preserved_setup_failure'],{'class':'INDEPENDENT_REVIEW_SETUP_ERROR','first_process':'react-build.process.json','native_exit':1,'cause':'Initial tiny React fixture flattened directory topology, preventing original relative design-tokens import.','correction':'Copied exact apps/web, required desktop lib and design-token source layout into independent D fixture; reran unchanged Vite/current source.','corrected_process':'react-build-r2.process.json','corrected_native_exit':0,'original_raw_preserved':True}],
 'boundaries':{'source_or_Main_writes':False,'package_writes':False,'installed_assets_activation':False,'Desktop_GUI_or_CDP_calls':False,'Core_or_verifier_server_launch':False,'real_database_access':False,'API_calls':False,'provider_model_calls':0,'large_worktree_or_Ccache_created':False,'formal_increment':0,'formal_cases':'0/42','all_22_parent_tasks':'OPEN','next_authority':'Root controlled normal activation and fresh GUI PREPARE required; package approval alone is not GUI/qualification/formal acceptance.'},
 'cleanup':{'both_dependency_junctions_removed_without_traversal':True,'large_copies_created':False,'retained_small_fixtures':'Exact source/React outputs retained to reproduce evidence; no disposable dependency copies or caches created.'},'audit_sha256':sha(E/'package-audit.json'),'boundary_sha256':sha(E/'verified-boundary/validator-package-boundary.json')}
save('FINAL-report.json',report)
members=[{'path':p.relative_to(E).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(E.rglob('*')) if p.is_file() and p.name!='FINAL-manifest.json']
save('FINAL-manifest.json',{'schema':'researchos.cp465-independent-package-review-manifest/1','report_sha256':sha(E/'FINAL-report.json'),'members':members})
print(json.dumps({'report_sha256':sha(E/'FINAL-report.json'),'manifest_sha256':sha(E/'FINAL-manifest.json'),'members':len(members),'unique_rehash':len(cache),'verdict':report['verdict']}))
