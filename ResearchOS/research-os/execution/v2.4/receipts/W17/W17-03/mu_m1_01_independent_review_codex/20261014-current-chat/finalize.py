import json,pathlib,hashlib,subprocess,datetime,re,os
R=pathlib.Path(__file__).parent;S=R/'source';SRC=R.parent/'mu-m1-wire-20261014';F=R.parent/'mu-pause-checkpoint-m0-v2-20261012';B=S/'.local/independent/mu-worker.mjs'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def save(n,o):(R/n).write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf8')
def git(*a):return subprocess.check_output(['git','-C',str(SRC),*a]).decode().strip()
before=read(R/'source-before.json');supp=read(R/'source-supplement.json')
assert git('rev-parse','HEAD')==before['head'] and not git('status','--porcelain')
for f in before['source8']:assert sha(SRC/f['path'])==f['sha256'] and sha(S/f['path'])==f['sha256']
for f in before['snapshot_files']+supp['files']:assert sha(S/f['path'])==f['sha256'],f['path']
author=read(SRC/'.local/m1-01/manifest.json')
for n,f in author['files'].items():assert sha(SRC/'.local/m1-01'/n)==f['sha256'],n
inputs=read(str(B)+'.inputs.json');meta=read(str(B)+'.build.json')
frozen=read(F/'.local/v6-final-20261014-r3/compiled-inputs-census.json')
expected={str(pathlib.Path(x['realpath']).resolve()).lower():x for x in frozen}
unknown=[]
for i in inputs:
 assert sha(i['realpath'])==i['sha256'],i['realpath']
 n=str(pathlib.Path(i['realpath']).resolve()).lower();prior=expected.get(n)
 if prior:assert prior['sha256']==i['sha256']
 else:unknown.append(i)
assert len(unknown)==1 and pathlib.Path(unknown[0]['realpath']).resolve()==(S/'adapters/runtime/mu/worker.mjs').resolve(),unknown
author_inputs=read(SRC/'.local/m1-01/mu-worker.mjs.inputs.json')
def normalized_input(i):
 p=pathlib.Path(i['realpath']).resolve()
 try:label='M1_SOURCE/'+p.relative_to(S.resolve()).as_posix()
 except ValueError:
  try:label='M1_SOURCE/'+p.relative_to(SRC.resolve()).as_posix()
  except ValueError:label=str(p).lower()
 return label,i['sha256']
assert sorted(map(normalized_input,inputs))==sorted(map(normalized_input,author_inputs))
assert len(inputs)==2118 and sha(B)==meta['bundle_sha256']
audit=read(str(B)+'.audit.json');assert audit['before']==audit['after']
fm=read(F/'.local/v6-final-20261014-r3/v6-final-manifest.json')
assert sha(F/'.local/v6-final-20261014-r3/v6-final-manifest.json')==meta['candidate_manifest_sha256']
for f in fm['source9']:assert sha(F/f['path'])==f['sha256']
save('input-validation.json',{'source_head':before['head'],'source_tree':before['tree'],'source8_unchanged':True,'snapshot_original_files_unchanged':len(before['snapshot_files'])+len(supp['files']),'author_frozen_members_unchanged':len(author['files']),'compiled_inputs_rehashed':len(inputs),'matched_frozen_sdk_census':len(inputs)-len(unknown),'new_input':unknown,'normalized_author_independent_inputs_identical':True,'sdk_frozen9_unchanged':True,'sdk_before_after_audit_identical':True,'independent_bundle':meta,'note':'Independent bundle hash differs from author because esbuild path comments depend on source snapshot location; all 2118 normalized input identities and bytes match.'})
results={n:read(R/'runs'/f'{n}.json') for n in ['build','node-r2','bridge','host-r2','independent-node-r2','independent','host-actual']}
assert all(r['exit']==0 for r in results.values())
for n in ['node-r2','independent-node-r2']:
 t=(R/'runs'/f'{n}.stdout.txt').read_text(encoding='utf8');assert 'fail 0' in t and 'skipped 0' in t
for n in ['bridge','host-r2','independent','host-actual']:
 t=(R/'runs'/f'{n}.stdout.txt').read_text(encoding='utf8');assert '\nPASS\n' in t and '--- SKIP' not in t
