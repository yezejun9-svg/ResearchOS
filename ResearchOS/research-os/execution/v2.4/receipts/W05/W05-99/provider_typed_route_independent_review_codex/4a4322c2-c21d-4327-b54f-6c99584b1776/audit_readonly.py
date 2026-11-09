import json,hashlib,pathlib,gzip,subprocess,datetime
MAIN=pathlib.Path.cwd();WT=MAIN/'.local/worktrees/codex-w0599-provider-binding';P=WT/'execution/v2.4/receipts/W05/W05-99/provider_binding_executor_codex/typed-route-final-6c47a88a198349b4bd2a3d3d223510b1';OUT=MAIN/'execution/v2.4/receipts/W05/W05-99/provider_typed_route_independent_review_codex/4a4322c2-c21d-4327-b54f-6c99584b1776'
def j(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def w(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
errors=[];sources=[]
for n,v in j(P/'source9.freeze.json').items():
 actual=ref(WT/n);blob=subprocess.run(['git','show','6fb5263681c17f0e50920c354dc07ed440a23714:'+n],cwd=WT,capture_output=True,check=True).stdout
 base=subprocess.run(['git','show','976c8c9a6bdf8703475e02b79b77f4c5fab2d650:'+n],cwd=WT,capture_output=True,check=True).stdout
 modified=n in ['internal/domain/runtime_model_verification.go','internal/domain/runtime_provider_binding_windows_test.go']
 d={'path':n,'actual':actual,'git_candidate_sha256':hashlib.sha256(blob).hexdigest(),'base976_sha256':hashlib.sha256(base).hexdigest(),'allowed_changed':modified}
 if actual['sha256']!=v['current']['sha256'] or actual['sha256']!=d['git_candidate_sha256'] or (not modified and actual['sha256']!=d['base976_sha256']):errors.append(d)
 sources.append(d);q=OUT/'actual_reads'/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((WT/n).read_bytes())
for n in ['internal/domain/runtime_dispatch.go','internal/domain/contracts.go','internal/domain/backup.go','internal/domain/backup_command_queue.go','internal/domain/backup_test.go','internal/domain/backup_command_queue_test.go']:
 q=OUT/'actual_reads'/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((WT/n).read_bytes())
inputs=[]
for name,v in j(P/'original-inputs.before.json').items():
 a=ref(pathlib.Path(v['original']['path']));b=ref(pathlib.Path(v['copy']['path']));inputs.append({'id':name,'original':a,'author_copy':b})
 if a['sha256']!=v['original']['sha256'] or b['sha256']!=a['sha256']:errors.append({'db_hash_mismatch':name})
results=[];total={'pass':0,'fail':0,'skip':0};summary=j(P/'execution-summary.json')
for item in summary['outcomes']:
 name=item['case'];r=j(P/(name+'.result.json'));events=[json.loads(line) for line in pathlib.Path(r['stdout']['path']).read_text(encoding='utf-8').splitlines() if line.strip()];counts={a:sum(e.get('Action')==a and bool(e.get('Test')) for e in events) for a in total}
 for a,c in counts.items():total[a]+=c
 for key in ['stdout','stderr']:
  a=ref(pathlib.Path(r[key]['path']))
  if a['sha256']!=r[key]['sha256']:errors.append({'raw_hash':name,'channel':key})
 if r['exit']!=0 or counts!={'pass':1,'fail':0,'skip':0}:errors.append({'outcome':name,'counts':counts,'exit':r['exit']})
 d={'case':name,'result_ref':ref(P/(name+'.result.json')),'raw':{'stdout':r['stdout'],'stderr':r['stderr']},'counts':counts,'exit':r['exit']}
 if name.startswith('case-'):
  spec=j(P/(name+'.json'));folder=pathlib.Path(spec['output']);actual=j(folder/'actual.json');b=json.loads(gzip.decompress((folder/'semantic-before.json.gz').read_bytes()));a=json.loads(gzip.decompress((folder/'semantic-after.json.gz').read_bytes()));changed=[t for t in b['tables'] if b['tables'][t]!=a['tables'].get(t)];schema_equal=b['schema']==a['schema'];positive=not spec['want_error'];
  d.update({'spec_ref':ref(P/(name+'.json')),'actual_ref':ref(folder/'actual.json'),'semantic_before_ref':ref(folder/'semantic-before.json.gz'),'semantic_after_ref':ref(folder/'semantic-after.json.gz'),'positive':positive,'complete_semantic_equal':a==b,'schema_equal':schema_equal,'changed_tables':changed,'allowed_tables':spec['allowed_mutation_tables'],'inventory_error':actual.get('inventory_error'),'stream_backup_error':actual.get('stream_backup_error'),'inventory_count':actual.get('inventory_count')})
  if not schema_equal or set(a['tables'])!=set(b['tables']) or not set(changed)<=set(spec['allowed_mutation_tables']) or (spec['mutation']=='none' and a!=b):errors.append({'semantic':name,'changed':changed})
 results.append(d)
prod=(WT/'internal/domain/runtime_model_verification.go').read_bytes();old=(P/'source-snapshot/internal__domain__runtime_model_verification.go.before').read_bytes();suffix=b'func providerSSEChunks';prefix=b'func providerOriginalRun'
protected={'prefix_before_originalRun_equal':prod.split(prefix)[0]==old.split(prefix)[0],'suffix_providerSSEChunks_equal':prod[prod.index(suffix):]==old[old.index(suffix):]}
if not all(protected.values()):errors.append({'protected':protected})
w('source_and_raw_audit.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':'6fb5263681c17f0e50920c354dc07ed440a23714','source9':sources,'original7_inputs':inputs,'case_counts':total,'actual_case_results':results,'protected_production_segments':protected,'errors':errors,'calls_executed_in_review':{'cases':0,'sql':0,'http':0,'models':0,'workers':0},'author_manifest_ref':ref(P/'manifest.json'),'author_handoff_ref':ref(P/'handoff.json')})
print(json.dumps({'sources':len(sources),'original_inputs':len(inputs),'raw_cases':len(results),'counts':total,'protected':protected,'errors':errors},ensure_ascii=False))
