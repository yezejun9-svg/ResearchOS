import ast,difflib,hashlib,json,re
from pathlib import Path
O=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
S=R/'execution/v2.4/receipts/W09/W09-99/w09_evidence_v5_source_preparation_codex/a1c93c361f85414db51b6aded781ab16'
C=[]
def ck(n,v,detail=None):C.append({'check':n,'passed':bool(v),'detail':detail})
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def doc(p):return json.loads(Path(p).read_bytes())
def verify(r):
 p=Path(r['path']);a=ref(p);ck('pin '+p.name,a['sha256']==r['sha256'] and a['bytes']==r['bytes']);return p.read_bytes()
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(O/n)
h=doc(S/'handoff.json');m=doc(S/'manifest.json');inv=doc(S/'source-inverse.json')
for name,sha in [('handoff.json','689588964835ebbd776fa9d4cb6fe046c2aae77001a0bb9a4322974ad7afcc84'),('manifest.json','89f35a999f30c4eb6edc8a90fc14e8e4947279de666ff35099111cf04dbc4026'),('source-inverse.json','42280a05776bfbfbb442543561e3686e6bef43bf81a9e5f6407389014a394ac6'),('report.json','82e43a6be9bef384272e811d511a4f5bdd186623ca9d7141d06e45686206c241')]:
 ck('supplied exactpin '+name,ref(S/name)['sha256']==sha)
ck('manifest14',len(m['members'])==m['member_count']==14)
ck('unique and own members',len({r['path'] for r in m['members']})==14 and all(Path(r['path']).parent==S for r in m['members']))
for r in m['members']:verify(r)
verify(inv['baseline_review_ref'])
oldreview=doc(inv['baseline_review_ref']['path'])
ck('prior REQUEST and I01',oldreview['decision']=='REQUEST_CHANGES' and any(f['id']=='W09-V4-I01-UNRECOVERED-INITIAL-SEAL' for f in oldreview['important_findings']))
pairs=[];sources={};patches={Path(x['path']).name:x for x in inv['four_changed_unified_diff_refs']}
for pair in inv['six_source_pairs']:
 old=verify(pair['old']);new=verify(pair['new']);p=Path(pair['new']['path']);sources[p.name]=new.decode('utf-8')
 ck('exact_copy declaration '+p.name,(old==new)==pair['exact_copy'])
 if not pair['exact_copy']:
  patch=verify(patches[p.name+'.patch']).decode('utf-8')
  generated=''.join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile='v4/'+Path(pair['old']['path']).name,tofile='v5/'+p.name))
  ck('whole unified diff exact '+p.name,generated==patch)
 if p.suffix=='.py':
  tree=ast.parse(new,filename=str(p));ck('AST '+p.name,True)
  if 'router' in p.name:
   oldt=ast.parse(old);names=inv['preserved_router_selector_AST']
   def assignments(t):
    return {target.id:ast.dump(node.value,include_attributes=False) for node in t.body if isinstance(node,ast.Assign) for target in node.targets if isinstance(target,ast.Name)}
   aa,bb=assignments(oldt),assignments(tree)
   for name in names:ck('router selector unchanged '+name,aa[name]==bb[name])
  if 'retrieval.v5' in p.name:
   pairs.append({'file':p.name,'old_ref':pair['old'],'new_ref':pair['new'],'delta_reviewed':'exclusive report/raw; postrun producer tool-run; native command unchanged'})
  if p.name.startswith('w09_evidence_closure'):
   ck('no subprocess calls in closure source','subprocess' not in sources[p.name])
 if p.name=='retrieval_test.v5.proposed.go':
  def messages(raw):return re.findall(r't\.(?:Fatal|Fatalf)\((.*?)\)',raw.decode(),re.S)
  ck('all prior Go failure assertion calls retained',messages(old)==messages(new))
  # Both snapshots and the same original three call arguments remain.
  rx=r'f\.s\.MaterializeTaskContext\([^\n]+?\)'
  ck('Materialize calls same count and arguments',re.findall(rx,old.decode())==re.findall(rx,new.decode()))
 pairs.append({'old_ref':pair['old'],'new_ref':pair['new'],'exact_copy':pair['exact_copy']})
closure=sources['w09_evidence_closure.v5.proposed.py'];router=sources['w09_formal_router.v5.proposed.py'];go=sources['retrieval_test.v5.proposed.go'];export=sources['w09_evidence_export_test.v5.proposed.go']
def loc(name,needle):
 lines=sources[name].splitlines();return {'path':str(S/name),'line':next(i+1 for i,x in enumerate(lines) if needle in x)}
