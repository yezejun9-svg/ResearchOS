import ast,hashlib,json,stat
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli58-fresh-held2-r334-56b244cd06264dc7b95d381fc3297d61'
checks=[];refs={}
def check(k,v):checks.append({'check':k,'passed':bool(v)})
def path(p):
    p=Path(p);return p if p.is_absolute() else R/p
def ref(p):
    p=path(p);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def pin(r):
    p=path(r['path']);a=ref(p);check('pin '+str(p),a['sha256']==r['sha256'] and a['bytes']==r['bytes']);refs[str(p)]=a;return p.read_bytes()
def doc(p):
    p=path(p);refs[str(p)]=ref(p);return json.loads(p.read_bytes())
def rd(r):return json.loads(pin(r))
def allrefs(v):
    if isinstance(v,dict):
        if {'path','sha256','bytes'}<=v.keys():yield v
        else:
            for x in v.values():yield from allrefs(x)
    elif isinstance(v,list):
        for x in v:yield from allrefs(x)
def save(name,v):
    with (O/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
mf=doc(N/'bound-scope.pre-review.manifest.json')
check('MF expected SHA',ref(N/'bound-scope.pre-review.manifest.json')['sha256']=='23ffbc9ba3ac305496fc2985ca609a1d1d95bd7a6f90aed1363b618e766b0498')
check('MF23',mf['count']==len(mf['entries'])==23 and mf['self_excluded'] is True)
for r in mf['entries']:pin(r)
s=doc(N/'scope_registration.json');b=doc(N/'binding.pre-review.json');params=doc(N/'root-construction.parameters.json')
check('scope expected SHA',ref(N/'scope_registration.json')['sha256']=='94775df2744809a2378a3a2182e9c6e3b341b20c53b26d54f4da508fa1491080')
for v in [s,b,params]:
    for r in allrefs(v):pin(r)
check('before/after tuples',s['expected_before_registration']==b['before']==[333,161,524] and s['expected_registration']==b['after']==[334,162,532])
check('fixed review path',path(s['controller_review_path'])==O/'review.json' and b['controller_review_ref'] is None)
check('same scope/binding fields',all(s[k]==b[k] for k in ['run_uuid','registration_namespace','new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root','controller_review_path','main_git','public_environment','runtime_resources_ref','compiler_resources_ref','current43_authority_ref','runner_ref','launcher_ref','authorization_gate_ref']))
check('no acceptance grant',s['source_acceptance'] is False and s['Main_integration_authorized'] is False and s['formal_increment']==0 and s['actual_cases'] is None)
check('two exact cases/caps',s['ordered_cases']==['real-existing-open-readonly','real-existing-self-send'] and s['limits']=={'cases':2,'upstream_dispatch_per_case':32,'proxy_admission_per_case':32,'qualifying_observed_HTTP_legs':128,'unobserved_client_outbound_hard_cap':None,'SDK_MODEL_Node_external_paid_private_calls':0})
check('budget/flags',s['launch_limits']=={'outer_timeout_seconds':3600,'inner_soft_deadline_seconds':3300,'termination_cleanup_seconds':5} and s['python_flags']==['-I','-S','-X','utf8'])
for k in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']:
    p=path(s[k]);check('fresh '+k,not p.exists());check('UUID '+k,p.name.endswith(s['run_uuid']))
for name in ['binding.json','prepare.started.json','prepared_refs.json']:check('not prepared '+name,not (N/name).exists())
cb=rd(b['canonical_before_ref']);before=[]
for row in cb['entries']:
    raw=pin(row['ref']);check('live canonical '+row['canonical_path'],path(row['canonical_path']).read_bytes()==raw);before.append(json.loads(raw))
cp,ow=before[:2];check('actual canonical tuple/head',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==b['before'] and cp['head']==s['source_commit'])
prefix=rd(b['failure_prefix430_ref']);check('430 historical prefix',cp['failure_counters'][:430]==prefix['failure_counters'])
cut=rd(b['origin_cut_ref']);check('cut exact8/tuple',len(cut['origins'])==8 and cut['before']==b['before'] and cut['after']==b['after'])
seen=set();oldkeys={x.get('evidence_ref',{}).get('sha256') for x in cp['failure_counters']}
for x in cut['origins']:
    r=x['evidence_ref'];raw=rd(r);check('opaque origin raw preserved '+r['sha256'],x['original_payload']==raw and x['counter_reset'] is False);check('new unique origin '+r['sha256'],r['sha256'] not in seen|oldkeys);seen.add(r['sha256'])
runtime=rd(s['runtime_resources_ref']);compiler=rd(s['compiler_resources_ref']);base=rd(params['runtime_base_ref'])
rt={x['path']:x for x in runtime['files']};check('runtime1220 unique',len(rt)==len(runtime['files'])==1220)
check('compiler22138 resources descriptor',len(compiler['files'])==22138 and len(compiler['compiler_images'])==9 and compiler['actual_compile_graph'] is None)
check('runtime base1212 unchanged',len(base['files'])==1212 and all(rt.get(x['path'])==x for x in base['files']))
module=path(b['metadata_code_refs'][-1]['path']);module_raw=module.read_bytes();ast.parse(module_raw)
check('module source SHA',hashlib.sha256(module_raw).hexdigest()=='4a5913346f0fa83f65824861077a05087de9244530be2754f138063821f7aeb4')
for i,r in enumerate(b['metadata_code_refs']):
    raw=pin(r);check('metadata ref ROOT relative '+str(i),r['path']==path(r['path']).relative_to(R).as_posix());project={**r,'path':str(path(r['path']))};check('metadata exactABS runtime '+str(i),rt.get(project['path'])==project);ast.parse(raw)
    if i<6:check('wrapper single pinned module '+str(i),b['metadata_code_refs'][-1]['sha256'].encode() in raw and repr(str(module)).encode() in raw)
mt=module_raw.decode();check('runtime verified canonicalABS and successful marker',"for r in b['metadata_code_refs']: verify(r)" in mt and "str(safe(r['path']))" in mt and "observation['all_observed_inputs_pre_pinned']=True" in mt)
source=rd(b['source_inputs_ref']);cat=rd(s['catalog_ref']);auth=rd(s['current43_authority_ref'])
check('catalog639/559Go',cat['file_count']==len(cat['files'])==639 and cat['all_platform_Go_count']==559 and cat['commit']==s['source_commit'])
check('source inputs639',source['count']==len(source['files'])==639 and source['source_commit']==s['source_commit'] and source['catalog_ref']==s['catalog_ref'])
actualsources={x['path']:x for x in source['files']};catalog={x['path']:x for x in cat['files']}
for r in cat['files']:
    raw=pin(r);p=path(r['path']);check('source actualGitBlob '+r['path'],hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==r['git_blob']);check('source no reparse '+r['path'],not (getattr(p.lstat(),'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT));check('source catalogue vector '+r['path'],actualsources.get(str(p))=={'path':str(p),'sha256':r['sha256'],'bytes':r['bytes']})
for r in allrefs(auth):pin(r)
combined=rd(auth['combined_source_set_ref']);closure=rd(auth['source_commit_closure_ref']);forward=rd(auth['forward_head_audit_ref'])
check('current58 source boundary',auth['unique_combined_source_paths']==58 and auth['source_commit']==s['source_commit'] and auth['source_parent']==s['actual_candidate_parent_expected'] and auth['source_acceptance'] is False and auth['fresh_compilation_or_cases_accepted'] is False)
source_scope=rd(closure['scope_ref']);expected=set(source_scope['shared38_paths']+source_scope['cli8_paths']+closure['source_paths']);check('exact58 union',len(expected)==58 and {x['path'] for x in combined['files']}==expected)
for r in combined['files']:pin(r);check('combined catalogue '+r['path'],r['sha256']==catalog[r['path']]['sha256'] and r['bytes']==catalog[r['path']]['bytes'])
check('closed forward only',forward['after']==[333,161,524] and forward['registered_head']==s['source_commit'] and forward['formal_increment']==0 and forward['source_acceptance'] is False)
check('canonical source closure state',cp['work_in_progress']['desktop_exact15_source_integration_state']=='CLOSED_PENDING_FRESH58_VALIDATION' and ow['card_path_bindings']['W13-03']['subtasks']['desktop_exact15_source_integration']['current_source_writer'] is None)
plan=rd(s['instrumentation_ref']);raw=pin(s['instrumented_source_ref']);back=raw
for edit in reversed(plan['changes']):
    a=edit['new'].encode();z=edit['old'].encode();check('instrumented edit inverse present',a in back);back=back.replace(a,z)
check('instrumentation whole original inverse',back==path(plan['original_path']).read_bytes() and hashlib.sha256(back).hexdigest()==plan['original_sha256'])
check('additional helper pin',plan['additional_file_ref']==s['instrumentation_helper_ref'])
gd=R/'.git';headraw=(gd/'HEAD').read_text().strip();actualhead=(gd/headraw[5:]).read_text().strip() if headraw.startswith('ref: ') else headraw
check('direct Main HEAD without Git',actualhead==s['source_commit']);index=(gd/'index').read_bytes();check('direct index empty',index[:4]==b'DIRC' and int.from_bytes(index[8:12],'big')==0)
obs=doc(O/'observed-resource-comparison.json');eligible={str(path(r['path'])).lower() for r in runtime['files']+compiler['files']}
missing=sorted({x['omitted_ref']['path'] for x in obs['missing_observed_records'] if x['omitted_ref']['path'].lower() not in eligible})
check('known historical loaded modules preapproved for replay',not missing)
for p in missing:
    row=next(x['omitted_ref'] for x in obs['missing_observed_records'] if x['omitted_ref']['path']==p);pin(row)
pubreview=R/'execution/v2.4/receipts/W13/W13-03/fresh58_public_source_publication_independent_review_codex/66b4835ecfe240cca4e481900d9897a7/review.json'
pr=doc(pubreview);check('publication independent review pinned',ref(pubreview)['sha256']=='19978700a163383fd07868b7eff60f748dfc21f655478eb8017affddefe7cf22')
result={'checks':checks,'failed':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'missing_historically_observed_runtime_paths':missing,'actual_candidate_calls':0,'compiler_resource_leaf_files_rehashed':False,'runtime_leaf_files_rehashed':'Only eight metadata overlay files and three missing historically observed DLLs; descriptor pins verified','current_source_files_rehashed':639,'publication_review_ref':ref(pubreview),'canonical_before':cb,'direct_head':actualhead}
save('audit.json',result)
print(json.dumps({'checks':len(checks),'failed':result['failed'],'missing':missing,'audit_ref':ref(O/'audit.json')},ensure_ascii=False))
