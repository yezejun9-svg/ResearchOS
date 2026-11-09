"""Pure IO/AST construction only. Candidate code is never imported or executed."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).parent
BASE=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99')
OLD=BASE/'f08_driver18_root_binding_revision_preparation_codex/ae14ede5d4d34ea493f9945886997cb2'
RV=BASE/'f08_driver18_root_adapter_revision_independent_source_review_codex/737531efcc2842cc9f8181ced4155872'
inputs={}
def pin(p,b=None):
    b=p.read_bytes() if b is None else b
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p,sha=None):
    b=p.read_bytes();r=pin(p,b)
    if sha is not None and r['sha256']!=sha:raise ValueError('Input pin '+str(p))
    inputs[str(p)]=r;return b
def write(name,b):
    with (OUT/name).open('xb') as f:f.write(b)
    return pin(OUT/name,b)
def save(name,obj):return write(name,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def revise(name,p,edits):
    old=read(p);s=old.decode('utf8')
    for e in edits:
        if s.count(e['old'])!=1:raise ValueError('Unique forward anchor '+e['label'])
        s=s.replace(e['old'],e['new'],1)
    inverse=s
    for e in reversed(edits):
        if inverse.count(e['new'])!=1:raise ValueError('Unique inverse anchor '+e['label'])
        inverse=inverse.replace(e['new'],e['old'],1)
    if inverse.encode('utf8')!=old:raise ValueError('Whole byte inverse')
    ast.parse(s,filename=name)
    ref=write(name,s.encode('utf8'))
    save(name+'.inverse.json',{'original_ref':pin(p,old),'candidate_ref':ref,'edits':edits,
         'whole_byte_inverse_equal':True,'candidate_executed':False})
    write(name+'.diff',''.join(difflib.unified_diff(old.decode('utf8').splitlines(True),s.splitlines(True),fromfile=str(p),tofile=name)).encode('utf8'))
    return ref,old,s.encode('utf8')

review=json.loads(read(RV/'review.json','86d92f10d4f2c3970c3df1fe6dffb35c05f2b91e5158eaa537b01d6140ad993c'))
read(OLD/'handoff.json','63507eb9989bb2fc93c59df1227841a769d9ee0c63f594f84a0c29add39bac3e')
mf=json.loads(read(OLD/'manifest.json','b7ccaee73bcb7add06766ab1d46976e0f490bb4d39123fadeaccbd0b540216b8'))
for ref in mf['files']:
    raw=read(Path(ref['path']),ref['sha256'])
    if len(raw)!=ref['bytes']:raise ValueError('Prior member bytes')
controller_ref=pin(OLD/'driver18_controller.v4.proposed.py')
if controller_ref['sha256']!='75d3f1180764c817d828d8765e1dd824f8fc6912fff4675c0cdb78e0fd8ee503':raise ValueError('Unchanged controller')
anchor="    need(d['actual_native_launcher_exit'] is None,'UNSAMPLED_OUTER_NATIVE_REMAINS_NULL')"
block="""    # Root captures original tool input and its paired response as immutable
    # action records. A claimed session on a completion summary is insufficient.
    iaref=original['tool_initial_action_ref'];ta_ref=d['terminal_tool_action_ref']
    ia=r.doc(iaref);ta=r.doc(ta_ref)
    identity={'launcher_ref':s['launcher_ref'],'argv':d['argv'],'cwd':str(ROOT),
              'phase':phase,'scope_ref':sref,'grant_ref':gref,
              'run_uuid':s['actual_Root_registration']['run_uuid']}
    keys={'schema','actor','tool_name','input_ref','response_ref','initial_action_ref',
          'command_identity','request_event_locator','response_event_locator'}
    for action in [ia,ta]:
        need(set(action)==keys and action['schema']=='researchos.driver18-original-tool-action.v1' and
             action['actor']=='codex:/root' and action['command_identity']==identity,
             'ORIGINAL_TOOL_ACTION_IDENTITY')
        need(all(isinstance(action[k],str) and action[k] for k in
                 ['request_event_locator','response_event_locator']), 'ORIGINAL_TOOL_EVENT_LOCATORS')
    need(ia['tool_name']=='exec_command' and ia['initial_action_ref'] is None and
         same_ref(ia['input_ref'],original['tool_initial_input_ref']) and
         same_ref(ia['response_ref'],original['tool_initial_result_ref']), 'INITIAL_ACTION_INPUT_RESULT')
    first_input=r.doc(ia['input_ref'])
    need(isinstance(first_input,dict) and isinstance(first_input['cmd'],str) and first_input['cmd'] and
         first_input['cmd']==original['tool_command'] and safe(first_input['workdir'])==ROOT,
         'ORIGINAL_INITIAL_COMMAND_AND_CWD')
    need(ta['tool_name']=='write_stdin' and same_ref(ta['initial_action_ref'],iaref) and
         same_ref(ta['response_ref'],d['tool_result_ref']) and not same_ref(ta_ref,iaref) and
         ta['request_event_locator']!=ia['request_event_locator'], 'TERMINAL_ACTION_EXACT_RESPONSE')
    terminal_input=r.doc(ta['input_ref'])
    need(isinstance(terminal_input,dict) and set(terminal_input)<=
         {'session_id','chars','yield_time_ms','max_output_tokens'} and
         type(terminal_input['session_id']) is int and
         terminal_input['session_id']==initial['session_id']==original['session_id'] and
         terminal_input.get('chars','')=='', 'ACTUAL_TERMINAL_WAIT_INPUT')
    # Only this concrete asynchronous exec_command -> write_stdin contract is
    # supported. Never synthesize a session/cursor for a direct completion.
    if 'session_id' in raw:
        need(type(raw['session_id']) is int and raw['session_id']==terminal_input['session_id'],
             'TERMINAL_RESPONSE_SESSION_CONTRADICTION')
