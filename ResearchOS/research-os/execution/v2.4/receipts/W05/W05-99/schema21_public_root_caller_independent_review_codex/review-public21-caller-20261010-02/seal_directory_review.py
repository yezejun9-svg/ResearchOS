from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,types,sys

R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
D=B/'schema21_public_root_caller_independent_review_codex/review-public21-caller-20261010-02'
N=B/'schema21_public_root_caller_source_codex/s21public-caller-20261010-02'
V=B/'schema21_public_root_caller_independent_review_codex/review-public21-caller-20261010-01'
P=R/'execution/v2.4/receipts/W09/W09-99/full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def load(p):return json.loads(Path(p).read_bytes())
def save(name,v):
 with (D/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
 return pin(D/name)
ordinal=int(sys.argv[1])
s=types.ModuleType('public21_directory_final_sealer_support');s.__file__=str(P);exec(compile(P.read_bytes(),str(P),'exec'),s.__dict__);s.D=D
origin=s.capture('a4fc75',1,1,ordinal)
save('original'+str(ordinal)+'.failure-origin.json',{'schema':'researchos.public21-independent-review-original-failure.v1','ordinal':ordinal,
 'chunk_id':'a4fc75','outer_exit':1,'Python_exit':1,'other_product_exits':None,'original_complete_IO':origin,
 'cause':'Reviewer compared Source publication display refs (D:/) with execution-gate refs (Windows backslashes) as whole dictionaries. Actual actor, hashes, sizes and target files match.',
 'original_script_ref':pin(D/'continue_directory_review.py'),'original_report_ref':pin(D/'narrow-directory-tail.json'),
 'original_guard_ref':pin(D/'narrow-tail-guard.closed.json'),'retained_handles_count':0,'successful_prefix_checks':11,'successful_tail_checks':2,'original_command_rerun':False,'failure_count_reset':False})
prefix=load(D/'finite-directory-delta-review.json');tail=load(D/'narrow-directory-tail.json');full=load(D/'source-guard.closed.json');tg=load(D/'narrow-tail-guard.closed.json')
assert sum(x['passed'] for x in prefix['checks'])==11 and sum(x['passed'] for x in tail['checks'])==2
assert all(g['verification']=='PASSED' and g['closed'] and g['retained_handles_count']==0 and g['errors']==[] for g in [full,tg])
held={x['path']:{k:x[k] for k in ('path','sha256','bytes')} for x in full['entries']};assert len(held)==59
href=held[str(N/'HDF.json')];mfref=held[str(N/'MF.json')];h=load(href['path']);aref=next(r for r in held.values() if r['path'].endswith('w09.public21-caller02-author.actual-audit.root.json'));audit=load(aref['path'])
refs=[aref,held[audit['original_capture_ref']['path']],href,mfref]+[pin(D/n) for n in ['finite-directory-delta-review.json','narrow-directory-tail.json','source-guard.closed.json','narrow-tail-guard.closed.json']]
guard=s.guard();finalcheck={}
try:
 guard.acquire(refs)
 lines=guard.get_buffer(audit['original_capture_ref']['path']).splitlines(keepends=True);assert len(lines)==3 and all(x.endswith(b'\n') for x in lines)
 header,meta,final=[json.loads(line) for line in lines];body=final['payload'];text=body['content'][0]['text']
 with Path(audit['source_audit_path']).open('rb') as f:
  for off,digest,line in zip(audit['source_line_offsets'],audit['original_line_sha256'],lines):
   assert type(off) is int and off+len(line)<=audit['source_prefix_size_observed'] and hashlib.sha256(line).hexdigest()==digest
   f.seek(off);assert f.read(len(line))==line
 envelope='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/backup_regression_resources\nPayload:\n';assert text.startswith(envelope)
 def pairs(rows):
  v={}
  for k,x in rows:
   if k in v:raise ValueError('DUPLICATE_SOURCE_DELIVERY_KEY')
   v[k]=x
  return v
 def badnum(v):raise ValueError(v)
 delivery=json.loads(text[len(envelope):],object_pairs_hook=pairs,parse_constant=badnum)
 assert header['type']=='session_meta' and header['ordinal']==0 and header['payload']['id']==h['parent_Root_thread']
 assert meta['type']=='inter_agent_communication_metadata' and final['type']=='response_item' and final['ordinal']==meta['ordinal']+1
 assert meta['timestamp']==final['timestamp'] and final['metadata']['client_authored'] is False
 assert body['type']=='agent_message' and body['author']=='/root/backup_regression_resources' and body['recipient']=='/root'
 assert len(body['content'])==1 and body['content'][0]['type']=='input_text'
 assert audit['actor_id']==delivery['source_author']==h['source_author'] and audit['Root_thread_id']==h['parent_Root_thread'] and audit['binding_sha256']==href['sha256']
 comparisons=[]
 for name,expected in [('hdf_ref',href),('mf_ref',mfref),('caller_ref',h['caller_ref']),('contract_ref',h['contract_ref'])]:
  shown=delivery[name]
  # Publication display can use either exact known separator spelling.
  # This does not rewrite or relax any executable HDF/decision/CLI ref object.
  assert shown['path'] in [expected['path'],Path(expected['path']).as_posix()]
  assert Path(shown['path']).resolve(strict=True)==Path(expected['path']).resolve(strict=True)
  assert shown['sha256']==expected['sha256'] and type(shown['bytes']) is int and shown['bytes']==expected['bytes']
  comparisons.append({'published_display_ref':shown,'unchanged_execution_ref':expected,'same_target_digest_size':True})
 finalcheck={'name':'actual-Caller02-author-Final-with-exact-known-display-spellings','passed':True,'audit_ref':aref,
  'source_offsets':audit['source_line_offsets'],'metadata_ordinal':meta['ordinal'],'Final_ordinal':final['ordinal'],'timestamp':final['timestamp'],
  'comparisons':comparisons,'execution_ref_objects_unchanged':True,'actual_Root_grant_or_review_witness_created':False}
except BaseException as exc:
 finalcheck={'passed':False,'error':repr(exc)};raise
finally:
 closed=guard.close();finalcheck['guard_closed']=closed['closed'];finalcheck['retained_handles_count']=closed['retained_handles_count']
 cg=save('final-author-guard.closed.json',closed);cr=save('final-author-delivery-check.json',finalcheck)
 assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]

