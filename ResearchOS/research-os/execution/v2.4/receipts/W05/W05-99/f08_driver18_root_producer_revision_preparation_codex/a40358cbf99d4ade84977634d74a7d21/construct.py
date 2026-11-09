"""Pure IO/AST construction only; never import or run the candidate."""
from pathlib import Path
import ast, datetime, difflib, hashlib, json

OUT=Path(__file__).resolve().parent
P=OUT.parent.parent
OLD=P/'f08_driver18_root_producer_revision_preparation_codex/dcfcd2f9a20e4962af5fa8278efa1ab0/driver18_root_producer.v2.proposed.py'
REVIEW=P/'f08_driver18_root_producer_revision_independent_review_codex/c34edd014fba47228e985d219ab51580/review.json'
GATE=P/'f08_driver18_root_binding_terminal_pairing_preparation_codex/f38b92cdbd4844529ce3da03d08630ad/authority_adapter.v3.proposed.py'
BINDER=GATE.with_name('binding_adapter.v3.proposed.py')
CONTROLLER=P/'f08_driver18_root_binding_revision_preparation_codex/ae14ede5d4d34ea493f9945886997cb2/driver18_controller.v4.proposed.py'
def need(ok,why):
    if not ok: raise ValueError(why)
def ref(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,raw):
    with (OUT/name).open('xb') as f:f.write(raw)
    return ref(OUT/name)
