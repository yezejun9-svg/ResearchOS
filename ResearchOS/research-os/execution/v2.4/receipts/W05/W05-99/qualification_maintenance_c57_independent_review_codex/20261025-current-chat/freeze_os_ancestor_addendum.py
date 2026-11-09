import pathlib,hashlib,json
B=pathlib.Path(__file__).parent
R=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
def info(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def ref(n):
 r=info(B/n);r['path']=n;return r
old={'PHASE1-manifest.json':'4f3965cf95e9f81e24087f162a16bd0eace4fafd1b18b7c7a3093804b1da9ba8','PHASE1-seal.json':'b6d293f2921b4a3619cd60f397eb6b6a725c89b1186329e2b42b11d427051c4b','PHASE1-boot-plan-binding-addendum-seal.json':'dabf5e26c77608af81ad3f755c8f07083d4db44c689232bdf3b9ec2986ca892b','PHASE1-persistent-fence-control-addendum-seal.json':'4fc32056b6f7777fc06f0a219f1c81c399abd20ab921e021fa127355517f6122'}
for n,h in old.items():assert ref(n)['sha256']==h
entries=[ref(n) for n in ['PHASE1-os-ancestor-token-semantics-addendum.md','freeze_os_ancestor_addendum.py','WEB-ancestor-semantics-primary-01.json','WEB-ancestor-semantics-primary-02.json']]
for d in ['022-fixed-ancestor-ref-discovery','023-fixed-ancestor-contract-read','024-fixed-ancestor-cutpoints']:
 assert json.loads((B/d/'result.json').read_text(encoding='utf-8'))['native_exit']==0
 for n in ['recipe.json','stdout.raw','stderr.raw','result.json']:entries.append(ref(d+'/'+n))
root=R/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat'
p=root/'C57-ancestor-contract-observation-cp540.json';observation=json.loads(p.read_text(encoding='utf-8-sig'));fixed=[info(p)]
for k in ['historical_resource','mutable_source_snapshot']:
 x=observation[k];a=info(pathlib.Path(x['path']));assert a['sha256']==x['sha256'];fixed.append(a)
p=R/'execution/v2.4/receipts/W05/W05-99/qualification_boot_supplement_independent_design_review_codex/20261015-current-chat/design-review.md'
a=info(p);assert a['sha256']=='3965106935192d75a8bff39d5c21edd3d98e63417f1ed19067c8a36d2e2f290c';fixed.append(a)
doc={'status':'FIXED_CONTRACT_CONSULTATION_NO_SOURCE_ACCEPTANCE','prior_refs_unchanged':[ref(n) for n in old],'fixed_inputs':fixed,'entries':entries,'previous_assertions_preserved':58,'added_assertions':['OA01','OA02','OA03','OA04','OA05','OA06','OA07','OA08'],'new_native_nonzero':0,'cumulative_reviewer_native_nonzero':2,'tool_diagnostic_count':0,'candidate_tests_executed':0,'original_acl_process_reads':0,'formal_increment':0,'capture_note':'Initial exploratory web search retained in tool transcript only; relied-on official page requests/responses persisted. Native command raw complete.','excluded':'025-os-ancestor-addendum-finalizer active capture; verify numeric native exit on return'}
with (B/'PHASE1-os-ancestor-token-semantics-addendum-seal.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(doc,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'addendum':ref('PHASE1-os-ancestor-token-semantics-addendum.md'),'seal':ref('PHASE1-os-ancestor-token-semantics-addendum-seal.json'),'new_native_nonzero':0,'cumulative_reviewer_native_nonzero':2},ensure_ascii=False,indent=2))
