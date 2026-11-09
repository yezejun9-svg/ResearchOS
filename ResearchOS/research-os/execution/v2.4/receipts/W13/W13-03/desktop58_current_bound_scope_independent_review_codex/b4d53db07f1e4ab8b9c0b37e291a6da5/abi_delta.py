from pathlib import Path
import json,hashlib,ast
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r337-'+O.name)
C=[];refs=[]
def ck(n,x):C.append({'check':n,'passed':bool(x)})
def p(x):
 z=Path(x);return z if z.is_absolute() else R/z
def pin(z):
 z=p(z);v=z.read_bytes();r={'path':str(z),'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)};refs.append(r);return r
def read(z):pin(z);return json.loads(p(z).read_bytes())
s=read(N/'scope_registration.json');b=read(N/'binding.pre-review.json');q=read(N/'root-construction.parameters.desktop58.json');ri=read(N/'root-inputs.desktop58.pre-review.json');ob=read(N/'tool-observations.sixth-construction.closed.original.json')
sr=pin(N/'scope_registration.json');sr['path']=(N/'scope_registration.json').relative_to(R).as_posix()
ck('Root actual scope exact3key ROOT_REL',sr['sha256']=='0caa54d359072e7200b7cbbc9fb72742ffb325adc82ad3b4622310ac7549e9c1' and set(sr)=={'path','sha256','bytes'} and not Path(sr['path']).is_absolute())
inputkeys=('scope_template_ref','runtime_resources_ref','compiler_resources_ref','current43_authority_ref','origin_cut_ref','canonical_before_ref','source_inputs_ref','metadata_code_refs_ref','failure_prefix430_ref','desktop_values_ref','toolchain_lock_ref')
for k in inputkeys:
 r=ri[k];a=pin(r['path']);ck('11Rootinput '+k,a['sha256']==r['sha256'] and a['bytes']==r['bytes'])
 if k not in ('metadata_code_refs_ref','desktop_values_ref'):ck('binding projection '+k,r==b[k])
ck('metadata8 input projection',read(ri['metadata_code_refs_ref']['path'])['entries']==b['metadata_code_refs'])
ck('Desktop values input projection',read(ri['desktop_values_ref']['path'])==b['desktop_scope_values'])
for k in ('owner','run_uuid','before','after','main_git','public_environment','registration_namespace','controller_review_path','controller_review_ref','formal_increment','new_output_root','new_wrapper_root','new_export_root','new_authorization_root','new_grant_preflight_root'):ck('Rootinput exact '+k,(Path(ri[k])==(R/b[k]) if k=='registration_namespace' else ri[k]==b[k]))
runtime=read(s['runtime_resources_ref']['path']);rt={x['path']:x for x in runtime['files']};overlay=runtime['desktop58_overlay'];wr=q['wldp_static_ref'];a=pin(wr['path'])
ck('fresh Wldp actualpin',a==wr and rt.get(wr['path'])==wr)
ck('Wldp false provenance',overlay['Windows_Wldp_static_ref']==wr and overlay['Windows_Wldp_static_evidence_ref']==q['wldp_candidate_report_ref'] and overlay['Windows_Wldp_actual_loaded_proven'] is False)
for r in b['metadata_code_refs']:
 z=dict(r,path=str(p(r['path']).resolve()));ck('runtime actualABS metadata '+p(r['path']).name,rt.get(z['path'])==z)
source_review=read(R/'execution/v2.4/receipts/W13/W13-03/desktop58_windows_resource_capture_independent_source_review_codex/97d706a51e1742c99e7d70843693144e/review.json')
ctor=p(N/'construct_root_inputs.desktop58.wldp.py');actual=pin(ctor)
ck('constructor actual reviewed SHA',actual['sha256']==source_review['source_sha256']=='9f64bd96b11ea017656e1262b0caaede1cf295ee5e75dd689751439a868834a7')
ck('candidate not inherited oldqualification',source_review['decision']=='READY_SOURCE_PREPARATION_ONLY' and source_review['actual_loaded_proven'] is False)
caller_review=read(R/'execution/v2.4/receipts/W13/W13-03/desktop58_root_caller_allocationsixth_independent_source_review_codex/afc06b382f074b3fb512ec4f6b64a2e9/review.json')
ck('caller actual nonauthor source only',caller_review['decision']=='READY_SOURCE_PREPARATION_ONLY' and caller_review['reviewer']=='codex:/root/w05_merge_review' and caller_review['actual_launch_authorized'] is False)
ck('actualOUTabsent',not (R/'execution/v2.4/receipts/W13/W13-03/desktop58_root_terminal_closure_codex/d8a016ddc71e440fb386a11957c098ea').exists())
gate=p(s['authorization_verifier_ref']['path']).read_text(encoding='utf-8');pipe=p(q['metadata_pipeline_ref']['path']).read_text(encoding='utf-8')
for token in ["'researchos.desktop58-controller-static-review.v1'","'codex:/root/w05_merge_review'","'READY_FOR_ROOT_CURRENT58_DESKTOP169_GO3_ONCE'"]:ck('fixed Gate independent identity '+token,token in gate and token in pipe)
ck('scope exactdict retained through producer',"'scope_ref':scope_ref" in pipe and "wip_values(b,scope_ref)" in pipe and "desktop_lease(b,scope_ref)" in pipe)
ck('future grant strict Reader identity',"grant['scope_ref'] == scope_ref" in gate and "wip['desktop58_finite_validation_scope_ref'] == scope_ref" in gate)
ck('runtime3 actualABS',all(Path(x).is_absolute() and str(Path(x).resolve())==x for x in s['expected_runtime_observation_paths']))
ck('unknown dynamic rejection remains',"Actual loaded module outside frozen runtime universe" in p(s['debug_helper_ref']['path']).read_text())
ck('metadata outer fields actual0 not grant',ob['product_native_calls']==0 and ob['canonical_writes']==0 and ob['formal_increment']==0)
with (O/'abi-delta.json').open('x',encoding='utf-8') as f:json.dump({'schema':'researchos.desktop58-actual-bound-abi-review.v1','checks':C,'failed':[x for x in C if not x['passed']],'refs':refs,'scope_ref':sr,'new_failure_origins':[]},f,ensure_ascii=False,indent=2)
print(json.dumps({'checks':len(C),'failed':[x for x in C if not x['passed']]},ensure_ascii=False))

