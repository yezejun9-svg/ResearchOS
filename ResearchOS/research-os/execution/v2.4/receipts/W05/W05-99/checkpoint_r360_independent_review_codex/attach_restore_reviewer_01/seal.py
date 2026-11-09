import pathlib,json,hashlib
O=pathlib.Path(__file__).resolve().parent;R=pathlib.Path(r'D:/作品集/ResearchOS/research-os')
def pin(p):
 x=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(x).hexdigest(),bytes=len(x))
def save(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
 return pin(O/n)
checks=json.loads((O/'review-checks.json').read_bytes());closing=json.loads((O/'closing-pins.json').read_bytes());guard=json.loads((O/'sourceguard.close.json').read_bytes())
canonical=[]
for n in ['checkpoint','path_ownership','step_state','commands']:
 p=R/'execution/v2.4'/(n+'.json');current=pin(p);ref=next(x['actual'] for x in closing['refs'] if pathlib.Path(x['actual']['path'])==p);assert current==ref;canonical.append(current)
finding=dict(id='CP360-EXIT-833-001',severity='Important',blocking=True,title='833 Python exit provenance is overstated as marked/directly observed',source_reported_python_exit=1,directly_observed_outer_exit=1,directly_observed_python_exit=None,markedPythonExit=None,native_exit=None,origin_ref=pin(R/'execution/v2.4/receipts/W05/W05-99/legacy_migration_fixture_source_codex/edd7ae2789974a469dd2fc3a1bce50a9/failure-origin.833.json'),required_correction='Preserve original origin. Store actual_python_exit=null unless direct original marker/process field is available; separately label source_reported/inferred=1 and remove marked-exit claim. Preserve ordinal and counts.')
save('findings.json',[finding])
save('final-verification.json',dict(decision='REQUEST_CHANGES_CHECKPOINT_EXIT_PROVENANCE',structural_checks_passed=checks['all_passed'],source_guard_verified=guard['verification'],source_guard_closed=guard['closed'],guard_entries=len(guard['entries']),retained_handles_count=guard['retained_handles_count'],canonical=canonical,source_and_canonical_pins_unchanged=closing['all_unchanged'],important_count=1,new_mechanical_failure_ordinals=[840],pending_root_registration=True,formal_acceptance=False))
h=dict(schema='researchos.independent-checkpoint-review-handoff.v1',decision='REQUEST_CHANGES_CHECKPOINT_EXIT_PROVENANCE',checkpoint_revision=360,checkpoint_ref=canonical[0],canonical_refs=canonical,report_ref=pin(O/'report.md'),findings_ref=pin(O/'findings.json'),verification_ref=pin(O/'final-verification.json'),input_pins_ref=pin(O/'input-pins.corrected.json'),source_guard_close_ref=pin(O/'sourceguard.close.json'),closing_pins_ref=pin(O/'closing-pins.json'),original_tool_io_ref=pin(O/'original-tool-io.json'),important_count=1,critical_count=0,old829prefix_preserved=True,registered_failures=836,highest_observed_ordinal=838,new_mechanical_failure_ordinals=[840],counter_reset=False,authority='CHECKPOINT_CONSISTENCY_REVIEW_ONLY',product_authority='NONE',formal_acceptance=False,reviewer_Go_SQL_native_model_executed=False,Main_canonical_Source_writes=False,STOP=True)
save('HDF.json',h)
save('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=[pin(p) for p in sorted(O.rglob('*')) if p.is_file() and p != O/'MF.json']))
print(json.dumps(dict(HDF=pin(O/'HDF.json'),MF=pin(O/'MF.json'),decision=h['decision'],guard_entries=len(guard['entries']),structural_checks_passed=checks['all_passed'],new_failure_ordinal=840),ensure_ascii=False))

