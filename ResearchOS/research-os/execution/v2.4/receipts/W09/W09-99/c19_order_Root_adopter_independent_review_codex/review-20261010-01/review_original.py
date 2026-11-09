from pathlib import Path
from datetime import datetime,timezone,timedelta
import ast,copy,hashlib,json,types
R=Path('D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W09/W09-99';N=Path(__file__).parent
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
C=W/'nf5_c19_main_order_candidate_source_codex/candidate-20261010-01'
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value,raw=False):
 with (N/name).open('xb') as f:f.write(value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(N/name)
script=S/'adopt_c19_order.Main.root.py'
assert pin(script)['sha256']=='a462eab1c5d0f8fb46d0cac9e8a6c6f344f360fb5156a93cc47bc1bbc6b7f9b8'
assert pin(script)['bytes']==21472
contract=C/'root-calling-adoption-contract.source.json'
assert pin(contract)['sha256']=='dfa8c84f37b2fa815ca9b070a38ed430b0680fc951c3c75d5a4f2c5636ff486b'
guard_path=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
guard_raw=guard_path.read_bytes();assert hashlib.sha256(guard_raw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
refs=[pin(p) for p in [script,contract,C/'HDF.json',C/'MF.json',C/'retrieval.before.source.py',C/'retrieval.source.py',guard_path,
 R/'execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py',
 W/'full_w09_main_native_producer_source_codex/fullw09-20261010-03/full_w09_runtime.source.py']]
gm=types.ModuleType('review_finite_source_guard');exec(compile(guard_raw,str(guard_path),'exec'),gm.__dict__)
guard=gm.SourceReadGuard()
try:
 guard.acquire(refs)
 raw=guard.get_buffer(str(script));tree=ast.parse(raw)
 funcs={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
 selected=['require','same_ref','refs_in','proofs','authority','guarded']
 isolated=ast.Module(body=[funcs[x] for x in selected],type_ignores=[])
 ns={'Path':Path,'ROOT':'codex:/root','THREAD':'01a11007-5233-7ca1-b71f-9e9e5ce84c98','AFTER':'b85fb90d9927a2427ee29a5ff756b8e7d18b0639e9a3910a7621991bc3788f11',
 'TARGET':R/'ops/ci/retrieval.py','datetime':datetime,'timezone':timezone,'IMPORT_PINS':[(Path('D:/synthetic/no-import'),'unused')]*3,'unique':lambda x:x}
 exec(compile(isolated,'EXACT_AST_FUNCTIONS_ONLY','exec'),ns)
 checks=[]
 def check(name,condition,detail):
  assert condition,name
  checks.append(dict(id=name,expected_counterexample_observed=True,detail=detail,synthetic_only=True))
 source=json.loads(guard.get_buffer(str(C/'HDF.json')));contractdoc=json.loads(guard.get_buffer(str(contract)))
 def fake_ref(name,digest='0'*64):return dict(path='D:/synthetic/'+name,sha256=digest,bytes=1)
 sr,cr,rr,rh,rm,aw,rw=[fake_ref(x) for x in ['source','contract','decision','review-hdf','review-mf','author-witness','review-witness']]
 review=dict(decision='REQUEST_CHANGES',actor_id='codex:/root/unrelated_actor',formal_acceptance=False,candidate=contractdoc['sourcecandidate_ref'])
 docs={sr['path']:source,cr['path']:contractdoc,rr['path']:review,rh['path']:{}}
 config=dict(source_handoff_ref=sr,calling_contract_ref=cr,review_decision_ref=rr,reviewer_actor='codex:/root/backup_fixture_review',
 review_acceptance_requirements=[(['formal_acceptance'],False)],author_witness_ref=aw,review_witness_ref=rw,
 review_witness_binding_sha256='f'*64,review_handoff_ref=rh,source_manifest_ref=source['manifest_ref'],review_manifest_ref=rm,closed_review_guard_refs=[])
 # Keep the exact actual source contract ref so source binding itself is not bypassed.
 config['calling_contract_ref']=source['calling_contract_ref'];docs[source['calling_contract_ref']['path']]=contractdoc
 audits=[]
 ns['load_ref']=lambda ref:copy.deepcopy(docs[ref['path']])
 ns['imported']=lambda *args:types.SimpleNamespace(actual_audit=lambda *args:audits.append(args))
 ns['proofs'](config)
 check('P1_rejected_review_and_wrong_actor_accepted',review['decision']=='REQUEST_CHANGES' and review['actor_id']!=config['reviewer_actor'],
       'Exact proofs() accepts only config-selected formal_acceptance=False; no fixed accepted decision or decision actor check. Actual audit primitive is mocked, not bypassed in production.')
 check('P1_unrelated_witness_digest_accepted',audits[-1][2]=='f'*64 and audits[-1][2]!=rr['sha256'],
       'Proofs forwards caller-selected witness digest instead of binding exact reviewed decision.')
 check('P1_missing_review_manifest_binding_and_empty_guard_set_accepted',docs[rh['path']]=={} and config['closed_review_guard_refs']==[],
       'Review HDF without manifest binding and empty closed-review-guard refs are permitted.')
 now=datetime.now(timezone.utc);sc=fake_ref('scope')
 scope=dict(issued_by=ns['ROOT'],root_thread_id=ns['THREAD'],write_targets=[str(ns['TARGET'])],execution_limit=1,
 lease_id='lease',lease_issued_at=(now-timedelta(minutes=1)).isoformat(),lease_expires_at=(now+timedelta(minutes=5)).isoformat())
 docs[sc['path']]=scope
 owner=dict(owner=ns['ROOT'],scope_ref=sc,state='ROOT_REGISTERED_SINGLE_TARGET_MAIN_ADOPTION',lease_id='lease',
 lease_status='REVOKED',lease_expires_at=(now-timedelta(days=1)).isoformat(),one_shot_consumed=True)
 worker=dict(owner,slice_id='key')
 cp=dict(workers=[worker]);ow=dict(active_integrator={'id':ns['ROOT']},card_path_bindings={'W09-99':dict(owner=ns['ROOT'],subtasks={'key':owner})})
 ns['authority'](dict(scope_ref=sc,owner_key='key'),cp,ow)
 check('P1_revoked_consumed_owner_with_expired_owner_lease_accepted',True,'authority() checks only scope expiry; it does not bind owner/worker lease state/expiry/consumed flag to scope or reject consumed flags.')
 # Reproduce the exact zip/all truncation predicate without reading any Canon or invoking register/adopt.
 current=[fake_ref('checkpoint'),fake_ref('ownership')];canon=[fake_ref(x) for x in ['checkpoint','ownership','step_state','commands']]
 passed=all(ns['same_ref'](p,ref) for p,ref in zip(canon,current))
 check('P1_truncated_four_vector_predicate_passes',passed,'No length/exact4 precondition around all(zip(CANON,current)); adopt only compares canonical path refs after its Main write.')
 class FakeGuard:
  def acquire(self,refs):return {}
  def close(self):return dict(closed=True,errors=[],retained_handles_count=0)
 ns['imported']=lambda *args:types.SimpleNamespace(SourceReadGuard=lambda **kw:FakeGuard())
 def fail_save(*args):raise OSError('cleanup-publication-error')
 ns['save']=fail_save
 def fail_action():raise ValueError('primary-action-error')
 try:ns['guarded']([],None,fail_action)
 except BaseException as exc:
  check('P2_cleanup_publication_replaces_primary_exception',isinstance(exc,OSError) and isinstance(exc.__context__,ValueError),
   'The top-level error becomes cleanup-publication-error; Python chains primary in __context__, but guarded returns no structured primary+secondary evidence.')
 before=guard.get_buffer(str(C/'retrieval.before.source.py'));after=guard.get_buffer(str(C/'retrieval.source.py'))
 old=b'selected = GROUPS[check] if check else list(TESTS)'
 new=b'selected = GROUPS[check] if check else [name for name in CASES[case] if name in TESTS]'
 assert before.count(old)==after.count(new)==1 and before.replace(old,new,1)==after
 save('finite-controls.json',dict(counterexamples=checks,counterexample_count=len(checks),exact_AST_only=selected,
 Root_stage_invocations=0,Native_Go_SQL_TP_calls=0,actual_audit_invocations=0,actual_manifest_inverse=True))
 save('input-pins.json',dict(refs=refs,all_pins_verified_while_held=True,live_Canon_Main_not_held=True))
 save('original-adopter.source.py',raw,True)
 findings=[
 dict(id='C19-ADOPT-REVIEW-001',priority=1,line=106,end_line=127,title='Mandatory independent acceptance and exact witness bindings are configurable or missing',
 evidence_controls=[x['id'] for x in checks[:3]],
 impact='Source adoption can accept a REQUEST_CHANGES decision or unrelated reviewer artifact when config supplies permissive acceptance requirements; the exact HDF/MF/source contract and closed guard set are not enforced.',
 required_fix='Hardcode accepted schema/actor/verdict and exact candidate/source HDF/MF/contract refs. Bind actual peer witness digest to the accepted decision. Require exact nonempty closed source/review guards and verify their relevant pins.'),
 dict(id='C19-ADOPT-AUTHORITY-002',priority=1,line=143,end_line=162,title='Current Canon and owner capability are not bound throughout the exclusive write',
 evidence_controls=[checks[3]['id'],checks[4]['id']],
 impact='adopt reads the supplied current vector without fixed canonical path/length validation, accepts inconsistent consumed/revoked owner fields, and releases Canon before acquiring the Main target. Final Canon check occurs after mutation.',
 required_fix='Validate exact4 paths/refs and request/config/scope/output consistency, all owner/worker lease/consumption bindings. Hold a separate Canon-only read guard across target exclusive acquisition/write/readback; close target then authority guard.'),
 dict(id='C19-ADOPT-FAILURE-003',priority=2,line=91,end_line=99,title='Cleanup/publication errors replace the primary action failure',
 evidence_controls=[checks[5]['id']],
 impact='guarded() close/save errors become the top exception; adopt failure/finally publication can similarly overwrite the main error. Python exception chaining is retained but structured primary/secondary outcomes can be absent.',
 required_fix='Collect primary exception and secondary guard/handle/publication errors separately; attempt cleanup even if receipt writes fail, and emit recoverable final failure state with actual partial/write/close observations.')
 ]
 save('findings.json',findings)
 save('decision.json',dict(schema='researchos.c19-root-adopter-independent-source-decision.v1',actor_id='codex:/root/attach_restore_independent_review',
 actor_role='INDEPENDENT_NON_AUTHOR_NON_EXECUTOR',source_author='codex:/root',decision='REQUEST_CHANGES_SOURCE_ONLY',
 source_ref=refs[0],calling_contract_ref=refs[1],findings_ref=pin(N/'findings.json'),controls_ref=pin(N/'finite-controls.json'),
 CAND_independent_review_substituted=False,contract_compatible_strengthening='Close original Source/review guards first; new Canon-only authority guard may remain through exclusive Main write, excluding TARGET. Close target before Canon guard.',
 imports_sha_verified=True,tuple_unpack_syntax_issue_found=False,Native_Go_SQL_TP_RootStage_calls=0,
 formal_acceptance=False,parent_acceptance=False,execution_grant=False,Main_adopted=False,STOP=True))
finally:
 closed=guard.close();save('input-guard.closed.json',closed)
assert closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
assert all(pin(ref['path'])==ref for ref in refs)
print(json.dumps(dict(decision_ref=pin(N/'decision.json'),guard_ref=pin(N/'input-guard.closed.json'),held_inputs=len(refs),guardclosed0=True,counterexamples=6),ensure_ascii=False))

