from pathlib import Path
import json,hashlib,ast,os,traceback
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W13/W13-03';O=Path(__file__).parent;U='1c4ea6999d4d4437a0202c4e81ce581b';N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-'+U);C=[];REF={}
def ck(k,v):C.append({'check':k,'passed':bool(v)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def ref(p):
 p=path(p);b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};REF[str(p)]=r;return r
def doc(p):ref(p);return json.loads(path(p).read_bytes())
def pin(r):
 p=path(r['path']);x=ref(p);ck('pin '+str(p),x['sha256']==r['sha256'] and x['bytes']==r['bytes']);return p
def scan(x):
 if isinstance(x,dict):
  if set(x)=={'path','sha256','bytes'}:pin(x)
  else:
   for v in x.values():scan(v)
 elif isinstance(x,list):
  for v in x:scan(v)
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
try:
 q=doc(N/'root-construction.parameters.desktop58.json');ck('request exact SHA',ref(N/'root-construction.parameters.desktop58.json')['sha256']=='8a8caf8f17deb264f5eefb09fd61746ca0c3ccaadd7f84175b252e46c245de3f');scan(q)
 ck('request schema actor noexecute',q['schema']=='researchos.desktop58-root-input-construction-request.v1' and q['actor']=='codex:/root' and q['source_acceptance'] is False and q['compile_or_case_execution_authorized'] is False and q['formal_increment']==0)
 ck('fixed tuple and21',q['before']==[334,162,532] and q['after']==[335,163,553] and len(q['pending_origin_refs'])==21)
 canon=['checkpoint','path_ownership','step_state','commands'];docs=[]
 for name,r in zip(canon,q['canonical_copies']):
  p=R/('execution/v2.4/'+name+'.json');ck('live original canonical '+name,p.read_bytes()==path(r['path']).read_bytes());docs.append(doc(p))
 cp,ow=docs[:2];ck('live actual tuple/head',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==q['before'] and cp['head']==q['source_commit'])
 pref=doc(q['failure_prefix430_ref']['path']);ck('original430 prefix',len(pref['failure_counters'])==430 and cp['failure_counters'][:430]==pref['failure_counters'])
 prior={v.get('evidence_ref',{}).get('sha256') for v in cp['failure_counters']};orig=[]
 for r in q['pending_origin_refs']:
  ck('unique unregistered opaque origin '+r['sha256'],r['sha256'] not in prior);prior.add(r['sha256']);raw=doc(r['path']);orig.append({'evidence_ref':r,'original_payload':raw})
 h=(R/'.git/HEAD').read_text().strip();head=(R/'.git'/h[5:]).read_text().strip() if h.startswith('ref: ') else h;ck('direct current E2 HEAD',head==q['source_commit']=='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7')
 ck('frozen Main expectation',q['main_git']=={'head':head,'status_sha256':'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4','status_bytes':894,'status_rows':13,'deleted_rows':11,'index_empty':True})
 lease=ow['card_path_bindings']['W13-03']['subtasks']['desktop_exact15_source_integration'];ck('source15 closed lease',lease['current_source_writer'] is None and lease['state']=='CLOSED_PENDING_FRESH58_VALIDATION')
 alloc=q['allocation'];ck('unique UUID/regnamespace',alloc['run_uuid']==U and path(alloc['registration_namespace'])==N)
 leaves=[]
 for k in ['new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root']:
  p=path(alloc[k]);ck('fresh leaf '+k,p.is_absolute() and p.is_relative_to(R) and not os.path.lexists(p) and U in str(p));leaves.append(p)
 ck('five disjoint fresh roots',len(set(leaves))==5 and all(not a.is_relative_to(b) for a in leaves for b in leaves if a!=b))
 ck('future review only path',path(q['controller_review_path']).parent.name==U and not path(q['controller_review_path']).exists())
 template=doc(q['scope_template_ref']['path']);scan(template)
 ck('template source-only',template['source_commit']==head and template['preparation_only'] is True and template['execution_authorized'] is False and 'source_catalog_ref' in template and 'catalog_ref' not in template)
 caps={'node_cases':169,'Go_top_cases':3,'native_top_command_cap':176,'loopback_HTTP_max':390,'offscreen_Electron_controls':2,'installed_visible_GUI_calls':0,'SDK_model_external_paid_calls':0,'process_cap':2048,'active_job_processes':16,'image_cap':64,'cleanup_seconds':5,'formal_increment':0}
 for k,v in caps.items():ck('fixed cap '+k,template[k]==v)
 ck('budgets explicit', [q[k] for k in ['inner_seconds','outer_seconds','builder_seconds','controller_evidence_reserve_seconds','launcher_evidence_reserve_seconds']]==[7200,7500,1800,60,60])
 ck('outer includes inner reserve cleanup',q['outer_seconds']>=q['inner_seconds']+q['launcher_evidence_reserve_seconds']+5 and q['builder_seconds']<q['inner_seconds']-q['controller_evidence_reserve_seconds']-30)
 ck('public environment fivekeys',set(q['public_environment'])=={'SystemRoot','WINDIR','ComSpec','PATH','PATHEXT'})
 mr=doc(N/'metadata-code-refs.json')['entries'];ck('metadata8',[len(mr),len(q['metadata_code_refs'])]==[8,8])
 for a,b in zip(mr,q['metadata_code_refs']):ck('REL serialized ABS runtime same '+Path(a['path']).name,path(a['path'])==path(b['path']) and not Path(a['path']).is_absolute() and Path(b['path']).is_absolute() and a['sha256']==b['sha256'] and a['bytes']==b['bytes'])
 for row in q['metadata_code_refs']:
  p=path(row['path']);ast.parse(p.read_bytes());ck('metadata byte AST '+p.name,True)
 ck('metadata exact modules membership',q['builder_source_ref'] in q['metadata_code_refs'] and q['metadata_pipeline_ref'] in q['metadata_code_refs'])
 cr=doc(P/'desktop58_root_metadata_scope_binding_revision_independent_source_review_codex/bb7399bc49d64d33a70408d4dd4ffb7d/review.json');ck('metadata nonauthor review exists',cr['requested_changes']==[])
 qual=doc(q['current58_CLI2_qualification_ref']['path']);qr=doc(q['current58_CLI2_review_ref']['path']);qm=doc(q['current58_CLI2_manifest_ref']['path'])
 ck('actual current58 qualified2',qual['source_commit']==head and qual['current58_fresh_held2_qualified'] is True and qual['qualified_case_count']==2 and qual['native_calls_exit0']==14 and qual['CLI_exit_codes']==[0,3] and qual['source_acceptance'] is False and qual['formal_increment']==0)
 ck('nonauthor CLI review',qr['reviewer']=='codex:/root/w05_merge_review' and qr['decision']=='CURRENT43_FRESH_HELD2_BOUNDED_QUALIFICATION_EVIDENCE_CLOSED' and qr['qualification_ref']['sha256']==q['current58_CLI2_qualification_ref']['sha256'])
 for k in ['current58_CLI2_qualification_ref','current58_CLI2_review_ref']:ck('qualification package member '+k,any(path(x['path'])==path(q[k]['path']) and x['sha256']==q[k]['sha256'] and x['bytes']==q[k]['bytes'] for x in qm['entries']))
 cat=doc(q['source_catalog_ref']['path']);auth=doc(q['current58_authority_ref']['path']);ck('source639/559/58',cat['commit']==head and cat['file_count']==len(cat['files'])==639 and cat['all_platform_Go_count']==559 and auth['source_commit']==head and auth['unique_combined_source_paths']==58)
 rt=doc(q['runtime_base_ref']['path']);comp=doc(q['compiler_base_ref']['path']);corr=doc(q['mandatory_correction_ref']['path']);ck('resource base correct sizes',len(rt['files'])==1242 and len(comp['files'])==22138 and corr['missing_Windows_count']==len(corr['missing_Windows_refs'])==40)
 ck('static16 unique',len(q['static_image_refs'])==16 and len({Path(x['path']) for x in q['static_image_refs']})==16)
 alias=doc(template['alias_roster_ref']['path']);aliasrows=alias['aliases'] if isinstance(alias,dict) and 'aliases' in alias else alias
 ck('alias declarations20',len(q['negative_alias_declarations'])==20)
 for n,x in enumerate(q['negative_alias_declarations']):
  want=path(alloc['new_export_root'])/'.local/desktop-wire-negative'/(U+'-'+str(n).zfill(2))/'resources/client-wire/researchos-client-wire-validator.exe';ck('exact nonce alias '+str(n),x['allocation_ordinal']==n and path(x['path'])==want and x['max_creates'] in [0,1])
 constructor=N/'construct_root_inputs.desktop58.v2.py';tree=ast.parse(constructor.read_bytes());ref(constructor);constants={}
 for x in tree.body:
  if isinstance(x,ast.Assign):
   for target in x.targets:
    if isinstance(target,ast.Name) and target.id in ['VALUE_KEYS','CODE_KEYS','PHASES']:constants[target.id]=ast.literal_eval(x.value)
 ck('VALUE_KEYS all literal except generated',all(k in q and q[k] is not None for k in constants['VALUE_KEYS'] if k not in ['source_catalog_ref','resource_catalog_ref','expected_runtime_observation_paths','runtime_observation_phases']))
 ck('CODE_KEYS actual all refs',all(isinstance(template[k],dict) and set(template[k])=={'path','sha256','bytes'} for k in constants['CODE_KEYS']))
 raw=constructor.read_text(encoding='utf-8');ck('relative metadata emitted ABI',"Path(row['path']).relative_to(ROOT).as_posix()" in raw and "'controller_review_ref': None" in raw)
 save('audit.json',{'checks':C,'failed_checks':[x for x in C if not x['passed']],'input_refs':list(REF.values()),'original_pending_payloads':orig,'constructor_constants':constants,'alias_roster_shape':{'type':type(alias).__name__,'keys':list(alias) if isinstance(alias,dict) else None},'selected_lease':lease,'full_resource_backing_files_hashed':False,'target_calls':0,'new_failure_origins':[]})
 print(json.dumps({'checks':len(C),'failed':[x for x in C if not x['passed']],'audit_ref':ref(O/'audit.json'),'alias_shape':{'type':type(alias).__name__,'keys':list(alias) if isinstance(alias,dict) else None}},ensure_ascii=False))
except BaseException as ex:
 save('audit.failure.json',{'error':repr(ex),'traceback':traceback.format_exc(),'checks':C,'input_refs':list(REF.values()),'target_calls':0});raise
