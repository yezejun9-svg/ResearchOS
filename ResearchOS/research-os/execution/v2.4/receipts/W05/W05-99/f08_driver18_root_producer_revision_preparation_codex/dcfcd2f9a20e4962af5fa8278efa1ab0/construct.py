"""Pure IO/AST candidate construction. Candidate code is never imported or run."""
import ast,difflib,hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
P=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99')
OLD=P/'f08_driver18_root_producer_preparation_codex/fe7a07dcb98a4f2aacb2f73d4ff60780'
REVIEW=P/'f08_driver18_root_producer_independent_source_review_codex/49c040cd134b4e46bfb2ed55b5680ae2'
inputs={};checks=[];edits=[]
def ref(p):
    p=Path(p);b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
    if str(p) in inputs:assert inputs[str(p)]==r
    inputs[str(p)]=r;return r
def load(p):ref(p);return json.loads(Path(p).read_bytes())
def save(name,value):
    b=value if isinstance(value,bytes) else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with (OUT/name).open('xb') as f:f.write(b)
    return {'path':str(OUT/name),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(name,v):checks.append({'name':name,'passed':bool(v)});assert v,name
rv=load(REVIEW/'review.json');handoff=load(REVIEW/'handoff.json')
check('review_fixed',ref(REVIEW/'review.json')['sha256']=='e09b078b87e7f30d1fc3b27617fcbe8a5a63795695789e6c5e9f93aae9e35038')
for name in ['manifest.json','REVIEW.md','counterexamples.NOT_RUN.json']:ref(REVIEW/name)
for name in ['handoff.json','manifest.json','postseal-audit.json']:ref(OLD/name)
for r in rv['frozen_consumers'].values():check('frozen_'+r['sha256'],ref(r['path'])['sha256']==r['sha256'])
ref(rv['mapping_ref']['path'])
p=OLD/'driver18_root_producer.proposed.py';old=p.read_bytes();ref(p)
check('original_SHA',hashlib.sha256(old).hexdigest()=='12cc3272edc3a24b9771418f0c1ab9f1ba9c732e9dc6a632fdaa490cbb0e44da')
check('actual_LF',old.count(b'\r\n')==0)
save('original.producer.py.txt',old)
source=old.decode()
def replace(a,b,label):
    global source
    check(label+'_unique',source.count(a)==1)
    source=source.replace(a,b,1);edits.append({'label':label,'before':a,'after':b})
fragment=(OUT/'new-functions.proposed.py.txt').read_text(encoding='utf-8');ast.parse(fragment)
replace('def leaf(text):\n','def leaf(text,checked=False):\n    need(checked,\'PREALLOCATION_REQUIRED\')\n','R01_leaf_guard')
replace('def immutable_manifest(out,extra=()):\n',fragment+'def immutable_manifest(out,extra=()):\n','new_contract_functions')
replace("    res=r.doc(s['resource_catalog_ref']);rows=res['files']\n","    res=exact_resource_catalog(r.doc(s['resource_catalog_ref']));rows=res['files']\n",'R02_runtime_exact')
replace("        need(key in allowed and g.same_ref(allowed[key],ref),'METADATA_CODE_NOT_PREPINNED')\n    need(g.same_ref(pin(Path(sys.executable).resolve()),res['python']),'ACTUAL_PYTHON')\n", "        need(key in allowed and allowed[key]==pin(g.safe(ref['path']).resolve()),'METADATA_CODE_NOT_PREPINNED')\n    need(pin(Path(sys.executable).resolve())==res['python'],'ACTUAL_PYTHON')\n",'R02_runtime_literal')
replace("    for item in x['provenance_refs']:r.verify(item)\n    r.unchanged();return save(out/'resource-catalog.json'", "    for item in x['provenance_refs']:r.verify(item)\n    exact_resource_catalog(x)\n    r.unchanged();return save(out/'resource-catalog.json'",'R02_catalog_before_save')
replace("    ref=save(out/'scope.proposed.json',s);g.scope(r,ref);r.unchanged();return ref\n", "    for k in ['work_root','prepare_output_root','execute_output_root','prepare_launcher_output_root','execute_launcher_output_root']:\n        need(s[k]==str(g.safe(s[k])),'EXACT_CONSUMER_ROOT_STRING_'+k)\n    exact_resource_catalog(r.doc(s['resource_catalog_ref']))\n    a=s['actual_Root_registration']\n    capture=g.safe(a['original_tool_capture_root']);reviewpath=g.safe(a['original_tool_capture_review_path'])\n    need(capture.is_relative_to(RECEIPTS) and a['run_uuid'] in capture.name and disjoint(capture,reviewpath.parent),'FUTURE_CAPTURE_REVIEW_PATHS')\n    need(all(disjoint(capture,g.safe(s[k])) and disjoint(reviewpath.parent,g.safe(s[k])) for k in ['work_root','prepare_output_root','execute_output_root','prepare_launcher_output_root','execute_launcher_output_root']),'CAPTURE_PHASE_OVERLAP')\n    ref=save(out/'scope.proposed.json',s);g.scope(r,ref);r.unchanged();return ref\n",'R02_scope_and_R03_future_paths')
replace("    g,r,s,sref,d,index,mfref,before,desired=reviewed(dref,regref);a=s['actual_Root_registration'];out=leaf(a['registration_output_root'])\n", "    g,r,s,sref,d,index,mfref,before,desired=reviewed(dref,regref);a=s['actual_Root_registration']\n    planned=allocation_check(a['registration_output_root'],[s],s,metadata=False)\n    need(planned.is_relative_to(g.safe(a['registration_namespace'])),'EXACT_REGISTRATION_OUTPUT_BOUNDARY')\n    out=leaf(str(planned),True)\n",'R01_registration_allocation')
start="    pf=leaf(preflight);auth=safe(authroot);need(auth.parent.is_dir() and not os.path.lexists(auth) and auth.is_relative_to(RECEIPTS) and a['run_uuid'] in auth.name and a['run_uuid'] in pf.name and not (auth.is_relative_to(pf) or pf.is_relative_to(auth)),'FRESH_DISJOINT_AUTH')\n    for k in ['prepare_output_root','execute_output_root','prepare_launcher_output_root','execute_launcher_output_root']:\n        q=g.safe(s[k]);need(not (auth==q or auth.is_relative_to(q) or q.is_relative_to(auth)),'AUTH_EXECUTION_OVERLAP')\n    proof=None if prepared_proof_ref is None else r.doc(prepared_proof_ref)\n    if a['phase']=='execute':need(proof is not None,'REAL_PREPARE_REQUIRED');g.prepared_evidence(r,s,proof)\n    else:need(proof is None,'NO_FUTURE_PREPARE_FACT')\n"
end="    proof=None if prepared_proof_ref is None else r.doc(prepared_proof_ref)\n    if a['phase']=='execute':need(proof is not None,'REAL_PREPARE_REQUIRED');g.prepared_evidence(r,s,proof)\n    else:need(proof is None,'NO_FUTURE_PREPARE_FACT')\n    inputs=[sref,s,bundleref,bundle,prepared_proof_ref,proof,list(r.refs.values()),pin(Path(__file__).resolve())]\n    pfpath=allocation_check(preflight,inputs,s,metadata=False);auth=allocation_check(authroot,inputs,s,metadata=False)\n    need(pfpath.parent==RECEIPTS/'f08_driver18_root_grant_preflight_codex' and auth.parent==RECEIPTS/'f08_driver18_root_authorization_codex' and pfpath.name==auth.name==a['run_uuid'] and disjoint(pfpath,auth),'DEDICATED_FRESH_GRANT_OUTPUTS')\n    live4(desired);r.unchanged();pf=leaf(str(pfpath),True)\n"
replace(start,end,'R01_grant_before_allocations')
replace("def capture_action(sref,gref,kind,inputref,responseref,request_locator,response_locator,initialref,out):\n", "def capture_action(sref,gref,kind,inputref,responseref,request_locator,response_locator,initialref,out,capture_refs,actionref):\n",'R03_capture_interface')
replace("    inp=r.doc(inputref);response=r.doc(responseref)\n", "    bundle=original_capture_closure(g,r,s,sref,gref,capture_refs)\n    event=next((x for x in bundle['events'] if x['action_ref']==actionref),None)\n    need(event is not None and event['tool_name']==kind and event['input_ref']==inputref and event['response_ref']==responseref and event['request_event_locator']==request_locator and event['response_event_locator']==response_locator,'CAPTURE_EXACT_ORIGINAL_EVENT')\n    need(r.doc(actionref)['initial_action_ref']==initialref,'CAPTURE_ORIGINAL_INITIAL_REF')\n    inp=r.doc(inputref);response=r.doc(responseref)\n",'R03_capture_origin_gate')
replace("    return save(out/'tool-action.json',{'schema':'researchos.driver18-original-tool-action.v1','actor':'codex:/root','tool_name':kind,'input_ref':iref,'response_ref':rref,'initial_action_ref':initialref,'command_identity':identity,'request_event_locator':request_locator,'response_event_locator':response_locator})\n", "    write(out/'tool-action.original.json',r.verify(actionref))\n    save(out/'capture-provenance.json',{'original_capture_closure':capture_refs,'original_action_ref':actionref,'copied_raw_refs':[iref,rref],'qualification':'EXTERNAL_ORIGINAL_PAIR_REVIEW_REQUIRED_NO_SELF_AUTHENTICATION'})\n    r.unchanged();return actionref\n",'R03_preserve_original_action_refs')
replace("def seal_outer(sref,gref,initialref,terminalref,out):\n    g,r,s=load(sref);phase=s['actual_Root_registration']['phase'];identity=action_identity(s,sref,gref,phase);ia=r.doc(initialref);ta=r.doc(terminalref);first=r.doc(ia['response_ref']);last=r.doc(ta['response_ref'])\n", "def seal_outer(sref,gref,initialref,terminalref,out,capture_refs):\n    g,r,s=load(sref);g.verify_authority(r,s,sref,r.doc(gref))\n    bundle=original_capture_closure(g,r,s,sref,gref,capture_refs)\n    need([x['action_ref'] for x in bundle['events']]==[initialref,terminalref],'OUTER_EXACT_ORIGINAL_CAPTURE_PAIR')\n    phase=s['actual_Root_registration']['phase'];identity=action_identity(s,sref,gref,phase);ia=r.doc(initialref);ta=r.doc(terminalref);first=r.doc(ia['response_ref']);last=r.doc(ta['response_ref'])\n",'R03_seal_outer_grant_and_capture')
replace("    cref=save(out/'outer-completion.json',completion)\n", "    completion['original_capture_closure']=capture_refs\n    cref=save(out/'outer-completion.json',completion)\n",'R03_outer_preserve_capture_chain')
replace("    proof={'prepare_scope_ref':sref,'prepare_grant_ref':gref,'outer_completion_ref':outerref}\n", "    outer=r.doc(outerref);capture_refs=outer['original_capture_closure']\n    bundle=original_capture_closure(g,r,s,sref,gref,capture_refs)\n    original=r.doc(outer['outer_invocation_ref'])\n    need([x['action_ref'] for x in bundle['events']]==[original['tool_initial_action_ref'],outer['terminal_tool_action_ref']],'PREPARE_CAPTURE_PAIR')\n    proof={'prepare_scope_ref':sref,'prepare_grant_ref':gref,'outer_completion_ref':outerref}\n",'R03_seal_prepare_required_capture')
replace("        inp=parse(x.input_ref.encode());data=parse(verify(inp));out=leaf(x.output_root)\n", "        inp=parse(x.input_ref.encode());data=parse(verify(inp))\n        planned=preallocate(action,data,inp,x.output_root);out=leaf(str(planned),True)\n",'R01_entry_preallocation')
replace("data['response_event_locator'],data['initial_action_ref'],out)\n", "data['response_event_locator'],data['initial_action_ref'],out,data['original_capture_closure'],data['original_action_ref'])\n",'R03_entry_capture_parameters')
replace("data['initial_action_ref'],data['terminal_action_ref'],out)\n", "data['initial_action_ref'],data['terminal_action_ref'],out,data['original_capture_closure'])\n",'R03_entry_outer_parameter')
candidate=source.encode();ast.parse(candidate)
inverse=source
for e in reversed(edits):
    check(e['label']+'_inverse_unique',inverse.count(e['after'])==1);inverse=inverse.replace(e['after'],e['before'],1)
check('whole_byte_inverse',inverse.encode()==old)
oldast=ast.parse(old);newast=ast.parse(candidate)
of={x.name:ast.dump(x,include_attributes=False) for x in oldast.body if isinstance(x,ast.FunctionDef)}
nf={x.name:ast.dump(x,include_attributes=False) for x in newast.body if isinstance(x,ast.FunctionDef)}
changed={'leaf','runtime','resource_catalog','prepare_scope','run_registration','grant','capture_action','seal_outer','seal_prepare','entry'}
for k in of:
    if k not in changed:check('unchanged_function_'+k,of[k]==nf[k])
check('original_function_names_preserved',set(of)<=set(nf))
check('fixed_globals_preserved',[ast.dump(x,include_attributes=False) for x in oldast.body if isinstance(x,ast.Assign)]==[ast.dump(x,include_attributes=False) for x in newast.body if isinstance(x,ast.Assign)])
cr=save('driver18_root_producer.v2.proposed.py',candidate)
save('producer.diff',''.join(difflib.unified_diff(old.decode().splitlines(True),source.splitlines(True),fromfile=str(p),tofile=cr['path'])).encode())
save('whole-inverse.json',{'original_ref':ref(p),'candidate_ref':cr,'edits':edits,'inverse_byte_equal':True})
save('required-new-inputs.json',{
    'producer_output_binding':{'schema':'researchos.driver18-producer-output-binding.v1','owner':'codex:/root','action':None,'metadata_output_root':None},
    'metadata_output_root':'P05/f08_driver18_root_producer_executor_codex/<fresh32hexUUID>; exact original input parameter required; parent Root-created before invocation',
    'grant_preflight_root':'P05/f08_driver18_root_grant_preflight_codex/<scope.run_uuid>',
    'grant_authorization_root':'P05/f08_driver18_root_authorization_codex/<scope.run_uuid>',
    'actual_Root_registration_additions':{'original_tool_capture_root':None,'original_tool_capture_review_path':None},
    'original_capture_closure':{'bundle_ref':None,'manifest_ref':None,'pair_review_ref':None,'pair_review_manifest_ref':None},
    'capture_review_contract':{'schema':'researchos.driver18-original-tool-pair-independent-review.v1','reviewer':'Actual frozen gate REVIEWERS, excluding Root and this producer author','decision':'ORIGINAL_HOST_TOOL_INPUT_RESPONSE_PAIR_VERIFIED','requested_changes':[],'non_author':True,'original_host_event_association_verified':True,'actual_candidate_execution':False,'exact_fields':['capture_bundle_ref','capture_manifest_ref','scope_ref','grant_ref','command_identity','host_capture_ref','events']},
    'capture_bundle_contract':{'schema':'researchos.driver18-original-host-tool-capture.v1','actor':'codex:/root','scope_ref':None,'grant_ref':None,'command_identity':None,'host_capture_ref':None,'events':'exact ordered exec_command/write_stdin original event rows; each original input,response,action ref and locators'},
    'capture_manifests':'files[] exact pinned refs, all members under original capture/review roots; includes original host capture, raw input/response, action records and bundle; review manifest binds actual pair review',
    'trust_boundary':'No filesystem actor string authenticates platform events. Root must supply actual original host-event export and a separate nonauthor review attesting precise request-response association. Missing evidence is FATAL_OPEN; no fake signatures or producer-minted pair review.',
    'no_cycle':'Scope freezes future capture-root and independent review path only, not future review hash. Real capture precedes external independent pair review, then refs are explicit input to source-pinned producer seal. Existing actual grant remains required.',
    'resources':'All files refs must equal actual canonical pin dict; python/go/images/offline refs literal members. Python current executable exact pin, GOROOT actual safe directory, work_root exact Windows str(Path) required.',
    'actual_Root_values':None,'future_execution':'NOT_RUN'})
controls=[
('R01-C1','Output under prior prepare_output_root/newleaf rejects before mkdir/raw'),('R01-C2','Output under prior launcher root or original input/ref parent rejects before write'),('R01-C3','Unknown action or changed output binding creates no leaf'),('R01-C4','Preflight/auth overlaps work/phase/proof/capture roots rejects before any source_guard'),
('R02-C1','Forward-slash or wrong-case file ref with matching hash rejects at catalog boundary'),('R02-C2','Equivalent but nonidentical python/offline refs reject before success catalog'),('R02-C3','Noncanonical work_root refuses scope emission'),('R02-C4','Missing/wrong GOROOT or wrong Go path refuses'),
('R03-C1','Missing original capture bundle/MF or nonauthor review refuses'),('R03-C2','Arbitrary nonempty locator/unrelated zero terminal response fails exact reviewed event tuple'),('R03-C3','Unrelated or invalid grant fails before outer seal'),('R03-C4','Producer-authored pair review or mismatched review scope/grant/command/raw refs rejects'),('R03-C5','Direct seal_prepare supplied old bare outer summary without capture closure rejects')]
save('future-controls.NOT_RUN.json',[{'id':i,'intent':s,'state':'NOT_RUN'} for i,s in controls])
save('fix-mapping.json',{'review_ref':ref(REVIEW/'review.json'),'R01':{'functions':['preallocate','allocation_check','receipt_input_trees','leaf','entry','grant','run_registration'],'effect':'Action/scope/read proofs and exclusions before allocation. Metadata leaves dedicated fresh UUID; preflight/auth dedicated run namespaces. Runtime/CAS authority not replaced by path binding.'},'R02':{'functions':['exact_resource_catalog','resource_catalog','prepare_scope','runtime'],'effect':'Reject representation mismatch rather than normalize sealed original evidence.'},'R03':{'functions':['original_capture_closure','capture_action','seal_outer','seal_prepare'],'effect':'Actual grant and original host capture/MF + external pair review required; actions remain original byte refs.'},'not_changed':'Frozen consumers, CAPS/I16/I18/I17 OPEN, two phase lease, registration CAS and source_guard functions unchanged.'})
save('inputs.before.json',list(inputs.values()))
for x in list(inputs.values()):ref(x['path'])
save('inputs.after.json',list(inputs.values()))
save('static-audit.json',{'checks':checks,'count':len(checks),'failed':sum(not x['passed'] for x in checks),'candidate_AST_parse':True,'candidate_imports':0,'candidate_execution':0,'Go_SQL_Node_Job_network_SDK_model_CAS':0,'actual_native_exit':None,'old_failure_origins_unchanged':True})
save('handoff.json',{'schema':'researchos.driver18-root-producer-revision-preparation.v1','actor':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_STOPPED_PENDING_NONAUTHOR_REVIEW','candidate_ref':cr,'original_ref':ref(p),'request_review_ref':ref(REVIEW/'review.json'),'request_handoff_ref':ref(REVIEW/'handoff.json'),'request_manifest_ref':ref(REVIEW/'manifest.json'),'checks':len(checks),'inverse_byte_equal':True,'fixed_consumers':rv['frozen_consumers'],'source_acceptance':False,'actual_execution':False,'future_controls':'NOT_RUN','partial17':'I01-I16,I18 only; I17/full18/SQL24 OPEN','actual_A01_A07':['Actual catalog and source tuple','Current Root review/lease','Actual canonical CAS/seal','Real original host action capture and nonauthor association review','Actual prepare artifacts','Execute grant and partial17 native evidence'],'new_failure_origins':[],'formal_increment':0})
entries=[]
for f in sorted(OUT.iterdir()):
    if f.is_file():
        b=f.read_bytes();entries.append({'path':str(f),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
mr=save('manifest.json',{'entries':entries,'count':len(entries),'excluded_only_self':True})
print(json.dumps({'candidate':cr,'handoff':ref(OUT/'handoff.json'),'manifest':mr,'checks':len(checks)},ensure_ascii=False))