def save(name,value):return write(name,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
inputs=[OLD,REVIEW,REVIEW.with_name('handoff.json'),REVIEW.with_name('manifest.json'),GATE,BINDER,CONTROLLER,OLD.with_name('handoff.complete.json'),OLD.with_name('manifest.complete.json')]
before=[ref(p) for p in inputs]
need(before[0]['sha256']=='802ba9d5c814ad1d08a34ab6d0b3c7f13aa03912bf017318a7159bde28738437','V2_PIN')
need(before[1]['sha256']=='af18457491a9f26a05e6d35952d25fb03b5a67bbc27b5f1905db987d1ef7adfc','REVIEW_PIN')
original=OLD.read_bytes();text=original.decode('utf-8');need(b'\r' not in original,'LF_INPUT')
write('original.v2.py.txt',original);save('inputs.before.json',before)
edits=[]
def swap(old,new,label):
    global text
    need(text.count(old)==1,'UNIQUE_ANCHOR_'+label)
    text=text.replace(old,new,1);edits.append({'label':label,'old':old,'new':new})
def function(name,new):
    nodes={n.name:n for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    n=nodes[name];lines=text.splitlines(keepends=True);old=''.join(lines[n.lineno-1:n.end_lineno])
    swap(old,new.strip()+'\n',name)

helpers=r'''
def registration_layout(g,value,a=None):
    """Root path intent only; not a CAS, grant, review, or execution authorization."""
    keys={'schema','run_uuid','registration_namespace','stage_output_root','draft_output_root','native_output_root'}
    need(isinstance(value,dict) and set(value)==keys and value['schema']=='researchos.driver18-producer-registration-layout.v1','EXACT_REGISTRATION_LAYOUT')
    uid=value['run_uuid'];need(type(uid)is str and len(uid)==32 and all(c in '0123456789abcdef' for c in uid),'LAYOUT_UUID')
    ns=g.safe(value['registration_namespace'],RECEIPTS)
    need(value['registration_namespace']==str(ns) and uid in ns.name and ns.is_dir(),'ROOT_EXISTING_REGISTRATION_PARENT')
    paths={k:g.safe(value[k],ns) for k in ['stage_output_root','draft_output_root','native_output_root']}
    need(all(value[k]==str(p) and str(p.parent)==str(ns) for k,p in paths.items()),'DIRECT_REGISTRATION_SIBLINGS')
    need(len({str(p).casefold() for p in paths.values()})==3,'DISTINCT_REGISTRATION_SIBLINGS')
    if a is not None:
        need(value['run_uuid']==a['run_uuid'] and value['registration_namespace']==a['registration_namespace'] and value['native_output_root']==a['registration_output_root'],'CURRENT_SCOPE_LAYOUT')
    return paths

def draft_inputs(g,r,s,sref,cref,stage_ref,text):
    """Validate all caller-supplied draft parameters before allocation/canonical copies."""
    a=s['actual_Root_registration'];layout=a['producer_layout'];paths=registration_layout(g,layout,a)
    need(str(g.safe(text,g.safe(a['registration_namespace'])))==str(paths['draft_output_root']),'EXACT_DRAFT_CHILD')
    need(paths['stage_output_root'].is_dir() and not os.path.lexists(paths['native_output_root']),'STAGED_CODE_AND_FRESH_NATIVE_SIBLING')
    need(all(disjoint(p,g.safe(s[k])) for p in paths.values() for k in ['work_root','prepare_output_root','execute_output_root','prepare_launcher_output_root','execute_launcher_output_root']),'LAYOUT_PHASE_OVERLAP')
    stage=r.doc(stage_ref);need(stage['producer_layout']==layout and str(g.safe(stage_ref['path']).parent)==str(paths['stage_output_root']),'STAGED_LAYOUT_BINDING')
    for key in ['producer_ref','register','wrapper']:
        r.verify(stage[key]);need(str(g.safe(stage[key]['path']).parent)==str(paths['stage_output_root']),'CODE_IN_STAGE_CHILD')
    need(stage['producer_ref']==pin(Path(__file__).resolve()) and stage['gate_ref']==GATE and stage['binder_ref']==BINDER,'EXACT_CURRENT_STAGED_PRODUCER')
    r.verify(stage['gate_ref']);r.verify(stage['binder_ref'])
    need(stage['actual_CAS'] is False and stage['actual_grant'] is False,'STAGE_NOT_AUTHORIZATION')
    cr=r.doc(cref)
    need(str(g.safe(cref['path']))==str(g.safe(a['controller_review_path'])) and cr['schema']=='researchos.driver18-bound-controller-review.v1' and cr['reviewer'] in g.REVIEWERS and cr['decision']=='READY_FOR_ROOT_DRIVER18_'+a['phase'].upper()+'_ONCE' and cr['requested_changes']==[] and cr['scope_sha256']==sref['sha256'] and cr['mode']=='PARTIAL_17_EXPLICIT','FULL_SCOPE_NONAUTHOR_REVIEW_BEFORE_COPY')
    for key in ['controller_ref','launcher_ref','authority_validator_ref','utility_ref','owned_helper_ref','debug_helper_ref']:need(cr['code_refs'][key]==s[key],'REVIEW_EXACT_CODE_BEFORE_COPY')
    r.unchanged();return stage
'''.lstrip()
swap('def preallocate(action,data,inp,text):\n',helpers+'\ndef preallocate(action,data,inp,text):\n','new_layout_and_draft_precheck')
function('preallocate',r'''
def preallocate(action,data,inp,text):
    allowed={'resources','stage-code','scope','draft','register','seal-registration','grant','launch-request','capture-action','seal-outer','seal-prepare'}
    need(action in allowed and isinstance(data,dict),'KNOWN_ACTION_BEFORE_ALLOCATION')
    binding=data['producer_output_binding']
    need(binding=={'schema':'researchos.driver18-producer-output-binding.v1','owner':'codex:/root','action':action,'metadata_output_root':text},'EXPLICIT_ROOT_OUTPUT_BINDING')
    s=None;r=None;extra=[];metadata=True
    if action=='scope':
        g=gate();r=g.Reader();b=module(BINDER,'driver18_preallocation_binder');s=b.build_scope(g,r,inp)
        registration_layout(g,s['actual_Root_registration']['producer_layout'],s['actual_Root_registration'])
    elif action in {'register','seal-registration'}:
        g,r,s,sref,d,index,mfref,before,desired=reviewed(data['draft_ref'],data['registration_review_ref']);extra=[sref,d,index,mfref]
    elif action not in {'resources','stage-code'}:
        g,r,s=load(data['scope_ref'])
        if action=='draft':
            extra.append(draft_inputs(g,r,s,data['scope_ref'],data['controller_review_ref'],data['staged_code_ref'],text));metadata=False
        if action in {'launch-request','capture-action','seal-outer','seal-prepare'}:
            g.verify_authority(r,s,data['scope_ref'],r.doc(data['grant_ref']))
    elif action=='resources':need(data['schema']=='researchos.driver18-root-resource-input.v1','RESOURCE_INPUT')
    else:
        need(data['schema']=='researchos.driver18-stage-code-input.v1','STAGED_SOURCE_INPUT')
        g=gate();paths=registration_layout(g,data['producer_layout'])
        need(text==str(paths['stage_output_root']) and all(not os.path.lexists(p) for p in paths.values()),'FRESH_STAGED_LAYOUT');metadata=False
    if r is not None:extra.extend(r.refs.values());r.unchanged()
    values=[inp,data,extra,GATE,BINDER,pin(Path(__file__).resolve())]
    if s is not None:values.append(s)
    return allocation_check(text,values,s,metadata=metadata)
''')
function('exact_resource_catalog',r'''
def exact_resource_catalog(res):
    """Reject aliases before emission; frozen consumers compare literal REF dictionaries."""
    rows=res['files'];need(type(rows)is list and rows,'NONEMPTY_EXACT_RESOURCE_ROWS')
    for row in rows:
        actual=safe(row['path']).resolve()
        need(type(row['path'])is str and row['path']==str(actual) and row==pin(actual),'RESOURCE_REF_NOT_ACTUAL_CANONICAL_PIN')
    need(len({str(safe(row['path'])).casefold() for row in rows})==len(rows),'RESOURCE_CASEFOLD_COLLISION')
    need(all(item in rows for item in [res['python'],res['go'],*res['compiler_images']]),'TOOLS_REQUIRE_EXACT_FILES_DICTIONARY')
    need(res['python']==pin(Path(sys.executable).resolve()),'RESOURCE_ACTUAL_CURRENT_PYTHON_PIN')
    for row in res['offline_modcache_copies']:need(row['ref'] in rows,'OFFLINE_REQUIRE_EXACT_FILES_DICTIONARY')
    goroot=safe(res['GOROOT']).resolve();need(goroot.is_dir() and res['GOROOT']==str(goroot),'EXACT_GOROOT_DIRECTORY')
    need(res['go']['path']==str((goroot/'bin/go.exe').resolve()),'GOROOT_GO_PAIR')
    return res
''')
swap("    initial=r.doc(events[0]['response_ref']);terminal_input=r.doc(events[1]['input_ref']);terminal=r.doc(events[1]['response_ref'])\n",r'''    initial_input=r.doc(events[0]['input_ref']);initial=r.doc(events[0]['response_ref']);terminal_input=r.doc(events[1]['input_ref']);terminal=r.doc(events[1]['response_ref'])
    need(str(g.safe(initial_input['workdir']))==str(ROOT) and isinstance(initial_input['cmd'],str) and type(initial.get('session_id'))is int and initial.get('exit_code') is None,'REAL_ASYNC_INITIAL_REQUIRED')
    quoted=["'"+v.replace("'","''")+"'" for v in identity['argv']]
    need(initial_input['cmd']=='& '+quoted[0]+' '+ ' '.join(quoted[1:])+'; exit $LASTEXITCODE','ACTUAL_DISPATCHED_COMMAND')
    need(set(terminal_input)<={'session_id','chars','yield_time_ms','max_output_tokens'} and type(terminal_input['session_id'])is int and terminal_input['session_id']==initial['session_id'] and terminal_input.get('chars','')=='','ORIGINAL_SESSION_PAIR')
''','shared_exact_original_command')
swap('def stage_sources(out):\n','def stage_sources(out,layout):\n','stage_signature')
swap("'actual_CAS':False,'actual_grant':False})\n","'actual_CAS':False,'actual_grant':False,'producer_layout':layout})\n",'stage_layout_fact')
swap("    need(out.is_relative_to(g.safe(a['registration_namespace'])),'DRAFT_NS')\n    for item in stage.values():\n        if isinstance(item,dict) and set(item)=={'path','sha256','bytes'}:r.verify(item)\n    need(stage['gate_ref']==GATE and stage['binder_ref']==BINDER,'STAGED_FROZEN_CONSUMERS')\n","    draft_inputs(g,r,s,sref,cref,stage_ref,str(out))\n",'draft_full_precheck')
swap("    planned=allocation_check(a['registration_output_root'],[s],s,metadata=False)\n    need(planned.is_relative_to(g.safe(a['registration_namespace'])),'EXACT_REGISTRATION_OUTPUT_BOUNDARY')\n",r'''    paths=registration_layout(g,a['producer_layout'],a)
    need(str(g.safe(dref['path']).parent)==str(paths['draft_output_root']) and str(g.safe(index['producer_ref']['path']).parent)==str(paths['stage_output_root']),'CURRENT_REGISTRATION_SIBLINGS')
    values=[s,sref,dref,regref,d,index,mfref,list(r.refs.values()),GATE,BINDER,pin(Path(__file__).resolve())]
    planned=allocation_check(a['registration_output_root'],values,s,metadata=False)
    need(str(g.safe(str(planned),g.safe(a['registration_namespace'])))==str(paths['native_output_root']),'EXACT_REGISTRATION_OUTPUT_BOUNDARY')
    r.unchanged();live4(before)
''','native_full_input_protection')
start="    inp=r.doc(inputref);response=r.doc(responseref)\n"
end="    # Copy caller-supplied original bytes, never reconstruct a response or locator.\n"
left=text.index(start,text.index('def capture_action('));right=text.index(end,left)
swap(text[left:right],"    # Shared closure above validates exact raw initial cmd/cwd and typed terminal/session pair.\n",'remove_capture_only_validation')
swap("elif action=='stage-code':result=stage_sources(out)","elif action=='stage-code':result=stage_sources(out,data['producer_layout'])",'stage_dispatch')

candidate=text.encode();ast.parse(candidate)
inverse=text
for e in reversed(edits):
    need(inverse.count(e['new'])==1,'INVERSE_ANCHOR_'+e['label']);inverse=inverse.replace(e['new'],e['old'],1)
need(inverse.encode()==original,'WHOLE_BYTE_INVERSE')
oldast=ast.parse(original);newast=ast.parse(candidate)
of={n.name:n for n in oldast.body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in newast.body if isinstance(n,ast.FunctionDef)}
changed={e['label'] for e in edits}
unchanged=[name for name in of if ast.dump(of[name],include_attributes=False)==ast.dump(nf[name],include_attributes=False)]
allowed={'preallocate','exact_resource_catalog','original_capture_closure','stage_sources','prepare_draft','run_registration','capture_action','entry'}
need(set(of)-set(unchanged)==allowed,'ONLY_AUTHORIZED_FUNCTIONS_CHANGED')
checks=[]
def check(name,value):need(value,name);checks.append({'id':name,'result':'STATIC_TRUE'})
check('whole_bytes_inverse',inverse.encode()==original)
check('new_functions_only',set(nf)-set(of)=={'registration_layout','draft_inputs'})
for name in unchanged:check('unchanged_AST_'+name,True)
for literal in ['PARTIAL_17_EXPLICIT','FORWARD_ONLY_NO_RETRY_NO_ROLLBACK','actual_native_exit','counter_reset']:
    check('preserved_literal_'+literal,literal in text)
check('shared_only_raw_command_guard',text.count("'ACTUAL_DISPATCHED_COMMAND'")==1)
for name in ['capture_action','seal_outer','seal_prepare']:
    check(name+'_uses_complete_capture_validator',any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='original_capture_closure' for n in ast.walk(nf[name])))
check('actual_resolved_resource_literal',"row['path']==str(actual) and row==pin(actual)" in text)
check('preallocate_before_leaf',text.index('planned=preallocate(action')<text.index('out=leaf(str(planned),True)',text.index('def entry(')))
check('draft_review_before_allocation',"extra.append(draft_inputs" in text[text.index('def preallocate'):text.index('def exact_resource_catalog')])
check('native_full_refs',"values=[s,sref,dref,regref,d,index,mfref,list(r.refs.values()),GATE,BINDER,pin(Path(__file__).resolve())]" in text)
check('no_scope_consumer_changed',before[4]['sha256']=='c391a1673856c4ff072474639bbcd843b0e87cb1910cef6db4bf1386b2fbc1c7')
check('no_binder_changed',before[5]['sha256']=='d2ad4dd777e1b5dfe2d96c20a1a36cfe25d245630fe3474e984f1c4276bc4f6b')
check('no_controller_changed',before[6]['sha256']=='75d3f1180764c817d828d8765e1dd824f8fc6912fff4675c0cdb78e0fd8ee503')
source=write('driver18_root_producer.v3.proposed.py',candidate)
save('whole-inverse.json',{'direction':'v3 -> exact dcf v2 bytes','base_ref':before[0],'candidate_ref':source,'edits':edits,'verified':True,'candidate_executed':False})
write('producer.v3.diff',''.join(difflib.unified_diff(original.decode().splitlines(True),text.splitlines(True),fromfile='frozen-v2',tofile='proposed-v3')).encode())
save('static-audit.json',{'schema':'researchos.source-preparation-static-audit.v1','checks':checks,'AST_parsed':True,'unchanged_functions':unchanged,'changed_existing_functions':sorted(allowed),'new_functions':['registration_layout','draft_inputs'],'candidate_imported_or_executed':False,'Go_SQL_Job_network_model_calls':0,'runtime_checks':'NOT_RUN','actual_native_exit':None})
after=[ref(p) for p in inputs];need(after==before,'FROZEN_INPUT_DRIFT');save('inputs.after.json',after)
print(json.dumps({'source':source,'static_checks':len(checks),'unchanged_functions':len(unchanged),'input_drift':0,'candidate_execution':False},ensure_ascii=False))
