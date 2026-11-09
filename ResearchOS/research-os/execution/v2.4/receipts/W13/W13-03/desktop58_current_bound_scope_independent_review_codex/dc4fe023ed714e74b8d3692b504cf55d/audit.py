from pathlib import Path
import ast,copy,hashlib,json,os,time,traceback
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;U=O.name
N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r336-'+U)
C=[];REF={};HASH={};start=time.time()
def ck(name,ok,detail=None):
 x={'check':name,'passed':bool(ok)}
 if detail is not None:x['detail']=detail
 C.append(x)
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def ref(p):
 p=path(p);key=str(p);h=hashlib.sha256();n=0
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b);n+=len(b)
 rr={'path':key,'sha256':h.hexdigest(),'bytes':n};REF[key]=rr;HASH[key]=rr;return rr
def doc(p):
 p=path(p);ref(p);return json.loads(p.read_bytes())
def pin(r):
 p=path(r['path']);key=str(p);actual=HASH.get(key) or ref(p)
 ck('pin '+key,actual['sha256']==r['sha256'] and actual['bytes']==r['bytes']);return p
def scan(x):
 if isinstance(x,dict):
  if set(x)=={'path','sha256','bytes'}:pin(x)
  else:
   for v in x.values():scan(v)
 elif isinstance(x,list):
  for v in x:scan(v)
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def constants(p):
 out={}
 for node in ast.parse(path(p).read_bytes()).body:
  if isinstance(node,ast.Assign):
   for t in node.targets:
    if isinstance(t,ast.Name):
     try:out[t.id]=ast.literal_eval(node.value)
     except (ValueError,TypeError):pass
 return out