node=B.parent/'node.exe';nodehash=sha(node)
assert node.resolve().is_relative_to(R.resolve()) and node.name=='node.exe' and nodehash==results['host-actual']['node_sha256']
node.unlink()
assert not list((R/'fixture-temp').iterdir())
save('cleanup.json',{'removed_single_file':str(node),'sha256':nodehash,'reason':'Temporary exact pinned node copy for actual candidate loader read test; executable remains at original verified tool path.','fixture_temp_empty':True})
report={'schema':'researchos.mu-m1-01-independent-review/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/attach_review_resume','verdict':'APPROVE_SOURCE_NATIVE_SYNTHETIC_M1_01_ONLY','findings':[],'source':{'worktree':str(SRC),'commit':before['head'],'tree':before['tree'],'base':before['base'],'exact_paths':before['source8'],'author_manifest_sha256':sha(SRC/'.local/m1-01/manifest.json'),'author_report_sha256':sha(SRC/'.local/m1-01/report.json')},'review_scope':['Candidate-only builder compiles complete accepted SDK base + exact9 with 2118 input hashes; default Mu8df builder unchanged','Typed explicit host candidate policy and actual rebuilt bundle accepted; default loader rejects candidate','Actual production worker pause/checkpoint/resume source and bound command ledger','Windows native Bridge captured >64KiB file, durable journal seal correlation, paused terminal and physical cleanup','Original SDK epoch/header/tree retained while separate same-Run epoch successor resumes cumulative effects'],
 'validation':{'original_node_tests':'11/11 no skip; candidate build + worker pause/restore/tool/control','native_bridge_top_level_tests':'7/7 no skip plus identity/stream subcases','host_top_level_tests':'2/2 no skip plus 8 metadata subcases','independent_worker_tests':'23/23 no skip (2 parents and 21 adversarial children)','independent_native_reader_seal_tests':'2/2 parents plus 7 seal subcases; exact12MiB and oversize/zero/directory/sharing checks','actual_candidate_loader_test':'1/1 no skip, real independent bundle and pinned node, default loader refuses','commands':results,'native_observation':{'checkpoint_bytes':88762,'checkpoint_sequence':6,'paused_sequence':7,'same_run_epoch_transition':[1,2],'restored_commands_consumed':2,'cumulative_model_calls':3,'original_prompt_count':1,'old_process_pid':37780,'new_process_pid':51360,'physical_process_stopped':True,'streams_drained':True,'cleanup_complete':True,'output_copied':True,'core_artifact_use_journal':'SYNTHETIC_FIXTURE_ONLY'},'tool_no_replay':'Existing production worker process test preserved completed read TOOL count and result; resumed TOOL effects zero.'},
 'independent_reviewer_corrections':[{'attempt':'runs/node.json','exit':1,'reason':'Reviewer omitted RESEARCHOS_QUEUE_WORKER_BUNDLE required by unchanged control regression; added explicit independent bundle environment and reran as node-r2.'},{'attempt':'runs/host.json','exit':1,'reason':'Minimal source archive omitted three local evaluation packages; git-archived exact candidate packages and reran as host-r2.'},{'attempt':'runs/independent-node.json','exit':1,'reason':'Reviewer harness generation assertion expected delimiter newline removed by split; no generated test existed. Fixed generation assertion and reran independent-node-r2.'},{'attempt':'read-only census console inspection','reason':'First Python read used default Windows encoding and failed JSON parsing. Explicit UTF-8 used by final audit; all compiled input hashes verified.'}],
 'boundaries':{'root_source_writes':False,'author_source_writes':False,'frozen_sdk_writes':False,'canon_writes':False,'original_db_access':False,'real_desktop_or_core_process_control':False,'gui_or_cdp_calls':False,'api_calls':False,'provider_or_real_model_calls':0,'installed_assets_writes':False,'M1_02_core_canonical_ledger_artifact_use_activation_CAS':'OPEN_NOT_IMPLEMENTED_OR_ACCEPTED_BY_THIS_REVIEW','live_provider_or_real_current_run_pause_resume':'NOT_VERIFIED','formal_increment':0,'formal_cases':'0/42','all_22_parent_tasks':'OPEN'},'evidence_root':str(R),'input_validation_sha256':sha(R/'input-validation.json')}
save('FINAL-report.json',report)
members=[]
for p in sorted(R.rglob('*')):
 if p.is_file() and p.name!='FINAL-manifest.json':members.append({'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
save('FINAL-manifest.json',{'schema':'researchos.mu-m1-01-review-manifest/1','report_sha256':sha(R/'FINAL-report.json'),'members':members})
print(json.dumps({'report_sha256':sha(R/'FINAL-report.json'),'manifest_sha256':sha(R/'FINAL-manifest.json'),'members':len(members),'verdict':report['verdict']}))
