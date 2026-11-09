"""Pure IO/hash/AST source preparation. Never import/execute the candidate."""
from pathlib import Path, PureWindowsPath
import ast,difflib,hashlib,json
OUT=Path(__file__).resolve().parent
P=OUT.parent.parent
BASE=P/'f08_driver18_root_producer_revision_preparation_codex/a40358cbf99d4ade84977634d74a7d21'
REVIEW=P/'f08_driver18_root_producer_v3_independent_review_codex/4f9673bf4d3148cbad024d81a8e346f1'
def need(ok,msg):
    if not ok:raise ValueError(msg)
def ref(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,b):
    with (OUT/name).open('xb') as f:f.write(b)
    return ref(OUT/name)
def save(name,x):return write(name,(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
inputs=[BASE/'driver18_root_producer.v3.proposed.py',BASE/'handoff.complete.json',BASE/'manifest.complete.json',BASE/'required-input-contract.json',BASE/'positive-path-example.NOT_RUN.json',REVIEW/'review.json',REVIEW/'handoff.json',REVIEW/'manifest.json',BASE/'inputs.before.json']
before=[ref(p) for p in inputs]
need(before[0]['sha256']=='5a4e421c7fe8c40c65bc6de8d90f904258f1d676440ed9a71f4c7682fc958310','V3_PIN')
need(before[5]['sha256']=='127e84b2c6212765070e542d376289225888255d77279333b5da4799224cc875','REVIEW_PIN')
need(before[6]['sha256']=='d5dd11bd0ad4637a33237f364d7ed595d4fc1f2f537890b5d1a28ec76175f5fd' and before[7]['sha256']=='490d8107609b2ddcd008e9825a7b5b09e2f44c32f7e92ff1f6dd9d3510884712','REVIEW_CLOSURE_PINS')
original=inputs[0].read_bytes();need(b'\r' not in original,'LF_SOURCE');text=original.decode()
edits=[
 {'id':'initial-stage-parent-empty','old':"        g=gate();paths=registration_layout(g,data['producer_layout'])\n",'new':"        g=gate();paths=registration_layout(g,data['producer_layout'])\n        need(not any(g.safe(data['producer_layout']['registration_namespace']).iterdir()),'INITIAL_REGISTRATION_PARENT_NOT_EMPTY')\n"},
 {'id':'adjacent-preallocation-recheck','old':"        planned=preallocate(action,data,inp,x.output_root);out=leaf(str(planned),True)\n",'new':"        planned=preallocate(action,data,inp,x.output_root)\n        if action=='stage-code':need(not any(safe(str(planned.parent)).iterdir()),'INITIAL_REGISTRATION_PARENT_NOT_EMPTY')\n        out=leaf(str(planned),True)\n"}]
for e in edits:
    need(text.count(e['old'])==1,'EXACT_ANCHOR_'+e['id']);text=text.replace(e['old'],e['new'],1)
inverse=text
for e in reversed(edits):
    need(inverse.count(e['new'])==1,'INVERSE_ANCHOR_'+e['id']);inverse=inverse.replace(e['new'],e['old'],1)
need(inverse.encode()==original,'EXACT_WHOLE_V3_INVERSE')
ot,nt=ast.parse(original),ast.parse(text)
old={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)}
new={n.name:n for n in nt.body if isinstance(n,ast.FunctionDef)}
need(set(old)==set(new) and len(old)==42,'NO_NEW_OR_REMOVED_FUNCTION')
changed=[n for n in old if ast.dump(old[n],include_attributes=False)!=ast.dump(new[n],include_attributes=False)]
need(changed==['preallocate','entry'],'ONLY_TWO_STAGE_ENTRY_FUNCTIONS_CHANGED')
unchanged=[n for n in old if n not in changed]
checks=[{'id':'whole_v3_byte_inverse','result':True},{'id':'only_preallocate_entry_changed','result':True},{'id':'42_original_functions_preserved','result':True}]
for name in unchanged:checks.append({'id':'unchanged_AST_'+name,'result':True})
entry=new['entry'];stage_if=[n for n in ast.walk(entry) if isinstance(n,ast.If) and ast.unparse(n.test)=="action == 'stage-code'" and len(n.body)==1 and isinstance(n.body[0],ast.Expr) and isinstance(n.body[0].value,ast.Call) and isinstance(n.body[0].value.func,ast.Name) and n.body[0].value.func.id=='need']
need(len(stage_if)==1,'ENTRY_STAGE_ONLY_GUARD')
guard=stage_if[0]
# Inspect actual Try statements rather than relying on a guessed child index.
tries=[n for n in entry.body if isinstance(n,ast.Try)];need(len(tries)==1,'ENTRY_TRY')
body=tries[0].body;idx=body.index(guard)
need(isinstance(body[idx-1],ast.Assign) and ast.unparse(body[idx-1].value)=='preallocate(action, data, inp, x.output_root)','RECHECK_AFTER_PREALLOCATE')
need(isinstance(body[idx+1],ast.Assign) and ast.unparse(body[idx+1].value)=='leaf(str(planned), True)','RECHECK_DIRECTLY_BEFORE_LEAF')
need(text.count("'INITIAL_REGISTRATION_PARENT_NOT_EMPTY'")==2,'EXACT_TWO_EMPTY_CHECKS')
checks.extend([{'id':x,'result':True} for x in ['entry_guard_only_stage','recheck_after_preallocate','recheck_immediately_before_leaf','exact_two_empty_checks','registration_layout_AST_unchanged','all_draft_native_guards_unchanged']])
source=write('driver18_root_producer.v4.proposed.py',text.encode())
write('original.v3.py.txt',original)
save('inputs.before.json',before)
save('whole-inverse.json',{'base_ref':before[0],'candidate_ref':source,'edits':edits,'inverse_verified':True,'candidate_executed':False})
write('producer.v4.diff',''.join(difflib.unified_diff(original.decode().splitlines(True),text.splitlines(True),fromfile='frozen-v3',tofile='proposed-v4')).encode())
save('static-audit.json',{'source_preparation_only':True,'checks':checks,'changed_functions':changed,'unchanged_functions':unchanged,'whole_inverse':True,'AST_parse':True,'candidate_import_or_execution':False,'runtime_tests':'NOT_RUN'})
save('required-input-amendment.json',{'base_contract_ref':before[3],'finding':'R01-V3-FRESH_PARENT','initial_stage_only':True,'requirement':'Root creates only a NEW EMPTY registration_namespace directory. Bootstrap input, reviewed producer, tools and all input refs reside outside that parent. First stage validates entire emptiness before selecting fresh children, and rechecks complete emptiness immediately before leaf creation. Any old manifest, file, hidden entry, symlink or unrelated child makes it nonempty and is refused; inspection errors propagate. No removal/cleanup/retry is added.','unchanged':'registration_layout remains unchanged and does not require emptiness. Subsequent draft/native can use the stage-containing parent under existing exact layout, reviews, refs, alias/fresh-child and native authority guards.','future_actual_tuple':None,'actual_Root_grant':None,'execution_authorized':False,'source_acceptance':False})
uid='11111111111111111111111111111111';ns=PureWindowsPath(str(P))/('FUTURE_EMPTY_PARENT_EXAMPLE_'+uid)
oldns=PureWindowsPath(str(P))/'f08_driver18_root_producer_revision_independent_review_codex/c34edd014fba47228e985d219ab51580'
examples=[
 {'id':'R01-V3-EMPTY_PARENT_POSITIVE','path':str(ns),'directory_entries_at_stage_validation':[],'directory_entries_immediately_before_leaf':[],'three_children':[str(ns/x) for x in ['stage-code','draft','native']],'expected':'Stage path remains reachable when real other predicates hold','actual':'NOT_RUN'},
 {'id':'R01-V3-NONEMPTY_PARENT','path':str(oldns),'known_member_ref':json.loads((BASE/'inputs.before.json').read_bytes())[1],'directory_entries_model':['review.json','manifest.json'],'expected':'Reject before leaf/request/source copy even if all three chosen children are absent','actual':'NOT_RUN'},
 {'id':'R01-V4-PARENT_CHANGED_BETWEEN_GUARDS','path':str(ns),'directory_entries_at_stage_validation':[],'directory_entries_immediately_before_leaf':['unexpected-entry'],'expected':'Second guard rejects before leaf creation','actual':'NOT_RUN'},
 {'id':'R01-V4-LATER_DRAFT_NATIVE','path':str(ns),'directory_entries_model':['stage-code'],'expected':'No global empty requirement added; later stages keep all existing scope and source predicates','actual':'NOT_RUN'}]
need(all(PureWindowsPath(x).parent==ns and PureWindowsPath(x)!=ns for x in examples[0]['three_children']),'STATIC_DIRECT_CHILDREN')
save('path-examples.NOT_RUN.json',{'classification':'STATIC_PATH_AND_LIST_ALGEBRA_ONLY','no_example_directory_created':True,'empty_model_satisfies_new_predicate':not any([]),'old_member_model_fails_new_predicate':bool(any(['review.json','manifest.json'])),'examples':examples,'runtime_validation':False})
after=[ref(p) for p in inputs];need(after==before,'INPUT_DRIFT');save('inputs.after.json',after)
save('tool-observations.json',{'observations':[{'chunk_id':'9b08c1','operation':'read full v3 independent review','outer_exit':0,'native_exit':None},{'chunk_id':'69db5d','operation':'create own fresh preparation namespace only','outer_exit':0,'native_exit':None}],'new_failure_origins':[],'candidate_calls':0,'Go_SQL_Job_Git_network_model_CAS_calls':0,'old_failure_counter_untouched':True})
handoff=save('handoff.json',{'schema':'researchos.source-preparation-handoff.v1','actor':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','finding':'R01-V3-FRESH_PARENT','source_ref':source,'base_ref':before[0],'review_ref':before[5],'review_handoff_ref':before[6],'review_manifest_ref':before[7],'inverse_ref':ref(OUT/'whole-inverse.json'),'input_contract_amendment_ref':ref(OUT/'required-input-amendment.json'),'static_audit_ref':ref(OUT/'static-audit.json'),'future_controls_ref':ref(OUT/'path-examples.NOT_RUN.json'),'input_count':len(before),'input_drift':0,'changed_functions':changed,'unchanged_functions':len(unchanged),'new_functions':0,'actual_candidate_execution':False,'actual_registration':False,'actual_grant':False,'source_acceptance':False,'new_failure_origins':[],'I17':'OPEN_NOT_AUTHORIZED','SQL24':'OPEN_NOT_AUTHORIZED','limits_and_consumers':'UNCHANGED','writer_status':'STOPPED_AFTER_SEAL'})
members=[ref(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']
manifest=save('manifest.json',{'schema':'researchos.immutable-source-preparation-manifest.v1','files':members,'member_count':len(members),'excluded_only_self':True})
print(json.dumps({'source':source,'handoff':handoff,'manifest':manifest,'member_count':len(members),'static_checks':len(checks),'input_drift':0,'new_origins':0},ensure_ascii=False))
