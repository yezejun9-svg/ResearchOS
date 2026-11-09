import hashlib,json,pathlib,sys
E=pathlib.Path(__file__).parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def put(name,v):
    with (E/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
put('013-seal.recipe.json',{'argv':[sys.executable,'-B','-Xutf8',str(E/'seal_preflight.py')],'mode':'SEAL_READ_ONLY_PREFLIGHT_NO_TEST_MERGE_OR_APPLICATION_START'})
rows=[{'path':p.relative_to(E).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(E.rglob('*')) if p.is_file() and p.name not in ['PREFLIGHT-MANIFEST.json','PREFLIGHT-SEAL.json']]
put('PREFLIGHT-MANIFEST.json',{'schema':'researchos.desktop-main-integration-preflight-manifest.v1','root':str(E),'files':rows})
for r in rows:assert sha(E/r['path'])==r['sha256']
seal={'schema':'researchos.desktop-main-integration-preflight-seal.v1','verdict':'PASS_FOR_EXACT_SEVEN_PATH_LOCAL_FAST_FORWARD','blocking_findings':0,'expected_main_before':'7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e','candidate_commit':'ecc28dd3c91a0f68dcddb41b53325aa7f0e81419','expected_tree_after':'1d44a02c9483fc529b08ffe81895ec443920bdd1','source_paths':7,'expected_tracked_dirty_preserved':20,'additional_commands_or_package_manifest_registration_required':False,'platform_shell_and_installer_commands_remain_UNBOUND':True,'evidence_reuse':'Exact same blobs/original location-bound bundle and historical run only; not whole dirty Main working-tree equivalence or fresh postmerge execution','report_sha256':sha(E/'MAIN-INTEGRATION-PREFLIGHT.md'),'manifest_sha256':sha(E/'PREFLIGHT-MANIFEST.json'),'diagnostics_sha256':sha(E/'DIAGNOSTICS.json'),'reference_count':len(rows),'source_or_shared_state_writes':0,'tests_executed':0,'application_starts':0,'formal_increment':0}
put('PREFLIGHT-SEAL.json',seal)
print(json.dumps({'verdict':seal['verdict'],'report_sha256':seal['report_sha256'],'manifest_sha256':seal['manifest_sha256'],'seal_sha256':sha(E/'PREFLIGHT-SEAL.json'),'reference_count':len(rows),'blocking_findings':0}))
