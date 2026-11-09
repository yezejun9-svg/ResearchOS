import pathlib,hashlib,json
B=pathlib.Path(__file__).parent
def ref(n):
 b=(B/n).read_bytes();return {'path':n,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
old={'PHASE1-manifest.json':'4f3965cf95e9f81e24087f162a16bd0eace4fafd1b18b7c7a3093804b1da9ba8','PHASE1-seal.json':'b6d293f2921b4a3619cd60f397eb6b6a725c89b1186329e2b42b11d427051c4b','PHASE1-boot-plan-binding-addendum-seal.json':'dabf5e26c77608af81ad3f755c8f07083d4db44c689232bdf3b9ec2986ca892b','PHASE1-persistent-fence-control-addendum-seal.json':'4fc32056b6f7777fc06f0a219f1c81c399abd20ab921e021fa127355517f6122','PHASE1-os-ancestor-token-semantics-addendum-seal.json':'ef81922a508df3a9b1e1f5bc742979a87705b8d08e67c7d1f9ff70950f45bfcf'}
for n,h in old.items():assert ref(n)['sha256']==h
assert ref('MUTABLE-token-api.snapshot.txt')['sha256']=='818181965d2dd256776cd8956b9d9edb84925bdd865456982a71a72a5306cc92'
entries=[ref(n) for n in ['PHASE1-business-token-api-contract-addendum.md','freeze_token_api_addendum.py','MUTABLE-token-api.snapshot.txt','WEB-token-api-primary-03.json','WEB-token-api-primary-04.json']]
for d in ['026-token-api-discovery','027-token-api-snapshot','028-fixed-token-api-callsites']:
 assert json.loads((B/d/'result.json').read_text(encoding='utf-8'))['native_exit']==0
 for n in ['recipe.json','stdout.raw','stderr.raw','result.json']:entries.append(ref(d+'/'+n))
doc={'status':'BOUNDED_SOURCE_API_CONSULTATION_NOT_ACCEPTANCE','prior_refs_unchanged':[ref(n) for n in old],'entries':entries,'previous_assertions_preserved':66,'added_assertions':['TOKEN-01','TOKEN-02','TOKEN-03','TOKEN-04','TOKEN-05','TOKEN-06','TOKEN-07'],'new_native_nonzero':0,'cumulative_reviewer_native_nonzero':2,'tool_diagnostic_count':0,'candidate_tests_executed':0,'original_process_acl_access':0,'privilege_changes':0,'formal_increment':0,'excluded':'029-token-api-addendum-finalizer active capture; verify numeric native exit on return'}
with (B/'PHASE1-business-token-api-contract-addendum-seal.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(doc,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'addendum':ref('PHASE1-business-token-api-contract-addendum.md'),'seal':ref('PHASE1-business-token-api-contract-addendum-seal.json'),'new_native_nonzero':0,'cumulative_reviewer_native_nonzero':2},ensure_ascii=False,indent=2))
