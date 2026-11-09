import hashlib,json,stat
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104';CONTROL=HERE/'product-v1-owned-verification-20261104';OUT=HERE/'product-v1-build14-root-postcheck.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
assert not OUT.exists();reg=read(BASE/'build14-scope/registration.json');binding=read(BASE/'build14-scope/registration-binding.json');scopepath=Path(binding['scope_path']);scope=read(scopepath)
assert sha(scopepath)==binding['scope_sha256']=='3338c07aa9fbcec4f96c149265b6865aae2d8e5121ecc9c15ce6313f417489fa'
rp=CONTROL/'runs/product-v1-build-14/RESULT.json';r=read(rp)
assert r['status']=='COMPLETED_OWNED_JOB_STOPPED' and r['root_exit_code']==0 and r['stop_proved'] and r['job_active_zero'] and not r['input_drift'] and not r['timed_out'] and not r['raw_limit_exceeded'] and r['errors']==[] and r['terminate_job_attempts']==r['terminate_original_root_attempts']==0
assert r['scope_sha256']==sha(scopepath)
for item in scope['inputs']:assert sha(Path(item['path']))==item['sha256'],item['path']
for item in r['raw']:assert sha(rp.parent/item['file'])==item['sha256']
producer=Path(reg['producer_receipts']);pr=read(producer/'result.json');assert pr['status']=='BUILT_NOT_NATIVE_TESTED' and not pr['source_drift'] and not pr['public_vendor_drift'] and pr['qualification_enabled'] and not pr['source_acceptance']
assert read(producer/'source.before.json')==read(producer/'source.after.json')
bundle=Path(reg['bundle']);mf=bundle/'development-manifest.json';m=read(mf);assert sha(mf)==pr['manifest_sha256']
assert m['source']['head']==reg['main_head']=='360c3eefd06ba82255352357c05ece00dae00d3a' and m['source']['candidate_delta']==[] and m['bundle_root']==str(bundle) and pr['output']==str(bundle)
pins=reg['source_sha256'];assert len(pins)==70 and hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()).hexdigest()==reg['source_union_sha256']=='954c293b52e5b83dcb8a779410e89fc3c74a4bad3550d3620ba0938cc67e15c2'
for ref,digest in pins.items():assert sha(ROOT/ref)==sha(Path(reg['clean_worktree'])/ref)==digest,ref
listed=set()
for row in m['files']:
 assert row['path'] not in listed;listed.add(row['path']);assert sha(bundle/row['path'])==row['sha256'],row['path']
actual=set()
for p in bundle.rglob('*'):
 st=p.lstat();assert not stat.S_ISLNK(st.st_mode) and not (st.st_file_attributes&0x400),str(p)
 if p.is_file():actual.add(p.relative_to(bundle).as_posix())
assert actual==listed|{'development-manifest.json'} and len(listed)==pr['files']
fixture=HERE/'product-v1-native-qualification-中文-root-01';helper='4ac03d2af358ab0ecb4d2f06a12bbc0bcde043e7e3610ee114a64c0416f1b4ef';q=m['qualification'];values={'researchos.local/research-os/internal/host.codexQualificationApprovedRoot':str(fixture),'researchos.local/research-os/internal/host.codexQualificationHelperSHA256':'sha256:'+helper}
assert q['enabled'] and q['status']=='BUILD_BOUND_NOT_NATIVE_TESTED' and q['core_linker_values']==values
core=bundle/'apps/desktop/resources/control/researchos-control.exe';assert sha(core)==m['core']['sha256']
assert m['core']['build_argv']==[str(ROOT/'.local/tools/go1.27.1/go/bin/go.exe'),'build','-mod=readonly','-trimpath','-ldflags',q['core_linker_flags'],'-o',str(core),'./apps/control']
for p in [HERE/'product-v1-native-helper-build01/buildout/qualification-helper.exe',fixture/'S/qualification-helper.exe',bundle/q['helper_bundle_relative']]:assert sha(p)==helper and p.stat().st_size==5335552
assert q['original_build']['provenance']=='PREBUILT_ORIGINAL_OWNED_BUILD_RECEIPT_NOT_CURRENT_GO_LIST'
for name,digest in q['original_build']['receipt_sha256'].items():assert sha(Path(q['original_build']['receipt_root'])/name)==digest
canaries=read(HERE/'product-v1-first-native-fixture-canaries-preparation.json');assert {p.name for p in (fixture/'S').iterdir()}==set(canaries['exact_initial_inventory'])
for name,item in canaries['exact_initial_inventory'].items():assert sha(fixture/'S'/name)==item['sha256']
protected=read(HERE/'product-v1-workbench-refinement-integration-plan.json')['protected_sha256']
for ref,digest in protected.items():assert (sha(ROOT/ref) if (ROOT/ref).is_file() else 'ABSENT_BEFORE')==digest
result=dict(status='BUILD14_COMPLETE_SOURCE_AND_BUNDLE_VERIFIED_NOT_GUI_OR_NATIVE_TESTED',main_head=reg['main_head'],source_pins_verified=len(pins),source_role='ALL70INTEGRATED_PINS_VERIFIED; CLI_AND_TEST_PINS_DO_NOT_IMPLY_PARTICIPATION_IN_CORE_COMPILATION',bundle_files_verified=len(listed),manifest_path=str(mf),manifest_sha256=sha(mf),core_sha256=sha(core),qualification_root=str(fixture),helper_sha256=helper,source_canaries_unchanged=True,protected_original_paths_verified=len(protected),original_job_result_path=str(rp),original_job_result_sha256=sha(rp),job_cumulative_processes=r['job_total_processes'],elapsed_seconds=r['elapsed_seconds'],scope_sha256=sha(scopepath),no_force_timeout_or_drift=True,new_app_helper_native_model_calls=0,formal_increment=0,product_increment=0)
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(dict(postcheck=str(OUT),sha256=sha(OUT),manifest_sha256=sha(mf),core_sha256=sha(core),source_pins=70,bundle_files=len(listed))))
