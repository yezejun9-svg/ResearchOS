"""Pure IO/AST source-preparation audit. Never imports/executes producer code."""
import ast,hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
P=ROOT/'execution/v2.4/receipts/W05/W05-99'
MAP=P/'f08_driver18_root_producer_contract_mapping_codex/172e0c45ad4a4b25b19e1da1822804f2'
inputs={};checks=[]
def read(p):
    b=p.read_bytes();inputs[str(p)]={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def ref(p):
    b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def doc(name,obj):
    p=OUT/name
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    return ref(p)
def need(v,label):
    if not v:raise ValueError(label)
    checks.append({'id':label,'result':'PASS_STATIC_ONLY'})
mapping=json.loads(read(MAP/'contract-map.json'))
need(inputs[str(MAP/'contract-map.json')]['sha256']=='7fec6433442a2fb6fa3f37c1af115e087a9f76541216d76a5fb2aff926af6644','fixed contract-map SHA')
for name in ['handoff.json','contract-map.md','manifest.json']:read(MAP/name)
consumers={}
for key,pin in mapping['consumer_refs'].items():
    raw=read(Path(pin['path']));need(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'fixed '+key);consumers[key]=raw.decode('utf-8')
for key in ['actual_cli_pipeline_ref','prior_independent_review_ref']:
    pin=mapping[key];raw=read(Path(pin['path']));need(hashlib.sha256(raw).hexdigest()==pin['sha256'] and len(raw)==pin['bytes'],'fixed '+key)
source=(OUT/'driver18_root_producer.proposed.py').read_bytes();tree=ast.parse(source);text=source.decode();func={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
need(len(func)==34,'34 concrete producer functions parsed')
def segment(name):return ast.get_source_segment(text,func[name])
for fn in func:need(bool(func[fn].body),'nonempty function '+fn)
gate_tree=ast.parse(consumers['authority']);binder_tree=ast.parse(consumers['binder'])
fixed=ast.literal_eval(next(n.value for n in gate_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FIXED' for t in n.targets)))
template=ast.literal_eval(next(n.value for n in binder_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TEMPLATE_REF' for t in n.targets)))
raw=read(Path(template['path']));need(hashlib.sha256(raw).hexdigest()==template['sha256'],'original scope template')
s=json.loads(raw)
selected_fixed={}
for key in fixed:
    pin=mapping['consumer_refs']['controller'] if key=='controller_ref' else s[key]
    b=read(Path(pin['path']));need(hashlib.sha256(b).hexdigest()==fixed[key] and len(b)==pin['bytes'],'unchanged fixed '+key);selected_fixed[key]=pin
fixed_inputs=json.loads(inputs[str(Path(selected_fixed['fixed_inputs_ref']['path']))] and Path(selected_fixed['fixed_inputs_ref']['path']).read_bytes())
# Only source/lock metadata are pinned here; no 1899-member module scan or DB read.
for k,v in fixed_inputs.items():
    if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}:
        b=read(Path(v['path']));need(len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'],'fixed input '+k)
need("if action in ['register_entry','wrapper_entry']" in text,'fixed executable role dispatch')
need("g.prepared_evidence(r,s,proof)" in segment('grant'),'execute grant requires complete actual prepare')
need("b.build_scope(g,r,inp)" in segment('prepare_scope') and "b.draft(g,r,sref,cref,copiesref,out)" in segment('prepare_draft'),'reuse actual frozen binder field producers')
need("g.registration(r,s,sref,bundle)" in segment('seal_registration'),'consumer registration semantic closure')
need("g.outer_completion(r,cref,s,sref,gref,phase)" in segment('seal_outer'),'consumer exact terminal action validation')
need("g.prepared_evidence(r,view,proof)" in segment('seal_prepare'),'consumer full prepared membership/roster validation')
need("live4(expected);os.replace(tmp,target)" in segment('register_entry'),'all4 CAS immediately before each atomic replace')
need("source_guard(g,r,s,out,'register-after'" in segment('register_entry') and ";live4(desired)" in segment('register_entry'),'final source guard then all4 CAS')
need(segment('grant').index("source_guard(g,r,s,pf,'preflight'")<segment('grant').index('auth.mkdir()'),'actual preflight before auth directory')
need("value['root_source_guard_ref']=source_guard(g,r,s,auth,'grant-final',copies);live4(desired)" in segment('grant'),'refresh facts after full long authority reads and before grant write')
need("row['original_payload']==r.doc(ref)" in segment('reviewed') and "pc==oldcp and po==oldow" in segment('reviewed'),'whole old failure prefix and unrelated canonical inverse')
need("result['actual_exit']" not in segment('seal_outer') and "'actual_native_launcher_exit':None" in segment('seal_outer'),'outer native never inferred from tool exit')
need("'stdout_ref':pin(so) if so.exists() else None" in segment('owned') and "'actual_native_exit':None if result is None" in segment('owned'),'nullable native and raw before owned failure check')
need("initialref is None" in segment('capture_action') and "'REAL_ASYNC_INITIAL_REQUIRED'" in segment('capture_action'),'real async initial action only')
need("inp['session_id']==ir['session_id']" in segment('capture_action') and "r.verify(responseref)" in segment('capture_action'),'original terminal input and response preserved and paired')
need('subprocess' not in text and 'taskkill' not in text and 'sqlite3' not in text,'no bare PID/subprocess/SQL path')
need(text.count('os.replace(')==1 and 'os.remove(' not in text and 'shutil' not in text,'only exact2 loop atomic writer no rollback')
need('sys.exit(exit_code)' in text and 'try:exit_code=entry' in text,'SystemExit outside try')
need("'PARTIAL_17_EXPLICIT'" in text and 'I17_NOT_AUTHORIZED' in consumers['authority'],'partial17 not full18')
need(mapping['caps']['native_calls']==32 and mapping['caps']['inner_seconds']==3300 and mapping['caps']['outer_seconds']==3600 and mapping['caps']['cleanup_seconds']==5,'original finite driver caps')
def dictionary_keys(fn,var):
    keys=set()
    for n in ast.walk(func[fn]):
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==var for t in n.targets) and isinstance(n.value,ast.Dict):
            keys.update(k.value for k in n.value.keys if isinstance(k,ast.Constant) and isinstance(k.value,str))
    return keys
outergate=next(x for x in mapping['gates'] if x['id']=='A05')
prep=next(x for x in mapping['gates'] if x['id']=='A06')
need(dictionary_keys('seal_prepare','pair')==set(prep['pair_exact_fields'])-{'automatic_retry:false','counter_reset:false'}|{'automatic_retry','counter_reset'},'all exact launcher-pair consumer keys')
action_keys={'schema','actor','tool_name','input_ref','response_ref','initial_action_ref','command_identity','request_event_locator','response_event_locator'}
capture_ast=func['capture_action'];lastdict=[n for n in ast.walk(capture_ast) if isinstance(n,ast.Dict) and len(n.keys)==9]
need(any({k.value for k in n.keys if isinstance(k,ast.Constant)}==action_keys for n in lastdict),'exact original action keys')
for item in ['resources','stage-code','scope','draft','register','seal-registration','grant','launch-request','capture-action','seal-outer','seal-prepare']:need(repr(item) in segment('entry'),'implemented action '+item)
after=[ref(Path(p)) for p in inputs];need(after==list(inputs.values()),'all fixed inputs unchanged')
doc('inputs.before.json',list(inputs.values()));doc('inputs.after.json',after)
doc('source-new-file-explanation.json',{'producer_ref':ref(OUT/'driver18_root_producer.proposed.py'),'new_file':True,'whole_file_inverse':'Not applicable: original file absent; no old source overwritten','reused_unchanged':mapping['consumer_refs'],'reused_pattern_ref':mapping['actual_cli_pipeline_ref'],'pattern_mappings':[{'old':'register 288-311','new':'register_entry','preserved':'immutable intent, raw original/desired, source guard, all4 immediately before each replace, final all4, no rollback'},{'old':'run_registration 313-333','new':'wrapper_entry/run_registration','preserved':'owned Job, actual nullable native and original raw; added separate actual wrapper Job'},{'old':'seal 335-351','new':'seal_registration','preserved':'actual results, postguard all4, separate audit and manifest; exact driver bundle fields'},{'old':'grant 353-460','new':'grant','preserved':'actual preflight before fresh auth, canonical copies, final fact refresh/CAS'}],'old_counter_or_grant_reused':False,'source_test_bodies_edited':False})
interfaces={
 'schema':'researchos.driver18-root-producer-source-interface.v1','status':'SOURCE_PREPARATION_ONLY','entry':'pinnedPython -I -S -X utf8 PRODUCER ACTION --input-ref EXACT_JSON_REF --output-root NEW_OWNED_ROOT',
 'actions':{
 'resources':{'input':'researchos.driver18-root-resource-input.v1 with exact files/python/go/GOROOT/compiler_images/offline_modcache_copies/provenance_refs','result':'new finite catalog; actual graph remains OPEN'},
 'stage-code':{'input':'explicit immutable Root staging request (must be readable; carries no execution authority)','result':'same producer bytes + register.py/run.py pinned bootstrap + staged-code.json; resource catalog must include these staged files'},
 'scope':{'input':'unchanged consumer researchos.driver18-root-binding-input.v1; every actual registration/resource/environment/output field caller-required','result':'binder output validated by unchanged gate.scope'},
 'draft':{'input':['scope_ref','controller_review_ref','staged_code_ref'],'result':'actual four live copies, full desired and inverse-protected draft, exact preaudit/prepared refs, draft manifest'},
 'register':{'input':['draft_ref','registration_review_ref'],'result':'future Root real two-write CAS inside inner owned Job plus separately observed outer wrapper Job; no auto retry'},
 'seal-registration':{'input':['draft_ref','registration_review_ref'],'result':'actual bundle accepted by unchanged gate.registration or fail with raw'},
 'grant':{'input':['scope_ref','registration_bundle_ref','prepared_proof_ref nullable prepare only','new_preflight_root','new_authorization_root'],'result':'current phase grant after actual full facts; execute requires prepare proof'},
 'launch-request':{'input':['scope_ref','grant_ref'],'result':'exact PowerShell command and tools.exec_command input; DOES NOT dispatch it'},
 'capture-action':{'input':['scope_ref','grant_ref','tool_name','original_input_ref','original_response_ref','request_event_locator','response_event_locator','initial_action_ref nullable initial only'],'result':'copies exact actual tool bytes; no tool call or invented locator'},
 'seal-outer':{'input':['scope_ref','grant_ref','initial_action_ref','terminal_action_ref'],'result':'paired exact actual outer completion; nonzero preserved then refused'},
 'seal-prepare':{'input':['scope_ref','grant_ref','outer_completion_ref'],'result':'exact launcher pair + full prepare proof validated by immutable consumer; no mutation of original launcher/inner trees'}},
 'registration_review_additional_required_field':'producer_ref exact staged engine ref, in addition to all existing consumer-required fields; binds actual source behind both pinned bootstraps',
 'scope_review_requirement':'Current independently reviewed complete phase scope plus separately reviewed producer implementation/current draft; old source-only verdict is not a runtime grant',
 'trust_boundary':'Root supplies original transport input/response and actual event locators from tools. Python cannot authenticate or invent its own tool transcript. This code preserves bytes and verifies consumer pairing; independent original-trace review remains mandatory.',
 'not_supported':['synchronous exec result without actual session ID','automatic retry or rollback after partial CAS','I17 incorporation/full18 PASS','new consumer or helper ABI','past CLI qualification reused as driver results']}
doc('interfaces.json',interfaces)
open_gates=[{'id':'A01','implementation':'resource_catalog/runtimes/immutable refs','actual':'OPEN actual selected catalog/loaded resources and dependency closure supplied and independently reviewed by Root; no trees copied here'}, {'id':'A02','implementation':'prepare_scope/prepare_draft/reviewed','actual':'OPEN explicit current tuples, origins, canonical snapshot and dedicated phase lease'}, {'id':'A03','implementation':'reviewed exact new bound and registration reviews','actual':'OPEN real separate nonauthor decisions; all author/source-only evidence insufficient'}, {'id':'A04','implementation':'register_entry/wrapper_entry/run_registration/seal_registration','actual':'NOT_RUN no canonical writes; actual Root execution requires full new source/draft review'}, {'id':'A05','implementation':'source_guard/grant/launch_request/capture_action/seal_outer','actual':'NOT_RUN no grant, tool dispatch, session, or raw transport facts manufactured'}, {'id':'A06','implementation':'seal_prepare delegates complete tree/roster/pair verification to exact immutable gate','actual':'NOT_RUN no prepare run/copied source/DB/Go'}, {'id':'A07','implementation':'unchanged v4 controller/launcher selected by immutable scope; separate execute lease after A06','actual':'NOT_RUN partial17 only, I17 OPEN_NOT_AUTHORIZED; all18 not qualified'}]
doc('A01-A07-implementation-and-open.json',open_gates)
doc('finite-operation-contract.json',{'caps':mapping['caps'],'driver_native_roster':next(x for x in mapping['gates'] if x['id']=='A07')['native_roster'],'Root_metadata_Git_and_Job_calls':'separate explicit phase registration_timeout_seconds; not silently charged to or used to expand 32 driver calls','I16':'unchanged three separate processes and complete original/fork module copies','I18':'unchanged full original TestRegisteredFunctions; 750s per test retained','I17':'OPEN_NOT_AUTHORIZED; new8a3c not silently imported','future_actual_tuple':None,'future_resource_catalog':None,'future_registration_review':None,'future_grant':None,'future_prepare_proof':None,'actual_all18_pass':False})
doc('future-negative-controls.NOT_RUN.json',{'status':'NOT_RUN','controls':['missing/null resource or private/unpinned Python module','offline pristine source collision/casefold duplicate','wrong bound scope review/full SHA/controller producer pin','old registration review/original copies/canonical desired inversion','foreign row mutation before first or second replace; partial CAS remains without rollback','different actual wrapper Job substituted for inner or missing real PID/ctime','nonzero/NULL registration exit/timeout/cleanup error','unrelated terminal response, wrong initial session/wait input/locator','empty or partial prepare roster/files; missing source overlay, wrong I16/I18 source','grant missing complete prepare proof or trying I17/full18','changed live four canonical files after source guard or before grant write']})
doc('tool-observations.json',{'records':[{'chunk_id':c,'actual_outer_exit':0,'actual_native_exit':None,'operation':op} for c,op in [('ce312f','read actual mapping/handoff; response truncated, exact map later read as JSON'),('7ab70b','read immutable binder/gate head'),('c10c04','read gate registration/prepare/outer consumers'),('1f6424','read exact A03/A04 and v7 registration algorithms'),('191b02','read fixed controller and v7 runtime source'),('60bacb','new exclusive owned receipt namespace'),('932781','pure AST of proposed producer')]],'new_failure_origins':[],'candidate_imports':0,'target_calls':0,'canonical_writes':0,'native_nullable_policy':'outer metadata exit does not invent a sampled native code'})
audit=doc('static-audit.json',{'checks':checks,'failed':0,'input_count':len(inputs),'input_drift':[],'producer_AST':True,'candidate_imports':0,'target_calls':0,'actual_tool_runtime_authority':False})
hdf=doc('handoff.json',{'schema':'researchos.driver18-root-producer-preparation-handoff.v1','author':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','writer':'STOPPED_AFTER_SEAL','producer_ref':ref(OUT/'driver18_root_producer.proposed.py'),'interfaces_ref':ref(OUT/'interfaces.json'),'implementation_open_ref':ref(OUT/'A01-A07-implementation-and-open.json'),'mapping_ref':ref(MAP/'contract-map.json'),'frozen_consumers':mapping['consumer_refs'],'static_audit_ref':audit,'input_before_ref':ref(OUT/'inputs.before.json'),'input_after_ref':ref(OUT/'inputs.after.json'),'new_file_explanation_ref':ref(OUT/'source-new-file-explanation.json'),'whole_inverse':'new file only; original consumer/binder/controller/v7 bytes unchanged and pinned','all_actual_A01_A07':'OPEN/NOT_RUN','I17':'OPEN_NOT_AUTHORIZED','new_failure_origins':[],'actual_CAS':False,'actual_grant':False,'Go_SQL_Job_model_network':0,'source_acceptance':False,'formal_increment':0})
members=[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json']
mf=doc('manifest.json',{'members':members,'member_count':len(members),'self_excluded':True,'old_files_mutated':False})
print(json.dumps({'handoff':hdf,'manifest':mf,'producer':ref(OUT/'driver18_root_producer.proposed.py'),'checks':len(checks),'inputs':len(inputs)},ensure_ascii=False))