ck('R1 exact00-19 raw labels',r'simulated-opinion-(?:0[0-9]|1[0-9])' in closure and r'simulated-opinion-(?:0[0-9]|1[0-9])' in router)
ck('R1 structured bindings retained','events.get("simulated-opinion-binding", [])' in closure and 'SIM_ORDINAL_BODY_SWAP' in closure)
ck('R2 post-run readonly branch source','source, report, tool = _pinned_native_report()' in router and 'NOT_RUN_POSTRUN_REVIEW_PENDING' in sources['retrieval.v5.proposed.py'])
ck('R2 native run removed from W09 formal branch','str(ROOT / "ops/ci/retrieval.py")' not in router)
ck('R3 typedref exact3 and guarded reads','set(claim) == {"path", "sha256", "bytes"}' in closure and 'path.lstat()' in closure and 'FILE_ATTRIBUTE_REPARSE_POINT' in closure)
ck('R3 six-token argv source','["cmd.exe", "/c", "mklink", "/J",' in closure and 'junction_event["target_path"]]' in closure)
ck('R4 C19 three actual POST joins',all(x in closure for x in ['exact_exchange("POST", "/content"','exact_exchange("POST", "/artifacts"','exact_exchange("POST", "/evidence"']))
materialize=R/'internal/domain/materialize.go';mat=materialize.read_text(encoding='utf-8')
ck('actual manifest no event ownership','manifest := Object{"project_id": project, "task_id": taskID,' in mat and '"_run_id"' not in mat and '"_test_name"' not in mat)
findings=[
{'id':'W09-V5-R01-A06-RAW-MANIFEST-CLASSIFICATION','severity':'BLOCKER','locations':[loc('retrieval_test.v5.proposed.go','w09ExportRaw(t, "a06-materialize-v1-manifest"'),loc('retrieval_test.v5.proposed.go','w09ExportRaw(t, "a06-materialize-after-delete-manifest"'),loc('w09_evidence_closure.v5.proposed.py','opaque = ('),loc('w09_evidence_closure.v5.proposed.py','item = json.loads(data)')],'impact':'A06 success manifests are raw Bytes(MaterializeTaskContext result), without _run_id/_test_name. verify_owned treats their a06-* labels as structured events and unconditionally rejects their owner fields before verify_a06. Valid A06/G01/G02 paths are unreachable.','recommendation':'Recognize exactly these two manifest raw labels as opaque in both consumers; keep their owning structured events mandatory and bind exact expected label/test/pin. Do not broadly skip a06-* or weaken owner validation for other events.','verification':'STATIC_PRODUCER_CONSUMER_PROOF_ONLY; candidate not executed'},
{'id':'W09-V5-R02-JUNCTION-REF-VS-PAYLOAD','severity':'BLOCKER','locations':[loc('w09_evidence_closure.v5.proposed.py','set(claim) == {"path", "sha256", "bytes"}'),loc('w09_evidence_closure.v5.proposed.py','_, raw = safe_repo_pin(root, item)'),loc('w09_evidence_closure.v5.proposed.py','junction_event.get("output") == junction.get("output_pin")'),loc('retrieval_test.v5.proposed.go','w09ExportEvent(t, "g02-junction-command"')],'impact':'junction is an exact-three-key typed REF, so junction.get(output_pin) is always None. The current event.output is a real raw pin; it cannot equal None and then also pass _raw_pin. Valid LIVE_WINDOWS G02 is impossible.','recommendation':'Take output_pin from the already verified researchos.w09-junction-witness.v1 payload in witness_values, preserving the outer REF exact three keys and all same-run/argv/root/target/owner/pin checks. Never add output_pin to the REF shape.','verification':'STATIC_LOGICAL_CONTRADICTION; candidate not executed'},
{'id':'W09-V5-R03-A06-PER-CALL-RESULT-JOIN','severity':'IMPORTANT','locations':[loc('w09_evidence_closure.v5.proposed.py','initial_manifest = _raw_pin('),loc('w09_evidence_closure.v5.proposed.py','require(initial_manifest and later_manifest'),loc('retrieval_test.v5.proposed.go','w09ExportEvent(t, "a06-bundle-initial"'),loc('retrieval_test.v5.proposed.go','w09ExportEvent(t, "a06-bundle-after-delete"')],'impact':'Even after fixing raw classification, the returned manifest bytes are only required nonempty and lacking a literal plaintext marker. Both events may cite the same valid raw member in this test; target_path strings being different does not distinguish raw calls. The consumer does not parse actual manifest task_id/bundle_ref/input_manifest, does not bind initial source_artifact_id to the captured snapshot row, or bind deleted_artifact_id to the deletion row. These leave prior R4 raw-call substitution/exclusion requirements open.','recommendation':'Pin exact initial/later raw labels and distinct refs; parse original manifests and bind project/task, original bundle identity/version, and input_manifest artifact refs/content hashes to exported bundle and snapshot facts. Export minimal original bundle/deleted snapshot IDs/version locators at existing calls if needed. Verify new_bundle root/principal and rejection target/error association; preserve all original business assertions.','verification':'STATIC_MISSING_JOIN_REVIEW; no crafted runtime receipt executed'}
]
matrix={'R1':{'status':'STATIC_LABEL_FIX_REVIEWED','evidence':'20 exact raw labels plus 20 owned structured bindings, ordinal body pin/ID/hash and C19 POST joins; no candidate execution.'},'R2':{'status':'STATIC_CYCLE_REMOVED_WITH_OPEN_RUNTIME','sequence':['native producer report/raw then tool-run','later distinct reviewer receipt','later decision pins receipt','readonly formal consumer consumes same report/run without native rerun'],'hash_cycle_found':False,'preserved_routes':'W09-01/W08/W17 still have original subprocess routes; readonly claim applies to six selected W09 formal routes only.'},'R3':{'status':'PARTIAL_REQUEST','guards':'Typed ROOT-relative, per-component lstat/reparse rejection before witness read; exact six-token command/root/target checks added.','open':['W09-V5-R02-JUNCTION-REF-VS-PAYLOAD','Actual Windows witness/resources/negative controls NOT_RUN.']},'R4':{'status':'PARTIAL_REQUEST','C19':'Actual content/artifacts/evidence POST bodies and response IDs connected to each simulation binding; original tests unexecuted.','A06':'Original materialize calls/errors now exported, but raw classification and per-call semantic joins remain incomplete.'},'I01':{'status':'OPEN_HISTORICAL','earliest_overwritten_bytes_recovered':False,'adjacent_original_wrapper_recovered':False,'current_packet':'New immutable current source packet verified; no claim of repaired historical bytes.'}}
audit=save('audit.json',{'schema':'researchos.w09-v5-readonly-static-audit.v1','checks':C,'failed_checks':[x for x in C if not x['passed']],'candidate_imported':False,'candidate_executed':False,'native_Git_Go_Node_SQL_HTTP_model_calls':0,'selected_sources':h['candidate_source_refs'],'six_source_pairs':pairs,'materialize_source_ref':ref(materialize),'new_failure_count':0})
report=save('report.json',{'schema':'researchos.w09-v5-source-review-report.v1','reviewer':'codex:/root/w05_merge_review','decision':'REQUEST_CHANGES','requested_changes':findings,'disposition':matrix,'audit_ref':audit,'new_failure_count':0,'author_existing_failure_refs_not_recounted':h['new_failure_origin_refs']})
v={'schema':'researchos.w09-v5-independent-source-review.v1','reviewer':'codex:/root/w05_merge_review','actor_id':'codex:/root/w05_merge_review','actor_role':'INDEPENDENT_NON_AUTHOR_SOURCE_REVIEWER','author':False,'decision':'REQUEST_CHANGES','requested_changes':findings,'report_ref':report,'audit_ref':audit,'manifest_input_ref':ref(S/'manifest.json'),'handoff_input_ref':ref(S/'handoff.json'),'source_inverse_ref':ref(S/'source-inverse.json'),'prior_review_ref':inv['baseline_review_ref'],'candidate_source_refs':h['candidate_source_refs'],'disposition':matrix,'verification_limits':{'Python_AST_only':True,'Go_AST_or_build':False,'candidate_imported_or_executed':False,'positive_negative_controls':'NOT_RUN','source_acceptance':False,'actual_Root_scope_or_grant':False,'formal_case_accepted_delta':0,'canonical_source_index_writes':0,'historical_I01':'OPEN'},'new_failure_count':0,'new_failure_origin_refs':[],'author_existing_failure_refs_not_recounted':h['new_failure_origin_refs'],'stage':'SOURCE_PREPARATION_ONLY','status':'STOPPED'}
rev=save('review.json',v)
hd=save('handoff.json',{'schema':'researchos.independent-review-handoff.v1','reviewer':v['reviewer'],'decision':v['decision'],'review_ref':rev,'report_ref':report,'audit_ref':audit,'new_failure_count':0,'new_failure_origin_refs':[],'status':'STOPPED','manifest_filename':'manifest.json'})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']
mf=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True})
print(json.dumps({'review_ref':rev,'report_ref':report,'manifest_ref':mf,'handoff_ref':hd,'checks':len(C),'failed_checks':[x for x in C if not x['passed']],'requested_changes':[f['id'] for f in findings],'new_failure_count':0},ensure_ascii=False))

