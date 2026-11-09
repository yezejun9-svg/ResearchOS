from pathlib import Path
import ast,difflib,hashlib,json
P=Path(__file__).parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(name,b):
 with (P/name).open('xb') as f:f.write(b)
 return pin(P/name)
def obj(name,x):return put(name,(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
base=(P/'original.r332.register.py.txt').read_bytes()
assert b'\r\n' not in base
old=(P/'forward_head_engine.final.proposed.py').read_bytes()
selected=old.replace(b'\r\n',b'\n')
assert selected.replace(b'\n',b'\r\n')==old
ast.parse(selected)
er=put('forward_head_engine.selected.proposed.py',selected)
oldbuilder=(P/'build_forward_draft.final.proposed.py').read_bytes()
builder=oldbuilder.replace(repr(str(P/'forward_head_engine.final.proposed.py')).encode(),repr(er['path']).encode()).replace(hashlib.sha256(old).hexdigest().encode(),er['sha256'].encode()).replace(f'len(raw) != {len(old)}'.encode(),f"len(raw) != {er['bytes']}".encode())
ast.parse(builder)
br=put('build_forward_draft.selected.proposed.py',builder)
bl=base.splitlines(keepends=True);nl=selected.splitlines(keepends=True)
ops=[]
for tag,a,b,c,d in difflib.SequenceMatcher(None,bl,nl,autojunk=False).get_opcodes():
 if tag!='equal':ops.append({'old_line_start':a,'old_line_end':b,'new_line_start':c,'new_line_end':d,'old_hex':b''.join(bl[a:b]).hex(),'new_hex':b''.join(nl[c:d]).hex()})
inverse=list(nl)
for op in reversed(ops):
 assert b''.join(inverse[op['new_line_start']:op['new_line_end']]).hex()==op['new_hex']
 inverse[op['new_line_start']:op['new_line_end']]=bytes.fromhex(op['old_hex']).splitlines(keepends=True)
assert b''.join(inverse)==base
obj('whole-inverse.selected.json',{'base':pin(P/'original.r332.register.py.txt'),'selected':er,'hunks':ops,'whole_bytes_restored':True,'line_ending':'original LF retained'})
put('forward-engine.selected.diff',''.join(difflib.unified_diff(base.decode().splitlines(True),selected.decode().splitlines(True),fromfile='r332/register.py',tofile='forward_head_engine.selected.proposed.py')).encode())
bt=ast.parse(base);nt=ast.parse(selected)
bf={n.name:n for n in bt.body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in nt.body if isinstance(n,ast.FunctionDef)}
same=[k for k in bf if k in nf and ast.dump(bf[k],include_attributes=False)==ast.dump(nf[k],include_attributes=False)]
samebytes=[]
for k in same:
 a=b''.join(bl[bf[k].lineno-1:bf[k].end_lineno]);b=b''.join(nl[nf[k].lineno-1:nf[k].end_lineno]);assert a==b;samebytes.append(k)
request={'schema':'researchos.desktop58-forward-head-request.v1','actor':'codex:/root','authorized':False,'source_acceptance':False,'formal_increment':0,'new_execution_grant':None,'registration_namespace':None,'run_uuid':None,'timestamp':None,'before_tuple':[332,160,516],'after_tuple':None,'head_before':'a510dbef4a7e08fb5c428df44c39b133f3ffa856','head_after':'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7','canonical_before':None,'original_copy_refs':None,'source_closure_review_ref':None,'source_closure_manifest_ref':None,'origin_cut_ref':None,'status_ref':None,'old_deleted_paths':None,'runtime_resources_ref':None,'toolchain_lock_ref':None,'helper_ref':None,'code_refs':{'engine':er,'builder':br},'immutable_inputs':None}
obj('request-contract.json',{'status':'TEMPLATE_NOT_EXECUTABLE_NULL_REQUIRED_FIELDS','shape':request,'ref_shape':{'path':'actual immutable path','sha256':'exact lowercase SHA256','bytes':'exact integer'},'origin_cut_shape':{'schema':'researchos.desktop58-forward-origin-cut.v1','before_tuple':'same request','after_tuple':'same request derived by Root','counter_reset':False,'origins':'full unchanged rows: evidence_ref/original_payload/count_once:true/counter_reset:false; no native inference'},'required_current_source_membership':'immutable_inputs must include each actual union58 path; bytes checked against sealed tree-after blob IDs','canonical_order':['checkpoint','path_ownership','step_state','commands'],'namespace':'fresh integration_codex/desktop58-post-integration-<explicit-root-revision>-<run_uuid>','runtime':'existing files1212; selected code_refs and emitted register/run/seal are additionally pinned code, not arbitrary runtime expansion','no_future_root_values_in_template':True})
flow=[
 {'step':'request -> builder','producer':'Root immutable request ref+explicit CLI SHA','consumer':'initialize_request/closure','checks':'sealed review/MFs/current58 blobs/origins/current4; no helper; fresh namespace'},
 {'step':'builder -> draft','producer':'prepare_request','files':['register.py','run.py','seal.py','prepared_refs.json','audit.json','original4','desired4'],'consumer':'independent W05 review','checks':'mode-only script derivation; all actual verified inputs pinned'},
 {'step':'review -> run -> register','producer':'W05 actual root-registration-source-review.v1','consumer':'review_ok and owned run','checks':'fourcode pins, before/after tuple, originalcopy4, positive decision/actualFalse; exact request argv'},
 {'step':'register -> seal','producer':'owned actual invocation/intent/verified/done2/afterruntime','consumer':'seal','checks':'native0, Job flags, current desired4, sourceguardthenfourtargetcheck'},
 {'step':'seal -> future work','producer':'registration audit/handoff/manifest','consumer':'Root future independent scope','checks':'no materialized scope/grant; fresh58/sourceacceptance/formal remain false'}]
obj('static-composition.json',{'status':'SOURCE_CONTROL_FLOW_INSPECTION_NOT_RUNTIME','positive_path':flow,'future_controls_NOT_RUN':['valid closed source request -> pure IO draft -> positive independent metadata review -> owned register -> seal','changed current58 hash拒绝','missing current58 immutable member拒绝','duplicate/already registered origin拒绝','old failure payload/native NULL rewritten拒绝','other task ownership mutation拒绝','live canonical ref inside immutable_inputs拒绝','canonical change during source_guard拒绝 before replace','foreign head/index/status拒绝','missing original tool terminal pairing拒绝','partial CAS preserves intent and first failure; no rerun','grant mode absent/unknown mode拒绝'],'source_function_byte_unchanged':samebytes,'inverse_hunks':len(ops),'whole_inverse':True,'AST_only':True,'candidate_imports':0,'candidate_native':0})
inputpaths=[ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop15-source-integration-r332-8792799f829a23452ae5d89a59e1b0cf/register.py',ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-post-integration-r324/register.py',ROOT/'execution/v2.4/receipts/W13/W13-03/desktop58_source_execution_independent_review_codex/a76cb528a87f45529adb3da26418eabb/review.json',ROOT/'execution/v2.4/receipts/W13/W13-03/desktop58_source_execution_independent_review_codex/a76cb528a87f45529adb3da26418eabb/manifest.json']
rv=json.loads(inputpaths[2].read_bytes())
inputpaths += [Path(rv[k]['path']) for k in ['completed_ref','source_intent_ref','outer_invocation_ref','root_tool_observations_ref','scope_ref','grant_ref','manifest_ref','outer_manifest_ref']]
before=[pin(p) for p in inputpaths]
assert before[0]['sha256']=='bb3beccc2a4c2a576b648871dacc0dcab8f8bbff5258e1f0369d1d0af0f13280'
assert before[1]['sha256']=='1b8f837711f66ab46bcf7ef8eb6783fdf5444bd60f170b70bfe70537808a3518'
assert before[2]['sha256']=='7d82779e61ff50c3072e9d008531b2409e3ee288235ec7ad12a24f276f4de4b7'
obj('inputs.final-before.json',{'files':before,'limit':'final sealing point-in-time hashes; earlier actual read pins are in source records/tools, not an invented pre-start vector'})
after=[pin(p) for p in inputpaths];assert before==after
obj('inputs.final-after.json',{'files':after,'drift':[]})
obj('tool-observations.json',{'candidate_execution':0,'successful_outer_chunks':['7e0f6b','ea1f80','d8796a','e7726e','7019ca','902277','1a9ca6','5e1162','fe9401','f831ac','4122f1','f0db97'],'constructor_initial_running':{'chunk':'14f71a','session':21572,'terminal_chunk':'fe9401','actual_outer_exit':0},'independently_sampled_native_exits':None,'one_failed_origin':pin(P/'failure-origin.09b17d.json'),'failed_input':pin(P/'failure-input.09b17d.json'),'no_retry':True,'limitation':'Tool response summaries retain observed chunk/exit values. Uncaptured complete tool stdout is not manufactured.'})
h=obj('handoff.json',{'schema':'researchos.desktop58-forward-head-source-preparation-handoff.v1','actor':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_STOPPED_PENDING_NONAUTHOR_REVIEW','selected_engine_ref':er,'selected_builder_ref':br,'request_contract_ref':pin(P/'request-contract.json'),'composition_ref':pin(P/'static-composition.json'),'inverse_ref':pin(P/'whole-inverse.selected.json'),'input_count':len(before),'input_final_drift':0,'unchanged_function_AST_and_bytes':samebytes,'removed_grant':True,'old_engine_ref':before[0],'source_closure_review_ref':before[2],'candidate_executed':False,'actual_draft_generated':False,'canonical_writes':0,'product_calls':0,'source_acceptance':False,'formal_increment':0,'new_failure_origins':[pin(P/'failure-origin.09b17d.json')],'OPEN':['Root actual immutable request/cut/tuples and fresh metadata namespace','Independent source/static review of this preparation','Root actual pureIO draft production and separate W05 registration review','Root owned run/CAS/seal','Future fresh58 and GUI/SQL24/formal remain not authorized'],'old_provisional_outputs_preserved':True})
members=[pin(p) for p in sorted(P.iterdir()) if p.is_file()]
m=obj('manifest.json',{'schema':'researchos.immutable-preparation-manifest.v1','count':len(members),'entries':members,'excluded_only':['manifest.json'],'source_acceptance':False})
print(json.dumps({'handoff':h,'manifest':m,'engine':er,'builder':br,'listed':len(members),'new_origins':1,'status':'STOPPED'},ensure_ascii=False))
