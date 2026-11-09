from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,types

R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
D=B/'schema21_public_root_caller_independent_review_codex/review-public21-caller-20261010-02'
N=B/'schema21_public_root_caller_source_codex/s21public-caller-20261010-02';O=B/'schema21_public_root_caller_source_codex/s21public-caller-20261010-01'
P=R/'execution/v2.4/receipts/W09/W09-99/full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def load(p):return json.loads(Path(p).read_bytes())
def write(name,v):
 with (D/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
 return pin(D/name)
s=types.ModuleType('public21_directory_narrow_host_capture');s.__file__=str(P);exec(compile(P.read_bytes(),str(P),'exec'),s.__dict__);s.D=D
origin=s.capture('0a7d51',1,1,1150)
write('original1150.failure-origin.json',{'schema':'researchos.public21-independent-review-original-failure.v1','ordinal':1150,'chunk_id':'0a7d51','actual_outer_exit':1,'actual_python_exit':1,'other_product_exits':None,
 'cause':'Reviewer assumed source-inputs.references was byte-identical; actual sole reference replacement is historical Caller01 to current Caller02.',
 'complete_original_IO':origin,'original_script_ref':pin(D/'review_directory_delta.py'),'original_report_ref':pin(D/'finite-directory-delta-review.json'),
 'original_closed_guard_ref':pin(D/'source-guard.closed.json'),'59_resources_guard_closed_zero':True,'successful_prefix_checks':11,'failure_count_reset':False,'original_command_rerun':False})
prefix=load(D/'finite-directory-delta-review.json');fullguard=load(D/'source-guard.closed.json')
assert prefix['status']=='FAILED' and len(prefix['checks'])==12 and sum(x['passed'] for x in prefix['checks'])==11
assert fullguard['verification']=='PASSED' and fullguard['closed'] and fullguard['retained_handles_count']==0 and fullguard['errors']==[]
held={x['path']:{k:x[k] for k in ('path','sha256','bytes')} for x in fullguard['entries']};assert len(held)==59
href=held[str(N/'HDF.json')];h=load(href['path']);aref=next(r for r in held.values() if r['path'].endswith('w09.public21-caller02-author.actual-audit.root.json'));audit=load(aref['path'])
tail=[held[str(N/'source-inputs.json')],held[str(O/'source-inputs.json')],href,aref,held[audit['original_capture_ref']['path']]]
for item in h['Root_original1146_and_Task102_witnesses']:
 tail.extend([held[item['witness_ref']['path']],held[item['original_capture_ref']['path']]])
tail.extend([pin(D/'finite-directory-delta-review.json'),pin(D/'source-guard.closed.json')])
unique={r['path']:r for r in tail};guard=s.guard();checks=[]
report={'schema':'researchos.public21-caller02-independent-narrow-tail.v1','checks':checks,'original_1150_ref':pin(D/'original1150.failure-origin.json'),
 'successful_prefix_checks_reused':11,'Source59_pins_repeated':False,'author13_old58_353_17_4154_rerun':False,
 'actual_products_or_Root_stages':0,'RootScope_issued':False,'runtime_qualification_issued':False,'live_Canon_held':False,
 'execution_grant':False,'formal_acceptance':False,'reviewed_utc':datetime.now(timezone.utc).isoformat()}
def check(name,ok,details=None):
 checks.append({'name':name,'passed':bool(ok),'details':details})
 if not ok:raise AssertionError(name)
try:
 guard.acquire(list(unique.values()))
 def data(r):return guard.get_buffer(r['path'])
 old=json.loads(data(held[str(O/'source-inputs.json')]));new=json.loads(data(held[str(N/'source-inputs.json')]))
 oldcaller=held[str(O/'public21_root.source.py')];newcaller=h['caller_ref'];expected=[newcaller if r==oldcaller else r for r in old['references']]
 changed={k for k in set(old)|set(new) if old.get(k)!=new.get(k)}
 check('Source-input-only-current-Caller-replacement-and-directory-metadata',new['references']==expected and changed=={'directory_revision','references'},
       {'changed_fields':sorted(changed),'removed_ref':oldcaller,'added_ref':newcaller,'other_33_declarations_unchanged':True})
 def verify3(audit,rawref):
  lines=data(rawref).splitlines(keepends=True);assert len(lines)==3 and all(x.endswith(b'\n') for x in lines)
  assert audit['source_line_offsets'][0]==0 and audit['source_line_offsets']==sorted(set(audit['source_line_offsets']))
  with Path(audit['source_audit_path']).open('rb') as stream:
   for off,digest,line in zip(audit['source_line_offsets'],audit['original_line_sha256'],lines):
    assert type(off) is int and off+len(line)<=audit['source_prefix_size_observed'] and hashlib.sha256(line).hexdigest()==digest
    stream.seek(off);assert stream.read(len(line))==line
  return [json.loads(line) for line in lines]
 witness=[]
 for item in h['Root_original1146_and_Task102_witnesses']:
  a=json.loads(data(item['witness_ref']));assert a['source_line_offsets']==item['source_offsets'];verify3(a,item['original_capture_ref']);witness.append(item)
 check('original1146-and-Task102-original-three-lines-retained',len(witness)==2,witness)
 rows=verify3(audit,audit['original_capture_ref']);header,meta,final=rows;body=final['payload'];actualtext=body['content'][0]['text']
 envelope='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/backup_regression_resources\nPayload:\n';assert actualtext.startswith(envelope)
 def pairs(items):
  v={}
  for k,x in items:
   if k in v:raise ValueError('DUPLICATE_SOURCE_DELIVERY_KEY')
   v[k]=x
  return v
 def badnumber(v):raise ValueError(v)
 delivery=json.loads(actualtext[len(envelope):],object_pairs_hook=pairs,parse_constant=badnumber)
 def refs(v):
  if type(v) is dict:
   if {'path','sha256','bytes'}<=set(v):yield {k:v[k] for k in ('path','sha256','bytes')}
   else:
    for x in v.values():yield from refs(x)
  elif type(v) is list:
   for x in v:yield from refs(x)
 delivered=list(refs(delivery));mfref=held[str(N/'MF.json')]
 check('actual-Caller02-author-anchored-Final-fullrefs-and-original-offsets',header['type']=='session_meta' and header['payload']['id']=='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
       and meta['type']=='inter_agent_communication_metadata' and final['type']=='response_item' and final['ordinal']==meta['ordinal']+1
       and meta['timestamp']==final['timestamp'] and final['metadata']['client_authored'] is False
       and body['type']=='agent_message' and body['author']=='/root/backup_regression_resources' and body['recipient']=='/root'
       and audit['actor_id']==h['source_author'] and audit['Root_thread_id']==h['parent_Root_thread']
       and audit['binding_sha256']==href['sha256'] and delivery['source_author']==h['source_author']
       and all(ref in delivered for ref in [href,mfref,h['caller_ref'],h['contract_ref']]),
       {'audit_ref':aref,'raw_ref':audit['original_capture_ref'],'source_offsets':audit['source_line_offsets'],'metadata_ordinal':meta['ordinal'],'Final_ordinal':final['ordinal'],'timestamp':final['timestamp']})
 report['status']='PASSED_SOURCE_ONLY';report['new_tail_checks_passed']=len(checks);report['total_unique_passed_checks']=11+len(checks)
 report['current_Source_bindings']=next(c['details'] for c in prefix['checks'] if c['name']=='actual-own-review-current-HDF-caller-registrar-and-decision-fields')
 report['contract_metadata_note']=prefix['contract_metadata_note'];report['held_new_Source_refs']=list(held.values())
 report['reused_prefix_report_ref']=pin(D/'finite-directory-delta-review.json');report['reused_full_guard_ref']=pin(D/'source-guard.closed.json')
except BaseException as exc:
 report['status']='FAILED';report['error']=repr(exc);raise
finally:
 closed=guard.close();gr=write('narrow-tail-guard.closed.json',closed);report['guard_closed']=closed['closed'];report['retained_handles_count']=closed['retained_handles_count'];rr=write('narrow-directory-tail.json',report)
 assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
 print(json.dumps({'status':report.get('status'),'passed_tail':sum(c['passed'] for c in checks),'reused_prefix':11,'held_new_Source_total':59,'narrow_held_refs':len(unique),'guard_closed_zero':True,'report_ref':rr,'guard_ref':gr,'original1150':origin},ensure_ascii=False))
