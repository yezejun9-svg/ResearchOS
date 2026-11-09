import json,hashlib,ast
from pathlib import Path
O=Path(__file__).parent
D=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/current58_whole_go_suite_revision2_source_preparation_codex/6e6556d821fe4457b23c6191fea96b1d')
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):return json.loads(p.read_bytes())
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
a=read(O/'audit.json');m=read(D/'manifest.selected.json');r=read(O/'review.json')
assert m['schema']=='researchos.source-preparation-sealed-members.v1' and m['member_count']==len(m['members'])==51
assert [x['label'] for x in a['checks'] if not x['passed']]==['manifest exact count51']
unchanged={}
for x in a['inverse']:
 p=Path(x['before']['path']);q=Path(x['after']['path'])
 if p.suffix!='.py':continue
 old={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
 new={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(q.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
 unchanged[q.name]={'unchanged_defs':[k for k in old if old[k]==new.get(k)],'changed_defs':[k for k in old if old[k]!=new.get(k)],'added_defs':sorted(set(new)-set(old))}
save('audit.supplement.json',{'schema':'researchos.source-static-audit-supplement.v1','original_audit_ref':pin(O/'audit.json'),'correction':'Original metadata predicate used nonexistent count; actual sealed manifest uses member_count. Original tool exit0/predicate false is preserved and is not a native failure.','corrected_manifest_check':True,'effective_checks_passed':90,'effective_checks_total':90,'new_source_defects_found_by_supplement':0,'function_AST_comparison':unchanged,'candidate_imported_or_executed':False})
r['audit_supplement_ref']=pin(O/'audit.supplement.json')
r['unsealed_intermediate_review_ref']=pin(O/'review.json')
r['intermediate_review_disposition']='Preserved; final findings same, audit member_count predicate corrected by immutable supplement.'
r['verification_summary']={'effective_static_checks':90,'passed':90,'MF51members_all_hashes_checked':True,'whole_file_inverse_sections':4,'python_AST_only':True,'candidate_imported':False,'controls_executed':False,'finite_packages':58,'local_calls':136,'local_selected_test_ids':743,'all_platform_ids':745,'model_ids_held':2}
r['status']='STOPPED'
save('review.final.json',r)
save('report.json',{'schema':'researchos.current58-whole-go-independent-source-report.v1','actor_id':'codex:/root/w05_merge_review','non_author':True,'decision':'REQUEST_CHANGES','review_ref':pin(O/'review.final.json'),'required_changes':r['requested_changes'],'R01_static_paths':['Overflow records stream/all actually-read bytes lower bound/cap under cause lock; kills only own process and preserves native poll value.','Complete raw requires EOF and no overflow. Incomplete joins expose no complete raw pin. list_names/strict_events/evaluate_run reject all failed states.','Second guarded_wall immediately precedes Popen after mkdir/setup. Cleanup/wait/drain/IO are bounded with final deadline rejection.','Returned invocation is a frozen copy; late daemon worker cannot mutate it. Remaining partial-file evidence is not a complete raw stream.'],'R02_static_paths':['Native result -> attestation without review ref -> non-author review -> scope dual refs forms a forward DAG.','Scope -> source registration -> source review -> grant -> authority remains forward. Source manifest root_registration_ref stays NULL/omitted; filling it creates avoidable inverse dependency.','Attestation typed schema must be fixed from contract v1 to gate-required v2 before a Root producer can follow the contract.'],'R03_static_paths':['Selected runner literal SHA/bytes equals actual selected gate and executes the verified raw buffer with no pyc loader.','Gate source parent-chain reparse guard runs before read/compile. Root/cwd/scope/registration/grant/lease/path authority match.','Interface stale gate SHA and rev8 filename remain contradictory; exact selected-source template itself correctly pins rev9.'],'negative_controls':[{'case':x,'status':'NOT_RUN_STATIC_PATH_ONLY'} for x in ['stderr overflow + native0 + valid stdout','stdout cap crossing at JSON boundary','missing EOF or drain worker incomplete','competing timeout/drain failure','pre-Popen budget exhausted','foreign cwd or worktree lease','changed gate/old pyc','absent cap producer/heartbeat','missing attestation/native review','model lane or bool numeric budget','wrong selected contract schema or stale gate pin']],'limits':r['still_open'],'original_audit_preserved':True,'new_tool_diagnostic_refs':r['new_tool_diagnostic_origins'],'new_nonzero_tool_failures':0,'candidate_calls':0,'Go_calls':0,'formal_delta':0})
save('handoff.json',{'schema':'researchos.source-independent-review-handoff.v1','actor_id':'codex:/root/w05_merge_review','decision':'REQUEST_CHANGES','review_ref':pin(O/'review.final.json'),'report_ref':pin(O/'report.json'),'audit_ref':pin(O/'audit.json'),'supplement_ref':pin(O/'audit.supplement.json'),'new_tool_diagnostic_refs':r['new_tool_diagnostic_origins'],'new_nonzero_tool_failures':0,'author_origins_recounted':False,'candidate_execution':False,'status':'STOPPED'})
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file()]
save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':members,'count':len(members),'self_excluded':True})
print(json.dumps({n:pin(O/n) for n in ['review.final.json','report.json','audit.supplement.json','handoff.json','manifest.json']},ensure_ascii=False))

