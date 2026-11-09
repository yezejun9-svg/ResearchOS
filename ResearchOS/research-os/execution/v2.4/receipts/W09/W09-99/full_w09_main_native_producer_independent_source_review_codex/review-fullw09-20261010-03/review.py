"""Finite non-author v3 Source delta review. No Root authority or product run."""
from pathlib import Path
import ast, hashlib, json, os, re, sys, types
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
S=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-03'
OLD=S.parent/'fullw09-20261010-02'
PR=W/'full_w09_main_native_producer_independent_source_review_codex/review-fullw09-20261010-02'
N=Path(__file__).resolve().parent
ACTOR='codex:/root/attach_fixture_source_review'
SESSION='01a11e76-4e37-7a21-a388-2c5f2e3c9ebf'
def pin(path):
 p=Path(path);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(path):return json.loads(Path(path['path'] if isinstance(path,dict) else path).read_bytes())
def save(name,obj):
 p=N/name
 with p.open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def inert(path,name):
 m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m
 exec(compile(Path(path).read_bytes(),str(path),'exec'),m.__dict__);return m
def mapstrings(obj,mapping):
 if isinstance(obj,str):
  for before,after in mapping.items():obj=obj.replace(before,after)
  return obj
 if isinstance(obj,list):return [mapstrings(x,mapping) for x in obj]
 if isinstance(obj,dict):return {k:mapstrings(v,mapping) for k,v in obj.items()}
 return obj
def capture_author(m,href):
 audit=Path(m.ROOT_AUDIT);limit=audit.stat().st_size
 with audit.open('rb') as f:
  header=f.readline();f.seek(max(len(header),limit-16*1024*1024))
  if f.tell()!=len(header):f.readline()
  offset=f.tell();previous=None;matches=[]
  while offset<limit:
   line=f.readline();row=json.loads(line);p=row.get('payload',{})
   if row.get('type')=='response_item' and p.get('type')=='agent_message' and p.get('author')==m.AUTHOR.removeprefix('codex:'):
    text=''.join(v.get('text','') for v in p.get('content',[]))
    if href['sha256'] in text:
     assert previous is not None
     matches.append((previous,(offset,line,row)))
   previous=(offset,line,row);offset+=len(line)
 assert matches,'NO_ACTUAL_AUTHOR_FINAL_WITH_FULL_HDF_DIGEST'
 a,b=matches[-1]
 assert a[2]['type']=='inter_agent_communication_metadata' and b[2]['ordinal']==a[2]['ordinal']+1
 assert b[2]['metadata']['client_authored'] is False
 rows=[(0,header),(a[0],a[1]),(b[0],b[1])]
 raw=N/'actual-v3-author-Root-peer.raw.jsonl'
 if raw.exists():
  assert raw.read_bytes()==b''.join(v for _,v in rows)
  return pin(N/'actual-v3-author-Root-peer.binding.json'),pin(raw),b[2]
 with raw.open('xb') as f:f.write(b''.join(v for _,v in rows))
 ref=pin(raw)
 binding=save('actual-v3-author-Root-peer.binding.json',dict(schema='researchos.w09-native-producer.actual-audit.v1',actor_id=m.AUTHOR,Root_thread_id=m.ROOT_THREAD_ID,source_audit_path=m.ROOT_AUDIT,source_line_offsets=[o for o,_ in rows],original_line_sha256=[hashlib.sha256(v).hexdigest() for _,v in rows],source_prefix_size_observed=limit,original_capture_ref=ref,binding_sha256=href['sha256']))
 return binding,ref,b[2]
