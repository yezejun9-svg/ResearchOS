import json,hashlib,collections,os
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W13/W13-03';O=Path(__file__).parent
D=P/'desktop58_failed_execution_root_closure_codex/4705959febf34a72a90e13e3ea2da9a4'
checks=[];seen={}
def path(r):
 p=Path(r['path']);return p if p.is_absolute() else R/p
def pin(p):
 h=hashlib.sha256();n=0
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b);n+=len(b)
 return {'path':str(p),'sha256':h.hexdigest(),'bytes':n}
def ck(k,v,detail=None):checks.append({'check':k,'passed':bool(v),'detail':detail})
def verify(r):
 p=path(r);key=str(p)
 if key not in seen:seen[key]=pin(p)
 a=seen[key];ck('hash '+key,a['sha256']==r['sha256'] and a['bytes']==r['bytes']);return p
def read(p):return json.loads(p.read_bytes())
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
r=read(D/'report.json');h=read(D/'handoff.json');m=read(verify(h['manifest_ref']))
verify(h['report_ref']);verify(h['resume_ref'])
for x in m['entries']:verify(x)
ck('manifest immutable',m['schema']=='researchos.immutable-manifest.v1' and m['mutable_after_seal'] is False)
ck('original refs39',len(r['all_closed_original_refs'])==39)
for x in r['all_closed_original_refs']:verify(x)
by={Path(x['path']).as_posix():x for x in r['all_closed_original_refs']}
def original(suffix):
 found=[x for x in r['all_closed_original_refs'] if x['path'].replace('\\','/').endswith(suffix)]
 assert len(found)==1,(suffix,len(found))
 return read(path(found[0]))
E=original('/desktop58_finite_executor_codex/72ff32d0d24a42c4a8effd849d54f882/result.json')
L=original('/desktop58_finite_launcher_codex/72ff32d0d24a42c4a8effd849d54f882/result.json')
B=original('/build-current58.invocation.json');j=B['result'];dc=j['debug_capture'];cleanup=j['job_cleanup']
ck('builder actual exit requestedtermination preserved',j['actual_exit']==cleanup['termination_code_requested']==3758097160)
ck('builder no timeout',j['timed_out'] is False)
ck('builder firstcause no fabricatedexit',E['first_error']['stage']=='build-current58' and E['first_error']['actual_native_exit'] is None)
ck('builder incomplete capture retained',dc['complete'] is False and 'outside frozen runtime universe' in j['error'])
ck('builder clean ownedhandle closure witherror retained',cleanup['job_idle_confirmed'] is True and cleanup['active_processes_last_observed']==0 and cleanup['explicit_owned_handle_count']==cleanup['explicit_owned_handle_close_successes']==8883 and cleanup['explicit_owned_handles_remaining']==0 and cleanup['handles_closed'] is True and len(cleanup['errors'])>0)
events=dc['events'];creates=[x for x in events if x['code']==3];exits=[x for x in events if x['code']==5]
ck('802 create exit actualevents',len(creates)==len(exits)==dc['create_process_count']==dc['exit_process_count']==802)
ck('generation PID sets close',collections.Counter((x['pid'],x.get('process_generation')) for x in creates)==collections.Counter((x['pid'],x.get('process_generation')) for x in exits))
ck('debug events continued',all(x.get('debug_event_continued') is True for x in events))
rej=dc['rejected_load_facts'];ck('one rejected actualhFile',len(rej)==1)
f=rej[0]
ck('known rejected wldp exactbytes',f['path_from_actual_file_handle'].casefold()==r'\\?\c:\windows\system32\wldp.dll' and f['before']=={'sha256':'ecf34c9c64b2e6be9f622f0ca3a6ca7b95dcfdb88eb0419b045b853934bae0ba','bytes':443664})
ck('rejectedidentity exact nativeint',type(f['creation_time_100ns']) is int and f['creation_time_100ns']==134359047744627646 and f['pid']==39468 and f['process_generation']==802)
ck('unknown not qualified',f['expected_pin'] is None and f['qualified_module'] is False and f['diagnostic_only'] is True)
ck('wldp not successmodule',not any(x['path_from_actual_file_handle'].casefold().endswith('\\wldp.dll') for x in dc['modules']))
ck('170 notstarted rows0 http0 native3',len(E['all_case_states'])==170 and all(x['state']=='NOT_STARTED' and x['native_exit'] is None and x['qualified'] is False for x in E['all_case_states']) and E['rows']==[] and E['actual_observed_HTTP_total']==0 and E['actual_native_top_commands']==3)
ck('no secondary controllercause',E['secondary_errors']==[])
ck('launcher propagated1 nullableouter',L['actual_native_inner_exit']==1 and L['actual_outer_native_exit'] is None and L['first_error']['actual_native_exit'] is None)
for label in ['git-head','export-blobs']:
 x=original('/'+label+'.invocation.json')['result']
 ck(label+' actual0',x['actual_exit']==0 and x['error'] is None and x['timed_out'] is False and x['debug_capture']['complete'] is True)
 ck(label+' jobclosed',x['job_cleanup']['job_idle_confirmed'] is True and x['job_cleanup']['errors']==[])
vectors=[]
for x in r['all_closed_original_refs']:
 if x['path'].endswith('.vector.json'):
  v=read(path(x));ck('vector internallyclosed '+Path(x['path']).name,v['expected_members']==v['observed_members'] and v['drift']==[] and v['file_count']==len(v['observed_members']))
  vectors.append({'ref':x,'revision':v['revision'],'file_count':v['file_count']})
