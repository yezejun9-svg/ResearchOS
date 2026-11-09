import ast,hashlib,json,sys,types
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
C=W/'main_c19_dispatcher_caller_independent_review_codex/c19v6-review-20261009'
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(r):assert pin(r['path'])==r;return Path(r['path']).read_bytes()
def fixed(p,s,n):
 r=dict(path=str(p.resolve(strict=True)),sha256=s,bytes=n);read(r);return r
def save(name,value):
 with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
initial=json.loads((N/'prepared-definition-decision.json').read_bytes());prior=json.loads(read(initial['actual_SourceGuard_ref']))
rh=fixed(C/'HDF.json','103ec67601f523d545499c8a7d0dc3b16f21d601c8152c232309f916815e0174',3327)
rm=fixed(C/'MF.json','0da7ad889c241c41c80ac309b32ea3cfc17e1401ac4a75ca9d32c56050a9a53c',3181)
rd=fixed(C/'source-decision.json','0586fb5d30533d656fbfd6d4a4d2741bc1e088cdf34bcac1801af88e500fae26',3653)
dh,dm,dd=[json.loads(read(r)) for r in (rh,rm,rd)]
caller=tuple(dd[k] for k in ('source_hdf_ref','source_mf_ref','caller_ref','root_contract_ref'))
source_mf=json.loads(read(caller[1]))
refs=[{k:e[k] for k in ('path','sha256','bytes')} for e in prior['entries']]+[rh,rm,rd,*caller,*dm['members'],pin(__file__),pin(N/'prepared-definition-decision.json'),initial['controls_ref'],initial['findings_ref']]
refs += [v for v in source_mf.values() if isinstance(v,dict) and set(v)=={'path','sha256','bytes'}]
unique={}
for ref in refs:
 read(ref);key=ref['path'].casefold();assert key not in unique or unique[key]==ref;unique[key]=ref
