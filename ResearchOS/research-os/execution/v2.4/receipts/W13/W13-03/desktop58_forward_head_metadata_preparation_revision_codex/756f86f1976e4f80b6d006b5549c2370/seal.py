"""Preparation evidence sealer; pure file IO, never imports either candidate."""
from pathlib import Path
import hashlib,json,sys
P=Path(__file__).parent
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def obj(n,x):
 with (P/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(P/n)
assert len(sys.argv)==7
reviewrefs=[]
for i in [1,3,5]:
 r=pin(Path(sys.argv[i]));assert r['sha256']==sys.argv[i+1];reviewrefs.append(r)
before=json.loads((P/'inputs.before.json').read_bytes())['files']
after=[pin(Path(x['path'])) for x in before]
assert before==after
codes=json.loads((P/'code-refs.final.json').read_bytes())
for r in codes.values():assert pin(Path(r['path']))==r
obj('inputs.final.json',{'prior_inputs':after,'prior_input_drift':[],'independent_request_refs':reviewrefs,'point_in_time_only':True})
obj('tool-observations.json',{'source_reads':{'chunk':'8a81a2','actual_outer_exit':0,'actual_native_exit':None},'namespace_creation':{'chunk':'656ff8','actual_outer_exit':0,'actual_native_exit':None},'pure_IO_AST_runtime_revision':{'chunk':'0c2830','actual_outer_exit':0,'actual_native_exit':None},'pure_IO_AST_final_revision':{'chunk':'dca15e','actual_outer_exit':0,'actual_native_exit':None},'candidate_or_product_executed':False,'new_failure_origins':[],'actual_native_exit_note':'Not separately sampled; outer0 is not relabeled native0.'})
h=obj('handoff.json',{'schema':'researchos.desktop58-forward-head-source-revision-handoff.v1','actor':'codex:/root/command_queue_impl','status':'SOURCE_PREPARATION_REPORTED_STOPPED_PENDING_NONAUTHOR_REVIEW','selected_engine_ref':codes['engine'],'selected_builder_ref':codes['builder'],'independent_request_refs':reviewrefs,'original_engine_ref':before[0],'original_builder_ref':before[1],'prior_handoff_ref':before[2],'prior_manifest_ref':before[3],'actual_scope_ref':before[4],'actual_runtime_catalog_ref':before[5],'fixes':[{'finding':'runtime catalog same-source binding omitted','change':'One same(scope.runtime_resources_ref,q.runtime_resources_ref) guard preserving existing canonical-path/SHA/bytes predicate.'},{'finding':'MODE bare substring self-count rejects valid request','change':'Count and both derivation callsites use the identical newline-delimited assignment anchor; pure IO count1 and three derived AST mode values, all reverse to the same source.'}],'whole_inverse_ref':pin(P/'whole-inverse.final.json'),'static_audit_ref':pin(P/'static-audit.final.json'),'changed_engine_functions':['setup','closure','prepare_request'],'unchanged_engine_AST_and_byte_functions':24,'inverse_hunks':4,'request_contract_unchanged':True,'only_builder_engine_path_sha_bytes_updated':True,'input_count':len(before)+len(reviewrefs),'input_drift':0,'candidate_imported':False,'candidate_executed':False,'actual_drafts_generated':False,'Root_params_canonical_product_writes':0,'Go_SQL_Node_Job_HTTP_models':0,'source_acceptance':False,'formal_increment':0,'new_failure_origins':[],'prior_failure_09b17d_preserved_not_recounted':True,'intermediate_runtime_only_v2_preserved':True,'future_Runtime_controls':'NOT_RUN','OPEN':['Non-author revision review','Root actual fixed request and pureIO draft generation','Independent registration draft review then actual Root CAS/seal','Fresh58/GUI/SQL24/formal gates remain ungranted']})
rows=[pin(x) for x in sorted(P.iterdir()) if x.is_file()]
m=obj('manifest.json',{'schema':'researchos.immutable-preparation-manifest.v1','count':len(rows),'entries':rows,'excluded_only':['manifest.json'],'source_acceptance':False})
print(json.dumps({'handoff':h,'manifest':m,'listed':len(rows),'selected':codes,'new_origins':0,'status':'STOPPED'},ensure_ascii=False))
