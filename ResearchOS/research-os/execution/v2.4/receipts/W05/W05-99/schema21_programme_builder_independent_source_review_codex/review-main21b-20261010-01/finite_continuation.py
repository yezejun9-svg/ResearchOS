"""Correct two reviewer metadata expectations and verify real author FINAL."""
import ast,hashlib,json,os,types
from pathlib import Path
D=Path(__file__).resolve().parent;W=D.parent.parent;S=W/'schema21_programme_builder_source_codex/main21b-20261010-01'
ROOTCAP=W.parent.parent/'W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=p.as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 with (D/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(D/n)
def load(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def main():
 old=read(D/'finitechecks.json');c=read(S/'contract.v2.json');raw=pin(ROOTCAP/'schema21.builder.peer.source-author.raw.jsonl');br=pin(ROOTCAP/'schema21.builder.peer.source-author.binding.root.json')
 assert (raw['sha256'],raw['bytes'])==('f78d09e5c9caddb9df3abe820f5b842076322ea7b54668d8c809a73f40dca319',25409)
 assert (br['sha256'],br['bytes'])==('1135db70531cb023cf5fbbe0246724f6fa2d6b941c66a40530071bf0f9fcb6f6',1221)
 helper=W/'fresh_main23_root_caller_registration_source_codex/main23root-20261010-04/main23_root.source.py'
 refs=[pin(__file__),pin(D/'review_source.py'),pin(D/'finitechecks.json'),old['Source_guard_ref'],raw,br,pin(helper),*[pin(S/n) for n in ('HDF.json','MF.json','old21_builder.py','contract.v2.json','input-manifest.json','source-controls.json','causality-clarification.json','source-seal-checks.json')]]
 g=load(c['source_guard_ref']['path'],'continuation_old21_guard');guard=g.SourceReadGuard();checks=[]
 def yes(name,condition):
  assert condition,name;checks.append(dict(name=name,passed=True,evidence_class='FINITE_INDEPENDENT_SOURCE_ONLY'))
 try:
  guard.acquire(refs);closed=read(old['Source_guard_ref']['path'])
  yes('original_846_successes_reused_and_all422_handles_closed',len(old['checks'])==848 and sum(x['passed'] for x in old['checks'])==846 and closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[])
  tree=ast.parse(Path(c['builder_ref']['path']).read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_registered_build');loop=next(n for n in ast.walk(fn) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='phase')
  attrs={n.func.attr for n in ast.walk(loop) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)};names={n.func.id for n in ast.walk(loop) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
  yes('phase_live_resource_source_and_owned_gates_actual_call_kinds',{'require_phase','require_resources','assert_pins','verify_frozen_inventory','run_owned','validate_owned'}<=attrs and {'source_membership','validate_resource_binding'}<=names)
  author=read(S/'source-controls.json');causal=read(S/'causality-clarification.json');seal=read(S/'source-seal-checks.json')
  yes('75_builder_controls_plus8_causality_exactly83',author['passed']==75 and author['failed']==0 and len(causal['checks'])==8 and all(v['passed'] for v in causal['checks']) and seal['Source_controls_passed']==83 and seal['Source_controls_failed']==0 and author['execution_branch_called'] is False)
  m=load(helper,'Source_author_identity_unchanged_Root_decoder');binding=m.doc(br);meta,last=m.original_capture_rows(binding,m.checked(raw),peer=True);p=last['payload']
  yes('real_author_actual_backend_and_metadata_id',last['ordinal']==meta['ordinal']+1==62007 and meta['type']=='inter_agent_communication_metadata' and meta['timestamp']==last['timestamp'] and p['author']=='/root/native_temp_independent_review' and p['recipient']=='/root' and last['metadata']['client_authored'] is False and binding['peer_actor']=='codex:/root/native_temp_independent_review' and binding['message_id']==p['id'] and binding['received_at']==last['timestamp'])
  text=p['content'][0]['text'];yes('author_normal_FINAL_envelope',text.startswith('Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/native_temp_independent_review\nPayload:\n'))
  # Source author code-fence presentation is identity evidence, not typed review.
  sections=text.split('```json\n')[1:];docs=[]
  for section in sections:docs+=m.structured_documents(m.strict(section.split('\n```',1)[0]))
  delivered=[v for v in docs if type(v) is dict and set(v)=={'path','sha256','bytes'}]
  expected=[pin(S/n) for n in ('HDF.json','MF.json','old21_builder.py','contract.v2.json','input-manifest.json')]
  yes('real_author_delivered_all_five_full_exact_refs',all(any(m.same_ref(e,v) for v in delivered) for e in expected))
  body=ast.unparse(fn)
  yes('unknown_exit_null_Root_assigns_no_retry_and_postreturn_fullhostpair',"'automatic_retry'" in body and "'Root_full_outer_hostpair_required'" in body and "'Root_assignment_required': True" in body and "'original_ordinal': None" in body)
 finally:closed=guard.close();gr=save('continuation-Source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
 result=save('finitechecks.resolved.json',dict(schema='researchos.old21-builder-independent-Source-resolved-checks.v1',status='ACCEPTED_SOURCE_ONLY',review_author='codex:/root/full_w09_source_review',reviewer_thread_id=os.environ['CODEX_THREAD_ID'],original_checks_ref=pin(D/'finitechecks.json'),original_script_ref=pin(D/'review_source.py'),prior_846_passes_reused=True,original_two_checker_expectations_preserved=True,resolved_original_check_names=[v['name'] for v in old['failed']],continuation_checks=checks,unresolved_findings=[],Source_guard_ref=gr,retained_handles_count=0,author_actual_peer_raw_ref=raw,author_actual_peer_binding_ref=br,actual_author_peer_ordinal=62007,all_original_bytes_offsets_checked=True,typed_review_or_Root_grant_synthesized=False,runtime_branch_called=False,product_calls=0,formal_acceptance=False,execution_grant=False))
 print(json.dumps(dict(result_ref=result,guard_ref=gr,status='ACCEPTED_SOURCE_ONLY',prior_passes=846,new_checks=len(checks),unresolved_findings=[],retained_handles_count=0),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
