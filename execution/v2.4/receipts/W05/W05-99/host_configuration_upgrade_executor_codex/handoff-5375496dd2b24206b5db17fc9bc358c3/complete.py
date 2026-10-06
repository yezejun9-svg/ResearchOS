import datetime, hashlib, json, pathlib

out=pathlib.Path(__file__).resolve().parent
root=out.parents[6]
receipts=out.parent
main=pathlib.Path('D:/作品集/ResearchOS/research-os')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(root).as_posix(),'sha256':sha(p)}
def save(name,value):
    p=out/name
    assert not p.exists(), p
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

run=receipts/'closure-8963f2d109b54e8d83e1710a4ece4197'
before=json.loads((run/'source_before.json').read_text('utf8'))
after=json.loads((run/'source_after.json').read_text('utf8'))
assert before==after and len(before)==39570
baseline=json.loads((receipts/'closure-1bdf02a977c9459cb024a3e803593c64/source_after.json').read_text('utf8'))
assert all(after.get(p)==h for p,h in baseline.items())
artifact=main/'.local/bin/researchos-remote.exe'
assert sha(artifact)=='aeda2d5eff0028529eaa53e9f5cc91fbcd668842577315eb744bd5f066834032'
copy=out/'historical14-control.exe'
assert not copy.exists()
copy.write_bytes(artifact.read_bytes())
assert sha(copy)==sha(artifact)
events=[json.loads(line) for line in (run/'test.stdout').read_text('utf8').splitlines()]
typed=[]
for n,event in enumerate(events,1):
    output=event.get('Output','')
    if output.startswith('W17_UPGRADE_ASSERTION '):
        typed.append(dict(actual=json.loads(output[len('W17_UPGRADE_ASSERTION '):]),raw={**ref(run/'test.stdout'),'locator':{'line_start':n,'line_end':n}}))