vmap={Path(x['ref']['path']).name:x for x in vectors}
ck('beforebuild failurefinal samebytes',vmap['before-build.vector.json']['ref']['sha256']==vmap['build-current58-native-after.vector.json']['ref']['sha256']==vmap['final.vector.json']['ref']['sha256'])
tree=read(verify(r['failed_export_tree_ref']))
ck('export diagnostic no posthocqualification',tree['qualification'] is False and tree['source_acceptance'] is False and tree['posthoc_resource_union'] is False)
ck('export5957',len(tree['files'])==5957)
for i,x in enumerate(tree['files']):verify(x)
exp=R/tree['root'];actual=[]
for root,dirs,files in os.walk(exp,followlinks=False):
 for dirname in list(dirs):
  p=Path(root)/dirname
  if p.is_symlink() or getattr(os.lstat(p),'st_file_attributes',0)&0x400:dirs.remove(dirname)
 for n in files:actual.append(str((Path(root)/n).relative_to(R)).replace('\\','/'))
ck('export exactfilemembership',set(actual)=={x['path'].replace('\\','/') for x in tree['files']})
for x in r['canonical_refs_unchanged']:verify(x)
ck('canonical snapshot335163580',r['canonical_tuple']==[335,163,580])
gitdir=R/'.git';head=(gitdir/'HEAD').read_text().strip() if gitdir.is_dir() else None
if head and head.startswith('ref: '):
 refpath=gitdir/head[5:]
 if refpath.is_file():head=refpath.read_text().strip()
 else:
  rows=(gitdir/'packed-refs').read_text().splitlines();head=next((z.split()[0] for z in rows if z.endswith(' '+head[5:]) and not z.startswith('#')),None)
ck('Main direct HEAD e2',head=='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7',head)
for x in h['pending_failure_origin_refs']:verify(x)
ck('root frozen pending19 not amended',len(h['pending_failure_origin_refs'])==19 and r['registered_failure_count']==580 and r['observed_failure_count']==599)
origins={str(i):read(D/('failure-origin-'+str(i)+'.json')) for i in [595,596,597,599]}
save('audit.json',{'schema':'researchos.failed-execution-independent-audit.v1','checks':checks,'count':len(checks),'passed':sum(x['passed'] for x in checks),'hashed_unique_files':len(seen),'root_manifest_members':len(m['entries']),'failed_export_hashes':5957,'vectors':vectors,'rejected_actualfact':f,'debug_counts':{'events':len(events),'create':len(creates),'exit':len(exits),'success_module_records':len(dc['modules'])},'origin_original_payloads':origins,'canonical_refs':r['canonical_refs_unchanged'],'no_candidate_execution':True})
review={'schema':'researchos.desktop58-failed-execution-independent-review.v1','actor':'codex:/root/w05_merge_review','non_author':True,'decision':'FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD' if all(x['passed'] for x in checks) else 'REQUEST_CHANGES','requested_changes':[x for x in checks if not x['passed']],'scope_uid':r['scope_uid'],'source_commit':'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7','root_report_ref':pin(D/'report.json'),'root_manifest_ref':pin(D/'manifest.json'),'root_handoff_ref':pin(D/'handoff.json'),'audit_ref':pin(O/'audit.json'),'native_facts':{'top_commands':3,'git_head_exit':0,'export_exit':0,'builder_exit':3758097160,'builder_requested_termination_code':3758097160,'primary_stage_exit_original':None,'caller_launcher_inner_propagation':'One underlying595; do not count3.','case_NOT_STARTED':170,'qualified_rows':0,'HTTP_cases_observed':0,'complete_debug_capture':False,'create_exit_count':802,'explicit_owned_handles_closed':8883,'remaining_owned_handles':0,'job_idle':True,'cleanup_errors_preserved':cleanup['errors']},'cause':{'confirmed':'Actual LOAD_DLL event6 generation802 actualhFile named wldp.dll with captured beforeSHA/bytes outside frozen universe; helper requestedtermination and incompletefinalization.','fact':f,'not_claimed':['No compiler source defect established.','No completedbuild/test/Node169/Go3/GUI/whole58qualification.','Posthoc failedexport inventory and future Wldp pin do not repair old closed run.','No DLL lifecycle qualification from cleanup alone.']},'count_boundary':{'registered':580,'root_frozen_observed':599,'later_parent_reported':601,'oldcut_unchanged':True,'underlying_execution_failure':1,'new_independent_review_failures':0},'source_acceptance':False,'formal_increment':0,'parent_acceptance_increment':0,'qualification':False,'same_scope_retry_allowed':False,'new_failure_origins':[],'scope_of_hashing':'WholeRootMF+39originals+5957failedexportfiles+4canon and19originrefs checked. Vector files compared internally; priorfull23900resource backing tree not rehashed.','status':'STOPPED'}
save('review.json',review)
save('handoff.json',{'schema':'researchos.independent-failure-closure-handoff.v1','decision':review['decision'],'review_ref':pin(O/'review.json'),'audit_ref':pin(O/'audit.json'),'qualification':False,'new_failure_origins':[],'new_failure_count':0,'status':'STOPPED'})
rows=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':rows,'count':len(rows),'self_excluded':True})
print(json.dumps({'checks':len(checks),'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],**{n:pin(O/n) for n in ['review.json','audit.json','handoff.json','manifest.json']}},ensure_ascii=False))

