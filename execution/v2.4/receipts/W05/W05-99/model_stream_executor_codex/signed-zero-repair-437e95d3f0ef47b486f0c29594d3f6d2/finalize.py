import pathlib,json,hashlib,subprocess,datetime,concurrent.futures
D=pathlib.Path(__file__).resolve().parent; R=D.parents[6]; M=pathlib.Path('D:/作品集/ResearchOS/research-os')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def save(n,x):
 with (D/n).open('x',encoding='utf8') as f: json.dump(x,f,ensure_ascii=False,indent=2); f.write('\n')
product=['internal/domain/runtime_model_stream.go','internal/domain/runtime_model_stream_test.go','apps/cli/cli_model_stream_integration_windows_test.go']
baseline='890d4c164bffad73e562ceacfdc216820d0313fd'
rows=[]
for name in product:
 raw=subprocess.check_output(['git','show',baseline+':'+name],cwd=R); dest=D/'before-source'/name; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(raw)
 rows.append({'path':name,'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':sha(R/name),'before_snapshot':ref(dest)})
save('product_source.json',{'baseline':baseline,'exact_paths':rows})
cohorts=[]
current={}
for name in ['closure-6f4e2cb1bf1d4aa48376dbc02eeb2b8c','closure-39d83fc9302f42ceb4e91d3403a96044']:
 c=D.parent/name; result=json.loads((c/'result.json').read_text()); before=json.loads((c/'source_before.json').read_text()); after=json.loads((c/'source_after.json').read_text())
 drift=[]
 def current_file(key):
  kind,rel=key.split(':',1); return R/rel if kind=='repo' else M/rel if kind=='main' else pathlib.Path(rel)
 def hash_current(key):
  p=current_file(key); return key,sha(p) if p.is_file() else 'MISSING'
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  current.update(pool.map(hash_current,[key for key in after if key not in current]))
 for key,value in after.items():
  kind, rel=key.split(':',1); file=(R/rel if kind=='repo' else M/rel if kind=='main' else pathlib.Path(rel))
  actual=current[key]
  if actual!=value: drift.append(key)
 lines=(c/'test.stdout').read_text(encoding='utf8').splitlines()
 counts={k:sum(line.lstrip().startswith('--- '+k+':') for line in lines) for k in ['PASS','FAIL','SKIP']}
 assert result['exit']==0 and before==after and not drift and counts['PASS']>0 and counts['FAIL']==0 and counts['SKIP']==0,(name,result,counts,drift)
 cohorts.append({'path':c.relative_to(R).as_posix(),'result_ref':ref(c/'result.json'),'invocation_ref':ref(c/'test.invocation.json'),'counts_inclusive':counts,'input_count':len(before),'before_after_current_equal':True})
save('cohort_verification.json',cohorts)
old=json.loads((D.parent/'closure-86d60d4092df4d1896858f6001034b37/source_before.json').read_text())
new=json.loads((D.parent/'closure-39d83fc9302f42ceb4e91d3403a96044/source_before.json').read_text())
save('prior_closure_inventory_delta.json',{'prior_input_count':len(old),'current_input_count':len(new),'removed':{k:old[k] for k in old.keys()-new.keys()},'added':{k:new[k] for k in new.keys()-old.keys()},'changed':{k:{'before':old[k],'after':new[k]} for k in old.keys()&new.keys() if old[k]!=new[k]},'note':'Current actual collected inventory is not labeled identical to previous39053 inputs; compare absent inputs to actual go-list and bundle source. No absent file restored.'})
status=subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=no'],cwd=R)
(D/'git-status.stdout').write_bytes(status)
deletions=[]
for line in status.decode('utf8').splitlines():
 if line.startswith(' D '):
  deletions.append(line)
save('initial_unowned_deletions_preserved.json',{'observed_again_at_finalization':deletions,'reported_to_root_before_edits':True,'root_confirmed_preserve':True,'not_restored_or_staged':True,'impact':'Current actual go-list/compiled closure and executed tests pass without these unrelated worktree files. Their original blobs remain in Git; the candidate does not stage their deletion. No global-clean claim.'})
patch=subprocess.check_output(['git','diff','--binary','--',*product],cwd=R); (D/'product.patch').write_bytes(patch)
save('failure_origins.json',{'new_expected_pre_fix_red':ref(D/'red.invocation.json'),'original_independent_failure':ref(D/'signed-zero-go.invocation.json'),'prior_890d_failure_origins':'execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/quarantine-repair-d0b997f135f24c748c6e99e98a5e7f01/failure_origins.json','reset_or_overwrite':False,'new_unexpected_test_failure_count':0,'diagnostic_read_failure':{'tool_chunk':'4fefa7','exit':1,'actual_operation':'PowerShell foreach count summary piped directly to ConvertTo-Json','raw_error':'ParserError: An empty pipe element is not allowed.','corrected_read_chunk':'c01691','test_outputs_modified':False}})
save('handoff.json',{'schema':'researchos.model-stream-signed-zero-repair.v1','status':'CANDIDATE_FOR_INDEPENDENT_REVIEW_ONLY','actor':'codex:/root/sources_parent_impl','baseline':baseline,'change':'SDK SameValueZero numeric Map key equivalence: canonicalize both binary64 signed zeros before tool lane indexing; retain existing full float64 number identity. SDK/JS/schema unchanged.','source_ref':ref(D/'product_source.json'),'same_input_raw_ref':ref(D/'signed-zero.sse'),'raw_sha256_expected':'fcdd996ddbdc4b1d41cddd072db831ec6d1d8c63bc83abd8ee780997be1f3920','red_ref':ref(D/'red.invocation.json'),'green_ref':ref(D/'green.invocation.json'),'fixed_sdk_semantic_positive_ref':ref(D/'sdk.invocation.json'),'cohorts':cohorts,'integration':'New secret-tool-json-signed-zero actual SDK/runtime/SQLite/compiled CLI case must retain prefix OBSERVED, reject protected tool-argument string preSDK, UNKNOWN and no END; same public synthetic token only. Original unrelated controls remain in full suite.','failure_origins_ref':ref(D/'failure_origins.json'),'unowned_deletions_ref':ref(D/'initial_unowned_deletions_preserved.json'),'paid_calls':0,'private_db_or_vault_reads':0,'formal_acceptance':False,'still_open':['F08 immutable idempotency ACK→final1811','Provider9 source/qualification not implemented','Old legacy failures and W14 UNKNOWN remain untouched']})
save('manifest.json',{'files':[ref(p) for p in sorted(D.rglob('*')) if p.is_file()]})
print(json.dumps({'handoff':ref(D/'handoff.json'),'manifest':ref(D/'manifest.json'),'cohorts':cohorts},ensure_ascii=False))
