import pathlib,json,hashlib
N=pathlib.Path(__file__).parent
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def js(name,obj):
 with (N/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=True,indent=2);f.write('\n')
members={str(p.relative_to(N)).replace('\\','/'):pin(p) for p in sorted(N.rglob('*')) if p.is_file()}
js('MF.json',{'schema':'researchos.independent-source-review-manifest.v1','members':members,'exclusions':['MF.json','HDF.json','postseal.json'],'formal_acceptance':False})
js('HDF.json',{'schema':'researchos.independent-source-review-handoff.v1','status':'SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL','reviewer':'codex:/root/attach_fixture_source_review','author':'codex:/root/command_queue_impl','source_hdf':pin(N.parent.parent/'session_attach_contract_fixture_revision_codex'/'af-1a11e3e93437fe089b15fdf6a164840'/'HDF.json'),'manifest_ref':pin(N/'MF.json'),'manifest_member_count':len(members),'report_ref':pin(N/'report.md'),'result_ref':pin(N/'result.json'),'guard_ref':pin(N/'guard.final.json'),'failure_ordinals':[886,887],'new_Go_SQL_native_model':False,'formal_acceptance':False,'production_ready':False,'canonical_writer':'Root only'})
guard=json.loads((N/'guard.initial.json').read_text(encoding='utf-8'))
source_unchanged=all(pin(pathlib.Path(r['path']))==r for r in guard)
member_unchanged=all(pin(pathlib.Path(r['path']))==r for r in members.values())
post={'source_unchanged':source_unchanged,'members_unchanged':member_unchanged,'source_inputs':len(guard),'manifest_member_count':len(members),'HDF':pin(N/'HDF.json'),'MF':pin(N/'MF.json')}
js('postseal.json',post)
print(json.dumps({**post,'postseal':pin(N/'postseal.json')}))
assert source_unchanged and member_unchanged

