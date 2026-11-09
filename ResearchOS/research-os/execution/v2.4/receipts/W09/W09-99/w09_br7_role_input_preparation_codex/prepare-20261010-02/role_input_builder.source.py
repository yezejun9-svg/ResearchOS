"""Root-run metadata builder. Import is inert; no Canon/registry/stage authority."""
from pathlib import Path, PurePosixPath
import argparse,copy,hashlib,json,ntpath,os,re,types

ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
W=ROOT/'execution/v2.4/receipts/W09/W09-99'
ORIGIN=ROOT/'execution/v2.4/root_original_events/W09/W09-99'
ROOT_LOG='C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
REGISTRY='execution/v2.4/root_delivery_captures/W09/W09-99/execution-roles.json'
INPUTS_SHA='50930e0d982b5c7c570280cf2f9e65ad273256176ea3eaf637763e8926244c12'
ROLE_ACTORS={'SOURCE_AUTHOR':'/root/full_w09_source_review','EXECUTOR':'codex:/root',
 'EVIDENCE_ASSEMBLER':'codex:/root','VERIFIER':'/root/backup_regression_resources','ROOT_OBSERVER':'codex:/root'}
ROOT_AUDITS={'EXECUTOR':'mode01_observation_audit_ref','EVIDENCE_ASSEMBLER':'assembly_owner_observation_audit_ref',
 'ROOT_OBSERVER':'scope_observation_audit_ref'}
REQUEST_FIELDS={'schema','actor_id','preparation_id','proposal_ref','context_seed_ref',*ROOT_AUDITS.values()}
CAPTURE_FIELDS={'schema','actor_id','Root_thread_id','source_audit_path','source_line_offsets','original_line_sha256',
 'source_prefix_size_observed','original_capture_ref','binding_sha256'}

def need(ok,code):
    if not ok:raise ValueError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def decode(raw):
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'NONFINITE_JSON'))
def exact(v,keys,code):need(type(v) is dict and set(v)==set(keys),code)
def ref_shape(ref):
    exact(ref,('path','sha256','bytes'),'EXACT_REF3')
    need(type(ref['path']) is str and bool(ref['path']) and type(ref['sha256']) is str
         and re.fullmatch('[0-9a-f]{64}',ref['sha256']) and type(ref['bytes']) is int and 0<ref['bytes']<=32*1024*1024,'TYPED_REF3')
    return ref
def path_for(value,external=False):
    need(type(value) is str and value and '\x00' not in value,'PATH_STRING')
    need('..' not in value.replace('\\','/').split('/'),'PATH_TRAVERSAL')
    p=Path(value)
    if not p.is_absolute():
        need('\\' not in value and not PurePosixPath(value).is_absolute(),'REPO_POSIX')
        p=ROOT/p
    need(re.fullmatch('[A-Za-z]:',p.drive) is not None,'LOCAL_DRIVE_ONLY')
    for part in (p,*p.parents):
        need(part.exists() and not part.is_symlink() and not part.is_junction()
             and not(getattr(part.lstat(),'st_file_attributes',0)&0x400),'REGULAR_PHYSICAL_PATH')
    p=p.resolve(strict=True)
    need(external or p.is_relative_to(ROOT),'REPO_READ_BOUNDARY')
    need(p.is_file(),'REGULAR_FILE')
    return p
def checked(ref,external=False):
    ref_shape(ref);p=path_for(ref['path'],external)
    with p.open('rb') as f:raw=f.read(ref['bytes']+1)
    need(len(raw)==ref['bytes'] and sha(raw)==ref['sha256'],'PIN_CHANGED')
    return raw
def pin(path,relative=False):
    p=path_for(str(path));raw=p.read_bytes()
    return dict(path=p.relative_to(ROOT).as_posix() if relative else str(p),sha256=sha(raw),bytes=len(raw))
def normalized(ref):
    checked(ref);return dict(ref,path=path_for(ref['path']).relative_to(ROOT).as_posix())
