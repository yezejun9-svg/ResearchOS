"""Seal an independently reviewed result; no product/state mutations."""
import json,pathlib,hashlib,datetime
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W04/W04-99'
O=pathlib.Path(__file__).parent
def load(p):return json.loads(pathlib.Path(p).read_bytes())
def digest(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':pathlib.Path(p).relative_to(R).as_posix(),'sha256':digest(p)}
def save(p,d):
 with pathlib.Path(p).open('x',encoding='utf8') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
a=load(O/'audit_result.json')
assert a['status']=='PASS' and a['check_count']==844
for p,h in a['input_hashes'].items():assert digest(p)==h,('changed',p)
for p,h in a['public_source_hashes'].items():assert digest(R/p)==h
ctxp=B/'integration_codex/current_context_codex.json';ctx=load(ctxp);idx=load(R/ctx['execution_index']['path'])
assert digest(ctxp)=='8615cc89a48146241674dbfc56ccfa68396fc44f4327f01cfe8d1131370cf101'
assert digest(R/ctx['execution_index']['path'])==ctx['execution_index']['sha256']
integration=B/'formal_validator_codex/generic-controls/runs/controls-0402346f0fc24bcd9d4c8572f89b9293/receipt.json'
d=load(integration);assert digest(integration)=='c6fbc046b9d1e36dc68bbcce43766ff305b5ec27249e8c9639dcdc7a7729c9d2'
assert type(d['exit_code']) is int and d['exit_code']==0 and d['source_unchanged_during_run']
assert digest(integration.parent/'stderr.txt')==d['stderr_sha256']
assert digest(integration.parent/'stdout.txt')==d['stdout_sha256']
assert 'Ran 2 tests in ' in (integration.parent/'stderr.txt').read_text('utf8')
assert (integration.parent/'stderr.txt').read_text('utf8').rstrip().endswith('OK')
for n,h in d['source_hashes'].items():assert digest(integration.parent/'source'/n)==h
path_observations=[]
for n in (3,4):
 r=load(O/f'attempt{n}_receipt.json');p=r['cwd'];script=r['actual_argv'][-1]
 assert r'\u' not in p and '作品集' in p and pathlib.Path(p).is_dir() and pathlib.Path(script).is_file()
 path_observations.append({'attempt':n,'decoded_cwd':p,'normalized_cwd':pathlib.Path(p).resolve().as_posix(),'decoded_script':script,'contains_literal_backslash_u':False,'actual_paths_exist':True,'receipt_unchanged':ref(O/f'attempt{n}_receipt.json')})
failure_details=[
 {'attempt':1,'error':'C04-03 actual array includes original decision ID and literal HTTP replay header string true; reviewer omitted ID and expected boolean.',
  'failure_ref':ref(O/'attempt1_failure.json'),'source_ref':ref(O/'attempt1_source.py'),'command_observation_window':['2026-10-05T23:08:33.448239Z','2026-10-05T23:08:40.659802Z'],'process_elapsed_seconds':1.0945821},
 {'attempt':2,'error':'Reviewer guessed bootstrap/dispatch.py; actual file is execution/command_dispatcher/dispatch.py.',
  'failure_ref':ref(O/'attempt2_failure.json'),'source_ref':ref(O/'attempt2_source.py'),'command_observation_window':['2026-10-05T23:08:58.181078Z','2026-10-05T23:09:07.019587Z'],'process_elapsed_seconds':1.0142626},
 {'attempt':3,'error':'Reviewer counted an aggregate Go parent failure as a failed leaf. Original raw retains five leaf failures, one parent test failure and two package failures.',
  'failure_ref':ref(O/'attempt3_receipt.json'),'source_ref':ref(O/'attempt3_source.py'),'raw_error_ref':ref(O/'attempt3.stderr')}]
for f in failure_details[:2]:
 f.update(scope='INDEPENDENT_REVIEW_HARNESS_FAILURE_NOT_PRODUCT_FAILURE',exit_code=1,product_commands_executed=0,
 actual_argv=['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe','-B','-X','utf8','execution/v2.4/receipts/W04/W04-99/independent-review-codex-final-20261006-61a0d2e7/audit.py'],cwd=R.as_posix(),
 timestamp_limit='Command observation window retained; precise child process start/end and separate stderr file were not captured on the first two attempts. No synthetic precise process timestamps are supplied.',
 input_refs=[ref(ctxp),ctx['execution_index'],ref(B/'executor_codex/runs/20261005T225411Z-9b77d17e0eb1/version_vector.json')])
 save(O/f"attempt{f['attempt']}_receipt.json",f)
failure_refs=[ref(O/'attempt1_receipt.json'),ref(O/'attempt2_receipt.json'),ref(O/'attempt3_receipt.json')]
static={
 'schema':'researchos.w04.independent-static-review.v1','scope':'BOUNDED_CURRENT_IMPLEMENTATION_AND_EVIDENCE_REVIEW',
 'verifier_id':'codex:/root/w1702_review','status':'PASS','reviewed_root_commit':'a1abcc56a993823b15125f57c84e03ba9103dc4c',
 'dynamic_audit':ref(O/'audit_result.json'),'read_only_audit_invocation':ref(O/'attempt4_receipt.json'),
 'focused_integration_controls':ref(integration),'focused_control_test_count':2,
 'source_review':[
  'Current-Mu project creation validates exact embedded rules bytes/provenance, seals one project-local source Artifact in the same transaction, advances Profile/State consistently and returns the updated profile revision. Legacy constructor, existing project continuation and startup do not bulk-install policy.',
  'Specification import preserves installed rules references, reuses the exact package file 15 Artifact instead of sealing a duplicate, retains separately imported nonmatching sources, extends only explicit v2.4 manifest metadata and preserves pin/path/unlisted/authority refusals.',
  'Current C03 and C04 execute the full shared legacy scenarios through CurrentMu fixtures: actual version-state concurrency, explicit integration, three duplicate deliveries and reversed predecessors. Current HTTP persistence/claim/evaluation/legacy compatibility tests are present in the actual complete package roster.',
  'Context restoration and empty-worker materialization recursively resolve frozen source references, validate sealed original hashes and current access, retain immutable old bundles, and refuse missing contract/original/authorization. Missing uploaded original is an observed SQL error, not a fabricated HTTP result.',
  'Parser repair binds exact package and test lifecycles and integer exits. Actual execution and registration are distinct; eleven native dispatcher receipts link the current complete execution index and the original real source invocations.',
  'Public aggregation follows four frozen owner mappings and only canonical accepted final-owner references; it requires independent issuance and complete current evidence, isolates invalid owners, and preserves history. Only W04 protocol currently supported; other nonempty accepted owners fail closed until implemented.',
  'Checkpoint integration loads only fixed repository source, records loaded bytes, rechecks formal dependency hashes and covered file inventory before CAS replace; prior priority/threshold/history logic remains unchanged. Derived parent report preserves default report output and separates reachability from formal acceptance.'
 ],
 'resolved_findings':[
  {'id':'W04-STATIC-01','resolution':'Exact package/test run-pass-completion roster and strict integer exit checks, with actual controls and independent memory counterexamples.'},
  {'id':'W04-STATIC-02','resolution':'Separate real deletion of sealed original content in an isolated fixture, preceded by successful materialization, now supplements the retained tampering case.'}
 ],
 'scope_boundaries':[
  'W04 results are FIXTURE. Real native folder selection, Authority/Scanner, and public domain workspace registration/bootstrap are covered. Client initialization protocol commands and GUI are not claimed by this fixture.',
  'Existing AGENTS and README original bytes are retained. The conflicting skip-inventory proposal cannot change installed policy or advance later stages. This review does not claim a general AGENTS interpretation/merge engine.',
  'Worker materialization is verified; real new-Agent full C01 and provider/prompt execution remain outside W04 and owned by W06. Other formal final owners and LIVE resource gates are not accepted here.',
  '65 validator controls, 30 generic controls, 2 focused checkpoint controls and 20 independent parser controls are synthetic integrity evidence, not product formal cases.',
  'No product business Acceptance object or canonical state is created by this independent review. Root must retain actual delivery, register observed issuance, and then accept the owner row before formal count becomes 3.'
 ],
 'reviewer_harness_failures':failure_details,'failure_receipt_refs':failure_refs,'decoded_path_observations':path_observations,
 'open_blockers':[]}
save(O/'static_review_and_scope.json',static)
baseline=R/'.local/worktrees/v24-continuation/spec/v2.4/contracts/acceptance.json';catalog={x['id']:x for x in load(baseline)['cases']}
statements={
 'C03':'CONFIRMED from current Mu fixture source and original Go output: immutable D1/D2 receipts represent logical generations 1/2; exact impacted set is T1 and A1, becoming NEEDS_REVALIDATION and STALE. T2 is absent from the impact set and successfully sends through task-context validation after propagation. The old execution output seals only as STALE history; old If-Match and incompatible submission return 412/409 and cannot promote it. Impact links, propagation events, immutable references and successful T2 receipt are retained. This is the frozen W04 FIXTURE case; no LIVE claim.',
 'C04':'CONFIRMED from two concurrent goroutines using distinct principals and the same ProjectState revision: one write succeeds (201), the other returns 412 without overwrite, then an explicit integration task yields one current decision and resolved conflict. Missing predecessors first produce WAITING_FOR_PREDECESSOR at sequence zero; reversed delivery and three duplicates converge to 22 unique ordered events and 22 once-only applications. Same-key replay returns the original decision ID with HTTP Idempotent-Replay header string true; changed body returns 409. Source and raw event IDs/sequences support the complete frozen FIXTURE case.',
 'A01':'CONFIRMED: pinned current specification import creates a separate Mu project/Goal with four explicit fact bases and project-only authority, retaining a single exact 12952-byte version-1.1 rule source. Six tamper/path/manifest/false-authority negative cases preserve original state. Package validator output remains PASS / SPECIFICATION_PACKAGE_ONLY / product_tests NOT_RUN. Two real authorized fixture directories use native folder selection and public domain registration/bootstrap with actual Authority/Scanner, distinct projects/rule IDs, scoped inventory and actual FOUND/NOT_CHECKED plus separate complete/unavailable scans for NOT_FOUND/NOT_ACCESSIBLE. Replay and alias continuation retain policy; sealed ContextBundle materialization in two empty worker directories resolves the same rule hash and readonly original. AGENTS/README bytes remain intact; local inventory completes while research/reuse/implementation remain NOT_STARTED. Scope is initialization/local fixture behavior, not GUI/client initialization protocol completion, general AGENTS merge semantics, real provider execution or W06 full C01.'
}
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
review={'schema':'researchos.w04.independent-review.v1','scope':'EXTERNAL_FIXTURE_VERIFICATION','task_id':'W04','step_id':'W04-99','executor_id':'codex:/root/w1102_impl','verifier_id':'codex:/root/w1702_review','issued_at':now,
 'acceptance_baseline_ref':ref(baseline),'evidence_index_ref':ctx['execution_index'],'current_context_ref':ref(ctxp),
 'owned_case_verdicts':[{'case_id':cid,'final_owner_task':'W04','mode':'FIXTURE','assertion_ids':[x['id'] for x in catalog[cid]['assertions']],'status':'PASS','evidence_pointer':'/cases/'+cid,'semantic_review':{'status':'CONFIRMED','statement':statements[cid],'raw_evidence_refs':a['raw_evidence_refs_by_case'][cid]}} for cid in ('C03','C04','A01')],
 'parent_gate_verdicts':[{'check_id':gid,'mode':'FIXTURE','status':'PASS','command_ref':r} for gid,r in idx['parent_gates'].items()],'open_blockers':[],'construction_decision':'ACCEPTED'}
for p,h in a['input_hashes'].items():assert digest(p)==h,('changed_before_issuance',p)
assert review['acceptance_baseline_ref']['sha256']=='ae8aa1ce632aecce595b2adbcb05fd73aa7360b8fd4186fcef6fd5e7872caa66'
save(B/'independent_review_codex.json',review)
manifest={'schema':'researchos.independent-review-manifest.v1','issued_at':now,'review_ref':ref(B/'independent_review_codex.json'),'files':[ref(p) for p in sorted(O.iterdir()) if p.is_file()],'failure_receipt_refs':failure_refs,'status':'PASS','product_commands_executed':0}
save(O/'manifest.json',manifest)
print(json.dumps({'review':ref(B/'independent_review_codex.json'),'issued_at':now,'manifest':ref(O/'manifest.json'),'static_review':ref(O/'static_review_and_scope.json'),'failure_receipt_refs':failure_refs},ensure_ascii=False,indent=2))

