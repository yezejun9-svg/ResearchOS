import datetime,hashlib,json,subprocess,traceback
from pathlib import Path

MAIN=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
E=MAIN/'execution/v2.4/receipts/W05/W05-99'
ROOT=E/'historical_qualification_public_provenance_codex/20261015-current-chat/attempt02'
HISTORY=E/'runtime_assets_resource_codex/20261012-current-chat'
ASSETS=MAIN/'.local/builds/current-chat-runtime-assets-20261012'
COMMIT='292ad860f9e76cf2795d5a3010da1d114d01ff56'
WRAPPER='0d50cea351f325f28ca5ee377eac36833768a28be42cf48ec0e50834c0ff6517'
BUNDLE='2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
def ref(p):
 p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def save(name,obj):
 with (OUT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def diag(obj):
 obj['at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (OUT/'diagnostics.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(obj,ensure_ascii=False)+'\n')
def git_blob(path,label):
 argv=['git','show',COMMIT+':'+path];r=subprocess.run(argv,cwd=MAIN,capture_output=True)
 (OUT/(label+'.stdout.raw')).write_bytes(r.stdout);(OUT/(label+'.stderr.raw')).write_bytes(r.stderr)
 save(label+'.invocation.json',{'argv':argv,'cwd':str(MAIN),'native_exit':r.returncode,'stdout':ref(OUT/(label+'.stdout.raw')),'stderr':ref(OUT/(label+'.stderr.raw'))})
 diag({'operation':'git-show','path':path,'native_exit':r.returncode})
 if r.returncode:raise RuntimeError('Git blob not available: '+path)
 return r.stdout
def anchor(path,start,end,meaning):
 lines=Path(path).read_text(encoding='utf-8').splitlines()
 return {'ref':ref(path),'start_line':start,'end_line':end,'excerpt':'\n'.join(lines[start-1:end]),'meaning':meaning}
def run():
 diag({'operation':'initial-exploratory-git-log','argv':['git','log','-8','--format=%H %s','--','adapters/runtime/mu/worker.mjs'],'native_exit':128,'outer_tool_exit':1,'stderr':'fatal: unable to read tree (064d33818101c336e5a587e65e844c107d2e97f2)','result':'History walk failed; exact known 292ad source blobs are separately available. No object repair.'})
 rootmanifest=ROOT/'COLLECTION-manifest.json'
 assert sha(rootmanifest)=='4d0458648de14ac99a0cfb093e0887bf52d290e4517ec4ae7f4ca470e3a8d87a'
 for item in load(rootmanifest)['files']:
  assert sha(item['path'])==item['sha256'] and Path(item['path']).stat().st_size==item['bytes']
 cp408=E/'resume_cp398_codex/20261012-current-chat/continuation-cp408/RESUME.current.json'
 p=load(cp408)['runtime_assets']['manifest_ref'];assert sha(HISTORY/'manifest.json')==p['sha256']=='7440d892f14704d50e184685ce71ddeb570fd77e1c9c7ac4d826ebb18ec00ca3'
 manifest=load(HISTORY/'manifest.json');inv=load(HISTORY/'build-invocation.json');metadata=load(ASSETS/'mu-worker.mjs.build.json')
 assert manifest['source_head']==COMMIT and inv['exit_code']==0
 assert inv['worker_source_sha256']==metadata['source_sha256']==WRAPPER
 assert manifest['build_meta']==metadata==load(HISTORY/'mu-worker.mjs.build.json')==json.loads((HISTORY/'build.stdout.raw').read_text(encoding='utf-8'))
 for item in manifest['assets']:
  assert sha(item['path'])==item['sha256'] and Path(item['path']).stat().st_size==item['bytes']
 assert sha(ASSETS/'mu-worker.mjs')==BUNDLE
 wrapper=git_blob('adapters/runtime/mu/worker.mjs','git-wrapper-292ad')
 build=git_blob('adapters/runtime/mu/build.mjs','git-build-292ad')
 assert hashlib.sha256(wrapper).hexdigest()==WRAPPER
 assert hashlib.sha256(build).hexdigest()==inv['source_sha256']=='9411e13e59a227abf0a4c497253ccf006c4d5962a5374c1f254c05d18cd0f575'
 vendor_raw=git_blob('third_party/mu.MANIFEST.json','git-vendor-manifest-292ad')
 lock_raw=git_blob('execution/v2.4/component_lock.json','git-component-lock-292ad')
 origin_raw=git_blob('third_party/VENDORED_FROM.md','git-vendor-origin-292ad')
 source_matches=[]
 for name in ('workspace-projection-20261012','qualification-read-lane-20261012'):
  p=Path('C:/Users/yqyyds/.codex/researchos-build-worktrees')/name/'adapters/runtime/mu/worker.mjs'
  assert sha(p)==WRAPPER;source_matches.append(ref(p))
 vendor=json.loads(vendor_raw);lock=json.loads(lock_raw)
 assert vendor['files']==len(vendor['entries'])==5083
 assert lock['mu']['commit']==metadata['mu_commit']=='8dfebe36508ac0c2508735bb866756dab9283e74'
 assert lock['mu']['file_count']==5083 and ('Commit: '+metadata['mu_commit']) in origin_raw.decode()
 assert hashlib.sha256(vendor_raw).hexdigest()==sha(MAIN/'third_party/mu.MANIFEST.json')
 drift=[]
 for rel,want in vendor['entries'].items():
  p=MAIN/rel
  if not p.is_file() or p.stat().st_size!=want['size'] or sha(p)!=want['sha256']:drift.append(rel)
 assert not drift,drift
 versions={key:load(MAIN/rel)['version'] for key,rel in {'sdk':'third_party/mu/packages/coding-agent/package.json','ai':'third_party/mu/packages/ai/package.json','esbuild':'third_party/mu/node_modules/esbuild/package.json'}.items()}
 assert versions=={'sdk':'0.87.1','ai':'0.87.1','esbuild':'0.28.2'}
 inputs={str(p):ref(p) for p in [MAIN/'adapters/runtime/mu/worker.mjs',MAIN/'adapters/runtime/mu/build.mjs',MAIN/'third_party/mu.MANIFEST.json',MAIN/'execution/v2.4/component_lock.json',MAIN/'third_party/VENDORED_FROM.md',ASSETS/'mu-worker.mjs',ASSETS/'mu-worker.mjs.build.json']}
 save('01-source-and-build-link.json',{'root_collection':ref(rootmanifest),'historical_resume_anchor':ref(cp408),'historical_manifest':ref(HISTORY/'manifest.json'),'historical_invocation':ref(HISTORY/'build-invocation.json'),'historical_stdout':ref(HISTORY/'build.stdout.raw'),'historical_stderr_warning':ref(HISTORY/'build.stderr.raw'),'researchos_source_commit':COMMIT,'historical_native_exit':0,'historical_argv':inv['argv'],'historical_cwd':inv['cwd'],'exact_git_wrapper_sha256':hashlib.sha256(wrapper).hexdigest(),'exact_git_build_sha256':hashlib.sha256(build).hexdigest(),'wrapper_bytes':len(wrapper),'build_bytes':len(build),'bundle':ref(ASSETS/'mu-worker.mjs'),'metadata':ref(ASSETS/'mu-worker.mjs.build.json'),'matched_later_source_snapshots':source_matches,'current_main_wrapper_different':sha(MAIN/'adapters/runtime/mu/worker.mjs')!=WRAPPER,'source_bytes_written':False,'bundle_rebuilt':False})
 save('02-vendor-toolchain-boundary.json',{'vendor_manifest_git_commit':COMMIT,'vendor_manifest':ref(MAIN/'third_party/mu.MANIFEST.json'),'same_manifest_bytes_as_historical_git':True,'current_entries_rehashed':5083,'current_drift':drift,'sdk_commit':metadata['mu_commit'],'sdk_commit_is_researchos_commit':False,'versions':versions,'esbuild_current_package':ref(MAIN/'third_party/mu/node_modules/esbuild/package.json'),'build_checks_vendored_files_before_bundle':True,'build_records_esbuild_version_not_binary_hash':True,'historical_full_transitive_input_vector_present_in_asset_receipt':False,'asset_receipt_filenames':sorted(p.name for p in HISTORY.iterdir() if p.is_file()),'not_provable':['Bit-for-bit reproducibility from a historically pinned full node_modules/esbuild binary/transitive generated dist input closure; no metafile or such input vector in the original runtime asset receipt.','The 5083 tracked vendor manifest does not cover all generated dist and node_modules inputs; current matching versions and source files are not historical fingerprints of those unrecorded inputs.'],'no_rebuild':True})
 chain=load(ROOT/'04-package-composition-chain.json')['chain']
 compositions=[Path(x['ref']['path']) for x in chain]
 compositions += [E/'approved_readlane_combined_desktop_build_codex/20261012-current-chat/composition.json',E/'approved_combined_desktop_build_codex/20261012-current-chat/composition.json']
 checks=[]
 for path in compositions:
  c=load(path);package=Path(c['package_root']);bundle=package/'apps/desktop/resources/control/runtime/mu-worker.mjs';meta=package/'apps/desktop/resources/control/runtime/mu-worker.mjs.build.json'
  assert sha(bundle)==BUNDLE and sha(meta)==sha(ASSETS/'mu-worker.mjs.build.json')
  matches=[item for value in c.values() if isinstance(value,list) for item in value if isinstance(item,dict) and 'mu-worker.mjs' in item.get('path','')]
  for item in matches:
   if 'sha256' in item: assert sha(package/item['path'])==item['sha256']
  checks.append({'composition':ref(path),'package_root':str(package),'bundle':ref(bundle),'metadata':ref(meta),'composition_mu_rows':matches})
 scripts=[E/'approved_attach_combined_desktop_build_codex/20261014-current-chat/assemble-attach.py',E/'approved_readlane_combined_desktop_build_codex/20261012-current-chat/assemble-readlane.py',E/'approved_combined_desktop_build_codex/20261012-current-chat/assemble-combined.py']
 save('03-existing-package-copy-chain.json',{'package_count':len(checks),'checks':checks,'script_edges':[ref(p) for p in scripts],'repair_to_root_chain':'approved_attach has no old_composition field; assemble-attach.py OLD_COMP explicitly points to approved_readlane. assemble-readlane OLD_HERE points to approved_combined; assemble-combined MU uses original runtime-assets directory.','staged_binding_evidence_reused_without_actual_data_access':ref(ROOT/'03-exact-staged-worker-bindings.json')})
 anchors=[anchor(OUT/'git-build-292ad.stdout.raw',8,23,'worktree versus mainRepo, third_party/mu, FIXED_MU_COMMIT and 5083 manifest constraint'),anchor(OUT/'git-build-292ad.stdout.raw',24,38,'All 5083 vendor regular-file size/hash checks occur before esbuild'),anchor(OUT/'git-build-292ad.stdout.raw',39,49,'esbuild resolved under vendor node_modules; versions pinned; generated dist entry checks'),anchor(OUT/'git-build-292ad.stdout.raw',56,81,'ResearchOS wrapper entryPoint, output bytes hash, source wrapper hash, and SDK commit are separate fields'),anchor(OUT/'git-wrapper-292ad.stdout.raw',1,10,'ResearchOS wrapper imports vendored coding-agent and AI API packages'),anchor(scripts[0],19,19,'Explicit missing JSON edge: attach OLD_COMP -> readlane composition'),anchor(scripts[1],13,17,'readlane MU and OLD_HERE -> combined builder'),anchor(scripts[2],13,23,'combined MU root and exact original asset hashes')]
 save('04-exact-source-semantic-anchors.json',{'anchors':anchors})
 assert all(sha(p)==record['sha256'] for p,record in inputs.items())
 save('05-readonly-input-guards.json',{'checked':list(inputs.values()),'all_unchanged':True,'shared_checkpoint_or_main_writes':False,'actual_DB_reads_or_writes':False,'core_or_model_execution':False,'private_configuration_read':False,'git_object_restore':False})
 diag({'operation':'bounded-provenance-collection','native_exit':0,'vendor_entries_checked':5083,'existing_package_copies_checked':len(checks),'wrapper_source_exactly_matched':True,'not_rebuilt':True})
 print(json.dumps({'source_commit':COMMIT,'wrapper_sha256':WRAPPER,'bundle_sha256':BUNDLE,'vendor_entries_checked':5083,'package_count':len(checks)},ensure_ascii=False))
if __name__=='__main__':
 try:run()
 except Exception as exc:
  diag({'operation':'collection-check','native_exit':1,'error':str(exc)});raise