assert len(typed)==5 and all(x['actual']['status']=='PASS' for x in typed)
save('historical14_environment_supplement.json',dict(status='ACTUAL_ORIGINAL_SELECTOR_PASS_NOT_FORMAL',actor='codex:/root/sources_parent_impl',original_failed_run=ref(receipts/'closure-214eca5bd7b542f195ff14c505c46e9f/test.invocation.json'),actual_invocation=ref(run/'test.invocation.json'),stdout=ref(run/'test.stdout'),stderr=ref(run/'test.stderr'),result=ref(run/'result.json'),environment=ref(run/'environment.json'),source_before=ref(run/'source_before.json'),source_after=ref(run/'source_after.json'),previous39568_intersection_equal=True,added_inputs={p:h for p,h in after.items() if p not in baseline},artifact_original_path=str(artifact),artifact_copy=ref(copy),typed_assertions=typed,remaining=['TestClientQueueFreshNumberedSchema unchanged hardpin22','TestW17UpgradeActiveRecovery current method on historical14 fixture missing runtime_dispatches'],source_edits=0,provider_calls=0))
save('historical14_recovery_gap.json',dict(status='OPEN_RESOURCE_OR_TEST_SCOPE_REQUIRED_NO_IMPLEMENTATION',source_ref=ref(root/'internal/domain/backup_upgrade_test.go'),function='upgradeActiveRecovery, SchemaUpgradePlan branch only',failed_invocation=ref(receipts/'closure-214eca5bd7b542f195ff14c505c46e9f/test.invocation.json'),failed_stdout=ref(receipts/'closure-214eca5bd7b542f195ff14c505c46e9f/test.stdout'),facts=['The exact historical14 helper constructs Service{DB,Contracts}; it does not migrate or start current product. Current ResumeCheckpoint depends on runtime_dispatches absent in14.', 'The successful fixed historical14 control HTTP read proves its authenticated read path, not a callable ResumeCheckpoint/effect observation protocol. No public ResumeCheckpoint route was found in current domain source; do not invent one.'],minimal_future_scope={'path':'internal/domain/backup_upgrade_test.go','boundary':'Only historical14 recovery executor selection/fixture plumbing and new same-file helper; retain every existing W17 assertion, original historical13/14 schema/hash guard and same Run/epoch/effect identity. FinalSchemaUpgradePlan branch must stay unchanged.','resource_gate':'Need an independently pinned source14 implementation/test-helper build exposing the actual historical ResumeCheckpoint/ObserveEffect execution to the same public fixture. Existing fixed14 exe alone has no proven interface for these methods. Snapshot/source and native binary must be exact bound; refusal, old-observation rejection and fresh-observation same-Run completion must all execute.','not_allowed':['No adding runtime_dispatches or later tables to fixed14 fixture','No disabling current production query or migration guard','No dropping/moving the original same-Run assertion and calling it passed','No synthetic completion or paid provider','No source change until Root independent scope approval']},alternative='Root may commission a separate matching-source historical recovery qualification and preserve this original failed test as inapplicable to current runtime; this is a scope/acceptance decision, not an executor-issued PASS.'))
save('tool_diagnostic_supplement.json',dict(product_source_changed=False,records=[{'chunk':'e651a4','actual_exit':1,'actual':'PowerShell ParserError while composing a Python -c command; command did not execute or create run.v5.py. Replaced with literal apply_patch new runner; original tool output remains.'},{'chunk':'890ca6','actual_exit':1,'actual':'rg Windows literal internal/domain/orchestration*.go path was invalid; successful preceding search showed no HTTP ResumeCheckpoint route. No writes.'}]))
save('final_handoff.json',dict(schema='researchos.configuration-upgrade-final-executor-handoff.v1',status='FROZEN_CANDIDATE_FOR_INDEPENDENT_REVIEW_WITH_TWO_OPEN_REGRESSION_GATES',executor='codex:/root/sources_parent_impl',verifier='codex:/root/w05_merge_review',root='codex:/root',formal_increment=0,main23_hold=True,base_handoff=ref(out/'handoff.json'),historical14_supplement=ref(out/'historical14_environment_supplement.json'),followup_test_proposal=ref(out/'followup_test_scope_proposal.json'),historical14_recovery_gap=ref(out/'historical14_recovery_gap.json'),current_source=ref(out/'source.before_after.json'),audit=ref(out/'current_compiled_closure_audit.json'),counts={'current_focused':{'pass':189,'fail':0,'skip':0},'current_full_cli':{'pass':194,'fail':0,'skip':0},'historical_extended_original':{'raw_pass':75,'fail':2,'skip':0,'zero_assertion_parent_not_credited':1},'historical14_correct_environment_rerun':{'pass':1,'typed_assertions':5,'fail':0,'skip':0},'original_fresh22_hardpin':{'pass':0,'fail':1,'skip':0}},open=['Unchanged original fresh22 hardpin; exact one-test-file proposal only','Unchanged W17 schema14 current-runtime ResumeCheckpoint dependency; matching historical executor not yet available'],limitations='All original failures retained; corrected historical14 environment resolves only W17CLI. G01 external release/binary binding protocol limit and G09 WAL/single-writer boundary unchanged. Source review, future tests scope and combined MAIN validation are non-executor responsibilities.',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat()))
files=sorted(p for p in receipts.rglob('*') if p.is_file())
save('manifest.json',dict(schema='researchos.executor.sealed-file-manifest.v1',actor='codex:/root/sources_parent_impl',scope='All immutable files under this new executor namespace, excluding only this manifest itself. Product10 public snapshots and before/after hashes are referenced by final_handoff; original receipts from other namespaces unchanged.',file_count=len(files),files=[{**ref(p),'bytes':p.stat().st_size} for p in files]))
print(json.dumps({'final_handoff':ref(out/'final_handoff.json'),'manifest':ref(out/'manifest.json'),'files':len(files)},ensure_ascii=False))
