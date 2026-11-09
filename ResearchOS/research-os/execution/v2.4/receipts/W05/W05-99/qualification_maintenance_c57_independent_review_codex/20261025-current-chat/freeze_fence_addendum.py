import pathlib,hashlib,json
B=pathlib.Path(__file__).parent
def ref(name):
 p=B/name;b=p.read_bytes();return {'path':name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
old={'PHASE1-manifest.json':'4f3965cf95e9f81e24087f162a16bd0eace4fafd1b18b7c7a3093804b1da9ba8','PHASE1-seal.json':'b6d293f2921b4a3619cd60f397eb6b6a725c89b1186329e2b42b11d427051c4b','PHASE1-boot-plan-binding-addendum-seal.json':'dabf5e26c77608af81ad3f755c8f07083d4db44c689232bdf3b9ec2986ca892b'}
for p,h in old.items():assert ref(p)['sha256']==h
entries=[ref('PHASE1-persistent-fence-control-addendum.md'),ref('read_fence_snapshot.py'),ref('freeze_fence_addendum.py')]
for d in ['017-mutable-fence-structure','018-mutable-fence-snapshot','019-snapshot-fence-cutpoints','020-snapshot-fixture-limits']:
 assert json.loads((B/d/'result.json').read_text(encoding='utf-8'))['native_exit']==0
 for n in ['recipe.json','stdout.raw','stderr.raw','result.json']:entries.append(ref(d+'/'+n))
for p in sorted((B/'MUTABLE-boot6-fence-snapshot').rglob('*')):
 if p.is_file():entries.append(ref(p.relative_to(B).as_posix()))
doc={'status':'BOUNDED_MUTABLE_SOURCE_OBSERVATIONS_NOT_ACCEPTANCE','prior_seals_unchanged':[ref(p) for p in old],'entries':entries,'findings':['FENCE-M01','FENCE-M02','FENCE-M03','FENCE-M04','FENCE-M05'],'new_assertions':['FC01','FC02','FC03','FC04','FC05','FC06','FC07','FC08'],'new_native_nonzero':0,'cumulative_reviewer_native_nonzero':2,'tool_diagnostic_count':0,'candidate_tests_executed':0,'acl_mutations':0,'formal_increment':0,'excluded':'021-fence-addendum-finalizer active capture; retain separately and verify numeric native exit on return'}
with (B/'PHASE1-persistent-fence-control-addendum-seal.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(doc,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'addendum':ref('PHASE1-persistent-fence-control-addendum.md'),'seal':ref('PHASE1-persistent-fence-control-addendum-seal.json'),'new_native_nonzero':0,'cumulative_reviewer_native_nonzero':2},ensure_ascii=False,indent=2))
