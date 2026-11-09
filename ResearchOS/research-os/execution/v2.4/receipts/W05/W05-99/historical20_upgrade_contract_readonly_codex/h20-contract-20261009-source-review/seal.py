import pathlib,json,hashlib
N=pathlib.Path(__file__).resolve().parent
def pin(p):
 p=pathlib.Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def js(n,o):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(o,f,ensure_ascii=True,indent=2);f.write('\n')
guard=json.loads((N/'guard.initial.json').read_text(encoding='utf-8'))
assert all(pin(r['path'])==r for r in guard)
members={p.relative_to(N).as_posix():pin(p) for p in sorted(N.rglob('*')) if p.is_file()}
js('MF.json',dict(schema='researchos.historical20-contract-research-manifest.v1',members=members,exclusions=['HDF.json','MF.json','postseal.json'],formal_acceptance=False))
js('HDF.json',dict(schema='researchos.historical20-contract-research-handoff.v1',status='READONLY_CONTRACT_AND_IMPLEMENTATION_BOUNDARY_IDENTIFIED',actor='codex:/root/attach_fixture_source_review',role='independent research; not new implementation author',historical_commit='3225a31fd25969c6a5e071a2fc686cb4a835e162',historical_tree='955430efd12ef450a0eeb86a5f07054518c0e058',report_ref=pin(N/'report.md'),contract_ref=pin(N/'contract-boundary.json'),manifest_ref=pin(N/'MF.json'),manifest_member_count=len(members),guard_ref=pin(N/'guard.final.json'),input_count=len(guard),historical_blobs_verified=32,implementation_required=True,source20_to21_exists=False,source20_full_chain_accepted=False,frozen_21_22_23_templates_modified=False,actual_Git_Go_SQL_native_model=False,private_keys_read=False,Main_canonical_modified=False,formal_acceptance=False,new_failure_ordinals=[895],counter_reset=False,STOP=True))
post=dict(inputs_unchanged=all(pin(r['path'])==r for r in guard),members_unchanged=all(pin(r['path'])==r for r in members.values()),input_count=len(guard),manifest_member_count=len(members),HDF=pin(N/'HDF.json'),MF=pin(N/'MF.json'))
js('postseal.json',post)
assert post['inputs_unchanged'] and post['members_unchanged']
print(json.dumps({**post,'postseal':pin(N/'postseal.json')}))

