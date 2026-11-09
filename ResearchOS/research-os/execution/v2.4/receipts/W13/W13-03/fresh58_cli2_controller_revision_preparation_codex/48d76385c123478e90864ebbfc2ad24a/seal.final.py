"""Immutable preparation sealing only. No candidate import/evaluation."""
import ast,hashlib,json,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
OLD=OUT.parents[1]/'fresh58_cli2_controller_preparation_codex/86d71652d03649879b13e03a974456d9'
def need(x,m):
    if not x:raise RuntimeError(m)
def ref(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,o):
    b=o if isinstance(o,bytes) else (json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
    with (OUT/n).open('xb') as f:f.write(b)
need(len(sys.argv)==7,'Review/HDF/MF path SHA pairs required')
reviews=[]
for i in [1,3,5]:
    p=Path(sys.argv[i]);r=ref(p);need(r['sha256']==sys.argv[i+1],'Original sealed REQUEST input');reviews.append(r)
before=json.loads((OUT/'inputs.before.json').read_bytes())
need([ref(Path(r['path'])) for r in before]==before,'Original source inputs changed')
old=(OLD/'authorization_gate.current58.proposed.py').read_bytes();new=(OUT/'authorization_gate.current58.final.proposed.py').read_bytes()
inverse=new
for e in reversed(json.loads((OUT/'gate.edits.final.json').read_bytes())):
    need(inverse.count(e['new'].encode())==1,'Inverse ambiguity');inverse=inverse.replace(e['new'].encode(),e['old'].encode(),1)
need(inverse==old,'Whole byte inverse')
ot,nt=ast.parse(old),ast.parse(new)
ol,nl=old.splitlines(True),new.splitlines(True)
of={n.name:n for n in ot.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};nf={n.name:n for n in nt.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
same=[]
for k in of:
    if k=='validate_current58_source':continue
    a,b=of[k],nf[k]
    need(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),'Unowned AST changed')
    need(b''.join(ol[a.lineno-1:a.end_lineno])==b''.join(nl[b.lineno-1:b.end_lineno]),'Unowned function byte change')
    same.append(k)
asts=[]
for p in sorted(OUT.glob('*.py')):ast.parse(p.read_bytes());asts.append(ref(p))
scope=json.loads((OUT/'scope.current58.final.proposed.json').read_bytes());oldscope=json.loads((OLD/'scope.current58.proposed.json').read_bytes())
sr=dict(scope);sr['authorization_gate_ref']=oldscope['authorization_gate_ref'];need(sr==oldscope,'Scope changed beyond gate REF')
for k in ['runner_ref','launcher_ref']:
    need(ref(Path(scope[k]['path']))==scope[k],'Retained source pin drift')
save('independent-request.refs.json',reviews)
save('inputs.final.json',[ref(Path(r['path'])) for r in before]+reviews)
save('static-audit.final.json',{'whole_byte_inverse':True,'gate_edits':5,'unchanged_functions_and_classes_byte_and_AST':same,'AST_files':asts,'scope_only_gate_ref':True,'source_set_actual_union_38_8_15_is_58':True,'tuple_field_sources':'Actual forward engine ref in inputs; no invented intent.before/after fields','candidate_imported':False,'candidate_executed':False,'runtime_controls':'NOT_RUN','new_failure_origins':[],'input_drift':0})
save('tool-observations.json',{'kind':'CHAT_TOOL_RETURN_TRANSCRIPTION_NO_SEPARATE_NATIVE_CAPTURE','observations':[{'tool_chunk':'0606c9','action':'exclusive new namespace mkdir','actual_outer_exit':0,'actual_native_exit':None},{'tool_chunk':'9532fe','action':'pure IO constructor + AST + whole inverse','actual_outer_exit':0,'actual_native_exit':None},{'tool_chunk':'7a40ea','action':'pure JSON scope binding proposal','actual_outer_exit':0,'actual_native_exit':None}], 'candidate_calls':0,'new_failure_origins':[],'Desktop_1622f8':'Previously reported distinct preparation origin; not re-counted here.'})
save('handoff.json',{'schema':'researchos.fresh58-cli2-gate-revision-handoff.v1','actor':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_NOT_ACCEPTED','state':'STOPPED','gate_ref':ref(OUT/'authorization_gate.current58.final.proposed.py'),'scope_proposal_ref':ref(OUT/'scope.current58.final.proposed.json'),'runner_ref':scope['runner_ref'],'launcher_ref':scope['launcher_ref'],'binding_contract_ref':ref(OUT/'binding-contract.final.json'),'prior_handoff_ref':ref(OLD/'handoff.json'),'prior_manifest_ref':ref(OLD/'manifest.json'),'independent_REQUEST_refs':reviews,'fix_mapping':[{'finding':'Exact original43 + Desktop15 source membership','change':'Original scope shared38_paths + cli8_paths + closed Desktop15 source_paths exact set equality; original predicates retained.'},{'finding':'Forward tuple type/count/origin pairing','change':'Three exact-int fields for audit/request before and after, exact typed intent transition pairs, actual request source head pair, verified tuple and all-three current upper bounds.'}],'whole_inverse_ref':ref(OUT/'gate.edits.final.json'),'static_audit_ref':ref(OUT/'static-audit.final.json'),'future_controls_ref':ref(OUT/'future-controls.NOT_RUN.json'),'inputs_ref':ref(OUT/'inputs.final.json'),'source_function_scope':['validate_current58_source'],'unchanged_function_byte_AST_count':len(same),'future_actual_Root_tuple':None,'future_actual_forward_seal':None,'future_resource_scope_review_grant':None,'candidate_calls':0,'Go_SQL_Node_Job_HTTP_models':0,'source_acceptance':False,'formal_increment':0,'new_failure_origins':[],'OPEN':['Non-author gate revision review','Root actual forward-head seal and new current58 catalogs/runtime/authority','Immutable full-scope review then actual Root registration and unique grant','New fresh same-head CLI2 execution and independent qualification'],'manifest_path':str(OUT/'manifest.json')})
files=sorted(p for p in OUT.iterdir() if p.is_file());save('manifest.json',{'schema':'researchos.immutable-preparation-manifest.v1','self_excluded':True,'count':len(files),'entries':[ref(p) for p in files]})
print(json.dumps({'handoff':ref(OUT/'handoff.json'),'manifest':ref(OUT/'manifest.json'),'gate':ref(OUT/'authorization_gate.current58.final.proposed.py'),'scope':ref(OUT/'scope.current58.final.proposed.json')},ensure_ascii=False))