"""+anchor
ar,oldA,newA=revise('authority_adapter.v3.proposed.py',OLD/'authority_adapter.v2.final.proposed.py',[
    {'label':'R02-T01-original-terminal-action-input-response-pair','old':anchor,'new':block}])
br,oldB,newB=revise('binding_adapter.v3.proposed.py',OLD/'binding_adapter.v2.final.proposed.py',[
    {'label':'new-authority-path-only','old':"with_name('authority_adapter.v2.final.proposed.py')",'new':"with_name('authority_adapter.v3.proposed.py')"},
    {'label':'new-authority-hash-only','old':"GATE_SHA='66c2229f71b5d159134908a2605736a58381fff40b09bc8a4859f39723a67e06'",'new':"GATE_SHA='"+ar['sha256']+"'"}])
def funcs(raw):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
f0,f1=funcs(oldA),funcs(newA)
for name,code in f0.items():
    if name!='outer_completion' and f1.get(name)!=code:raise ValueError('Other authority function changed '+name)
if funcs(oldB)!=funcs(newB):raise ValueError('Binding functions changed')
for name in ['scope.UNBOUND.adapter.v2.proposed.json','root-input.UNBOUND.v2.proposed.json']:
    doc=json.loads(read(OLD/name));doc['authority_validator_ref']=ar
    save(name.replace('.v2.','.v3.'),doc)
contract={
 'schema':'researchos.driver18-terminal-tool-pair-contract.v1','status':'PREPARATION_ONLY',
 'prior_review_ref':pin(RV/'review.json'),'controller_ref_unchanged':controller_ref,
 'selected_authority_ref':ar,'selected_binding_ref':br,
 'only_semantic_delta':'outer_completion reads exact original initial tool action/input/result plus terminal wait action/input/result pairing.',
 'required_original_outer_invocation_fields_added':['tool_initial_action_ref','tool_initial_input_ref','tool_command'],
 'required_outer_completion_field_added':'terminal_tool_action_ref',
 'tool_action_schema':'researchos.driver18-original-tool-action.v1',
 'tool_action_fields':['schema','actor','tool_name','input_ref','response_ref','initial_action_ref','command_identity','request_event_locator','response_event_locator'],
 'initial_action':{'tool_name':'exec_command','initial_action_ref':None,'input_ref':'Exact original tool arguments JSON, including actual cmd and explicit workdir ROOT.','response_ref':'Exact original asynchronous tool response containing actual session_id and exit_code absent/null.'},
 'terminal_action':{'tool_name':'write_stdin','input_ref':'Exact original terminal write_stdin arguments JSON. session_id equals initial actual session; chars absent or empty. Only actual supported tool input keys allowed.','response_ref':'Exact raw final tool response, ref equal to completion.tool_result_ref; strict integer exit_code=0 is still required.','initial_action_ref':'Exact ref to the same captured initial action record.'},
 'event_locators':'Root preserves real request and paired response transport event locators. These are mandatory original capture metadata, never invented IDs. No capture producer or records are minted here.',
 'command_identity':'Both action records bind identical pinned launcher/actual argv/cwd/phase/scope/grant/run UUID. Initial cmd equals original outer invocation tool_command; workdir must resolve to ROOT.',
 'scope_of_supported_transport':'Asynchronous exec_command followed by an actual terminal write_stdin. The API uses session_id, not a cursor. Generic wait/cell tools, direct completion, invented session IDs, and synthetic normalized substitutes are unsupported and fail closed.',
 'capture_limits':'Raw tool response alone does not expose its request. Pair authenticity relies on separately reviewed Root original transport capture/sealer. Hash validation prevents substitution after that capture; this adapter cannot manufacture or independently attest the transport event.',
 'acyclic_capture_order':['actual initial input/result -> Root initial action record','actual terminal input/result -> Root terminal action record referencing initial action','outer invocation/completion and launcher pairing -> Root prepared proof','execute grant after independently reviewed actual prepare evidence'],
 'native_exit':'actual_native_launcher_exit remains NULL where not explicitly sampled; no inference of native0 from outer0.',
 'R01_R03':'All functions untouched; prior closed source review retained, not newly self-accepted.',
 'budgets_and_cases':'Controller identical 75d3; native30<=32, 600/750/3300/3600/5, image64/process2048/job16 unchanged. Exact18 prepare roster, partial17 execution, I16/I18 bytes unchanged, I17 OPEN_NOT_AUTHORIZED.',
 'Root_A01_A07':'All original actual-resource/binding/review/CAS/capture/grant/prepared/compiler execution gates remain OPEN.',
 'candidate_execution':False,'actual_grant':False,'actual_CAS':False,'SQL24_adoption':False}
contractref=save('terminal-pairing-contract.json',contract)
controls=[
 'Genuine captured initial and terminal input/result pair with correct session and pinned argv passes preparation-only provenance checks.',
 'Different actual terminal input session rejects even when completion summary claims expected session.',
 'Same summary session but action.response_ref points at unrelated response rejects.',
 'Missing terminal action or exact input ref rejects.',
 'Wrong initial action/result/input ref, command string, cwd, launcher/scope/grant binding rejects.',
 'Nonempty write_stdin chars, unknown tool kind or contradictory response session rejects.',
 'Direct completed initial response without real session remains unsupported; never mint session/cursor.',
 'Unsampled native remains NULL; outer0 cannot substitute native0.']
save('future-controls.NOT_RUN.json',{'controls':[{'id':f'T{i:02d}','description':c,'status':'NOT_RUN'} for i,c in enumerate(controls,1)],'executions':0})
save('static-audit.json',{'AST_parsed_candidates':2,'candidate_imports':0,'whole_byte_inverse_files':2,
 'authority_unchanged_functions':[name for name in f0 if name!='outer_completion'],
 'binding_all_functions_AST_equal':True,'controller_reused_exact_bytes':controller_ref,
 'source_acceptance':False,'new_failure_origins':[],'dynamic_controls':'NOT_RUN'})
save('inputs.before.json',{'files':list(inputs.values())})
after=[]
for ref in inputs.values():
    got=pin(Path(ref['path']))
    if got!=ref:raise ValueError('Input drift '+ref['path'])
    after.append(got)
save('inputs.after.json',{'files':after,'drift':[]})
save('tool-observations.json',{'observed':[{'tool_chunk':'2583cd','purpose':'Complete latest independent review','outer_exit':0,'native_exit':None},
 {'tool_chunk':'48f3c4','purpose':'Own new namespace and exact outer_completion source span','outer_exit':0,'native_exit':None}],
 'new_failure_origins':[],'note':'Preparation script final native/outer result reported after return; not guessed inside this script.'})
h=save('handoff.json',{'schema':'researchos.driver18-terminal-pair-preparation-handoff.v1',
 'actor':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','writer':'STOPPED',
 'request':'R02-T01','review_ref':pin(RV/'review.json'),'authority_ref':ar,'binding_ref':br,
 'controller_ref_unchanged':controller_ref,'contract_ref':contractref,
 'whole_byte_inverse':True,'other_functions_AST_unchanged':True,'input_drift':[],
 'target_calls':0,'actual_grant':False,'actual_CAS':False,'new_failure_origins':[],
 'I17':'OPEN_NOT_AUTHORIZED','source_acceptance':False,'Root_A01_A07':'OPEN',
 'original_ae14_and_737531_untouched':True})
members=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file()]
m=save('manifest.json',{'schema':'researchos.receipt-file-manifest.v1','files':members,'excluded_only_self':True,'listed':len(members)})
print(json.dumps({'handoff':h,'manifest':m,'authority':ar,'binding':br,'inputs':len(inputs),'new_origins':0},ensure_ascii=False))
