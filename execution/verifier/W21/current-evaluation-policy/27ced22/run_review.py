from pathlib import Path
import datetime,hashlib,json,os,subprocess
root=Path(r'D:/作品集/ResearchOS/research-os');out=Path(__file__).parent
go=root/'.local/tools/go1.27.1/go/bin/go.exe'
target='27ced22e73da7631d65bdd6e1844de24dd198065'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
git=lambda *a:subprocess.check_output(['git','-C',str(root),*a]).decode('utf-8').strip()
write=lambda name,value:(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
paths=git('ls-files','*.go','*.sql','go.mod','go.sum','spec/v2.0/contracts/*.json','adapters/protectedstore/frozen_development.json','execution/toolchains/locked.json').splitlines()
def snapshot():return {'head':git('rev-parse','HEAD'),'tracked_status':git('status','--porcelain','--untracked-files=no'),'files':{p:sha(root/p) for p in paths}}
before=snapshot();write('source-before.json',before)
assert before['head']==target
locked=load(root/'execution/toolchains/locked.json')['tools']['go'];assert str(go).replace('/','\\').lower()==locked['path'].lower() and sha(go)==locked['sha256']
prior={c:load(root/f'execution/receipts/W11/{run}/{c}.json') for c,run in [('C07','8a5ca295-69c0-4ebd-9ae3-8a8e266bc942'),('C08','8a5ca295-69c0-4ebd-9ae3-8a8e266bc942'),('A08','6b9ede5e-9edb-4f07-af80-d8220ba6ccfa')]}
scope_paths=['internal/domain/'+x for x in ['decision.go','decision_test.go','decision_regression_test.go','decision_boundaries_test.go','qualification.go','qualification_live.go','qualification_import.go','domain_test.go','context_test.go','orchestration_test.go','runtime_test.go','orchestration.go','runtime.go','runtime_dispatch.go','acceptance.go','changes.go','change_impact.go','store.go','http.go','contracts.go','protected_artifacts.go']]+['adapters/decision/jev.go','adapters/protectedstore/frozen_summary.go','adapters/protectedstore/frozen_development.go','adapters/protectedstore/frozen_development.json','evaluation/holdout/jev/rubric.go','internal/canonical/jcs.go','internal/store/sqlite.go']
comparison={}
for case,receipt in prior.items():
 inventory=receipt['version_manifest']['source_sha256'];base=receipt['version_manifest']['git_head']
 rows=[]
 for p in scope_paths:
  actual=sha(root/p);accepted=inventory.get(p);status='UNCHANGED_EXACT_RECORDED_BYTES' if accepted==actual else 'CHANGED' if accepted else 'NOT_IN_ACCEPTED_INVENTORY'
  blob_equal=git('rev-parse',base+':'+p)==git('rev-parse',target+':'+p) if accepted else None
  rows.append({'path':p,'current_sha256':actual,'accepted_sha256':accepted,'status':status,'git_blob_equal':blob_equal})
 comparison[case]={'accepted_revision':base,'subset_only':True,'dependency_closure_complete':'NOT_CLAIMED','files':rows}
write('historical-source-comparison.json',comparison)
accepted=load(root/'execution/verifier/W11/6b9ede5e-9edb-4f07-af80-d8220ba6ccfa.json')
manifest_path=root/accepted['artifact_manifest_reference'];assert sha(manifest_path)==accepted['artifact_manifest_sha256']
manifest={x['path']:x for x in load(manifest_path)['files']}
evidence=[]
for lang in ['zh','zh-en']:
 for suffix in ['qualification-before','acceptance-persisted','qualification-persisted','public-summary-artifact','public-summary-content']:
  p=f'execution/verifier/W11/product-live-591d16e/{lang}-{suffix}.response.json';d=manifest[p];actual=sha(root/p);assert actual==d['sha256'];evidence.append({'path':p,'sha256':actual,'matches_accepted_manifest':True})
write('accepted-public-inputs.json',{'acceptance_receipt_sha256':sha(root/'execution/verifier/W11/6b9ede5e-9edb-4f07-af80-d8220ba6ccfa.json'),'artifact_manifest_sha256':sha(manifest_path),'files':evidence,'qualification_state':accepted['qualification_state'],'service_freshness':'NOT_QUERIED_UNVERIFIED'})
overlay={'Replace':{str(root/'internal/domain/zz_independent_w21_a08_policy_test.go'):str(out/'accepted_a08_policy_test.go')}};write('overlay.json',overlay)
env=os.environ.copy();env.update(GOENV='off',GOTOOLCHAIN='local',GOWORK='off',GOPROXY='off',GOSUMDB='off',GOFLAGS='-mod=readonly',RESEARCHOS_GO=str(go))
cmd=[str(go),'test','-overlay',str(out/'overlay.json'),'./internal/domain','-run','^(TestW11HardGates|TestW11ManualDecisionHardGate|TestW11HostAndFallback|TestW11PromptBoundaries|TestIndependentW21AcceptedA08PolicyReferences)$','-count=1','-json']
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out/'tests.raw.jsonl').open('wb') as stdout,(out/'tests.stderr.log').open('wb') as stderr:
 result=subprocess.run(cmd,cwd=root,env=env,stdout=stdout,stderr=stderr,timeout=180)
(out/'tests.exit.txt').write_text(str(result.returncode)+'\n',encoding='utf-8')
after=snapshot();write('source-after.json',after)
events=[json.loads(x) for x in (out/'tests.raw.jsonl').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
assertions=[];chunks={}
for event in events:chunks.setdefault(event.get('Test',''),[]).append(event.get('Output',''))
for test,parts in chunks.items():
 for text in ''.join(parts).splitlines():
  for prefix in ['W11_ASSERTION ','R03_ASSERTION ']:
   if text.startswith(prefix):
    a=json.loads(text[len(prefix):]);assertions.append({'test':test,'assertion_id':a['assertion_id'],'status':a['status'],'expected':a.get('expected'),'actual':a.get('actual'),'scope':'PUBLIC_FIXTURE_ONLY' if prefix.startswith('W11') else 'PUBLIC_ACCEPTED_AGGREGATE_PURE_BINDING_ONLY'})
write('assertion-results.json',assertions)
record={'argv':cmd,'cwd':str(root),'environment':{k:env[k] for k in ['GOENV','GOTOOLCHAIN','GOWORK','GOPROXY','GOSUMDB','GOFLAGS','RESEARCHOS_GO']},'go_sha256':sha(go),'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':result.returncode,'raw_sha256':sha(out/'tests.raw.jsonl'),'stderr_sha256':sha(out/'tests.stderr.log'),'source_files_count':len(paths),'source_unchanged':before['files']==after['files'],'pass':[e['Test'] for e in events if e.get('Action')=='pass' and e.get('Test')],'skip':[e['Test'] for e in events if e.get('Action')=='skip' and e.get('Test')],'fail':[e.get('Test',e.get('Package')) for e in events if e.get('Action')=='fail'],'assertion_count':len(assertions),'failed_assertions':[a['assertion_id'] for a in assertions if a['status']!='PASS']}
write('command.json',record);print(json.dumps({k:v for k,v in record.items() if k not in ['argv','environment','pass']},ensure_ascii=True))