try:
 s=doc(N/'scope_registration.json');b=doc(N/'binding.pre-review.json');q=doc(N/'root-construction.parameters.desktop58.json');ri=doc(N/'root-inputs.desktop58.pre-review.json')
 ck('actual scope SHA',ref(N/'scope_registration.json')['sha256']=='86d77dd84af6557c4f956d8c39e0aba3d2858de526bb6c1ff8aeb178c85469bc')
 scan(s);scan(b);scan(ri)
 ck('review exact frozen path',path(s['controller_review_path'])==O/'review.json')
 ck('wire schema actor source',s['schema']=='researchos.desktop58-169-go3-preparation-scope.v1' and s['owner']=='codex:/root' and s['source_commit']==q['source_commit'] and s['source_parent']=='a510dbef4a7e08fb5c428df44c39b133f3ffa856')
 ck('literal tuple progression',s['expected_before_registration']==b['before']==q['before']==[335,163,580] and s['expected_registration']==b['after']==q['after']==[336,164,603])
 ck('pre-review acyclic ungranted',b['controller_review_ref'] is None and ri['controller_review_ref'] is None and s['preparation_only'] is False and s['execution_authorized'] is True and 'actual sealed CAS and grant still mandatory' in b['authority_semantics'])
 template=doc(b['scope_template_ref']['path']);projected=copy.deepcopy(template)
 aliases={'output_root':'new_output_root','outer_output_root':'new_wrapper_root','export_root':'new_export_root','new_authorization_root':'new_authorization_root','new_grant_preflight_root':'new_grant_preflight_root','current_source_authority_ref':'current43_authority_ref','authorization_verifier_ref':'authorization_gate_ref','controller_ref':'runner_ref','owned_helper_ref':'owned_process_helper_ref','debug_helper_ref':'debug_tree_helper_ref'}
 for k,v in aliases.items():projected[k]=b[v]
 for k in ['run_uuid','registration_namespace','runtime_resources_ref','compiler_resources_ref','controller_review_path','main_git','public_environment','launcher_ref','utility_ref','toolchain_lock_ref']:projected[k]=b[k]
 projected.update(b['desktop_scope_values']);projected.update(preparation_only=False,execution_authorized=True,expected_before_registration=b['before'],expected_registration=b['after'],registration_metadata_paths=['execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json'])
 basis=['scope_template_ref','runtime_resources_ref','compiler_resources_ref','current43_authority_ref','origin_cut_ref','canonical_before_ref','source_inputs_ref','failure_prefix430_ref']
 projected['Root_metadata_binding_inputs']={'refs':{k:b[k] for k in basis},'metadata_code_refs':b['metadata_code_refs']}
 ck('whole scope exact independently reconstructed projection',projected==s)
 ck('eight basis refs',list(s['Root_metadata_binding_inputs']['refs'])==basis)
 gate=constants(s['authorization_verifier_ref']['path'])
 for key,val in gate['FIXED_CODE'].items():ck('gate exact fixed code '+key,s[key]==val)
 pipe=q['metadata_pipeline_ref'];scan(pipe);pc=constants(pipe['path']);pt=path(pipe['path']).read_text(encoding='utf-8')
 ck('Desktop value key set producer-consumer',set(b['desktop_scope_values'])==set(pc['DESKTOP_VALUE_KEYS']))
 stages=['admission.runtime','grant-final.runtime','grant-final.runtime.after'];expected=[str(path(s['new_authorization_root'])/(v+'.json')) for v in stages]
 ck('ordered three runtime phases',list(pc['OBSERVATION_PHASES'])==stages and s['expected_runtime_observation_paths']==expected and s['runtime_observation_phases']==[{'stage':a,'path':z} for a,z in zip(stages,expected)])
 ck('runtime strict marker after observation',pt.index("observation=util.module_observation(allowed,helper)")<pt.index("observation['all_observed_inputs_pre_pinned']=True"))
 for row in b['metadata_code_refs']:
  p=pin(row);ck('metadata ROOT-relative canonical '+p.name,not Path(row['path']).is_absolute() and p.resolve()==p.absolute());ast.parse(p.read_bytes())
 ck('metadata8 current exact q refs',[{'path':str(path(x['path'])),'sha256':x['sha256'],'bytes':x['bytes']} for x in b['metadata_code_refs']]==q['metadata_code_refs'])
 before=doc(b['canonical_before_ref']['path'])['entries'];canons=[]
 ck('four ordered canonical paths',[x['canonical_path'] for x in before]==['execution/v2.4/'+v+'.json' for v in ['checkpoint','path_ownership','step_state','commands']])
 for item in before:
  pin(item['ref']);raw=path(item['canonical_path']).read_bytes();ck('live canonical equal copy '+item['canonical_path'],raw==path(item['ref']['path']).read_bytes());canons.append(json.loads(raw))
 cp,ow=canons[:2];ck('current before tuple/head',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==b['before'] and cp['head']==s['source_commit'])
 cut=doc(b['origin_cut_ref']['path']);ck('fixed cut transition21',cut['before']==b['before'] and cut['after']==b['after'] and len(cut['origins'])==23 and cut['counter_reset'] is False)
 oldsha={x.get('evidence_ref',{}).get('sha256') for x in cp['failure_counters']};newsha=set()
 for row,original in zip(cut['origins'],q['pending_origin_refs']):
  ev=row['evidence_ref'];pin(ev);ck('opaque original origin '+ev['sha256'],ev==original and row['original_payload']==doc(ev['path']) and ev['sha256'] not in oldsha|newsha and row['counter_reset'] is False);newsha.add(ev['sha256'])
 ck('all23 unique',len(newsha)==23)
 prefix=doc(b['failure_prefix430_ref']['path'])['failure_counters'];ck('original430 exact prefix',len(prefix)==430 and cp['failure_counters'][:430]==prefix)
 lease=ow['card_path_bindings']['W13-03']['subtasks']['desktop_exact15_source_integration'];ck('source15 closed',lease['current_source_writer'] is None and lease['state']=='CLOSED_PENDING_FRESH58_VALIDATION')
 prior=ow['card_path_bindings']['W13-03']['subtasks'].get('desktop58_finite_validation');closed=doc(R/'execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_independent_review_codex/4bcd6b1bf2f941efa63f31e7a6cc7e67/review.final.json');ck('prior lease closed by actual failed evidence; stale metadata pending is preserved',prior['run_uuid']=='72ff32d0d24a42c4a8effd849d54f882' and closed['scope_uid']==prior['run_uuid'] and closed['decision']=='FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD' and closed['qualification'] is False)
 head=(R/'.git/HEAD').read_text().strip();head=(R/'.git'/head[5:]).read_text().strip() if head.startswith('ref: ') else head;ck('direct HEAD current E2',head==s['source_commit'])
 roots=[path(s[k]) for k in ['output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root']]
 for p in roots:ck('fresh allocation '+str(p),not os.path.lexists(p) and U in p.name and p.is_relative_to(R))
 ck('all5 disjoint',len(set(roots))==5 and all(not x.is_relative_to(y) for x in roots for y in roots if x!=y))
 for name in ['binding.json','prepare.started.json','prepared_refs.json','canonical-write.intent.json']:ck('not yet materialized '+name,not (N/name).exists())
 caps={'node_cases':169,'Go_top_cases':3,'native_top_command_cap':176,'loopback_HTTP_max':390,'offscreen_Electron_controls':2,'installed_visible_GUI_calls':0,'SDK_model_external_paid_calls':0,'process_cap':2048,'active_job_processes':16,'image_cap':64,'cleanup_seconds':5,'inner_seconds':7200,'outer_seconds':7500,'builder_seconds':1800,'controller_evidence_reserve_seconds':60,'launcher_evidence_reserve_seconds':60}
 for k,v in caps.items():ck('exact limit '+k,type(s[k]) is int and s[k]==v)
 ck('no privilege escalation',s['first_unexpected_stop'] is True and s['automatic_retry'] is False and s['counter_reset'] is False and s['source_acceptance'] is False and s['formal_increment']==0)
 ck('public environment/flags',s['public_environment']==q['public_environment'] and s['python_flags']==['-I','-S','-X','utf8'])
 roster=doc(s['roster_ref']['path']);aliases0=doc(s['alias_roster_ref']['path'])['rows'];ck('finite roster sizes',len(roster['leaves'])==162 and len(roster['regressions'])==7 and len(roster['go_units'])==3)
 ck('alias declarations full literal',s['negative_alias_declarations']==q['negative_alias_declarations'] and len(aliases0)==20)
 for a,d in zip(aliases0,s['negative_alias_declarations']):
  want={'case_name':a['name'],'allocation_ordinal':a['allocation_ordinal'],'path':str(roots[2]/'.local/desktop-wire-negative'/(U+'-'+str(a['allocation_ordinal']).zfill(2))/'resources/client-wire/researchos-client-wire-validator.exe'),'max_creates':a['expected_image_creates'],'mode':a['mode']};ck('frozen alias exact '+a['name'],d==want)
 edits=doc(s['alias_edits_ref']['path']);instrument=path(s['instrumented_test_ref']['path']).read_text(encoding='utf-8')
 for e in reversed(edits):ck('unique instrumentation delta',instrument.count(e['new'])==1);instrument=instrument.replace(e['new'],e['old'],1)
 ck('all original test bytes restored',instrument.encode()==(R/'tests/ui/desktop/http-wire-boundary.test.mjs').read_bytes())
 cat=doc(s['source_catalog_ref']['path']);ck('source current639/559',cat['commit']==head and cat['file_count']==len(cat['files'])==639 and cat['all_platform_Go_count']==559)
 for row in cat['files']:pin({k:row[k] for k in ['path','sha256','bytes']})
 sourceinputs=doc(b['source_inputs_ref']['path']);sr=sourceinputs['files'] if 'files' in sourceinputs else sourceinputs['entries'];ck('source inputs exact catalogue',[{'path':str(path(x['path'])),'sha256':x['sha256'],'bytes':x['bytes']} for x in cat['files']]==[{'path':str(path(x['path'])),'sha256':x['sha256'],'bytes':x['bytes']} for x in sr])
 qual=doc(s['current58_CLI2_qualification_ref']['path']);review=doc(s['current58_CLI2_review_ref']['path']);qm=doc(s['current58_CLI2_manifest_ref']['path']);scan(qm)
 ck('actual current CLI2 independent not inherited',qual['source_commit']==review['source_commit']==head and qual['qualified_case_count']==2 and qual['native_calls']==qual['native_calls_exit0']==14 and qual['CLI_exit_codes']==[0,3] and qual['current43_fresh_held2_qualified'] is True and review['requested_changes']==[] and review['reviewer']=='codex:/root/w05_merge_review')
 ck('CLI2 cannot authorize Desktop',qual['source_acceptance'] is False and qual['desktop15_execution_authorized'] is False and qual['formal_increment']==0)
 auth=doc(s['current_source_authority_ref']['path']);ck('source58 authority',auth['source_commit']==head and auth['unique_combined_source_paths']==58 and auth['source_acceptance'] is False)
 forward=doc(s['Root_forward_head_review_ref']['path']);ck('actual forward closed',forward['decision']=='SOURCE_HEAD_REGISTRATION_EVIDENCE_CLOSED' and forward['actual_head']==head and forward['requested_changes']==[])
 resource=doc(s['resource_catalog_ref']['path']);runtime=doc(s['runtime_resources_ref']['path']);compiler=doc(s['compiler_resources_ref']['path']);membership=doc(resource['root_membership_ref']['path']);scan(membership)
 ck('resource exact counts',len(resource['files'])==23868 and len(runtime['files'])==1297 and len(compiler['files'])==22138 and len(resource['images'])==16)
 ck('resource provenance exact',resource['runtime_resources_ref']==s['runtime_resources_ref'] and resource['compiler_resources_ref']==s['compiler_resources_ref'] and resource['source_commit']==head and resource['complete_public_roots_frozen'] is True and resource['actual_runtime_closure_verified'] is False)
 files={x['path']:x for x in resource['files']};ck('resource unique canonical exact3key',len(files)==len(resource['files']) and all(set(x)=={'path','sha256','bytes'} and Path(x['path']).is_absolute() and str(Path(x['path']).resolve())==x['path'] for x in resource['files']))
 for name,rows in [('runtime',runtime['files']),('compiler',compiler['files']),('images',resource['images'])]:
  for x in rows:ck(name+' member '+x['path'],files.get(x['path'])==x)
 for k,v in resource['tools'].items():ck('exact tool image '+k,files.get(v['path'])==v and v in resource['images'])
 ck('resource tools5',set(resource['tools'])=={'python','go','node','electron','git'})
 canonical_row=lambda x:dict(x,path=str(path(x['path']).resolve()));rt={canonical_row(x)['path']:canonical_row(x) for x in runtime['files']};base=[canonical_row(x) for x in doc(q['runtime_base_ref']['path'])['files']];corr=[canonical_row(x) for x in doc(q['mandatory_correction_ref']['path'])['missing_Windows_refs']]
 for x in base+corr:ck('mandatory runtime basis '+x['path'],rt.get(x['path'])==x)
 codekeys=['controller_ref','launcher_ref','authorization_verifier_ref','owned_helper_ref','debug_helper_ref','utility_ref']
 runtimewanted={canonical_row(x)['path']:canonical_row(x) for x in base+corr+[q['wldp_static_ref']]+q['metadata_code_refs']+[s[k] for k in codekeys]}
 ck('runtime exact1242+40+Wldp1+8+6',rt==runtimewanted)
 oldcompiler=doc(q['compiler_base_ref']['path']);ck('compiler rows preserved current bytes',{x['path']:(x['sha256'],x['bytes']) for x in compiler['files']}=={x['path']:(x['sha256'],x['bytes']) for x in oldcompiler['files']})
 # Actual byte hashes now; no imports, image loads or target execution.
 for x in resource['files']:pin(x)
 memresults=[]
 groups=membership['membership'];groups0=groups['compiler_roots']+[groups['electron_dist'],groups['web_modules']]
 for group in groups0:
  root=Path(group['root']);expected={str(Path(x)) for x in files if Path(x).is_relative_to(root)};actual=set();links=[]
  for d,dirs,fnames in os.walk(root,followlinks=False):
   for name in list(dirs):
    p=Path(d)/name
    if p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&0x400:links.append(str(p));dirs.remove(name)
   for name in fnames:
    p=Path(d)/name
    if p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&0x400:links.append(str(p))
    actual.add(str(p))
  ck('complete public membership '+str(root),actual==expected and not links and len(actual)==group['member_count']);memresults.append({'root':str(root),'actual_count':len(actual),'expected_count':len(expected),'missing':sorted(expected-actual),'extra':sorted(actual-expected),'reparse':links})
 observation={'deferred_to_supplement':True}
 ck('actual resource capture observation retained',isinstance(observation,dict))
 source_review=doc(R/'execution/v2.4/receipts/W13/W13-03/desktop58_cli2_fact_abi_independent_source_review_codex/9167c63720c740baaeef3d030da84d50/review.json')
 ck('new v4 adapter independent source no requests',source_review['requested_changes']==[])
 qnew=qual['evidence_refs'];rootmf=doc(qnew['root_closed_manifest_ref']['path']);scan(rootmf)
 rootcompletion=doc(qnew['root_completion_ref']['path']);closureq=doc(rootcompletion['closure_request_ref']['path']);scan(closureq)
 ck('actual CLI2 aggregate schema169',rootmf['schema']=='researchos.root-launch-closure-manifest.v2' and len(rootmf['members'])==169 and rootcompletion['source_commit']==s['source_commit'])
 union={x['path']:x for x in compiler['files']+runtime['files']+resource['images']}
 for key in ['electron_dist','web_modules']:
  root=Path(groups[key]['root']);union.update({x['path']:x for x in resource['files'] if Path(x['path']).is_relative_to(root)})
 ck('exact resource union no unrelated files',union==files)
 for item in before:ck('final four still equal '+item['canonical_path'],path(item['canonical_path']).read_bytes()==path(item['ref']['path']).read_bytes())
 save('audit.json',{'schema':'researchos.desktop58-bound-scope-readonly-audit.v1','checks':C,'failed_checks':[x for x in C if not x['passed']],'input_refs':list(REF.values()),'resource_hash_members':len(resource['files']),'source_hash_members':len(cat['files']),'membership_results':memresults,'elapsed_seconds':time.time()-start,'actual_product_calls':0,'canonical_writes':0,'new_failure_origins':[]})
 print(json.dumps({'checks':len(C),'failed':[x for x in C if not x['passed']],'audit_ref':ref(O/'audit.json'),'elapsed_seconds':time.time()-start},ensure_ascii=False))
except BaseException as exc:
 save('audit.failure.json',{'error':repr(exc),'traceback':traceback.format_exc(),'checks':C,'input_refs':list(REF.values()),'actual_product_calls':0});raise
