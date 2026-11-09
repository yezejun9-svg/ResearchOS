"""Finite independent v4 Source review; no operational entrypoint executes."""
import ast
import copy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import types
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
S=B/'public22_root_caller_registration_source_codex/p22root-20261009-04'
ACTOR='codex:/root/attach_fixture_source_review'
checks=[]
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,x):
 with (N/name).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
def mod(p):
 m=types.ModuleType('source_review_'+Path(p).stem);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok:raise AssertionError(name)
def reject(name,call,code):
 try:call()
 except ValueError as e:check(name,str(e)==code,str(e));return dict(type=type(e).__name__,message=str(e))
 else:check(name,False,'unexpected acceptance')
def main():
 h=read(S/'HDF.json');mf=read(h['manifest_ref']['path']);inputs=read(h['source_inputs_ref']['path'])
 c=mod(h['caller_ref']['path']);g=mod(h['registrar_ref']['path']);leaf=read(h['runner_review_ref']['path'])
 source=c.resolve_runner_source_hdf(leaf,leaf['runner_ref'],leaf['contract_ref'])
 leafinputs=c.doc(source['source_inputs_ref']);leafmf=c.doc(source['manifest_ref']);contract=c.doc(leaf['contract_ref'])
 references=[pin(__file__),pin(S/'HDF.json'),h['manifest_ref'],*mf['members'],*inputs['references'],leaf['source_hdf_ref'],source['source_inputs_ref'],source['manifest_ref'],*leafmf['members'],*leafinputs['references']]
 references.extend(pin(p) for p in N.glob('guarded-read-*.json'))
 normalized={}
 for ref in references:
  actual=pin(ref['path']);check('pinned input '+Path(ref['path']).name,c.same_ref(actual,ref));normalized[c.regular_path(actual['path'])]=actual
 heldrefs=list(normalized.values());guardmod=mod(g.GUARD);guard=guardmod.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
 guard.acquire(heldrefs)
 try:
  check('exact handed Source HDF',(pin(S/'HDF.json')['sha256'],pin(S/'HDF.json')['bytes'])==('0d275d0ce81848864089114931f2e0e89bd6475c57dae063ec73912d2ed0096a',6434))
  check('exact handed MF',(h['manifest_ref']['sha256'],h['manifest_ref']['bytes'])==('7f8b0e570881816b8ac9521c62d5667b3210ded24f1c6ff971a4d21d4857d869',3251))
  before,cp,ow=g.before();check('9members56pins56sourcecontrols',len(mf['members'])==9 and len(inputs['references'])==56 and read(h['source_controls_ref']['path'])['pass']==56)
  live=g.pending(h['repair_pending_ref']);base=g.pending(dict(path=str(g.BASE_PENDING[0]),sha256=g.BASE_PENDING[1],bytes=g.BASE_PENDING[2]))
  check('immutable first8 plus real1013to1017',live['pending'][:8]==base['pending'] and [x['ordinal'] for x in live['pending'][8:]]==list(range(1013,1018)))
  check('real leaf review to source HDF to549inputs',len(leafinputs['references'])==549 and source==c.doc(leaf['source_hdf_ref']))
  reject('wrong review used as source HDF',lambda:c.resolve_runner_source_hdf(dict(leaf,source_hdf_ref=h['runner_review_ref']),leaf['runner_ref'],leaf['contract_ref']),'RUNNER_SOURCE_HDF_BINDING')
  reject('wrong runner ref',lambda:c.resolve_runner_source_hdf(leaf,leaf['contract_ref'],leaf['contract_ref']),'RUNNER_SOURCE_HDF_BINDING')
  for name,ref in [('guard',contract['source_guard']),('job',contract['owned_job']),('leafmanifest',source['manifest_ref']),('leafinputs',source['source_inputs_ref'])]:
   snapshot=copy.deepcopy(ref)
   check('foreign slash preserved accepted '+name,len(c.checked(ref))==ref['bytes'] and g.exact(ref)==ref and snapshot==ref)
   reject('sha mismatch '+name,lambda ref=ref:c.checked(dict(ref,sha256='0'*64)),'REF_CHANGED')
   reject('bytes mismatch '+name,lambda ref=ref:g.exact(dict(ref,bytes=ref['bytes']+1)),'REF_CHANGED')
  for name,value,code in [('traversal','D:/x/../y','REF_REGULAR_PATH'),('ads','D:/x:stream','REF_LOCAL_PATH'),('device','D:/CON','REF_REGULAR_PATH')]:
   reject(name,lambda value=value:c.regular_path(value),code)
  check('loader actual foreign guard/job import',hasattr(c.module(contract['source_guard'],'guard_import'),'SourceReadGuard') and hasattr(c.module(contract['owned_job'],'job_import'),'runtime_resource_paths'))
  unique=c.unique_refs([*leafinputs['references'],*leafmf['members'],contract['source_guard'],contract['owned_job']])
  check('affected runtime source refs validate',len(unique)>500)
  alias=lambda r:dict(r,path=r['path'].replace('\\','/'))
  excluded=g.held_without_canonical_pair([*before,alias(before[0]),alias(before[2])],before[:2])
  check('guard excludes pair dedups source path aliases',len(excluded)==2 and {Path(r['path']) for r in excluded}==set(g.CANON[2:]))
  synth=lambda n:dict(path='D:/Synthetic/'+n,sha256=n*64,bytes=1)
  sr,orr,wr=synth('1'),synth('2'),synth('3');out='D:/Synthetic/schema22-public-'+'a'*32
  common=dict(step_id='W05-99',slice_id=g.SLICE,state=g.STATE,scope_ref=sr,output_root=out,owner=g.ROOT,lease_status='ACTIVE',lease_expires_at='2099-01-01T00:00:00Z')
  docs={sr['sha256']:dict(output_root=out),orr['sha256']:dict(common,owner_id=g.ROOT,selected_worker_id=g.ROOT),wr['sha256']:dict(common,worker_id=g.ROOT,selected_owner_ref=orr)}
  facts=dict(before_canonical_refs=before,scope_ref=sr,owner_ref=orr,worker_ref=wr,source_hdf_ref=synth('4'),review_decision_ref=synth('5'),created_utc='2026-10-09T00:00:00Z')
  oldread,oldpin=g.read,g.pin;attempted=[]
  def denied(p):
   if Path(p) in g.CANON[:2]:attempted.append(str(p));raise PermissionError('SIMULATED_EXCLUSIVE_CANON')
   return oldpin(p)
  try:
   g.read=lambda r:copy.deepcopy(docs[r['sha256']]);g.pin=denied
   a,b=g.transform(cp,ow,facts,synth('6'),live,before,cp,ow)
   reject('exclusive callback rejects changed passed CP',lambda:g.transform(dict(cp,revision=369),ow,facts,synth('6'),live,before,cp,ow),'OWNER_WORKER_ACYCLIC')
   reject('exclusive callback rejects changed expected vector',lambda:g.transform(cp,ow,facts,synth('6'),live,[],cp,ow),'OWNER_WORKER_ACYCLIC')
  finally:g.read,g.pin=oldread,oldpin
  check('exclusive-boundary pure transform no Canon reopen',not attempted)
  check('complete old1002prefix exact append13',a['failure_counters'][:1002]==cp['failure_counters'] and len(a['failure_counters'])==1015 and a['work_in_progress']['root_next_failure_ordinal_live']==1018)
  inversecp=copy.deepcopy(a);inverseow=copy.deepcopy(b)
  for key in ('failure_counters','workers','work_in_progress','revision','expected_previous_revision','updated_at','updated_by','note'):inversecp[key]=copy.deepcopy(cp[key])
  del inverseow['card_path_bindings']['W05-99']['subtasks'][g.KEY]
  for key in ('revision','updated_at','updated_by'):inverseow[key]=copy.deepcopy(ow[key])
  check('independent full inverse byte equality',g.encoded(inversecp)==g.encoded(cp) and g.encoded(inverseow)==g.encoded(ow))
  # Bounded pending negative: only replace the content loader for one actual
  # capture binding, leaving reference/byte validation and all other rows real.
  row=next(r for r in live['pending'][8:] if r['capture_binding_ref'] is not None)
  bindingref=row['capture_binding_ref'];original=g.read
  try:
   g.read=lambda r:dict(actual_capture_ref=h['source_inputs_ref']) if r==bindingref else original(r)
   reject('wrong actual_capture_ref rejects',lambda:g.pending(h['repair_pending_ref']),'ORIGINAL_CAPTURE_BINDING')
   g.read=lambda r:{} if r==bindingref else original(r)
   reject('missing actual original capture key rejects',lambda:g.pending(h['repair_pending_ref']),'ORIGINAL_CAPTURE_BINDING')
  finally:g.read=original
  callertext=Path(h['caller_ref']['path']).read_text();regtext=Path(h['registrar_ref']['path']).read_text()
  check('callback uses preloaded before documents','refs,old_cp,old_ow),N,\'activate\')' in regtext)
  check('Source HDF inputs in held chain',"runner_review['source_hdf_ref'],runner_source_hdf['manifest_ref']" in callertext and "runner_ref,contract_ref,runner_source_hdf['source_inputs_ref']" in callertext)
  oldsource=read(h['superseded_v3_hdf_ref']['path'])
  oldcaller=Path(oldsource['caller_ref']['path']).read_text()
  check('exact single caller repair relative to independently reviewed v3',callertext==oldcaller.replace("pin(V/'../project_identity.json')","pin(R/'execution/project_identity.json')"))
  check('registrar unchanged from reviewed v3',(h['registrar_ref']['sha256'],h['registrar_ref']['bytes'])==(oldsource['registrar_ref']['sha256'],oldsource['registrar_ref']['bytes']))
  tree=ast.parse(callertext);execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execute')
  calls=[n for n in ast.walk(execute) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='pin' and len(n.args)==1 and 'project_identity.json' in ast.unparse(n.args[0])]
  check('one internal identity call',len(calls)==1)
  internal=eval(compile(ast.Expression(calls[0].args[0]),'<finite_actual_identity_expression>','eval'),c.__dict__)
  identity=c.pin(internal)
  check('actual identity expression now accepts exact real file',identity==pin(R/'execution/project_identity.json') and any(c.same_ref(identity,r) for r in inputs['references']))
  reject('external traversal remains rejected',lambda:c.pin(c.V/'../project_identity.json'),'REF_REGULAR_PATH')
  # Review executable dispatch shape without calling its entrypoints.
  rt=ast.parse(regtext);main=next(n for n in rt.body if isinstance(n,ast.If) and '__name__' in ast.unparse(n.test))
  check('registrar main binds mode and exact3key refs',"len(sys.argv) == 8" in ast.unparse(main) and "build(first) if mode == 'build' else register(mode, first, live)" in ast.unparse(main))
  check('registrar mode rejects extra action',"mode in ('check', 'activate')" in ast.unparse(next(n for n in rt.body if isinstance(n,ast.FunctionDef) and n.name=='register')))
  build=ast.unparse(next(n for n in rt.body if isinstance(n,ast.FunctionDef) and n.name=='build'))
  check('build scope then owner then worker no cycle',build.index("save('scope-registration.root.json'")<build.index("save('owner-document.root.json'")<build.index("save('worker-document.root.json'"))
  check('Root review witness and after-review live mandatory',all(s in regtext for s in ('ROOT_EXTERNAL_REVIEW_HOSTPAIR','ROOT_POSTREVIEW_LIVE_REFRESH','ACTIVATION_REQUIRES_FRESH_ROOT_LIVE','ACTIVATION_WITNESS_NOT_BOUND')))
  check('per phase live lease precedes phase advance',c.PHASES==('prepare','bootstrap22','keygen22','backup22','verify22') and ast.unparse(ast.parse(callertext)).index('self._fresh()')>=0)
  reject('end23 blocked',lambda:c.LiveScope(None,None,None,None,None,None,None,{}).qualified_current_main23(),'MAIN23_NOT_QUALIFIED_FOR_THIS_END22_SCOPE')
  reject('unheld live capability blocked',lambda:c.LiveScope(None,None,None,None,None,None,None,{})._fresh(),'ROOT_HELD_CLOSURE_RELEASED')
  check('run failure retains outside caller receipt and no retry',"'runner-returned-state.root.json'" in callertext and "'last_child_exit':None" in callertext and 'runner.run_registered_case(contract_ref,case_ref,live)' in callertext)
  check('repaired original three P1 do not change acceptance scope',c.PHASES==('prepare','bootstrap22','keygen22','backup22','verify22') and h['formal_acceptance'] is False)
  check('current4 unchanged',g.before()[0]==before)
  for ref in heldrefs:check('still pinned '+Path(ref['path']).name,pin(ref['path'])==ref)
 finally:closed=guard.close()
 check('real guard closed0',closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[])
 gr=save('sourceguard.closed.json',closed);cr=save('independent-controls.json',dict(checks=checks,count=len(checks),pass_count=len(checks),scope='FINITE_SOURCE_ONLY_WITH_MODELED_EXCLUSIVE_CALLBACK',actual_Canon_exclusive_open=False,product_calls=0))
 fr=save('findings.json',dict(decision='ACCEPTED_SOURCE_ONLY',resolved_previous_findings=['P22-01','P22-02','P22-03','P22-V3-01'],blocking_source_findings=[],new_original_failures=[]))
 common=dict(actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=g.AUTHOR,decision='ACCEPTED_SOURCE_ONLY',reviewed_utc=datetime.now(timezone.utc).isoformat(),source_hdf_ref=pin(S/'HDF.json'),source_mf_ref=h['manifest_ref'],caller_ref=h['caller_ref'],registrar_ref=h['registrar_ref'],formal_acceptance=False,execution_grant=False,parent_acceptance=False)
 dr=save('source-decision.json',dict(common,findings_ref=fr,review_controls_ref=cr,source_guard_ref=gr,held_read_refs=len(heldrefs),current_canonical_refs=before,Source_input_pending_cutoff=1018,Root_next_observed_from_parent=1020,later_Root_originals_not_yet_bound_in_review=[1018,1019],new_original_failures=[],Main_Canon_changes=0,Native_SQLite_dispatcher_model_calls=0,Root_actual_registration_required=True,Root_fresh_external_review_witness_required=True))
 mr=save('MF.json',dict(members=[pin(S/'HDF.json'),h['manifest_ref'],dr,fr,cr,gr,pin(__file__)],source_input_refs=heldrefs,excludes=['HDF.json','MF.json']))
 hr=save('HDF.json',dict(common,manifest_ref=mr,source_decision_ref=dr,findings_ref=fr,review_controls_ref=cr,source_guard_ref=gr,blocking_source_findings=0,held_read_refs=len(heldrefs),guard_closed=True,product_processes_executed=0,Root_actual_registration=False,STOP=True,FINAL=True))
 print(json.dumps(dict(HDF=hr,MF=mr,decision=dr,findings=fr,checks=len(checks),held=len(heldrefs)),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