def provenance_ref(ref):
    value=normalized(ref);need(value['path'].startswith('execution/v2.4/receipts/W09/'),'ROLE_ORIGIN_PREFIX');return value
def ref2(ref):return {k:ref[k] for k in ('path','sha256')}
def same(a,b):
    ref_shape(a);ref_shape(b)
    def ident(r):
        p=Path(r['path']);return ntpath.normcase(ntpath.normpath(str(p if p.is_absolute() else ROOT/p)))
    return ident(a)==ident(b) and (a['sha256'],a['bytes'])==(b['sha256'],b['bytes'])
def document(ref):return decode(checked(ref))
def request_shape(q):
    exact(q,REQUEST_FIELDS,'REQUEST_FIELDS')
    need(q['schema']=='researchos.w09-role-input-builder-request.v1' and q['actor_id']=='codex:/root','ROOT_METADATA_REQUEST')
    need(type(q['preparation_id']) is str and re.fullmatch('[0-9a-f]{32}',q['preparation_id']),'FRESH_PREPARATION_ID')
    for name in ('proposal_ref','context_seed_ref',*ROOT_AUDITS.values()):ref_shape(q[name])
def allowed_bindings(raw_ref,origin):
    result={raw_ref['sha256']}
    for name in ('source_hdf_ref','source_mf_ref','source_review_ref','scope_ref','independent_review_ref'):
        value=origin.get(name)
        if type(value) is dict:result.add(value.get('sha256'))
    result.add(origin.get('report_sha256'))
    return {x for x in result if type(x) is str and re.fullmatch('[0-9a-f]{64}',x)}
def capture_shape(cap):
    need(type(cap) is dict and (set(cap)==CAPTURE_FIELDS or set(cap)==CAPTURE_FIELDS|{'role'}),'CAPTURE_FIELDS')
    need(cap['schema'] in ('researchos.w09-native-producer.actual-audit.v1','researchos.w09.actual-role-audit.v1'), 'CAPTURE_SCHEMA')
    need(cap['Root_thread_id']==THREAD and ntpath.normcase(ntpath.normpath(cap['source_audit_path']))==ntpath.normcase(ntpath.normpath(ROOT_LOG)),'FIXED_ROOT_LOG')
    offsets,digests=cap['source_line_offsets'],cap['original_line_sha256']
    need(type(offsets) is list and len(offsets)==3 and all(type(x) is int and x>=0 for x in offsets)
         and offsets==sorted(set(offsets)) and type(digests) is list and len(digests)==3
         and all(type(x) is str and re.fullmatch('[0-9a-f]{64}',x) for x in digests)
         and type(cap['source_prefix_size_observed']) is int,'CAPTURE_RANGES')
    ref_shape(cap['original_capture_ref'])
