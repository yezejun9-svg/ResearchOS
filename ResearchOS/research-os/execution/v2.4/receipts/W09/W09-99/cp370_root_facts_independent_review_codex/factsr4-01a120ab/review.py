"""Independent review of actual prepared Root facts; no registrar command or transaction."""
import ast
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import types

N=Path(__file__).resolve().parent;W=N.parent.parent
S=W/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v4'
ROOTDIR=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
PREV=W/'cp370_registrar_v4_independent_review_codex/regr4-01a120ab'
PD=W/'checkpoint_r369_native_source_root/cp369-c19-20261009'
checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,x):
 with (N/name).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def mod(p):
 m=types.ModuleType('factsreview_'+Path(p).stem);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def record(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok:raise AssertionError(name)

def main():
 fref=pin(S/'registration-facts.root.json');cref=pin(S/'registration.check.root.json')
 record('exact handed off actual facts',(fref['sha256'],fref['bytes'])==('285a0ebebaa067be95108e25ba32500e027652eefe81adfb77e2dd796a809232',4843))
 record('exact handed off actual check',(cref['sha256'],cref['bytes'])==('c527967e31e1bb3a14fe9e8a1c4c41cfa42491120ff990ce0b8b702adc3d6b43',897))
 facts=read(fref['path']);check=read(cref['path']);h=read(S/'HDF.json');mf=read(h['manifest_ref']['path']);m=mod(h['registrar_ref']['path'])
 previous_hdf=read(PREV/'HDF.json');previous=read(previous_hdf['source_decision_ref']['path'])
 record('exact v4 Source previous nonauthor acceptance',previous['decision']=='ACCEPTED_SOURCE_ONLY' and previous['source_hdf_ref']==pin(S/'HDF.json') and previous['source_mf_ref']==h['manifest_ref'] and previous['registrar_ref']==h['registrar_ref'] and previous['root_contract_ref']==h['root_contract_ref'])
 live=m.load(facts['live_ref']);request=m.load(facts['build_request_ref']);scope=m.load(facts['scope_ref']);owner=m.load(facts['owner_document_ref']);worker=m.load(facts['worker_document_ref']);q=m.load(facts['source_qualification_ref']);w=m.load(live['seed_witness_ref']);binding=m.load(w['capture_binding_ref'])
 pending_ref=pin(PD/'pending-diagnostics.live1005.root.json');resume_ref=pin(PD/'RESUME.cp369-main-profile-adopted.live1005.root.json')
 record('Root live1005 actual pending pin',(pending_ref['sha256'],pending_ref['bytes'])==('3c53c0613a91c65d4d892d56c79d5ad3c134ee6b215063d7b7eac941dc9b7f90',33252))
 record('Root live1005 actual resume pin',(resume_ref['sha256'],resume_ref['bytes'])==('e815b24a7815d82435534bbb087257d062be647ef1bd1143aab8affa93a27bd7',15210))
 pending=read(pending_ref['path']);resume=read(resume_ref['path'])
 bgr=pin(S/'build-source-guard.cleanup.root.json');cgr=pin(S/'source-guard.cleanup.check.root.json');bg=read(bgr['path']);cg=read(cgr['path'])
 bios={mode:read(ROOTDIR/('registrar-v4-'+mode+'.actual.original-tool-io.root.json')) for mode in ('build','check')}
 refs=[fref,cref,pin(__file__),pin(S/'HDF.json'),h['manifest_ref'],*mf['members'],pin(PREV/'HDF.json'),previous_hdf['manifest_ref'],previous_hdf['source_decision_ref'],bgr,cgr,pending_ref,resume_ref]
 for value in (facts,live,request,scope,owner,worker,q,w,binding,pending,resume):refs.extend(m.embedded_refs(value))
 for g in (bg,cg):refs.extend({k:e[k] for k in ('path','sha256','bytes')} for e in g['entries'])
 refs.extend(pin(ROOTDIR/('registrar-v4-'+mode+'.actual.original-tool-io.root.json')) for mode in ('build','check'))
 # Locate two original paired Root calls using bounded post-seed audit bytes.
 audit=Path(binding['source_audit_path']);limit=audit.stat().st_size
 targets={bio['result']['chunk_id']:mode for mode,bio in bios.items()};calls={};captures={}
 with audit.open('rb') as file:
  header=file.readline();header_item=json.loads(header);start=binding['source_line_offsets'][1];file.seek(start);offset=start
  record('actual audit Root identity',header_item['type']=='session_meta' and header_item['payload']['id']==m.ROOT_THREAD_ID)
  while offset<limit:
   line=file.readline();item=json.loads(line);payload=item.get('payload',{})
   if item.get('type')=='response_item' and payload.get('type')=='custom_tool_call':calls[payload['call_id']]=(offset,line,item)
   if item.get('type')=='response_item' and payload.get('type')=='custom_tool_call_output' and isinstance(payload.get('output'),list):
    for block in payload['output']:
     try:value=json.loads(block.get('text',''))
     except (ValueError,TypeError,AttributeError):continue
     if isinstance(value,dict) and value.get('chunk_id') in targets:
      mode=targets[value['chunk_id']];call=calls[payload['call_id']]
      record('unique actual host result '+mode,mode not in captures)
      records=[(0,header),(call[0],call[1]),(offset,line)]
      with (N/(mode+'.actual-host.raw.jsonl')).open('xb') as out:out.write(b''.join(r[1] for r in records))
      cap=pin(N/(mode+'.actual-host.raw.jsonl'))
      capture_binding=save(mode+'.actual-host.binding.json',dict(source_audit_path=str(audit),source_prefix_size_observed=limit,source_line_offsets=[r[0] for r in records],source_line_bytes=[len(r[1]) for r in records],original_line_sha256=[hashlib.sha256(r[1]).hexdigest() for r in records],original_capture_ref=cap,original_call_id=payload['call_id'],tool_call_timestamp=call[2]['timestamp'],tool_result_timestamp=item['timestamp'],tool_result_chunk_id=value['chunk_id'],actual_outer_exit=value['exit_code'],actual_python_exit=0,actual_native_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
      captures[mode]=dict(ref=cap,binding_ref=capture_binding,call=call[2],output=item,result=value,records=records)
      refs.extend((cap,capture_binding))
   offset+=len(line)
 record('both actual Root build check pairs found',set(captures)=={'build','check'})
 guard,count=m.held_guard(refs,False)
 try:
  before,cp,ow=m.check_before_pair()
  record('actual four Canon equal CP369 baseline',facts['before_canonical_refs']==before)
  m.validate_root_build_request(request,live);qualified=m.validate_live(live)
  caller=m.ensure_caller_source(facts['source_hdf_ref'],facts['source_mf_ref']);rh,rm,rd,decision=m.validate_review(request,caller)
  record('actual Caller6 review bindings in facts',(rh,rm,rd)==(facts['source_review_hdf_ref'],facts['source_review_mf_ref'],facts['source_review_decision_ref']))
  cm=mod(caller[2]['path']);cm.validate_scope(scope);cm.validate_source_review(decision,scope,*caller)
  record('real Scope only frozen two routes no acceptance',scope['routes']==['test.research.fixture','test.retrieval'] and scope['formal_acceptance'] is False and scope['parent_acceptance'] is False and scope['formal_case_accepted_delta']==0)
  # Evaluate only the five dictionary construction expressions, never the builder.
  parsed=ast.parse(Path(h['registrar_ref']['path']).read_text(encoding='utf-8'));builder=next(f for f in parsed.body if isinstance(f,ast.FunctionDef) and f.name=='build_root_docs')
  exprs={target.id:node.value for node in ast.walk(builder) if isinstance(node,ast.Assign) for target in node.targets if isinstance(target,ast.Name) and target.id in {'scope','common','owner_doc','worker_doc','facts'}}
  context=dict(request=request,request_ref=facts['build_request_ref'],decision=decision,decision_ref=rd,caller=caller,refs=before,rh=rh,rm=rm,live=live,scope_ref=facts['scope_ref'],owner_ref=facts['owner_document_ref'],worker_ref=facts['worker_document_ref'])
  actual={'scope':scope,'owner_doc':owner,'worker_doc':worker,'facts':facts}
  for name in ('scope','common','owner_doc','worker_doc','facts'):
   expected=eval(compile(ast.Expression(exprs[name]),h['registrar_ref']['path'],'eval'),m.__dict__,context);context[name]=expected
   if name in actual:record('actual builder exact '+name,expected==actual[name])
  for key in ('scope_ref','owner_document_ref','worker_document_ref'):
   record('actual built bytes '+key,m.encoded(m.load(facts[key]))==Path(facts[key]['path']).read_bytes())
  for archive,old in zip(request['historical_cp369_archives'],before):record('full byte archive '+Path(archive['path']).name,Path(archive['path']).read_bytes()==Path(old['path']).read_bytes())
  record('qualified seed actual 1004 and zero reset',live['next_original_failure_ordinal']==1004 and len(qualified)==38 and facts['source_cutoff']=={'highest_ordinal':965,'next_failure_ordinal':966})
  for mode,bio in bios.items():
   cap=captures[mode];actual=m.extract_original_result_block(cap['output']['payload']['output'])
   record('actual Root host equals saved args result '+mode,actual==bio['result'] and bio['actual_outer_exit']==actual['exit_code']==0 and bio['actual_python_exit']==0 and json.dumps(bio['args']['cmd'],ensure_ascii=False)[1:-1] in cap['call']['payload']['input'])
   record('actual Root call after v4 source acceptance '+mode,m.utc(cap['call']['timestamp'])>m.utc(previous['reviewed_at']) and m.utc(cap['call']['timestamp'])<m.utc(cap['output']['timestamp']))
   expected_ref=fref if mode=='build' else cref
   lines=bio['result']['output'].splitlines();record('actual returned exact output ref '+mode,len(lines)==2 and json.loads(lines[0])==expected_ref and lines[1]=='ROOT_SOURCE_PYTHON_EXIT=0')
   input_ref=facts['build_request_ref'] if mode=='build' else fref
   tokens=["'"+h['registrar_ref']['path']+"' "+mode,"'"+input_ref['path']+"' "+input_ref['sha256']+' '+str(input_ref['bytes']),"'"+facts['live_ref']['path']+"' "+facts['live_ref']['sha256']+' '+str(facts['live_ref']['bytes'])]
   record('actual argv binds mode Source facts seed '+mode,all(t in bio['args']['cmd'] for t in tokens))
   record('no observed Native dispatcher model exit '+mode,all(bio[k] is None for k in ('actual_native_exit','actual_dispatcher_exit','actual_model_exit')))
  for label,g in (('build',bg),('check',cg)):
   record('Root actual '+label+' SourceGuard zero closed',g['verification']=='PASSED' and g['closed'] is True and g['retained_handles_count']==0 and g['errors']==[] and all(e['verified'] and e['final_path_match'] and e['closed'] for e in g['entries']))
  buildpaths={e['path'].casefold() for e in bg['entries']};checkpaths={e['path'].casefold() for e in cg['entries']}
  record('Root build held four canonical baseline inputs',all(p['path'].casefold() in buildpaths for p in before))
  record('Root check excluded only mutable pair and held SS commands',all(p['path'].casefold() not in checkpaths for p in before[:2]) and all(p['path'].casefold() in checkpaths for p in before[2:]))
  record('Root check held actual facts scope owner worker seed',all(r['path'].casefold() in checkpaths for r in (fref,facts['scope_ref'],facts['owner_document_ref'],facts['worker_document_ref'],facts['live_ref'],facts['source_qualification_ref'],h['registrar_ref'],h['root_contract_ref'])))
  record('Root check held seed transitive sources',all(r['path'].casefold() in checkpaths for r in m.embedded_refs(q) if r['path'].casefold() not in {x['path'].casefold() for x in before[:2]}))
  proposed=m.transformed_pair(copy.deepcopy(cp),copy.deepcopy(ow),facts,live,cp,ow,fref)
  proposed_refs=[dict(path=str(path),sha256=hashlib.sha256(m.encoded(value)).hexdigest(),bytes=len(m.encoded(value))) for path,value in zip(m.CANON[:2],proposed)]
  record('independent pure output exact Root check proposed byte refs',proposed_refs==check['proposed_after_refs'],proposed_refs)
  cp2,ow2=proposed
  record('full inverse old963 records workers pending preserved',cp2['failure_counters'][:963]==cp['failure_counters'] and cp2['workers'][:-1]==cp['workers'] and cp2['work_in_progress']['later_diagnostics_observed_after_cutoff'][:4]==cp['work_in_progress']['later_diagnostics_observed_after_cutoff'])
  record('unique real Owner Worker current Caller6 lease',len(cp2['workers'])==len(cp['workers'])+1 and len([r for r in cp2['workers'] if r.get('slice_id')==m.SLICE])==1 and ow2['card_path_bindings']['W09-99']['subtasks'][m.KEY]['owner_document_ref']==facts['owner_document_ref'])
  cm.validate_canon_lease(cp2,ow2,scope,facts['scope_ref'],caller[0],rd,facts['owner_document_ref'],facts['worker_document_ref'],owner,worker,Path(scope['authorized_output_root'])/'independent-lease-check')
  record('actual check never committed transaction',check['mode']=='check' and check['transaction'] is None and check['complete_inverse'] is True and check['prior_failure_records_preserved']==963 and check['later_originals_registered']==38 and check['source_guard_ref_count']==len(cg['entries']))
  projected=[{k:r[k] for k in ('ordinal','origin_ref','description')} for r in pending['pending']]
  record('Root latest pending adds exactly original1004',len(projected)==39 and projected[:-1]==live['pending'] and projected[-1]['ordinal']==1004)
  future=copy.deepcopy(live);future['next_original_failure_ordinal']=1005;future['pending']=projected
  future_q=copy.deepcopy(qualified)
  for row in future_q.values():row['exit_qualification']['diagnostic_source_ref']=pending_ref
  future_q[1004]=copy.deepcopy(pending['pending'][-1])
  m.validate_qualification_continuity(live,qualified,future,future_q)
  record('future1005 append continuity only remains legal',True,'Pure memory continuity only. No future qualification/witness artifact exists or is claimed here.')
  record('old NULL typed exits retained',all(future_q[k]['actual_native_exit']==qualified[k]['actual_native_exit'] and future_q[k]['actual_outer_exit']==qualified[k]['actual_outer_exit'] for k in qualified))
  record('original1004 Root failure preserves observed outer Python1',pending['pending'][-1]['actual_outer_exit']==1 and pending['pending'][-1]['actual_python_exit']==1)
  record('four current Canon unchanged after review',[pin(p) for p in m.CANON]==before)
  for ref in refs:record('final held pin '+Path(ref['path']).name,pin(ref['path'])==ref)
  with audit.open('rb') as file:
   for mode,cap in captures.items():
    for offset,raw in cap['records']:file.seek(offset);record('final actual audit range '+mode,file.read(len(raw))==raw)
 finally:
  cleanup=guard.close();gr=save('sourceguard.closed.json',cleanup)
 record('independent SourceGuard closed zero',cleanup['closed'] and cleanup['retained_handles_count']==0 and cleanup['errors']==[])
 controls=save('independent-controls.json',dict(checks=checks,count=len(checks),guard_refs=count,actual_registrar_entrypoint_executed=False,actual_Native_or_dispatcher_executed=False,pure_actual_fact_transform_refs=proposed_refs))
 findings=save('findings.json',dict(blocking_findings=[],actual_prepared_facts_verified=True,current_Canon='CP369/OW173 unchanged',future_qualification1005_created=False,scope='Source acceptance of actual prepared facts and read-only check; no activation/formal/parent acceptance.'))
 decision=dict(schema='researchos.w09-cp370-registrar-independent-source-decision.v1',decision='ACCEPTED_SOURCE_ONLY',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=m.AUTHOR,source_hdf_ref=pin(S/'HDF.json'),source_mf_ref=h['manifest_ref'],registrar_ref=h['registrar_ref'],root_contract_ref=h['root_contract_ref'],root_facts_ref=fref,root_seed_live_ref=facts['live_ref'],root_check_ref=cref,reviewed_at=datetime.now(timezone.utc).isoformat(),blocking_findings=0,findings_ref=findings,checks_ref=controls,source_guard_ref=gr,actual_registration=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,Main_or_Canon_written=False,Native_or_dispatcher_executed=False,new_original_failures=[],Root_next_original_observed_before_review=1005,SourceAcceptedonly=True,noactualorformal=True)
 dr=save('source-decision.json',decision)
 om=save('MF.json',dict(schema='researchos.cp370-registrar-independent-review-manifest.v1',source_hdf_ref=decision['source_hdf_ref'],source_mf_ref=decision['source_mf_ref'],root_facts_ref=fref,root_seed_live_ref=facts['live_ref'],members=[pin(__file__),controls,findings,gr,dr,*[cap[k] for cap in captures.values() for k in ('ref','binding_ref')]]))
 oh=save('HDF.json',dict(schema='researchos.cp370-registrar-independent-review-handoff.v1',decision=decision['decision'],actor_id=decision['actor_id'],actor_role=decision['actor_role'],manifest_ref=om,source_decision_ref=dr,source_hdf_ref=decision['source_hdf_ref'],source_mf_ref=decision['source_mf_ref'],registrar_ref=h['registrar_ref'],root_contract_ref=h['root_contract_ref'],root_facts_ref=fref,root_seed_live_ref=facts['live_ref'],guard_ref_count=count,guard_closed=True,retained_handles_count=0,checks=len(checks),blocking_findings=0,Main_or_Canon_written=False,build_check_activate_executed=False,STOP=True,FINAL=True))
 for ref in (oh,om,dr,*refs):assert pin(ref['path'])==ref
 print(json.dumps(dict(HDF=oh,MF=om,decision=dr,checks=len(checks),guard_refs=count),ensure_ascii=False))

if __name__=='__main__':main()
