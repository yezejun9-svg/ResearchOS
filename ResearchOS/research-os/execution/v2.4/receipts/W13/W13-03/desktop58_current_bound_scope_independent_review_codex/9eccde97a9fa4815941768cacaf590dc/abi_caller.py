from pathlib import Path
import ast,hashlib,json,os
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;U=O.name
N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r339-'+U)
A=R/('execution/v2.4/receipts/W13/W13-03/desktop58_root_caller_allocationseventh_source_preparation_codex/'+U)
C=[];refs={}
def p(v):
    z=Path(v);return z if z.is_absolute() else R/z
def raw(v):
    z=p(v);v=z.read_bytes();refs[str(z)]={'path':str(z),'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)};return v
def doc(v):return json.loads(raw(v))
def ck(n,v):C.append({'check':n,'passed':bool(v)})
def pin(r):
    z=raw(r['path']);ck('pin '+str(r['path']),hashlib.sha256(z).hexdigest()==r['sha256'] and len(z)==r['bytes']);return z
def walk(v):
    if isinstance(v,dict):
        if set(v)=={'path','sha256','bytes'}:pin(v)
        else:
            for x in v.values():walk(x)
    elif isinstance(v,list):
        for x in v:walk(x)
def dump(n,v):
    with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
s=doc(N/'scope_registration.json');b=doc(N/'binding.pre-review.json');q=doc(N/'root-construction.parameters.desktop58.json');ri=doc(N/'root-inputs.desktop58.pre-review.json')
sr=dict(refs[str(N/'scope_registration.json')],path=(N/'scope_registration.json').relative_to(R).as_posix())
ck('scope ROOT-relative exact3keys',not Path(sr['path']).is_absolute() and set(sr)=={'path','sha256','bytes'} and sr['sha256']=='c8f9b66b22b2fd3092bd7161f3dd30cd927bc5bc192bb6e9ebece38582db9859')
keys=('scope_template_ref','runtime_resources_ref','compiler_resources_ref','current43_authority_ref','origin_cut_ref','canonical_before_ref','source_inputs_ref','metadata_code_refs_ref','failure_prefix430_ref','desktop_values_ref','toolchain_lock_ref')
for k in keys:
    pin(ri[k])
    if k not in ('metadata_code_refs_ref','desktop_values_ref'):ck('Root11 projection '+k,ri[k]==b[k])
ck('metadata8 projection',doc(ri['metadata_code_refs_ref']['path'])['entries']==b['metadata_code_refs'])
ck('Desktop values projection',doc(ri['desktop_values_ref']['path'])==b['desktop_scope_values'])
for k in ('owner','run_uuid','before','after','main_git','public_environment','registration_namespace','controller_review_path','controller_review_ref','formal_increment','new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root'):
    ck('Root literal binding '+k,p(ri[k])==p(b[k]) if k=='registration_namespace' else ri[k]==b[k])
runtime=doc(s['runtime_resources_ref']['path']);rt={x['path']:x for x in runtime['files']}
for r in b['metadata_code_refs']:
    a=dict(r,path=str(p(r['path']).resolve()));ck('runtime canonicalABS metadata '+p(r['path']).name,rt.get(a['path'])==a)
delta=doc(q['conhost_resource_delta_ref']['path']);images=doc(s['resource_catalog_ref']['path'])['images']
for r in delta['additions_to_catalog_and_runtime']:
    a=dict(r,path=str(p(r['path']).resolve()));ck('conhost6 canonical actual bytes '+p(r['path']).name,rt.get(a['path'])==a);pin(a)
    ck('conhost-only image '+p(r['path']).name,(a in images)==(p(r['path']).name.casefold()=='conhost.exe'))
ck('PROPSYS original-case predicate superseded by physical-path equality',any(p(r['path']).name.casefold()=='propsys.dll' and str(p(r['path']).resolve()) in rt for r in delta['additions_to_catalog_and_runtime']))
gate=pin(s['authorization_verifier_ref']).decode();pipe=pin(q['metadata_pipeline_ref']).decode()
for token in ("'researchos.desktop58-controller-static-review.v1'","'codex:/root/w05_merge_review'","'READY_FOR_ROOT_CURRENT58_DESKTOP169_GO3_ONCE'"):ck('actual consumer identity '+token,token in gate and token in pipe)
ck('scope exact producer-consumer dict',all(t in pipe for t in ("'scope_ref':scope_ref","wip_values(b,scope_ref)","desktop_lease(b,scope_ref)")) and "grant['scope_ref'] == scope_ref" in gate and "wip['desktop58_finite_validation_scope_ref'] == scope_ref" in gate)
ck('runtime3 canonicalABS',len(s['expected_runtime_observation_paths'])==3 and all(Path(x).is_absolute() and str(Path(x).resolve())==x for x in s['expected_runtime_observation_paths']))
ck('unknown dynamic refusal unchanged','Actual loaded module outside frozen runtime universe' in pin(s['debug_helper_ref']).decode())
h=doc(A/'handoff.json');ca=doc(A/'audit.json');mf=doc(A/'manifest.json');walk(h);walk(mf)
new=pin(h['proposed_source_ref']);old=pin(ca['base_source_ref'])
inverse=new.replace(U.encode(),b'b4d53db07f1e4ab8b9c0b37e291a6da5').replace(b'fd6fec9e9d2a482d98203421ac21a82b',b'd8a016ddc71e440fb386a11957c098ea').replace(b'desktop58-finite169-go3-r339-',b'desktop58-finite169-go3-r337-')
ck('caller exact five literals wholebyte inverse',inverse==old and new.count(U.encode())==3 and new.count(b'fd6fec9e9d2a482d98203421ac21a82b')==1)
ck('caller full AST inverse',ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False))
nt=ast.parse(new);ot=ast.parse(old)
nd={x.name:ast.dump(x,include_attributes=False) for x in nt.body if isinstance(x,ast.FunctionDef)};od={x.name:ast.dump(x,include_attributes=False) for x in ot.body if isinstance(x,ast.FunctionDef)}
ck('all three helpers AST unchanged',nd==od and set(nd)=={'need','pin','save'})
ck('scope-read to EOF originalbytes',new[new.index(b'scope_path ='):]==old[old.index(b'scope_path ='):])
cs=new.decode();ck('actual three arguments scope/grantSHA/freshOUT',"len(sys.argv) == 4" in cs and "SCOPE_SHA, GRANT_SHA = sys.argv[1:3]" in cs and "OUT = Path(sys.argv[3])" in cs)
ck('future SHA unassigned',"SCOPE_SHA = None" in cs and "GRANT_SHA = None" in cs)
ck('exact registration/auth UUID',s['registration_namespace'] in cs and s['run_uuid']==U and ('desktop58_finite_authorization_codex/'+U) in cs)
ck('scope actual sourcepin binding',h['scope_ref']==sr and ca['actual_scope_ref']==sr)
ck('outer caller no OS qualification',"'caller_OS_lifecycle_qualification': False" in cs and "timeout=7800, check=False" in cs and cs.count('subprocess.run(')==1)
ck('caller no retry nullable failure retained',"result.returncode if result else None" in cs and "secondary.append" in cs and "'automatic_retry': False" in cs and "'first_cause': error" in cs)
ck('actual inner/outer budget consistency',ca['budgets']=={'caller_timeout_seconds':7800,'launcher_outer_seconds':7500,'controller_inner_seconds':7200,'builder_seconds':1800,'controller_evidence_reserve_seconds':60,'launcher_evidence_reserve_seconds':60,'cleanup_seconds':5} and s['inner_seconds']==7200 and s['outer_seconds']==7500)
ck('six execution/caller roots absent',all(not os.path.lexists(p(s[k])) for k in ('output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root')) and not (R/'execution/v2.4/receipts/W13/W13-03/desktop58_root_terminal_closure_codex/fd6fec9e9d2a482d98203421ac21a82b').exists())
before=doc(b['canonical_before_ref']['path'])['entries']
for r in before:ck('current four exact again '+r['canonical_path'],raw(r['canonical_path'])==pin(r['ref']))
dump('abi-caller.json',{'schema':'researchos.desktop58-bound-scope-caller-abi-audit.v1','checks':C,'failed':[x for x in C if not x['passed']],'input_refs':list(refs.values()),'scope_ref':sr,'caller_ref':h['proposed_source_ref'],'caller_budget_declaration':ca['budgets'],'caller_OS_lifecycle_qualification':False,'source_acceptance':False,'actual_execution':False,'new_failure_origins':[]})
print(json.dumps({'checks':len(C),'failed':[x for x in C if not x['passed']]}))
