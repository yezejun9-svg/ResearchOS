"""Receipt-only static finalization; no candidate import or target invocation."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).parent
ROOT=Path('D:/作品集/ResearchOS/research-os')
BASE=ROOT/'execution/v2.4/receipts/W05/W05-99'
OLD=BASE/'f08_driver18_root_binding_preparation_codex/a03c54991b5b44f9bdb6743d8b78b0c9'
RV=BASE/'f08_driver18_root_adapter_independent_source_review_codex/3a2dfa5a7b9545dbb85c82703e519be7'
inputs=json.loads((OUT/'inputs.before.json').read_bytes())['files']

def pin(p,raw=None):
    raw=p.read_bytes() if raw is None else raw
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):
    b=p.read_bytes();q=pin(p,b)
    if q not in inputs:inputs.append(q)
    return b
def write(name,raw):
    with (OUT/name).open('xb') as f:f.write(raw)
    return pin(OUT/name,raw)
def save(name,obj):return write(name,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def revised(name,preliminary,original,edits):
    old=read(original);raw=preliminary.read_bytes();text=raw.decode('utf8')
    inherited=json.loads((OUT/(preliminary.name+'.inverse.json')).read_bytes())['edits']
    for e in edits:
        if text.count(e['old'])!=1:raise ValueError('Exact final anchor '+e['label'])
        text=text.replace(e['old'],e['new'],1)
    inverse=text
    for e in reversed(inherited+edits):
        if inverse.count(e['new'])!=1:raise ValueError('Exact inverse '+e['label'])
        inverse=inverse.replace(e['new'],e['old'],1)
    if inverse.encode('utf8')!=old:raise ValueError('Inverse differs')
    ast.parse(text,filename=name)
    ref=write(name,text.encode('utf8'))
    save(name+'.inverse.json',{'original_ref':pin(original,old),'candidate_ref':ref,
        'whole_byte_inverse_equal':True,'edits':inherited+edits,'candidate_executed':False})
    write(name+'.diff',''.join(difflib.unified_diff(old.decode('utf8').splitlines(True),text.splitlines(True),fromfile=str(original),tofile=name)).encode('utf8'))
    return ref

old_manifest=json.loads(read(OLD/'manifest.json'))
for ref in old_manifest['members']:
    actual=pin(Path(ref['path']),read(Path(ref['path'])))
    if (actual['sha256'],actual['bytes'])!=(ref['sha256'],ref['bytes']):raise ValueError('Old manifest drift')
for name in ['handoff.json','manifest.json','origins.json']:read(RV/name)
review=json.loads(read(RV/'review.json'))
for ref in review['source_refs'].values():
    actual=pin(Path(ref['path']),read(Path(ref['path'])))
    if (actual['sha256'],actual['bytes'])!=(ref['sha256'],ref['bytes']):raise ValueError('Review source drift')

ar=revised('authority_adapter.v2.final.proposed.py',OUT/'authority_adapter.v2.proposed.py',OLD/'authority_adapter.proposed.py',[
    {'label':'R02-strict-roster-bools','old':"         'EXACT_PREPARE_18_ROSTER_NOT_PASS')",'new':"         'EXACT_PREPARE_18_ROSTER_NOT_PASS')\n    need(all(x['qualified'] is False and x['actual_exit'] is None for x in result['roster']), 'STRICT_ROSTER_TYPES')"},
    {'label':'R02-strict-outer-exit-types','old':"d['phase']==phase and d['actual_outer_exit']==0 and raw['exit_code']==0 and",'new':"d['phase']==phase and zero(d['actual_outer_exit']) and zero(raw['exit_code']) and"}
])
oldar=json.loads((OUT/'candidate-refs.json').read_bytes())['authority_validator_ref']
br=revised('binding_adapter.v2.final.proposed.py',OUT/'binding_adapter.v2.proposed.py',OLD/'binding_adapter.proposed.py',[
    {'label':'final-authority-path','old':"with_name('authority_adapter.v2.proposed.py')",'new':"with_name('authority_adapter.v2.final.proposed.py')"},
    {'label':'final-authority-pin','old':"GATE_SHA='"+oldar['sha256']+"'",'new':"GATE_SHA='"+ar['sha256']+"'"}
])
cr=json.loads((OUT/'candidate-refs.json').read_bytes())['controller_ref']

# Static comparison only: no function body is executed.
def top_assign(tree,name):
    for x in tree.body:
        if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id==name for y in x.targets):return ast.literal_eval(x.value)
    raise ValueError('Missing static literal '+name)
def funcs(raw):
    return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(raw).body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
currentA=Path(ar['path']).read_bytes();currentB=Path(br['path']).read_bytes();currentC=Path(cr['path']).read_bytes()
oldA=read(OLD/'authority_adapter.proposed.py');oldB=read(OLD/'binding_adapter.proposed.py')
ci=json.loads((OUT/'driver18_controller.v4.proposed.py.inverse.json').read_bytes());oldC=read(Path(ci['original_ref']['path']))
caps=top_assign(ast.parse(oldC),'CAPS')
if top_assign(ast.parse(currentC),'CAPS')!=caps or top_assign(ast.parse(currentA),'CAPS')!=caps:raise ValueError('Caps changed')
allowed={'authority':{'scope','registration','outer_completion','prepared_evidence','verify_authority','member_manifest'},
         'binding':{'build_scope','draft'},'controller':{'main'}}
unchanged={}
for label,old,new in [('authority',oldA,currentA),('binding',oldB,currentB),('controller',oldC,currentC)]:
    a,b=funcs(old),funcs(new);names=[]
    for name,val in a.items():
        if name not in allowed[label]:
            if b.get(name)!=val:raise ValueError('Unexpected AST delta '+label+':'+name)
            names.append(name)
    unchanged[label]=names
if top_assign(ast.parse(currentA),'FIXED')['controller_ref']!=cr['sha256']:raise ValueError('Controller pin')
if top_assign(ast.parse(currentB),'GATE_SHA')!=ar['sha256']:raise ValueError('Gate pin')

template=json.loads(read(OLD/'scope.UNBOUND.adapter.proposed.json'))
template['controller_ref']=cr;template['authority_validator_ref']=ar
scope_ref=save('scope.UNBOUND.adapter.v2.proposed.json',template)
rootinput=json.loads(read(OLD/'root-input.UNBOUND.proposed.json'))
rootinput['authority_validator_ref']=ar
# Remain explicitly UNBOUND; required additional registration fields are declared
# in the contract, not populated with current Root tuples/outputs.
inputref=save('root-input.UNBOUND.v2.proposed.json',rootinput)
proof=json.loads(read(OLD/'execute-prepared-evidence.UNBOUND.proposed.json'))
for key in ['launcher_stdout_ref','launcher_stderr_ref','launcher_pairing_ref']:proof[key]=None
proofref=save('execute-prepared-evidence.UNBOUND.v2.proposed.json',proof)
bundle=json.loads(read(OLD/'registration-evidence.UNBOUND.proposed.json'))
for key in ['draft_manifest_ref','requested_ref','wrapper_invocation_ref']:bundle[key]=None
bundleref=save('registration-evidence.UNBOUND.v2.proposed.json',bundle)

contract={
 'schema':'researchos.driver18-root-adapter-revision-contract.v2',
 'status':'SOURCE_PREPARATION_ONLY_PENDING_NONAUTHOR_REVIEW',
 'source_acceptance':False,'actual_CAS':False,'actual_grant':False,'target_executions':0,
 'selected_source_refs':{'controller_ref':cr,'authority_validator_ref':ar,'binding_adapter_ref':br},
 'superseded_unsealed_construction_outputs':['authority_adapter.v2.proposed.py','binding_adapter.v2.proposed.py','candidate-refs.json'],
 'originals_preserved':[pin(OLD/'handoff.json',read(OLD/'handoff.json')),pin(RV/'review.json',read(RV/'review.json'))],
 'R01':{'windows_keys':'casefold only for physical comparison; preserve original exact path/hash/bytes refs',
   'deny':'Every descendant of modernc.org/sqlite@v1.60.1, in any case, is excluded from offline_modcache_copies.',
   'controller_delta':'After offline copies, before source overlays and before any Go call, re-enumerate actual pristine files. Require exact 1899 casefold membership and original SHA/bytes; verify no reparse aliases.',
   'prepared_recheck':'Expected set independently reconstructed from both fixed 1899 locks + every offline mapping + exactly 8 source overlays. Reject collisions, missing/extra files and alias paths; actual work tree must equal it.'},
 'R02':{'roster':'Exact ordered 18 dictionaries I01..I18, NOT_STARTED, qualified is false, actual_exit null; strictly int zero native_calls/actual_Go_calls. No vacuous all().',
   'raw_names':'prepare_output_root/{prepared.json,result.json,manifest.json}; prepare_launcher_output_root/{requested.json,inner.invocation.json,stdout.raw,stderr.raw,completed.json,manifest.json}',
   'complete_manifests':'Actual full file-set equality, only manifest itself excluded. Original outputs must not be modified by the later Root sealer.',
   'launcher_pairing':'Root sealed researchos.driver18-root-sealed-launcher-pair.v1 stores exact original request/invocation/raw/manifest/result/prepared refs plus actual child PID/creationTime/native exit, not substitute generated success fields.',
   'outer_pairing':'Root completion references actual original outer invocation, initial tool response session ID and terminal tool response. Exact Python/launcher/phase/scope/grant argv, cwd ROOT, same run UUID and both output roots. Unsampled outer native exit remains null.',
   'known_limit':'Original owned-helper result has no argv. It cannot independently attest argv. Pairing therefore uses immutable exact requested.json + frozen launcher source + original owned result and Root captured original tool invocation/completion. Root source sealer remains OPEN and must bind these actual originals; directory adjacency alone is insufficient.',
   'same_work_lifetime':'Prepare and execute scopes deliberately share the same run_uuid/work/prepare output roots, but have distinct phase leases, registration namespaces, execute output leaves and independent full-scope reviews.'},
 'R03':{'new_registration_scope_fields':['registration_output_root (strict descendant of registration_namespace)','registration_timeout_seconds (explicit Root metadata budget, no template default)'],
   'draft_fields':['current_root_lease','invocation_contract {cwd ROOT, env scope.public_environment, timeout explicit Root value, output_root, registration_review_path}'],
   'review_fields':['current_scope_ref','registration_draft_ref','registration_draft_manifest_ref','canonical_paths exact ordered 4','original_refs exact ordered 4','desired_refs exact ordered 4','current_root_lease'],
   'prepared_refs_schema':'researchos.driver18-registration-prepared-refs.v1: current_scope_ref,registration_draft_ref,canonical_paths,original_refs,desired_refs,current_root_lease (exact shape)',
   'preaudit_schema':'researchos.driver18-registration-preexecution-audit.v1: actual_registration_executed=false,current_scope_ref,registration_draft_ref,original_refs,desired_refs',
   'acyclic_order':['bound phase scope (review paths only)','full-scope independent review','draft with original+desired+lease+invocation contract','prepared_refs and PRE-execution audit','draft manifest','independent registration review binds all prior hashes','exact requested invocation resolved with actual review ref','intent and actual Root CAS','post-CAS verified/audit/actual invocation and wrapper evidence','final registration manifest and bundle','Root phase grant'],
   'child_argv':['PINNED_PYTHON','-I','-S','-X','utf8','PINNED_REGISTER','--registration-draft','DRAFT_PATH','--draft-sha256','DRAFT_SHA','--registration-review','REVIEW_PATH','--review-sha256','REVIEW_SHA','--output-root','BOUND_REGISTRATION_OUTPUT'],
   'wrapper_argv':['PINNED_PYTHON','-I','-S','-X','utf8','PINNED_WRAPPER','--request','EXACT_REQUEST_PATH','--request-sha256','EXACT_REQUEST_SHA'],
   'runtime_pairs':'Actual child request/invocation full argv,cwd,env,timeout + current_scope_ref/draft/review/request refs; actual wrapper argv/cwd/env/request/inner_invocation + independent full Job result. Intent/audit/verified also bind exact scope,draft,request.',
   'namespace':'draft/code/prepared/preaudit/manifest/bundle under exact declared registration namespace; actual request/invocation/intent/audit/verified/raw/final MF under exact registration_output_root.',
   'NO_CYCLE':'Post-execution audit is distinct from independently reviewed PRE-execution audit. Neither draft nor its manifest contains the subsequent registration review SHA or actual request SHA.'},
 'caps':caps,'target_native_operation_graph':{'go_version':1,'graphs':3,'builds':4,'buildinfo':3,'cases':17,'I16_extra_stages':2,'total':30,'cap':32},
 'unchanged_boundaries':['I18 original body / fixed test source','I16 three stages and original module selection','partial17 I01..I16+I18 only','I17 OPEN_NOT_AUTHORIZED','normal/debug helper bytes','compiler/test/inner/outer/cleanup time limits','source writes and SQL24 adoption false'],
 'Root_A01_A07_OPEN':['A01 actual complete finite resources/offline catalog/Python OS inventory','A02 explicit phase tuples/cut/run roots/metadata budget/source guards','A03 actual bound scope nonauthor reviews','A04 actual Root CAS writer/wrapper/sealer implementation and independent review: two writes, immediate all4 CAS and final guards, forward-only failure preservation','A05 actual request/child/wrapper/tool raw evidence and unique grant producer','A06 prepare actual completion and immutable full closure before execute scope/review/CAS/grant','A07 actual Go graph/WORK/archives/buildinfo and tests NOT_RUN'],
 'no_claims':['No runtime semantic tests executed','No registration evidence minted','No current Root tuple invented','No all18 success or SQL24 permission','No independent source acceptance by author']}
contractref=save('revision-contract.json',contract)

controls=[
 ('R01','lowercase, mixedcase and uppercase pristine descendants including new leaf reject'),
 ('R01','case-only duplicate resource/manifest/destination rejects'),
 ('R01','valid unrelated dependency retains same exact source pin'),
 ('R01','post-copy pristine missing/extra/same-count replacement/changedbytes reject'),
 ('R02','complete real prepare exact18 roster and complete raw chain accepted as prepare only'),
 ('R02','empty/partial/duplicate/reordered roster and numeric fake bool reject'),
 ('R02','empty/missing/extra/case-colliding prepared file list rejects'),
 ('R02','foreign or missing launcher stdout/stderr/request/invocation/manifest rejects'),
 ('R02','wrong cwd, output root, phase, grant, PID/ctime pairing rejects'),
 ('R02','unrelated exit0 outertool, wrong initial/completion session rejects; nativeNULL retained'),
 ('R03','full current scope/draft/four canonical refs/lease and actual invocation chain accepted'),
 ('R03','same tuple other draft/scope/review rejects'),
 ('R03','same register prefix other argument or output/cwd/request rejects'),
 ('R03','wrong wrapper request/inner invocation/native result or namespace rejects'),
 ('R03','post-audit substituted as pre-audit or cyclic review binding rejects')]
save('future-controls.NOT_RUN.json',{'cases':[{'id':f'F{i:02d}','request':r,'description':v,'status':'NOT_RUN'} for i,(r,v) in enumerate(controls,1)],'target_calls':0})
save('static-audit.json',{'status':'STATIC_ONLY','AST_selected_files':3,'whole_byte_inverse_selected_files':3,
    'unchanged_AST_functions':unchanged,'caps_exact_equal':True,'fixed_inputs_and_launcher_unchanged':True,
    'native_operation_graph_static_total':30,'native_cap':32,'candidate_imports':0,'dynamic_negative_controls':0,
    'source_acceptance':False,'new_failure_origins':[],
    'provisional_constructor_outputs':'Preserved as produced; only final selected refs in handoff are proposed for review.'})
after=[]
for ref in inputs:
    actual=pin(Path(ref['path']))
    if actual!=ref:raise ValueError('Input drift '+ref['path'])
    after.append(actual)
save('inputs.final.before.json',{'files':inputs})
save('inputs.after.json',{'files':after,'drift':[]})
save('tool-observations.json',{'observations':[
  {'tool_chunk':'4d72d4','purpose':'Complete independent review read','outer_exit':0,'native_exit':None},
  {'tool_chunk':'687821','purpose':'Original full authority adapter read','outer_exit':0,'native_exit':None},
  {'tool_chunk':'273f04','purpose':'Original full binding adapter read','outer_exit':0,'native_exit':None},
  {'tool_chunk':'87be0b','purpose':'Original full controller read','outer_exit':0,'native_exit':None},
  {'tool_chunk':'0528a5','purpose':'Original launcher read','outer_exit':0,'native_exit':None},
  {'tool_chunk':'01c3b7','purpose':'Original evidence templates and fixed inputs read','outer_exit':0,'native_exit':None},
  {'tool_chunk':'5d9a84','purpose':'Own fresh namespace created','outer_exit':0,'native_exit':None},
  {'tool_chunk':'dadd5b','purpose':'Own pure IO/AST constructor','outer_exit':0,'native_exit':0}],
  'new_failure_origins':[],'target_executions':0,'note':'Final sealer invocation actual tool outcome supplied separately after return; never inferred here.'})
handoff=save('handoff.json',{'schema':'researchos.driver18-root-adapter-revision-handoff.v2','actor':'codex:/root/command_queue_impl',
 'status':'SOURCE_PREPARATION_REPORTED_PENDING_NONAUTHOR_REVIEW','writer':'STOPPED','review_ref':pin(RV/'review.json'),
 'selected_source_refs':{'controller_ref':cr,'authority_validator_ref':ar,'binding_adapter_ref':br},
 'contract_ref':contractref,'scope_template_ref':scope_ref,'root_input_template_ref':inputref,
 'prepared_proof_template_ref':proofref,'registration_bundle_template_ref':bundleref,
 'request_mapping':{'R01':'casefold physical subtree exclusion + postcopy exact pristine inventory + complete prepared reconstruction',
 'R02':'exact typed18 roster/full prepared membership + original launcher raw/complete MF + Root tool invocation/completion binding',
 'R03':'exact current scope/draft/four CAS/lease review + acyclic draft manifest/preaudit + actual full request/child/wrapper/CAS envelope'},
 'unchanged_controller_source_inverse':True,'unchanged_other_functions_AST':True,
 'full_original_files_preserved':True,'target_calls':0,'actual_CAS':False,'actual_grant':False,'new_failure_origins':[],
 'Root_remaining_OPEN':contract['Root_A01_A07_OPEN'],'I17':'OPEN_NOT_AUTHORIZED','source_acceptance':False,
 'original_author_role':'Driver/controller/adapter author; this is not independent source acceptance.'})
members=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file()]
mf=save('manifest.json',{'schema':'researchos.receipt-file-manifest.v1','files':members,'excluded_only_self':True,'listed':len(members)})
print(json.dumps({'handoff':handoff,'manifest':mf,'sources':{'controller':cr,'authority':ar,'binding':br},'inputs':len(inputs),'new_origins':0},ensure_ascii=False))