bindings=next(c['details'] for c in prefix['checks'] if c['name']=='actual-own-review-current-HDF-caller-registrar-and-decision-fields')
assert bindings=={'source_hdf_ref':href,'source_mf_ref':mfref,'caller_ref':h['caller_ref'],'registrar_ref':h['registrar_ref'],'calling_contract_ref':h['contract_ref']}
now=datetime.now(timezone.utc).isoformat();errors=[load(D/'original1149.failure-origin.json'),load(D/'original1150.failure-origin.json'),load(D/('original'+str(ordinal)+'.failure-origin.json'))]
reportref=save('review-report.json',{'schema':'researchos.public21-caller02-independent-review-report.v1','reviewed_utc':now,
 'resolved_finding':'PUBLIC21-CALLER-DIRECTORY-ROOT-001','status':'ACCEPTED_SOURCE_ONLY','successful_prefix_ref':pin(D/'finite-directory-delta-review.json'),
 'successful_tail_ref':pin(D/'narrow-directory-tail.json'),'final_author_check_ref':cr,'unique_passed_checks':14,
 'full_new_Source_refs_verified':59,'full_Source_guards_closed_zero':True,'author13_old58_353_17_4154_rerun':False,
 'contract_metadata_note':prefix['contract_metadata_note'],'previous_Task99_refs':{name:pin(V/name) for name in ['HDF.json','MF.json','source-decision.json']},
 'original1146_and_Task102_refs':h['Root_original1146_and_Task102_witnesses'],'new_review_originals':errors,
 'runtime_qualification_status':'OPEN_PENDING_FRESH_ROOT_RESOURCE_SCOPE','execution_grant':False,'formal_acceptance':False})
common={'review_author':'codex:/root/full_w09_source_review','review_thread_id':s.THREAD,'source_author':h['source_author'],
 'root_thread_id':h['parent_Root_thread'],'reviewed_utc':now,'status':'ACCEPTED_SOURCE_ONLY','verdict':'SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION',
 'independent_non_author':True,**bindings,'review_report_ref':reportref,'findings':[],
 'contract_metadata_note':prefix['contract_metadata_note'],'runtime_qualification_status':'OPEN_PENDING_FRESH_ROOT_RESOURCE_SCOPE',
 'Root_scope_or_runtime_qualification_granted':False,'formal_programme_qualification':False,'execution_grant':False,'formal_acceptance':False,'parent_acceptance':False}
decisionref=save('source-decision.json',dict(common,schema='researchos.public21-caller-independent-source-decision.v1'))
members=[pin(p) for p in sorted(D.iterdir()) if p.is_file() and p.name not in ['HDF.json','MF.json']]
reviewmf=save('MF.json',{'schema':'researchos.independent-source-review-manifest.v1','review_author':'codex:/root/full_w09_source_review','members':members,'exclusions':['MF.json self','HDF.json references the completed manifest'],'immutable_after_publish':True,'execution_grant':False,'formal_acceptance':False})
guards=[pin(D/name) for name in ['source-guard.closed.json','narrow-tail-guard.closed.json','final-author-guard.closed.json']]
reviewhdf=save('HDF.json',dict(common,schema='researchos.public21-caller-independent-source-review-handoff.v1',manifest_ref=reviewmf,
 source_decision_ref=decisionref,guard_refs=guards,all_guards_closed=True,retained_handles_count=0,
 independent_checks_passed=14,author13_old58_353_17_4154_rerun=False,full_new_Source_refs_verified=59,
 original1146_preserved=True,new_original_failures=[{'ordinal':e['ordinal'],'origin_ref':pin(D/('original'+str(e['ordinal'])+'.failure-origin.json'))} for e in errors],
 Main_written=False,Canon_written=False,Leaf_RootScope_Native_Go_SQLconnection_model_TP_calls=0,STOP=True))
print(json.dumps({'schema':'researchos.public21-peer-review-delivery.v1','operation':'SOURCE_REVIEW_WITNESS','review_author':'codex:/root/full_w09_source_review',
 'root_thread_id':h['parent_Root_thread'],'verdict':'SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION','review_refs':[reviewhdf,reviewmf,decisionref],
 'new_unique_checks_passed':14,'new_Source_refs_verified':59,'all_guards_closed_zero':True,'preserved_originals':[1146,1149,1150,ordinal],
 'runtime_qualification_status':'OPEN_PENDING_FRESH_ROOT_RESOURCE_SCOPE','formal_acceptance':False,'execution_grant':False,'STOP':True},ensure_ascii=False))