src=initial['registrar_ref'];tree=ast.parse(read(src));module=types.ModuleType('cp370_final_prepared_check');module.__file__=src['path'];sys.modules[module.__name__]=module
exec(compile(ast.Module(body=[n for n in tree.body if not isinstance(n,ast.If)],type_ignores=[]),src['path'],'exec'),module.__dict__)
gp=pin(module.GP);assert (gp['sha256'],gp['bytes'])==module.EXACT[str(module.GP)]
gm=types.ModuleType('cp370_final_prepared_guard');gm.__file__=gp['path'];sys.modules[gm.__name__]=gm;exec(compile(read(gp),gp['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=512*1024*1024)
guard.acquire(list(unique.values()))
try:
 assert dh['manifest_ref']==rm and dh['source_decision_ref']==rd and rd in dm['members']
 assert all(dh[k]==dd[k] for k in ('source_hdf_ref','source_mf_ref','caller_ref','root_contract_ref','actor_id','actor_role'))
 assert source_mf['caller_source_ref']==caller[2] and source_mf['contract_ref']==caller[3]
 actual_caller=module.ensure_caller_source(caller[0],caller[1]);assert actual_caller==caller
 actual_review=module.validate_review(dict(review_hdf_ref=rh,review_mf_ref=rm,review_decision_ref=rd),caller)
 assert actual_review[:3]==(rh,rm,rd) and actual_review[3]['decision']=='ACCEPTED_SOURCE_ONLY'
 supplement=save('Caller-v6-binding-addendum.json',dict(schema='researchos.cp370-prepared-caller-v6-addendum.v1',Caller_review_hdf_ref=rh,Caller_review_mf_ref=rm,Caller_review_decision_ref=rd,exact4_refs=list(caller),readonly_registrar_source_binding_passed=True,readonly_registrar_review_binding_passed=True,Caller_manifest_top_level_refs_are_valid_membership=True,initial_missing_Caller_limitation='SUPERSEDED_BY_THIS_VERIFIED_V6_INPUT',final_Caller_runtime_and_lease_not_executed=True,build_check_activate=False,formal_acceptance=False))
 findings=json.loads(read(initial['findings_ref']))
 findings['findings'][0].update(title='Independent review manifest is not associated with its decision or Source bindings',actual='validate_review loads rm but never inspects it: an empty review MF with no decision membership and no Source refs passes. Canonical Root path alias /root also passes actor inequality. The current real v6 review is valid; the negative malformed-packet control exposes a registrar validation gap.',fix='Require review MF decision membership and its exact source_hdf/source_mf associations, bind the canonical designated independent reviewer and original handoff provenance. Caller MF top-level caller_source_ref/contract_ref already seal those two members; no members-array requirement is needed there.')
 findings['clarifications']=['The initial controls label for empty caller MF members is a successful valid top-level-ref representation, not a blocker; only the unused independent review MF is defective.','Early Source context may precede Source review; fresh activation context must be a separately bound postseal input.','Distinct invocation selectors within the same original file are legal; deduplicate actual invocation identity, never file-ref alone.','Final Caller v6 availability is now verified and is not a defect. Final Registrar Source acceptance is still not granted.']
 finalfindings=save('findings.final.json',findings)
finally:
 cleanup=guard.close();gr=save('sourceguard.final-v6-closeout.json',cleanup)
assert cleanup['closed'] is True and cleanup['retained_handles_count']==0 and not cleanup['errors']
decision=dict(initial)
decision.update(findings_ref=finalfindings,initial_prepared_definition_decision_ref=pin(N/'prepared-definition-decision.json'),Caller_v6_binding_addendum_ref=supplement,final_Caller_SourceAccepted_inputs='VERIFIED_V6_EXACT4_AND_REVIEW_HDF_MF_DECISION',final_registration_SourceAccepted=False,actual_SourceGuard_ref=gr,prior_controls_SourceGuard_ref=initial['actual_SourceGuard_ref'],retained_handles_count=0,final_Caller_runtime_and_lease_validation='NOT_RUN_PREPARED_DEFINITION_ONLY')
dr=save('prepared-definition-final-decision.json',decision)
source=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T10-20-32-01a11e76-4e37-7a21-a388-2c5f2e3c9ebf.jsonl')
calls={};origin=None
with source.open('r',encoding='utf-8') as f:
 for ordinal,line in enumerate(f):
  item=json.loads(line);p=item.get('payload',{});cid=p.get('call_id')
  if item.get('type')!='response_item' or not cid:continue
  if p.get('type') in ('function_call','custom_tool_call'):calls[cid]=(ordinal,line,item)
  if p.get('type') not in ('function_call_output','custom_tool_call_output'):continue
  out=p.get('output','');out=out if isinstance(out,str) else json.dumps(out)
  if 'a23daf' in out and 'PYTHON_EXIT=0' in out:
   prior_call=calls[cid];origin=dict(source_path=str(source),call_ordinal=prior_call[0],output_ordinal=ordinal,original_call_event=prior_call[2],original_output_event=item,original_call_line=prior_call[1],original_output_line=line);break
assert origin is not None
save('review-a23daf.original-tool-io.json',origin)
for ref in unique.values():read(ref)
mf=save('MF.json',dict(schema='researchos.cp370-prepared-definition-independent-manifest.v1',members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]))
hr=save('HDF.json',dict(schema='researchos.cp370-prepared-definition-independent-handoff.v1',decision='PREPARED_DEFINITION_REQUEST_CHANGES',actor_id='codex:/root/attach_fixture_source_review',actor_role='INDEPENDENT_NON_AUTHOR',manifest_ref=mf,decision_ref=dr,findings_ref=finalfindings,controls_ref=initial['controls_ref'],Caller_v6_binding_addendum_ref=supplement,source_prepared_manifest_ref=initial['source_prepared_manifest_ref'],registrar_ref=src,actual_SourceGuard_ref=gr,prior_controls_SourceGuard_ref=initial['actual_SourceGuard_ref'],retained_handles_count=0,blocking_count=5,final_Caller_SourceAccepted_inputs='VERIFIED_V6',final_registration_SourceAccepted=False,RootScopeCreated=False,CanonWritten=False,NativeExecuted=False,DispatcherExecuted=False,formal_case_accepted_delta=0,parent_acceptance=False,new_original_failures=[],Root_next_original_failure=993,STOP=True,FINAL=True))
print(json.dumps(dict(handoff_ref=hr,manifest_ref=mf,decision_ref=dr,findings_ref=finalfindings,addendum_ref=supplement,final_guard_ref=gr,final_guard_refs=len(unique),new_original_failures=[]),ensure_ascii=False))
