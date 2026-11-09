import hashlib,json,stat
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104'
CONTROL=HERE/'product-v1-owned-verification-20261104'
OUT=HERE/'product-v1-build13-root-postcheck.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
assert not OUT.exists()
reg=read(BASE/'build13-scope/registration.json')
effective=read(BASE/'build13-scope/registration.effective-v1.json')
result_path=CONTROL/'runs/product-v1-build-13/RESULT.json';r=read(result_path)
assert r['status']=='COMPLETED_OWNED_JOB_STOPPED' and r['root_exit_code']==0 and r['stop_proved'] and r['job_active_zero'] and not r['input_drift'] and not r['timed_out'] and not r['raw_limit_exceeded'] and r['errors']==[] and r['terminate_job_attempts']==r['terminate_original_root_attempts']==0
assert r['scope_sha256']==effective['scope_sha256']=='478fc79a6a70383714fb2f129b8ff1bcf95be2223a991f97e39ba2e227bc0275'
scope_path=Path(effective['scope_path']);assert sha(scope_path)==r['scope_sha256']
for item in read(scope_path)['inputs']:assert sha(Path(item['path']))==item['sha256'],item['path']
bundle=Path(reg['bundle']);manifest=bundle/'development-manifest.json';m=read(manifest)
assert sha(manifest)=='5d9277b3d7be35f8577325859c2033d612dbad0b6077902964be15637533ad85'
assert m['source']['head']==reg['main_head']=='998fc6330ba735056cd31f8ebf68dd50a8251c1b' and m['source']['candidate_delta']==[]
assert len(reg['source_sha256'])==67 and len(m['files'])==135
for ref,digest in reg['source_sha256'].items():assert sha(ROOT/ref)==sha(Path(reg['clean_worktree'])/ref)==digest,ref
listed=set()
for row in m['files']:
    assert row['path'] not in listed
    listed.add(row['path']);p=bundle/row['path'];assert sha(p)==row['sha256'],row['path']
actual=set()
for p in bundle.rglob('*'):
    s=p.lstat();assert not stat.S_ISLNK(s.st_mode) and not (s.st_file_attributes&0x400),str(p)
    if p.is_file():actual.add(p.relative_to(bundle).as_posix())
assert actual==listed|{'development-manifest.json'}
fixture=HERE/'product-v1-native-qualification-中文-root-01'
helper_sha='4ac03d2af358ab0ecb4d2f06a12bbc0bcde043e7e3610ee114a64c0416f1b4ef'
values={'researchos.local/research-os/internal/host.codexQualificationApprovedRoot':str(fixture),'researchos.local/research-os/internal/host.codexQualificationHelperSHA256':'sha256:'+helper_sha}
q=m['qualification'];assert q['enabled'] and q['status']=='BUILD_BOUND_NOT_NATIVE_TESTED' and q['core_linker_values']==values
core=bundle/'apps/desktop/resources/control/researchos-control.exe'
assert sha(core)==m['core']['sha256']=='caf115d9578378c0520feaeda0c492d1b9be9bb262daf37314e2fac113403fce'
assert m['core']['build_argv']==[str(ROOT/'.local/tools/go1.27.1/go/bin/go.exe'),'build','-mod=readonly','-trimpath','-ldflags',q['core_linker_flags'],'-o',str(core),'./apps/control']
for p in [HERE/'product-v1-native-helper-build01/buildout/qualification-helper.exe',fixture/'S/qualification-helper.exe',bundle/q['helper_bundle_relative']]:
    assert sha(p)==helper_sha and p.stat().st_size==5335552
assert q['original_build']['provenance']=='PREBUILT_ORIGINAL_OWNED_BUILD_RECEIPT_NOT_CURRENT_GO_LIST'
for name,digest in q['original_build']['receipt_sha256'].items():assert sha(Path(q['original_build']['receipt_root'])/name)==digest
canaries=read(HERE/'product-v1-first-native-fixture-canaries-preparation.json')
assert {p.name for p in (fixture/'S').iterdir()}==set(canaries['exact_initial_inventory'])
for name,item in canaries['exact_initial_inventory'].items():assert sha(fixture/'S'/name)==item['sha256']
protected=read(HERE/'product-v1-native-prelaunch-intent-integration-plan.json')['protected_sha256']
for ref,digest in protected.items():assert (sha(ROOT/ref) if (ROOT/ref).is_file() else 'ABSENT_BEFORE')==digest,ref
out=dict(status='BUILD13_COMPLETE_SOURCE_AND_BUNDLE_VERIFIED_NOT_NATIVE_TESTED',main_head=reg['main_head'],source_pins_verified=67,bundle_files_verified=135,manifest_path=str(manifest),manifest_sha256=sha(manifest),core_sha256=sha(core),qualification_root=str(fixture),helper_sha256=helper_sha,source_canaries_unchanged=True,protected_original_paths_verified=len(protected),original_job_result_path=str(result_path),original_job_result_sha256=sha(result_path),job_cumulative_processes=r['job_total_processes'],elapsed_seconds=r['elapsed_seconds'],scope_sha256=r['scope_sha256'],no_force_timeout_or_drift=True,new_app_helper_native_model_calls=0,formal_increment=0,product_increment=0)
OUT.write_bytes((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
print(json.dumps(dict(postcheck=str(OUT),sha256=sha(OUT),core_sha256=sha(core),source_pins=67,bundle_files=135,old_protected_paths=len(protected),native_qualified=False)))
