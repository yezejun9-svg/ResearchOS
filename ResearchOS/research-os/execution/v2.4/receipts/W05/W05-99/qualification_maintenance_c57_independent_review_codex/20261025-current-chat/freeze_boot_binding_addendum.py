import hashlib,json,pathlib
B=pathlib.Path(__file__).parent
def ref(name):
 p=B/name; raw=p.read_bytes(); return {'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
assert ref('PHASE1-manifest.json')['sha256']=='4f3965cf95e9f81e24087f162a16bd0eace4fafd1b18b7c7a3093804b1da9ba8'
assert ref('PHASE1-seal.json')['sha256']=='b6d293f2921b4a3619cd60f397eb6b6a725c89b1186329e2b42b11d427051c4b'
rows=[ref('PHASE1-boot-plan-binding-addendum.md'),ref('freeze_boot_binding_addendum.py')]
for dirname in ['014-mutable-plan-binding-read','015-mutable-plan-binding-lines']:
 result=json.loads((B/dirname/'result.json').read_text(encoding='utf-8'))
 assert result['native_exit']==0
 for name in ['recipe.json','stdout.raw','stderr.raw','result.json']: rows.append(ref(dirname+'/'+name))
seal={'status':'APPEND_ONLY_PHASE1_CONTRACT_BINDING_NO_SOURCE_ACCEPTANCE','original_phase1_manifest':ref('PHASE1-manifest.json'),'original_phase1_seal':ref('PHASE1-seal.json'),'entries':rows,'new_assertions':9,'candidate_tests_executed':0,'new_native_nonzero':0,'cumulative_reviewer_native_nonzero':2,'tool_diagnostic_count':0,'formal_increment':0,'excluded':'016-boot-plan-binding-finalizer active capture retained separately; verify numeric exit on return'}
with (B/'PHASE1-boot-plan-binding-addendum-seal.json').open('x',encoding='utf-8',newline='\n') as f: json.dump(seal,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'addendum':ref('PHASE1-boot-plan-binding-addendum.md'),'seal':ref('PHASE1-boot-plan-binding-addendum-seal.json'),'new_native_nonzero':0,'cumulative_reviewer_native_nonzero':2},ensure_ascii=False,indent=2))
