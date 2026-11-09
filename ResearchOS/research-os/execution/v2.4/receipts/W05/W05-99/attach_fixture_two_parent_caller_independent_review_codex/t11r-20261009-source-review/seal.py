import pathlib,json,hashlib
N=pathlib.Path(__file__).resolve().parent
A=N.parents[1]/'integration_codex'/'attach-fixture-current-two-parent-root-source-t11-1a11e7f5205729390aaee9f47b28ce6'
def pin(p):
 p=pathlib.Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def js(n,o):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(o,f,ensure_ascii=True,indent=2);f.write('\n')
guard=json.loads((N/'guard.initial.json').read_text(encoding='utf-8'))
assert all(pin(r['path'])==r for r in guard)
members={p.relative_to(N).as_posix():pin(p) for p in sorted(N.rglob('*')) if p.is_file()}
js('MF.json',dict(schema='researchos.root-caller-independent-review-manifest.v1',members=members,exclusions=['MF.json','HDF.json','postseal.json'],formal_acceptance=False))
js('HDF.json',dict(schema='researchos.root-caller-independent-review-handoff.v1',status='SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL',reviewer='codex:/root/attach_fixture_source_review',author='codex:/root/command_queue_impl',source_handoff=pin(A/'HDF.json'),source_manifest=pin(A/'MF.json'),prepare_ref=pin(A/'prepare_attach_fixture_two_parent.actual_owned.py'),validate_ref=pin(A/'validate_attach_fixture_two_parent.actual_owned.py'),choice_ref=pin(A/'source.integration.choice.json'),manifest_ref=pin(N/'MF.json'),manifest_member_count=len(members),report_ref=pin(N/'report.md'),checks_ref=pin(N/'checks.json'),guard_ref=pin(N/'guard.final.json'),source_members=58,preserved_parent_count=54,selected_parent_names=['TestClientAttachSettledAcquisitionCompletesAndReplays','TestClientAttachPreservesStaleAndBindingGates'],nonselected_parent_count=52,all_source_declared_parent_count=132,ordinary_history20_full_release_program_rehearsal_authority='BLOCKED',failure_ordinals=[],actual_Git_Go_SQL_native_model=False,formal_acceptance=False,production_ready=False,canonical_writer='Root only'))
post=dict(source_unchanged=all(pin(r['path'])==r for r in guard),members_unchanged=all(pin(r['path'])==r for r in members.values()),guarded_unique_inputs=len(guard),manifest_member_count=len(members),HDF=pin(N/'HDF.json'),MF=pin(N/'MF.json'))
js('postseal.json',post)
assert post['source_unchanged'] and post['members_unchanged']
print(json.dumps({**post,'postseal':pin(N/'postseal.json')}))