def validate_records(role,cap,raw,binding,origin,origin_ref):
    capture_shape(cap)
    actor=ROLE_ACTORS[role];lines=raw.splitlines(keepends=True)
    need(len(lines)==3 and all(x.endswith(b'\n') for x in lines),'THREE_ORIGINAL_LF_RECORDS')
    head,call,result=[decode(x) for x in lines]
    need(all(type(v) is dict for v in (head,call,result)),'RECORD_OBJECTS')
    need(head.get('type')=='session_meta' and head.get('ordinal')==0 and head.get('payload',{}).get('id')==THREAD,'ROOT_SESSION_HEADER')
    need(type(call.get('ordinal')) is int and call['ordinal']>0 and type(result.get('ordinal')) is int and result['ordinal']>call['ordinal'],'RECORD_ORDER')
    first,last=call.get('payload',{}),result.get('payload',{})
    need(type(first) is dict and type(last) is dict,'RECORD_PAYLOADS')
    if actor=='codex:/root':
        need(cap['actor_id']==actor and call.get('type')==result.get('type')=='response_item'
             and first.get('type') in ('function_call','custom_tool_call') and last.get('type') in ('function_call_output','custom_tool_call_output')
             and type(first.get('call_id')) is str and bool(first['call_id']) and first['call_id']==last.get('call_id')
             and type(first.get('name')) is str and bool(first['name']),'ACTUAL_ROOT_TOOL_PAIR')
    else:
        need(call.get('type')=='inter_agent_communication_metadata' and result.get('type')=='response_item'
             and result['ordinal']==call['ordinal']+1 and call.get('timestamp')==result.get('timestamp')
             and last.get('type')=='agent_message' and last.get('author')==actor and last.get('recipient')=='/root'
             and result.get('metadata',{}).get('client_authored') is False and type(last.get('content')) is list
             and len(last['content'])==1 and type(last['content'][0]) is dict and last['content'][0].get('type')=='input_text'
             and type(last['content'][0].get('text')) is str,'ACTUAL_BACKEND_DELIVERY')
    need(binding in allowed_bindings(origin_ref,origin) and binding in (lines[1]+lines[2]).decode('utf-8'),'ACTUAL_ALLOWED_BINDING')
    need([sha(x) for x in lines]==cap['original_line_sha256'],'ACTUAL_LINE_HASHES')
    need(all(off+len(line)<=cap['source_prefix_size_observed'] for off,line in zip(cap['source_line_offsets'],lines)),'ACTUAL_PREFIX_BOUNDARY')
    return lines
def audit_payload(role,cap,copy_ref,binding):
    return dict(schema='researchos.w09.actual-role-audit.v1',actor_id=ROLE_ACTORS[role],role=role,Root_thread_id=THREAD,
        source_audit_path=ROOT_LOG,source_line_offsets=copy.deepcopy(cap['source_line_offsets']),
        original_line_sha256=copy.deepcopy(cap['original_line_sha256']),source_prefix_size_observed=cap['source_prefix_size_observed'],
        original_capture_ref=copy_ref,binding_sha256=binding)
def unique_refs(refs):
    out={}
    for r in refs:
        ref_shape(r);p=Path(r['path']);key=ntpath.normcase(ntpath.normpath(str(p if p.is_absolute() else ROOT/p)))
        need(key not in out or same(out[key],r),'CONFLICTING_PROTECTION_REFS');out.setdefault(key,r)
    return list(out.values())
def write(path,value,raw=False):
    with path.open('xb') as f:f.write(value if raw else encoded(value));f.flush();os.fsync(f.fileno())
    return pin(path,True)
def safe_new_directory(path,boundary):
    need(path.is_relative_to(boundary) and path!=boundary and not path.exists(),'FRESH_OUTPUT_DIRECTORY')
    for p in (path.parent,*path.parent.parents):
        if p.exists():need(p.is_dir() and not p.is_symlink() and not p.is_junction() and not(getattr(p.lstat(),'st_file_attributes',0)&0x400),'OUTPUT_PARENT_ALIAS')
    path.parent.mkdir(parents=True,exist_ok=True);path.mkdir()
