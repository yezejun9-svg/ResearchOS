import ast,hashlib,json,re
from pathlib import Path
O=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
def pin(p):
 b=Path(p).read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
def read(n):return (O/n).read_text(encoding='utf-8')
inv=json.loads(read('source-inverse.json'));c=read('w09_evidence_closure.v6.proposed.py');router=read('w09_formal_router.v6.proposed.py');g=read('retrieval_test.v6.proposed.go')
checks=[]
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)})
 if not v:raise ValueError(n)
for pair in inv['pairs']:
 ck('newpin '+Path(pair['new']['path']).name,pin(pair['new']['path'])==pair['new'])
 old=Path(pair['old']['path']).read_bytes();new=Path(pair['new']['path']).read_bytes()
 if Path(pair['new']['path']).suffix=='.py':
  aa=ast.parse(old);bb=ast.parse(new)
  if 'closure' in pair['new']['path']:changed={'verify_owned','verify_a06','verify_mode'}
  elif 'router' in pair['new']['path']:changed={'_owned_exact'}
  else:changed=set()
  olddefs={x.name:ast.dump(x,include_attributes=False) for x in aa.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
  newdefs={x.name:ast.dump(x,include_attributes=False) for x in bb.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
  ck('same top defs '+Path(pair['new']['path']).name,set(olddefs)==set(newdefs))
  for name in olddefs:
   if name not in changed:ck('unchanged def '+name,olddefs[name]==newdefs[name])
 if 'retrieval_test' in pair['new']['path']:
  for pat in [r't\.(?:Fatal|Fatalf)\([^\n]*',r'f\.s\.MaterializeTaskContext\([^\n]*',r'w09Assertion\(t,[^\n]*']:
   ck('Go original calls preserved '+pat,re.findall(pat,old.decode())==re.findall(pat,new.decode()))
constant=next(n for n in ast.parse(c).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='A06_MANIFEST_RAW_LABELS' for t in n.targets))
labels=ast.literal_eval(constant.value.args[0])
ck('only two exact opaque raw labels',labels=={'a06-materialize-v1-manifest','a06-materialize-after-delete-manifest'})
ck('router consumes same label constant','safe_repo_rel, A06_MANIFEST_RAW_LABELS' in router and 'label in A06_MANIFEST_RAW_LABELS' in router)
ck('typed witness shape unchanged','set(claim) == {"path", "sha256", "bytes"}' in c)
ck('outputpin from verified payload','witness_values["researchos.w09-junction-witness.v1"].get("output_pin")' in c and 'junction.get("output_pin")' not in c)
ck('strong structured owner unchanged','item.get("_run_id") == report["run_id"]' in c and 'item.get("_test_name") == path.parent.name' in c)
ck('single exact raw label and same owner','A06_MATERIALIZE_EXACT_RAW_LABEL' in c and '_raw_pin(claim, members, test)' in c)
ck('fullbundle before v1 and later raw unchanged callsites','"bundle": bundle, "bundle_ref": Ref(bundle, "ContextBundle")' in g and '"bundle": newBundle, "bundle_ref": Ref(newBundle, "ContextBundle")' in g)
sourceproof={}
for rel in ['internal/domain/materialize.go','internal/domain/context.go','internal/domain/context_test.go','internal/domain/contracts.go']:
 p=R/rel;sourceproof[rel]=pin(p)
mat=(R/'internal/domain/materialize.go').read_text(encoding='utf-8')
context=(R/'internal/domain/context.go').read_text(encoding='utf-8')
ct=(R/'internal/domain/context_test.go').read_text(encoding='utf-8')
ck('actual materialize return schema','manifest := Object{"project_id": project, "task_id": taskID, "bundle_ref": Ref(bundle, "ContextBundle"), "version_vector": bundle["version_vector"], "input_manifest": entries, "source_manifest_hash": bundle["source_manifest_hash"]' in mat)
ck('actual authorized snapshots enter versionvector','for _, rawID := range snapshotIDs {' in context and 'refs = append(refs, Ref(a, "Artifact"))' in context)
ck('actual bundle HTTP status and path', 'return f.expect(201, "POST", f.path("/context-bundles")' in ct)
def loc(text,needle,file):
 return {'path':str(O/file),'line':next(i+1 for i,l in enumerate(text.splitlines()) if needle in l)}
matrix=[
{'id':'R01-positive','case':'Only original two A06 business manifests opaque; structured owning events mandatory','producer':'w09ExportRaw(Bytes(actualManifest)) inside original successful Materialize call; w09ExportEvent wraps call facts','consumer':loc(c,'if label.startswith(opaque)','w09_evidence_closure.v6.proposed.py'),'static_result':'finite exact label classification; no _run_id invented on original business JSON'},
{'id':'R01-negative-unknown-label','case':'Other a06-* JSON lacking _run_id/_test_name','consumer':loc(c,'item = json.loads(data)','w09_evidence_closure.v6.proposed.py'),'static_result':'still structured/owner checked; no broad a06 skip'},
{'id':'R01-negative-swap','case':'Initial event references later manifest or other same-test raw','consumer':loc(c,'require(len(expected) == 1','w09_evidence_closure.v6.proposed.py'),'static_result':'exact label/pin and distinct path plus original call order reject'},
{'id':'R02-positive','case':'Typed three-key junction REF -> guarded raw read -> same-run verified witness payload -> output_pin','consumer':loc(c,'witness_values["researchos.w09-junction-witness.v1"].get("output_pin")','w09_evidence_closure.v6.proposed.py'),'static_result':'REF remains strict3; payload output matched to actual event raw pin'},
{'id':'R02-negative','case':'Missing/wrong output_pin, run/report/source/command or target/root','consumer':loc(c,'witness_values["researchos.w09-junction-witness.v1"].get("output_pin")','w09_evidence_closure.v6.proposed.py'),'static_result':'same-run guards, full six argv, decision roots and _raw_pin reject'},
{'id':'R03-positive','case':'Original f.bundle HTTP response -> full bundle event -> Materialize manifest identity and inputs -> captured original/deleted snapshot rows','consumer':loc(c,'def materialize_result(','w09_evidence_closure.v6.proposed.py'),'static_result':'actual product schema is used: project/task/bundle_ref/version_vector/source_manifest_hash/input_manifest; original calls and assertions unchanged'},
{'id':'R03-negative-missing','case':'Missing raw/ref/bundle/entry/hash/ID/HTTP event','consumer':loc(c,'def materialize_result(','w09_evidence_closure.v6.proposed.py'),'static_result':'strict guards/indexing fail closed before formal PASS'},
{'id':'R03-negative-substitution','case':'Different task/bundle/project/principal/root or swapped initial/later valid same-test raw','consumer':loc(c,'A06_MATERIALIZE_TASK_BUNDLE_JOIN','w09_evidence_closure.v6.proposed.py'),'static_result':'manifest exact event identity/HTTP result/owner label/order reject'},
{'id':'R03-negative-exclusion','case':'Wrong original/deleted artifact ID, foreign content hash, excluded IDs remain in later input_manifest','consumer':loc(c,'A06_MATERIALIZE_SNAPSHOT_EXCLUSION_JOIN','w09_evidence_closure.v6.proposed.py'),'static_result':'actual snapshot rows/body hashes and later manifest inputs reject'},
{'id':'R03-negative-call','case':'Stale-rejection target/error moved to another call, same raw reused','consumer':loc(c,'A06_MATERIALIZE_TARGET_OR_REJECTION','w09_evidence_closure.v6.proposed.py'),'static_result':'exact target from frozen test root parent, nonempty original error, original sequence and two distinct refs'},
{'id':'preserved-R1','case':'20 simulation raw plus20 binding events and threePOST joins','static_result':'verify_c19 exact AST unchanged'},
{'id':'preserved-R2','case':'native sealed report/raw -> later nonauthor review -> readonly W09 consumer, no rerun','static_result':'retrieval wholebytes same; main/_pinned_native_report/verify_native/decision flow same'},
{'id':'preserved-R3','case':'typedROOTREL/reparse before witness read,6argv/root/target same run','static_result':'safe_repo_rel/safe_repo_pin exact AST same; only output source corrected'}
]
for row in matrix:row['runtime_test_status']='NOT_RUN';row['candidate_function_executed']=False
matrixref=put('producer-consumer-static-matrix.json',{'schema':'researchos.w09-v6-static-dataflow-matrix.v1','rows':matrix,'source_contract_refs':sourceproof,'candidate_calls':0,'no_runtime_PASS_claim':True})
auditref=put('author-static-supplement.json',{'schema':'researchos.w09-v6-author-static-supplement.v1','checks':checks,'failed':[],'source_proofs':sourceproof,'candidate_imported':False,'candidate_executed':False,'new_failure_count':0})
report=put('report.json',{'schema':'researchos.w09-v6-source-report.v1','author':'codex:/root/w05_merge_review','decision':'REVIEW_REQUESTED','self_acceptance':False,'repairs':{'R01':'Only two precise raw materialization labels; one shared classifier constant consumed by router and closure. Event owner checks retained.','R02':'output_pin from already verified junction witness payload; typed REF remains exact3.','R03':'Original bundle JSON/ref captured at existing call sites. Exact raw labels/order, actual original HTTP bundle response, project/task/bundle/version/hash/input entries/snapshot ID and exclusion joins; exact materialize destination and original error event.'},'candidate_source_refs':[x['new'] for x in inv['pairs']],'inverse_ref':pin(O/'source-inverse.json'),'static_audit_ref':pin(O/'static-audit.json'),'static_supplement_ref':auditref,'dataflow_matrix_ref':matrixref,'preserved':'v5 simulation20+20, C19 POST graph, two-stage no-rerun contract, witness path guard, business/native selectors/assertions all retained. Three sources exact copied.','historical_I01':'OPEN; earliest overwritten bytes and adjacent wrapper not restored. v6 is a new source packet only.','runtime_positive_negative_controls':'NOT_RUN; static tracing only','formal_case_accepted_delta':0,'source_acceptance':False,'candidate_calls':0,'new_failure_origin_refs':[],'required_next':'Different non-author independently reviews concrete v6 source and contracts; Root scope/adoption/grant/execution remain separate.','stage':'STOPPED_SOURCE_PREPARATION_ONLY'})
handoff=put('handoff.json',{'schema':'researchos.w09-v6-source-preparation-handoff.v1','author':'codex:/root/w05_merge_review','decision':'REVIEW_REQUESTED','candidate_source_refs':[x['new'] for x in inv['pairs']],'report_ref':report,'source_inverse_ref':pin(O/'source-inverse.json'),'dataflow_matrix_ref':matrixref,'prior_independent_review_ref':inv['input_review_ref'],'historical_I01':'OPEN','new_failure_origin_refs':[],'formal_case_accepted_delta':0,'source_acceptance':False,'actual_native_or_formal_run':False,'independent_review_required':True,'manifest_filename':'manifest.json','status':'STOPPED'})
entries=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']
mf=put('manifest.json',{'schema':'researchos.w09-v6-source-preparation-manifest.v1','members':entries,'member_count':len(entries),'self_excluded':True,'formal_case_accepted_delta':0,'source_acceptance':False,'historical_I01':'OPEN'})
print(json.dumps({'report_ref':report,'handoff_ref':handoff,'manifest_ref':mf,'supplement_checks':len(checks),'matrix_ref':matrixref,'source_inverse_ref':pin(O/'source-inverse.json'),'new_failure_count':0,'decision':'REVIEW_REQUESTED'},ensure_ascii=False))

