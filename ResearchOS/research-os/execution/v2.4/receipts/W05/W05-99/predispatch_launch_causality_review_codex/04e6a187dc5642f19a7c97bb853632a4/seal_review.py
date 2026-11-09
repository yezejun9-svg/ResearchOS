import pathlib,json,hashlib
O=pathlib.Path(__file__).parent
R=pathlib.Path(r"D:/作品集/ResearchOS/research-os")
inputs=[]
def pin(p):
 p=pathlib.Path(p);raw=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def take(p,expected=None):
 r=pin(p)
 if expected:assert r['sha256']==expected['sha256'] and r['bytes']==expected['bytes'],str(p)
 if not any(x['path']==r['path'] for x in inputs):inputs.append(r)
 return pathlib.Path(p).read_bytes()
def put(n,d):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
hpath=R/'execution/v2.4/receipts/W05/W05-99/model_trial_failure745_component_review_codex/18f25bd65ef34e189490677e760b9864/handoff.json'
h=json.loads(take(hpath,dict(sha256='b3d192b3b325469328d39bab4318cd0e3c3b3f3bc617b4ec92f65152c1d86be3',bytes=2590)))
m=json.loads(take(h['manifest_ref']['path'],h['manifest_ref']))
for k in ['review_ref','business_state_ref']:
 take(h[k]['path'],h[k])
original={pathlib.Path(x['path']).name:x for x in m['input_refs']}
for name in ['host-execute-admitted.stderr.raw','root-coordinator.lifecycle.json','execute.go']:
 take(original[name]['path'],original[name])
spans={
'internal/domain/runtime_coordinator_windows.go':[(121,158),(189,244),(318,339),(437,563),(935,1022)],
'internal/domain/runtime_recovery_windows.go':[(171,285)],
'internal/domain/resources.go':[(17,19)],
'internal/domain/runtime.go':[(127,151)],
'internal/domain/runtime_dispatch.go':[(96,126)],
'internal/domain/runtime_model_windows.go':[(19,45)],
'adapters/runtime/bridge_windows.go':[(129,219),(270,297)],
'adapters/runtime/runtime_windows.go':[(98,118)],
'adapters/runtime/process_windows.go':[(174,194)],
'adapters/runtime/data_root_windows.go':[(13,34),(58,107)],
'ops/experiment_sandbox/async_windows.go':[(58,93)],
'ops/experiment_sandbox/sandbox_windows.go':[(293,330)]
}
excerpts=[]
for relative,ranges in spans.items():
 p=R/relative;exp=original.get(p.name) if p.name=='runtime_coordinator_windows.go' else None
 raw=take(p,exp);lines=raw.decode('utf-8').splitlines()
 excerpts.append(dict(path=str(p),ranges=[dict(start=a,end=b,lines=[dict(line=i,text=lines[i-1]) for i in range(a,min(b,len(lines))+1)]) for a,b in ranges]))
helper=pathlib.Path(original['execute.go']['path']);lines=helper.read_text(encoding='utf-8').splitlines()
excerpts.append(dict(path=str(helper),ranges=[dict(start=a,end=b,lines=[dict(line=i,text=lines[i-1]) for i in range(a,b+1)]) for a,b in [(206,237),(451,490)]]))
for r in inputs:
 x=pin(r['path']);assert x['sha256']==r['sha256'] and x['bytes']==r['bytes']
put('source-evidence.json',dict(input_refs=inputs,line_excerpts=excerpts,input_drift=0,actual_SQL_performed=False,private_state_read=False))
put('review.json',dict(schema='researchos.predispatch-causality-review.v1',actor_id='codex:/root/command_queue_impl',decision='SOURCE_ORDERING_CONFIRMED_CONDITIONAL_NO_LAUNCH_FENCE_NOT_GLOBAL_ABSENCE',report_ref=pin(O/'review.md'),failure751_ref=pin(O/'failure-origin.751.json'),source_evidence_ref=pin(O/'source-evidence.json'),actual745_handoff_ref=pin(hpath),source_commit_before_StartBridge=True,StartBridge_before_DB_STARTED_locator_window_found=False,crash_windows=['committed STARTED before bridge journal or native process exists','suspended process exists before identity journal and DB identity persist','journal and DB identity persist before ResumeThread','resumed worker before terminal observation'],prepared_empty_fields_conclusion='Under same intact DB/project/run/epoch and reviewed exclusive path without record regression: launch fence not crossed. Snapshot alone is not global historical absence or future exclusion.',private_ExecuteClaim_status='UNOBSERVED',actual745_branch_conclusion='Pinned prior numeric-decode failure supports this invocation returning before claim write and RunAdmitted; no private-state absence asserted.',existing_Recovery='Missing/partial worker journal including PREPARED becomes UNKNOWN; no synthetic observation or relaunch.',business_reconciliation='OPEN',provider_requests=None,recorded_model_effects=0,formal_acceptance=False,qualification=False,new_failure_ordinals=[751],outer_failure751_exit=1,python_failure751_exit=None,native_failure751_exit=None,reviewer_SQL_Native_provider_calls=0,Source_canonical_private_state_mutations=0,input_drift=0))
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
put('manifest.json',dict(schema='researchos.independent-source-causality-manifest.v1',members=members,member_count=len(members),input_refs=inputs,input_drift=0,excludes_self_and_handoff=True))
put('handoff.json',dict(schema='researchos.predispatch-causality-review-handoff.v1',actor_id='codex:/root/command_queue_impl',decision='SOURCE_ORDERING_CONFIRMED_CONDITIONAL_NO_LAUNCH_FENCE_NOT_GLOBAL_ABSENCE',manifest_ref=pin(O/'manifest.json'),review_ref=pin(O/'review.json'),report_ref=pin(O/'review.md'),failure751_ref=pin(O/'failure-origin.751.json'),input_count=len(inputs),input_drift=0,private_ExecuteClaim_status='UNOBSERVED',business_reconciliation='OPEN',Source_canonical_SQL_Native_provider_mutations=0,new_failures=[751],stopped=True))
print(json.dumps(dict(handoff_ref=pin(O/'handoff.json'),manifest_ref=pin(O/'manifest.json'),review_ref=pin(O/'review.json'),failure751_ref=pin(O/'failure-origin.751.json'),input_count=len(inputs),member_count=len(members),input_drift=0)))