def run(request_ref):
    q=document(request_ref);request_shape(q)
    ir=pin(HERE/'source-inputs.json');need(ir['sha256']==INPUTS_SHA,'FIXED_SOURCE_INPUTS');i=document(ir)
    refs=[request_ref,ir,pin(__file__),*i['fixed_refs']]
    need(all(checked(r) for r in i['fixed_refs']),'FIXED_INPUTS')
    proposal=document(q['proposal_ref']);context=document(q['context_seed_ref'])
    need(proposal['schema']=='researchos.w09-bridge-proposal.v1' and proposal['generation']=='bridge-20261010-07'
         and same(proposal['source_ref'],i['bridge_source_ref']) and same(proposal['context_seed_ref'],q['context_seed_ref'])
         and proposal['c19_policy']=='RUN_CURRENT_CM40','BR7_PROPOSAL_CONTEXT')
    need(context['schema']=='researchos.w09.current-context.v1' and context['executor_id']=='codex:/root'
         and type(context['run_id']) is str and bool(context['run_id']),'ROOT_CONTEXT')
    for rows in (proposal['planned_routes'],context['registered_commands']):
        need(type(rows) is list and len(rows)==6 and {tuple(r[k] for k in ('command_key','check_id','case_id')) for r in rows}=={tuple(r) for r in i['routes']},'EXACT_SIX_ROUTES')
    mainpin=next(r for r in context['version_vector']['source_files'] if r['path']=='execution/v2.4/formal_profile_w09.py')
    need(mainpin['sha256']==i['Main_ref']['sha256'],'CONTEXT_CURRENT_MAIN_PIN')
    refs.extend([q['proposal_ref'],q['context_seed_ref']])
    docs=proposal['documents'];origins={};orefs={}
    for name in ('consumers','assembly'):
        sr,ow=docs[name]['scope_ref'],docs[name]['owner_ref'];scope,owner=document(sr),document(ow);refs.extend((sr,ow))
        need(scope['issued_by']=='codex:/root' and scope['source_actor']==ROLE_ACTORS['SOURCE_AUTHOR']
             and scope['generation']=='bridge-20261010-07' and same(scope['source_hdf_ref'],i['bridge_hdf_ref'])
             and same(scope['source_ref'],i['bridge_source_ref']) and owner['owner_id']=='codex:/root'
             and owner['selected_worker_id']=='codex:/root' and owner['lease_status']=='ACTIVE' and same(owner['scope_ref'],sr),'PROPOSAL_ORIGIN_CHAIN')
        need(scope['slice_id']==('W09_FULL_FORMAL_CONSUMERS' if name=='consumers' else 'W09_FULL_FORMAL_ASSEMBLY')
             and scope['schema']==('researchos.w09-full-formal-consumers-scope.v1' if name=='consumers' else 'researchos.w09-full-formal-assembly-scope.v1'),'SCOPE_SLICE')
        if name=='consumers':
            need(all(r[0] in owner['routes'] and r[0] in scope['routes'] for r in i['routes']),'SIX_ROUTE_OWNER')
            for role in ('SOURCE_AUTHOR','ROOT_OBSERVER'):origins[role]=scope;orefs[role]=provenance_ref(sr)
        else:origins['EVIDENCE_ASSEMBLER']=owner;orefs['EVIDENCE_ASSEMBLER']=provenance_ref(ow)
    mode=document(i['mode01_ref'])
    need(mode['schema']=='researchos.w09-mode-decision.v2' and mode['decision']=='QUALIFIED'
         and mode['reviewer_role']=='INDEPENDENT_NON_AUTHOR' and mode['producer_id']=='codex:/root'
         and mode['reviewer_id']==ROLE_ACTORS['VERIFIER'],'EXISTING_MODE01')
    seedmode=next(r['mode_decision_ref'] for r in context['registered_commands'] if r['check_id']=='W09-G01')
    need(seedmode==ref2(normalized(i['mode01_ref'])),'SEED_MODE01_BINDING')
    for role in ('EXECUTOR','VERIFIER'):origins[role]=mode;orefs[role]=provenance_ref(i['mode01_ref'])
    caps={};raws={};bindings={}
    for role in ROLE_ACTORS:
        cr=i['peer_audits'][role] if role in i['peer_audits'] else q[ROOT_AUDITS[role]]
        cap=document(cr);capture_shape(cap);raw=checked(cap['original_capture_ref'],external=True)
        refs.extend((cr,dict(cap['original_capture_ref'],path=str(path_for(cap['original_capture_ref']['path'],external=True)))))
        caps[role]=cap;raws[role]=raw
        bindings[role]=i['bridge_hdf_ref']['sha256'] if role=='SOURCE_AUTHOR' else orefs[role]['sha256']
    out=W/'w09_br7_role_inputs_root'/q['preparation_id'];origin_out=ORIGIN/('roles-'+q['preparation_id'])
    need(not out.exists() and not origin_out.exists(),'UNUSED_BOTH_OUTPUT_ROOTS')
    gr=i['guard_ref'];g=types.ModuleType('role_builder_guard');g.__file__=gr['path'];exec(compile(checked(gr),gr['path'],'exec'),g.__dict__)
    guard=g.SourceReadGuard(per_file_cap=32*1024*1024,total_cap=256*1024*1024);created=False;primary=None;result=None;closed=None;cleanup_errors=[]
    try:
        guard.acquire([dict(r,path=str(path_for(r['path'],external=True))) for r in unique_refs(refs)])
        for r in refs:checked(r,external=True)
        for role in ROLE_ACTORS:
            lines=validate_records(role,caps[role],raws[role],bindings[role],origins[role],orefs[role])
            with Path(ROOT_LOG).open('rb') as f:
                for offset,line in zip(caps[role]['source_line_offsets'],lines):f.seek(offset);need(f.readline()==line,'ROOT_SOURCE_RANGE_CHANGED')
        safe_new_directory(out,W);created=True;safe_new_directory(origin_out,ORIGIN)
        template=document(i['template_ref']);template['run_id']=context['run_id'];protection=[]
        for proof in template['provenance']:
            role=proof['role'];copied=write(origin_out/(role.lower()+'.raw.jsonl'),raws[role],True)
            need(copied['sha256']==caps[role]['original_capture_ref']['sha256'] and copied['bytes']==caps[role]['original_capture_ref']['bytes'],'COPY_EXACT')
            audit=write(out/(role.lower()+'.actual-role-audit.json'),audit_payload(role,caps[role],copied,bindings[role]))
            proof['raw_ref'].update(ref2(orefs[role]));proof['actual_audit_ref']=audit
            protection.extend((copied,audit,orefs[role]))
        for row in template['route_execution_refs']:
            row['scope_ref']=provenance_ref(docs['consumers']['scope_ref']);row['owner_ref']=provenance_ref(docs['consumers']['owner_ref'])
        protection.extend(normalized(docs[name][k]) for name in ('consumers','assembly') for k in ('scope_ref','owner_ref'))
        input_ref=write(out/'role-registry-input.json',template)
        protection_ref=write(out/'role-protection-refs.json',dict(role_protection_refs=unique_refs(protection)))
        policy_ref=write(out/'context-role-policy.template.json',dict(role_policy=dict(schema='researchos.w09.execution-role-policy.v1',
            registry_ref=dict(path=REGISTRY,sha256=None,bytes=None)),version_vector=dict(input_files=[dict(path=REGISTRY,sha256=None)])))
        result=write(out/'result.json',dict(schema='researchos.w09-role-input-builder-result.v1',request_ref=request_ref,
            role_registry_input_ref=input_ref,role_protection_refs_ref=protection_ref,context_policy_template_ref=policy_ref,
            raw_copy_directory=str(origin_out),registered_ref3=None,registry_ref2=None,Root_stage_calls=0,
            Canon_Scope_Main_fixed_registry_writes=0,formal_acceptance=False,execution_grant=False))
    except BaseException as exc:primary=exc
    finally:
        try:closed=guard.close()
        except BaseException as exc:cleanup_errors.append(repr(exc))
        if created:
            try:write(out/'source-guard.closed.json',dict(observation=closed,cleanup_errors=cleanup_errors))
            except BaseException as exc:cleanup_errors.append(repr(exc))
    if primary is not None or cleanup_errors:
        raise RuntimeError(json.dumps(dict(primary_error=repr(primary) if primary is not None else None,cleanup_errors=cleanup_errors),ensure_ascii=False)) from primary
    need(closed['closed'] and closed['retained_handles_count']==0 and not closed['errors'],'SOURCE_GUARD_CLOSED')
    return result
def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--request',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--bytes',required=True,type=int)
    a=ap.parse_args(argv);result=run(dict(path=a.request,sha256=a.sha256,bytes=a.bytes));print(json.dumps(dict(result_ref=result),ensure_ascii=False))
if __name__=='__main__':main()
