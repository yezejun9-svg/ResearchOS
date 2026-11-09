"""Bounded v4 delta review with both real Root host envelopes; no registrar command runs."""
import ast
import copy
from datetime import datetime,timezone,timedelta
import hashlib
import json
from pathlib import Path
import types

N=Path(__file__).resolve().parent
W=N.parent.parent
S=W/'checkpoint_r370_c19_dispatcher_source_codex/cp370proposal-20261009-v4'
PREV=W/'cp370_registrar_v3_independent_review_codex/regr3-01a120ab'
CALLER=W/'w09_main_c19_dispatcher_caller_source_codex/c19call-01a12d10-v6'
CR=W/'main_c19_dispatcher_caller_independent_review_codex/c19v6-review-20261009'
checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,x):
 with (N/name).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def mod(p):
 m=types.ModuleType('review_'+Path(p).stem);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def record(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok:raise AssertionError(name)
def reject(name,fn,expected):
 try:fn()
 except ValueError as e:record(name,str(e)==expected,str(e))
 else:record(name,False,'BAD_INPUT_ACCEPTED')
def treefuncs(p):return {f.name:ast.dump(f,include_attributes=False) for f in ast.parse(Path(p).read_text(encoding='utf-8')).body if isinstance(f,ast.FunctionDef)}

def main():
 hr=pin(S/'HDF.json');mr=pin(S/'MF.json')
 record('supplied HDF pin',(hr['sha256'],hr['bytes'])==('36b3f37527ccba3c64c4e55d723e34735c4a93214342210d498c7dee64ed824e',2760))
 record('supplied MF pin',(mr['sha256'],mr['bytes'])==('f0ca65b9f3ed8510d156cefbfc0a65ff89c755395bc681cb679ca52c11edf570',7286))
 h=read(hr['path']);manifest=read(mr['path']);sr=h['registrar_ref'];m=mod(sr['path'])
 record('supplied registrar pin',(sr['sha256'],sr['bytes'])==('d3a824904bc171bea8db5d9d2dcf64bd0577ecb0a8c2cf53471cd31cf325f95c',59180) and pin(sr['path'])==sr)
 record('supplied contract pin',(h['root_contract_ref']['sha256'],h['root_contract_ref']['bytes'])==('4ca3b198b132c5798993012ff56633038750f2bffa954c0290fde2fd0c36ace3',7290))
 refs=[hr,mr,pin(__file__),*manifest['members'],pin(PREV/'HDF.json'),pin(PREV/'MF.json')]
 refs.extend({k:e[k] for k in ('path','sha256','bytes')} for e in read(h['guard_cleanup_ref']['path'])['entries'])
 for path in (PREV/'HDF.json',PREV/'MF.json',CALLER/'HDF.json',CR/'HDF.json'):
  refs.append(pin(path));refs.extend(m.embedded_refs(read(path)))
 seeds={}
 for number in (996,1004):
  wr=manifest['seed'+str(number)+'_witness_ref'];w=read(wr['path']);q=read(w['qualification_ref']['path']);pending=read(q['source_pending_ref']['path'])
  refs.extend([wr,*m.embedded_refs(w),*m.embedded_refs(q),*m.embedded_refs(pending)])
  live=dict(schema='researchos.root-cp370-source-live-context.v2',issued_by=m.ROOT,root_thread_id=m.ROOT_THREAD_ID,created_utc=datetime.now(timezone.utc).isoformat(),source_cutoff=q['source_cutoff'],next_original_failure_ordinal=number,pending=[{k:r[k] for k in ('ordinal','origin_ref','description')} for r in pending['pending']],qualification_ref=w['qualification_ref'],seed_witness_ref=wr)
  seeds[number]=(live,w,q)
 guard,count=m.held_guard(refs,False)
 try:
  for ref in manifest['members']:record('manifest pin '+Path(ref['path']).name,pin(ref['path'])==ref)
  ph=read(h['prior_source_hdf_ref']['path']);old=treefuncs(ph['registrar_ref']['path']);new=treefuncs(sr['path'])
  record('only observed envelope handling changed',{k for k in old if new.get(k)!=old[k]}=={'validate_root_witness'} and set(new)-set(old)=={'extract_original_result_block'})
  for name in ('validate_observed_result','validate_postseal_host_provenance','validate_activation_context','validate_qualification_continuity','held_guard','transformed_pair','register','build_root_docs'):
   record('v3 accepted boundary AST unchanged '+name,new[name]==old[name])
  prior_decision=read(read(PREV/'HDF.json')['source_decision_ref']['path'])
  record('v3 independent acceptance exact base',prior_decision['decision']=='ACCEPTED_SOURCE_ONLY' and prior_decision['registrar_ref']==ph['registrar_ref'] and prior_decision['actor_id']=='codex:/root/attach_fixture_source_review')
  before,cp,ow=m.check_before_pair();qualified={};blocks_by={}
  for number,(live,w,q) in seeds.items():
   qualified[number]=m.validate_live(live)
   raw=Path(w['actual_host_capture_ref']['path']).read_bytes()
   records=[json.loads(line) for line in raw.splitlines()];blocks=records[2]['payload']['output'];blocks_by[number]=blocks
   original=read(w['original_tool_io_ref']['path'])
   got=m.extract_original_result_block(blocks)
   record('real Seed'+str(number)+' exact actual result extraction',got==original['result'] and len(blocks)==(3 if number==996 else 2))
   record('real Seed'+str(number)+' full witness qualification',len(qualified[number])==number-966)
  m.validate_qualification_continuity(seeds[996][0],qualified[996],seeds[1004][0],qualified[1004])
  record('real 996 to 1004 appended eight originals preserve immutable prior events',True)
  two=blocks_by[1004];three=blocks_by[996]
  for label,blocks,code in (
    ('one block',[two[-1]],'HOST_OUTPUT_NOT_PLAINTEXT'),
    ('two result blocks',[two[0],two[-1],two[-1]],'HOST_OUTPUT_MULTIPLE_RESULTS'),
    ('missing terminal result',[two[0],dict(type='input_text',text='{}')],'HOST_OUTPUT_FINAL_RESULT_REQUIRED'),
    ('wrong terminal type',[two[0],dict(type='input_text',text='[]')],'HOST_OUTPUT_FINAL_RESULT_REQUIRED'),
    ('non JSON terminal',[two[0],dict(type='input_text',text='not-json')],'HOST_OUTPUT_FINAL_RESULT_REQUIRED'),
    ('four blocks',[three[0],three[1],three[1],three[2]],'HOST_OUTPUT_NOT_PLAINTEXT'),
    ('misplaced result',[two[-1],two[0]],'HOST_OUTPUT_METADATA_INVALID')):
   reject('v4 rejects '+label,lambda blocks=blocks:m.extract_original_result_block(blocks),code)
  live,w,q=seeds[1004];origload=m.load;original=read(w['original_tool_io_ref']['path'])
  changed=copy.deepcopy(original);changed['result']['chunk_id']='SYNTHETIC_CHANGED_CHUNK'
  m.load=lambda ref:copy.deepcopy(changed) if ref==w['original_tool_io_ref'] else origload(ref)
  try:reject('v4 unique terminal result must equal original IO',lambda:m.validate_root_witness(live['seed_witness_ref'],live,'SEED'),'HOST_ORIGINAL_TOOL_IO_MISMATCH')
  finally:m.load=origload
  changed=copy.deepcopy(original);changed['args']['cmd']='SYNTHETIC_UNRELATED_COMMAND_NOT_EXECUTED'
  m.load=lambda ref:copy.deepcopy(changed) if ref==w['original_tool_io_ref'] else origload(ref)
  try:reject('new real seed preserves actual argument binding',lambda:m.validate_root_witness(live['seed_witness_ref'],live,'SEED'),'HOST_CALL_ARGUMENTS_NOT_BOUND')
  finally:m.load=origload
  actual_observed=json.loads(original['result']['output'].splitlines()[0])
  reject('new real seed qualification stdout binding',lambda:m.validate_observed_result(actual_observed,dict(live,qualification_ref=dict(live['qualification_ref'],sha256='0'*64)),q['source_pending_ref'],w,0,'ROOT_SOURCE_PYTHON_EXIT=0'),'HOST_STDOUT_QUALIFICATION_NOT_BOUND')
  binding=read(w['capture_binding_ref']['path'])
  reject('new seed cannot replay its call as postreview activation',lambda:m.validate_postseal_host_provenance(binding,binding,datetime.now(timezone.utc).isoformat(),w['actual_host_capture_ref'],w['actual_host_capture_ref']),'POSTSEAL_REQUIRES_NEW_HOST_CALL_AFTER_REVIEW')
  altered=copy.deepcopy(qualified[1004]);altered[967]['actual_outer_exit']=0
  reject('actual 1004 continuity preserves original 967 failure',lambda:m.validate_qualification_continuity(seeds[996][0],qualified[996],live,altered),'SOURCE_ORIGINALS_CHANGED_AFTER_SEAL')
  nested=[*refs,*m.embedded_refs(w),*m.embedded_refs(q)]
  pg,pc=m.held_guard(nested,True);closed=pg.close();pgr=save('sourceguard.pair-excluded.closed.json',closed)
  paths={e['path'].casefold() for e in closed['entries']}
  record('all nested sources held except exclusive Canon pair',all(r['path'].casefold() in paths for r in nested if r['path'].casefold() not in {str(p).casefold() for p in m.CANON[:2]}) and all(str(p).casefold() not in paths for p in m.CANON[:2]))
  record('pair-excluded finite guard closed',closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[])
  caller=m.ensure_caller_source(pin(CALLER/'HDF.json'),pin(CALLER/'MF.json'));crh=read(CR/'HDF.json')
  request=dict(review_hdf_ref=pin(CR/'HDF.json'),review_mf_ref=crh['manifest_ref'],review_decision_ref=crh['source_decision_ref'])
  rh,rm,rd,decision=m.validate_review(request,caller)
  output=str((N/'synthetic-output-not-created').resolve());ch=read(CALLER/'HDF.json')
  request.update(frozen_plan_ref=ch['frozen_plan_ref'],native_hdf_ref=ch['native_qualified_hdf_ref'],native_handoff_ref=ch['native_handoff_ref'],native_historical_request_ref=sr,authorized_output_root=output)
  tree=ast.parse(Path(sr['path']).read_text(encoding='utf-8'));builder=next(f for f in tree.body if isinstance(f,ast.FunctionDef) and f.name=='build_root_docs')
  expression=next(f.value for f in builder.body if isinstance(f,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='scope' for t in f.targets))
  scope=eval(compile(ast.Expression(expression),sr['path'],'eval'),m.__dict__,dict(request=request,decision=decision,decision_ref=rd,caller=caller,refs=before))
  fake=lambda name:dict(path=str(N/name),sha256='0'*64,bytes=0)
  sf,orr,wr,fr=[fake(s) for s in ('synthetic.scope','synthetic.owner','synthetic.worker','synthetic.facts')]
  common=dict(step_id='W09-99',slice_id=m.SLICE,state=m.STATE,scope_ref=sf,output_root=output,routes=m.ROUTES,lease_status='ACTIVE',lease_expires_at=(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat())
  owner=dict(common,owner_id=m.ROOT,selected_worker_id=m.ROOT);worker=dict(common,worker_id=m.ROOT,selected_owner_ref=orr)
  facts=dict(scope_ref=sf,owner_document_ref=orr,worker_document_ref=wr,source_hdf_ref=caller[0],source_review_decision_ref=rd)
  synthetic={sf['path']:scope,orr['path']:owner,wr['path']:worker};m.load=lambda ref:copy.deepcopy(synthetic[ref['path']]) if ref['path'] in synthetic else origload(ref)
  try:
   cp2,ow2=m.transformed_pair(copy.deepcopy(cp),copy.deepcopy(ow),facts,live,cp,ow,fr)
   record('real Seed1004 pure complete inverse actual Caller6 lease',cp2['revision']==370 and ow2['revision']==174 and len(cp2['failure_counters'])==1001)
   record('all previous workers failure prefix four pending preserved',cp2['workers'][:-1]==cp['workers'] and cp2['failure_counters'][:963]==cp['failure_counters'] and cp2['work_in_progress']['later_diagnostics_observed_after_cutoff'][:4]==cp['work_in_progress']['later_diagnostics_observed_after_cutoff'])
   record('single Owner Worker two routes no formal delta',len(cp2['workers'])==len(cp['workers'])+1 and scope['routes']==m.ROUTES and scope['formal_acceptance'] is False and scope['parent_acceptance'] is False and scope['formal_case_accepted_delta']==0)
  finally:m.load=origload
  record('four actual Canon unchanged',[pin(p) for p in m.CANON]==before)
  for ref in refs:record('final pin '+Path(ref['path']).name,pin(ref['path'])==ref)
 finally:
  cleanup=guard.close();gr=save('sourceguard.closed.json',cleanup)
 record('review guard closed zero',cleanup['closed'] and cleanup['retained_handles_count']==0 and cleanup['errors']==[])
 controls=save('independent-controls.json',dict(checks=checks,count=len(checks),guard_refs=count,pair_guard_refs=pc,SyntheticNonAuthoritative=True,registrar_entrypoints_executed=False))
 findings=save('findings.json',dict(blocking_findings=[],delta='Only real 2/3 block unique terminal result support; preserved v3 acceptance boundary by exact AST and real Seed1004 pure validator/transform regression.',real_seed1004_ref=manifest['seed1004_witness_ref'],actual_build_facts_reviewed=False))
 decision=dict(schema='researchos.w09-cp370-registrar-independent-source-decision.v1',decision='ACCEPTED_SOURCE_ONLY',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=m.AUTHOR,source_hdf_ref=hr,source_mf_ref=mr,registrar_ref=sr,root_contract_ref=h['root_contract_ref'],reviewed_at=datetime.now(timezone.utc).isoformat(),blocking_findings=0,findings_ref=findings,checks_ref=controls,source_guard_ref=gr,pair_guard_ref=pgr,actual_registration=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,Main_or_Canon_written=False,Native_or_dispatcher_executed=False,new_original_failures=[],Root_next_original_observed_before_review=1005,SourceAcceptedonly=True,noactualorformal=True,real_seed1004_ref=manifest['seed1004_witness_ref'])
 dr=save('source-decision.json',decision)
 outmf=save('MF.json',dict(schema='researchos.cp370-registrar-independent-review-manifest.v1',source_hdf_ref=hr,source_mf_ref=mr,members=[pin(__file__),controls,findings,gr,pgr,dr]))
 outhdf=save('HDF.json',dict(schema='researchos.cp370-registrar-independent-review-handoff.v1',decision=decision['decision'],actor_id=decision['actor_id'],actor_role=decision['actor_role'],manifest_ref=outmf,source_decision_ref=dr,source_hdf_ref=hr,source_mf_ref=mr,registrar_ref=sr,root_contract_ref=h['root_contract_ref'],guard_ref_count=count,pair_guard_ref_count=pc,guard_closed=True,retained_handles_count=0,blocking_findings=0,checks=len(checks),Main_or_Canon_written=False,build_check_activate_executed=False,STOP=True,FINAL=True))
 for ref in (outhdf,outmf,dr,*refs):assert pin(ref['path'])==ref
 print(json.dumps(dict(HDF=outhdf,MF=outmf,decision=dr,checks=len(checks),guard_refs=count,pair_guard_refs=pc),ensure_ascii=False))

if __name__=='__main__':main()