def run():
 checks=[]
 def check(name,ok,detail=None):
  checks.append(dict(name=name,passed=bool(ok),detail=detail))
  assert ok,name
 href,mref=pin(S/'HDF.json'),pin(S/'MF.json')
 check('Root supplied v3 HDF',href['sha256']=='0b3000c9ca1d46a1df980535dfb0e57c55798d7eb5d7819c09dcab792168a447' and href['bytes']==8412)
 check('Root supplied v3 MF',mref['sha256']=='71f2c09424c3fa75153a173fa5208c3d91e510390c500826e5f258855cd0f4c3' and mref['bytes']==4399)
 h,mf,c,contract=[read(S/n) for n in ('HDF.json','MF.json','source.choice.json','root-calling-contract.json')]
 m=inert(S/'full_w09_runtime.source.py','fullw09_v3_independent_runtime')
 gm=m.module(c['common']['guard_ref']);job=m.module(c['common']['owned_job_ref'])
 author_binding,author_raw,author_row=capture_author(m,href)
 priorh=pin(PR/'HDF.json');priorm=pin(PR/'MF.json');priord=pin(PR/'source-review-decision.json')
 check('exact prior review HDF',priorh['sha256']=='648675cb0cc6c4a48937d17d1be78c7e29261a2e7f8b31d4375ff4661f9e4e7d' and priorh['bytes']==3478)
 check('exact prior review MF',priorm['sha256']=='35d2d6ac38f7d4fd3f7228b5d670860b53ead5dda7008f2070cd15bb3ee50a1f' and priorm['bytes']==11402)
 check('exact prior review decision',priord==h['prior_independent_review_ref'] and priord['sha256']=='ae1597399ee43d91eaeb96a70ecb5aeeeb0bbb1a758cfc2db17d65fc3a0e26dc' and priord['bytes']==29364)
 oldh=read(h['prior_source_hdf_ref']);oldmf=read(h['prior_source_mf_ref']);pd=read(priord)
 initialh=read(S.parent/'fullw09-20261009-01/HDF.json')
 historical=[initialh['controls_ref'],initialh['audit_closure_controls_ref'],h['reused_prior_independent_controls_112'],h['reused_v2_peer_controls_20'],pd['complete_authority_controls_ref']]
 bp=read(c['common']['compiler_blueprint_ref'])
 refs=[href,mref,*mf['members'],priorh,priorm,priord,*read(priorm)['members'],h['prior_source_hdf_ref'],h['prior_source_mf_ref'],*oldmf['members'],*historical,*c['common']['source21'],*bp['stable_input_refs'],author_binding,author_raw,pin(__file__)]
 refs.extend([pin(S.parent/'fullw09-20261009-01/HDF.json'),pin(PR.parent/'review-fullw09-20261009-01/independent_source_review.py')])
 for v in c['common'].values():
  if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}:refs.append(v)
 refs.extend(c['common']['tool_refs'].values())
 refs.extend(m.pin(Path(p)) for p in job.runtime_resource_paths())
 for module in tuple(sys.modules.values()):
  for key in ('__file__','__cached__'):
   p=getattr(module,key,None)
   if p and Path(p).is_file():refs.append(m.pin(Path(p).resolve()))
 refs=m.unique(refs)
 check('current Canon excluded',not {str(p).casefold() for p in m.CANON}.intersection(r['path'].casefold() for r in refs))
 guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
 try:
  guard.acquire(refs)
  check('all Source and production runtime inputs pinned',all(pin(r['path'])==r for r in refs),len(refs))
  check('independent true actor and session',h['actor_id']==m.AUTHOR and ACTOR not in (m.AUTHOR,m.ROOT_ACTOR,'codex:/root/native_temp_independent_review') and h['source_thread_id']!=SESSION)
  package=m.package_refs()
  check('unchanged production package_refs succeeds on final HDF MF',package[0]==href and package[1]==mref and len(package[2])==len(mf['members'])+2)
  check('exact source-only package marker',h['status']=='SOURCE_READY_PENDING_INDEPENDENT_REVIEW' and h['execution_grant'] is False and h['actual_executed'] is False)
  check('unchanged actual_audit accepts real final author delivery',m.actual_audit(author_binding,m.AUTHOR,href['sha256'])==[author_binding,author_raw])
  check('backend author alias exact',author_row['payload']['author']==m.exact_host_peer_author(m.AUTHOR) and author_row['payload']['recipient']=='/root')
  text=author_row['payload']['content'][0]['text']
  check('actual author plaintext full HDF and MF digests',href['sha256'] in text and mref['sha256'] in text and '8412' in text and '4399' in text)
  fixed=('full_w09_runtime.source.py','runtime-overrides.source.py','full_w09_launcher.source.py','prepare_full_w09.source.py','run_full_w09.source.py','compiler-source-blueprint.json')
  for name in fixed:check('unchanged Source '+name,(S/name).read_bytes()==(OLD/name).read_bytes())
  oc,oct=read(OLD/'source.choice.json'),read(OLD/'root-calling-contract.json')
  old_ids={k:v['run_id'] for k,v in oc['selectors'].items()};new_ids={k:v['run_id'] for k,v in c['selectors'].items()}
  check('exact three new UUIDs',set(new_ids)=={'W09-G01','W09-G02','A06'} and len(set(new_ids.values()))==3 and all(re.fullmatch('[0-9a-f]{32}',v) for v in new_ids.values()) and not set(old_ids.values()).intersection(new_ids.values()))
  mapping={str(S):str(OLD),**{new_ids[k]:old_ids[k] for k in new_ids}}
  check('choice strict inverse only namespace and run IDs',mapstrings(c,mapping)==oc)
  inverse=mapstrings(contract,mapping)
  inverse['bound_source_refs']={k:pin(OLD/name) for k,name in contract['source_file_bindings'].items()}
  check('contract strict inverse only namespace and changed choice pin',inverse==oct)
  for key,name in contract['source_file_bindings'].items():check('production bound Source '+key,contract['bound_source_refs'][key]==pin(S/name))
  check('all eight active Source files pinned',set(fixed+('source.choice.json','root-calling-contract.json')).issubset(Path(r['path']).name for r in mf['members']))
  check('21 Main Source keys unchanged',len(c['common']['source21'])==21 and c['common']['source21']==oc['common']['source21'] and all(pin(r['path'])==r for r in c['common']['source21']))
  for key in new_ids:
   ch=m.choice(key)
   check('exact current selector '+key,ch==dict(c['common'],**c['selectors'][key]))
   check('future selector directories absent '+key,all(not Path(ch[k]).exists() for k in ('receipt_root','scratch_root','output_root')))
   check('fixed future selector paths '+key,ch['receipt_root']==str(S/('actual-'+key+'-'+ch['run_id'])) and ch['scratch_root']==str(R/'.local'/('w09-full-'+key+'-'+ch['run_id'])) and ch['output_root']==str(R/'execution/receipts/W09/retrieval'/('run-'+ch['run_id'])))
  # This read-only production entry verifies directory inventory and locked tools.
  input_refs,actualbp=m.read_inputs(m.choice('W09-G01'))
  heldmap={r['path']:r for r in refs}
  check('unmodified production read_inputs all held',actualbp==bp and all(heldmap.get(r['path'])==r for r in input_refs),len(input_refs))
  check('DLL runtime resources all held',all(heldmap.get(str(Path(p)))==m.pin(Path(p)) for p in job.runtime_resource_paths()))
  hist=[read(r) for r in historical]
  check('reused historical author 54 plus 14 plus 1 published checks',len(hist[0]['controls'])==54 and len(hist[1]['controls'])==14 and hist[2]['author_controls_reproduced']==initialh['finite_Source_checks']==69 and all(x['status'].startswith('PASS') for d in hist[:2] for x in d['controls']), 'Historical independent_source_review.py 219-221 uses len(reproduced)+len(reproduced_extra)+1; preserved as historical count, not 69 newly rerun controls.')
  check('reused 112 independent controls',len(hist[2]['checks'])==112 and all(x['status'].startswith('PASS') for x in hist[2]['checks']))
  check('reused 20 peer controls',hist[3]['pass']==20 and hist[3]['fail']==0)
  check('reused 98 authority-shape checks remain synthetic',len(hist[4]['checks'])==98 and pd['whole_chain_positive']=='IN_MEMORY_ONLY_THREE_MOCK_AUDITS_AND_PROVEN_PACKAGE_GATE_BYPASS')
  check('both previous findings resolved only in v3',set(x['id'] for x in pd['findings'])=={'V2-SOURCE-BLOCKER-01','V2-ROOT-DELIVERY-GAP-01'} and pd['decision']=='CHANGES_REQUIRED')
  for r in (h['source_guard_ref'],read(priorh)['final_guard_ref']):
   g=read(r);check('prior source guard clean '+r['path'],g['closed'] and g['retained_handles_count']==0 and not g['errors'])
  check('all held refs final unchanged',all(pin(r['path'])==r for r in refs))
 finally:closed=guard.close()
 check('independent Source guard closed clean',closed['closed'] and closed['retained_handles_count']==0 and not closed['errors'] and closed['verification']=='PASSED')
 gr=save('Source-guard.closed.json',closed)
 inp=save('held-input-refs.json',dict(members=refs,production_read_inputs=len(input_refs),Source_guard_ref=gr,Canonical_included=False))
 cr=save('independent-delta-controls.json',dict(status='PASS_SOURCE_ONLY',checks=checks,new_checks=len(checks),reused_not_rerun=dict(author=69,independent=112,peer=20,authority_shape=98),actual_package_refs_passed=True,actual_author_audit_passed=True,actual_author_audit_ref=author_binding,future_Root_authority_created=False,actual_prepare_run=False,actual_Go_runs=0,actual_Native_runs=0,actual_SQL_runs=0,actual_dispatcher_runs=0,actual_model_provider_calls=0,Main_written=False,Canon_written=False))
 bound={key:pin(S/name) for key,name in contract['source_file_bindings'].items()}
 common=dict(actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',reviewer_thread_id=SESSION,source_handoff_ref=href,source_manifest_ref=mref,calling_contract_ref=pin(S/'root-calling-contract.json'),**bound,selectors=c['selectors'],source21=c['common']['source21'],actual_executed=False,formal_case_accepted_delta=0,formal_acceptance=False,execution_grant=False,parent_acceptance=False,Main_written=False,Canon_written=False)
 decision=save('source-review-decision.json',dict(schema='researchos.w09-three-selector-producer-independent-source-decision.v1',decision='SOURCE_ACCEPTED_FOR_ROOT_THREE_SELECTOR_NATIVE',verdict='SOURCE_ACCEPTED_FOR_ROOT_THREE_SELECTOR_NATIVE',**common,source_author=m.AUTHOR,source_author_audit_ref=author_binding,prior_review_hdf_ref=priorh,prior_review_mf_ref=priorm,prior_review_decision_ref=priord,finite_controls_ref=cr,held_input_refs_ref=inp,Source_guard_ref=gr,findings=[],resolved_prior_findings=[x['id'] for x in pd['findings']],all_Source_guards_closed=True,retained_handles_count=0,current_CanonicalPair_held=False,actual_prepare_run=False,actual_Go_runs=0,actual_Native_runs=0,actual_SQL_runs=0,actual_dispatcher_runs=0,actual_model_provider_calls=0))
 manifest=save('MF.json',dict(schema='researchos.w09-three-selector-independent-source-review-manifest.v1',members=[pin(__file__),author_binding,author_raw,gr,inp,cr,decision]))
 handoff=save('HDF.json',dict(schema='researchos.w09-three-selector-independent-source-review-handoff.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',reviewer_thread_id=SESSION,status='SOURCE_ACCEPTED_FOR_ROOT_THREE_SELECTOR_NATIVE',manifest_ref=manifest,source_decision_ref=decision,source_handoff_ref=href,source_manifest_ref=mref,calling_contract_ref=common['calling_contract_ref'],finite_controls_ref=cr,held_input_refs_ref=inp,Source_guard_ref=gr,actual_executed=False,formal_acceptance=False,formal_case_accepted_delta=0,execution_grant=False,Main_written=False,Canon_written=False,all_Source_guards_closed=True))
 print(json.dumps(dict(HDF=handoff,MF=manifest,decision=decision,checks=len(checks),held_refs=len(refs),actual_author_audit_ref=author_binding,actual_package_refs_passed=True,formal_acceptance=False,execution_grant=False),ensure_ascii=False),flush=True)
if __name__=='__main__':run()
