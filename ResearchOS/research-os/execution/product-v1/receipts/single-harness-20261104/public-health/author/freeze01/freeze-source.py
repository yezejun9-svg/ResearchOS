from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
BASE=Path(__file__).resolve().parent
WT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-public-health-20261104')
SCOPE=Path('D:/作品集/ResearchOS/research-os/execution/product-v1/receipts/single-harness-20261104/public-health/scope.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
scope=json.loads(SCOPE.read_text(encoding='utf-8'))
directory=BASE/'final';directory.mkdir(exist_ok=False)
git='C:/Program Files/Git/cmd/git.exe'
raws={}
for name,args in [('git-status',['status','--porcelain=v1','--untracked-files=all']),('git-diff-check',['diff','--check']),('git-head',['rev-parse','HEAD'])]:
    argv=[git,'-C',str(WT),*args]
    r=subprocess.run(argv,capture_output=True,timeout=30)
    (directory/(name+'.stdout.raw')).write_bytes(r.stdout);(directory/(name+'.stderr.raw')).write_bytes(r.stderr)
    write(directory/(name+'.command.json'),{'argv':argv,'exit_code':r.returncode})
    assert r.returncode==0,(name,r.stderr)
    raws[name]=r.stdout.decode('utf-8')
paths=scope['production_paths']+scope['test_paths']
assert {line[3:] for line in raws['git-status'].splitlines() if line}==set(paths)
assert raws['git-head'].strip()==scope['base_head']
pins={}
for rel in paths:
    target=directory/'source'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((WT/rel).read_bytes())
    pins[rel]=sha(target);assert pins[rel]==sha(WT/rel)
overlay=json.loads((BASE/'checks-02-c-overlay/input-manifest.json').read_text())
for row in overlay['files']:
    if row['origin']=='CURRENT_SCOPE_EXACT2':assert pins[row['path']]==row['sha256']
test_result=json.loads((BASE/'checks-02-c-overlay/result.json').read_text())
assert test_result['exit_code']==0 and test_result['all_overlay_live_unchanged']
tap=(BASE/'checks-02-c-overlay/stdout.raw').read_text(encoding='utf-8')
assert '# tests 135\n' in tap and '# pass 135\n' in tap and '# fail 0\n' in tap and '# skipped 0\n' in tap
checks=json.loads((BASE/'checks-01/results.json').read_text())
assert all(row['exit_code']==0 for row in checks if row['name']!='pure-tests')
manifest={'schema':'researchos.public-health.source-manifest/1','scope_path':str(SCOPE),'scope_sha256':sha(SCOPE),'worktree':str(WT),'base_head':scope['base_head'],'source_sha256':pins,'all_snapshots_match_live':True,'exact2_git_status':True,'construction_frozen':True,'source_modification_permitted':False,'formal_increment':0}
write(directory/'source-manifest.json',manifest)
diagnostics={'schema':'researchos.public-health.diagnostics/1','events':[
 {'origin':'preparation-first-parallel-read','classification':'READONLY_EXEC_SERVER_TRANSPORT_DISCONNECTED','status':'ORIGINAL_OUTPUT_UNAVAILABLE','count':2,'original_error':'CreateProcess Rejected(Failed to create unified exec process: exec-server transport disconnected)','detail':'Original calls were read-only and provided no usable output; no write or test requested. Root provided new CP616 recovery evidence. Fresh readback 957a32 and escalated Git 969e1c terminal0; implementation 129a61 terminal0. No blind replay or inferred success.'},
 {'origin':'42dc37/856500:checks-01-ui-source-dependencies','classification':'SPARSE_WORKTREE_FIXTURE_DEPENDENCY_MISSING','exit_code':1,'raw':'checks-01/pure-tests.stdout.raw','event_counts':{'tests':112,'pass':108,'fail':4,'skip':0},'product_assertion_failures':0,'detail':'Four fail events are missing activity.js/harness.js imports and missing main.jsx/workbench.jsx reads, before their intended assertions. New public health77 cases passed. Same five test selections repeated unchanged in C overlay with 43 explicitly pinned public source files from exact base plus exact2; no D dependency/source expansion or weakened assertion. checks02 actual135PASS/0fail/skip.'}
 ],'unique_origin_count':2,'all_failures_retained':True,'product_failures_observed':0}
write(directory/'diagnostics.json',diagnostics)
summary={'schema':'researchos.public-health.author-summary/1','status':'IMPLEMENTED_FROZEN_FOR_INDEPENDENT_SOURCE_QA','author_acceptance':False,'source_sha256':pins,
 'behavior':['Only exact status.health bypasses legacy principal; ensureCore and validated local discovery execute first.','Only an empty plain/null-prototype object or absent/null body is accepted; fixed GET /healthz, empty payload/headers. No caller request/identity fields are adopted.','All non-health reads, mutations, provider classification, principal checks, v2 and UI strict health shape remain unchanged.','No principal file creation and no health-based writer/model/Harness permission claim.'],
 'checks':{'pure':{'exit_code':0,'tests':135,'pass':135,'fail':0,'skip':0,'top_level':42,'subtests':93,'new_public_health_cases':77,'existing_ui_startup_compatibility_cases':58,'raw_stdout':'checks-02-c-overlay/stdout.raw','raw_stderr':'checks-02-c-overlay/stderr.raw','input_manifest':'checks-02-c-overlay/input-manifest.json'},'ipc_syntax':0,'new_test_syntax':0,'git_diff_check':0,'git_exact2':True,'base_matches':True,'all_scope_sources_match_tested_overlay':True},
 'unchanged_ui_startup_sha256':next(row['sha256'] for row in overlay['files'] if row['path']=='apps/web/src/startup.js'),
 'real_execution':{'gui':0,'http_sockets':0,'native':0,'cli':0,'model':0,'user_auth_file_access':0,'user_db_access':0,'old_probe_replay':0},
 'limits':['Actual callCore/ensureCore/discovery/principal/request behavior exercised with in-memory fs/HTTP substitutes only.','Real fresh-profile Desktop header health and model behavior are not executed or accepted here.','C public-source dependency overlay is source-only, not a new runtime authority or copied user profile.'],
 'pending_author_sessions':0,'independent_review_required':True,'formal_increment':0,'product_acceptance_increment':0}
write(directory/'summary.json',summary)
frozen={'schema':'researchos.public-health.freeze/1','at':datetime.now(timezone.utc).isoformat(),'construction_frozen':True,'source_modification_permitted':False,'source_manifest_sha256':sha(directory/'source-manifest.json'),'summary_sha256':sha(directory/'summary.json'),'diagnostics_sha256':sha(directory/'diagnostics.json'),'all2_source_pins_match_live':True,'pending_author_sessions':0,'author_self_acceptance':False,'formal_increment':0,'product_acceptance_increment':0}
write(directory/'FROZEN.json',frozen)
selected=sorted([p for p in BASE.rglob('*') if p.is_file() and p.name not in ['EVIDENCE_MANIFEST.json','archive-file-list.json']],key=lambda p:p.relative_to(BASE).as_posix())
write(BASE/'EVIDENCE_MANIFEST.json',{'schema':'researchos.public-health.evidence/1','source_sha256':pins,'files':[{'path':p.relative_to(BASE).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in selected],'cache_or_runtime_data_included':False})
write(BASE/'archive-file-list.json',{'schema':'researchos.public-health.archive/1','root':str(BASE),'files':[p.relative_to(BASE).as_posix() for p in selected]+['EVIDENCE_MANIFEST.json','archive-file-list.json'],'note':'Includes the narrow43 source-only overlay needed for reproducible assertions; no full Git baseline, node_modules/cache/dist/executable/profile/auth/DB/model.','evidence_manifest_sha256':sha(BASE/'EVIDENCE_MANIFEST.json')})
for rel,digest in pins.items():assert sha(WT/rel)==digest
print(json.dumps({'status':'FROZEN','source_manifest_sha256':sha(directory/'source-manifest.json'),'freeze_sha256':sha(directory/'FROZEN.json'),'summary_sha256':sha(directory/'summary.json'),'diagnostics_sha256':sha(directory/'diagnostics.json'),'evidence_sha256':sha(BASE/'EVIDENCE_MANIFEST.json'),'archive_list_sha256':sha(BASE/'archive-file-list.json'),'evidence_files':len(selected),'source_sha256':pins,'all2_live_pins_match':True}),flush=True)
