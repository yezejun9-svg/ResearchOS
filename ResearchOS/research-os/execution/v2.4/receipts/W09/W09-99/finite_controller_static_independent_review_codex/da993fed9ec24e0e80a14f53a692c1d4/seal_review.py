"""Independent static metadata only; no candidate import/process/SQL/API."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path('D:/作品集/ResearchOS/research-os')
N=Path(__file__).parent
S=ROOT/'execution/v2.4/receipts/W09/W09-99/finite_controller_preparation_codex/2098f8232b5a4331b0cac70eccd32ce0'
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(name,d):
 with (N/name).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
manifest=load(S/'manifest.json');spec=load(S/'spec.json');before=load(N/'read-audit.before.json')
after=[]
for member in manifest['members']:
 actual=ref(Path(member['path']))
 after.append({'ref':member,'actual':actual,'matches':actual==member})
save('read-audit.after.json',{'manifest_ref':ref(S/'manifest.json'),'members':after,'mismatches':sum(not x['matches'] for x in after),
 'actual_files_in_preparation':len([p for p in S.rglob('*') if p.is_file()]),'self_plus_members':len(after)+1})
snapshot=N/'snapshots';snapshot.mkdir()
source=Path(load(S/'inputs/3-handoff.json')['worktree'])
inputs=[]
for p in [S/x for x in ['launch.py','case_worker.py','controller_common.py','controller.py','windows_debug_job_tree.py','seal_readonly.py','implementation-conditions.json','spec.json','finite-roster.json']]+[
 source/x for x in ['go.mod','internal/domain/skills.go','internal/domain/runtime_coordinator_windows.go','internal/domain/qualification_live.go']]+[Path(spec['source_review_ref']['path'])]:
 raw=p.read_bytes();dest=snapshot/(str(len(inputs)).zfill(2)+'-'+p.name)
 with dest.open('xb') as f:f.write(raw)
 inputs.append({'original_ref':ref(p),'copy_ref':ref(dest)})
for pin in spec['exact4_pins']:
 p=source/pin['path'];actual=ref(p)
 inputs.append({'original_ref':actual,'frozen_candidate_sha256':pin['sha256'],'matches':actual['sha256']==pin['sha256'] and actual['bytes']==pin['bytes']})
save('read-source-inputs.json',inputs)

def finding(id,priority,file,lines,fact,change):
 return {'id':id,'priority':priority,'source_ref':ref(S/file),'lines':lines,'static_fact':fact,'required_change':change,'actual_case_executed':False}
changes=[
 finding('W09-CTRL-01','BLOCKER','controller.py',[88,111],
 'Git export includes only internal/adapters/migrations/spec/go.mod/go.sum. The pinned source directly imports ops/experiment_sandbox (runtime_coordinator_windows.go:25), evaluation/skills (skills.go:7), evaluation/holdout/jev (qualification_live.go:8); none can exist in that export. With GOPROXY=off, go list cannot close the domain package.',
 'Freeze a complete explicit public local-package/embedded-resource catalog for cd0 before any Go call, export each required immutable Git blob, and verify membership/hash. Reuse approved public compiler catalog as a starting locator only, reconciling current cd0 blobs. Do not export private holdout data, execute generators, or claim fresh combined Main; compilation remains a separately granted next phase.'),
 finding('W09-CTRL-02','HIGH','controller_common.py',[58,94],
 'The authorization gate accepts authorized:true plus nonempty authority_refs/independent_review_refs whose bytes merely hash-match. It does not parse the Root actor/completed registration, actual review decision, exact source/spec/caps binding, canonical immutable copies or sealed CAS completion. Controller Ledger adds resources/controller/spec only; grant and authority/review references are absent from pre-case/final frozen inputs.',
 'Specify and validate the actual future Root grant/registration/reviewer schemas and exact immutable links, including successful sealed registration and independently approved controller/caps. Bind the actual grant, all consumed authority/review/manifest/canonical-copy files and spec into initial/per-native/per-case/final vectors. Use immutable canonical snapshots so later unrelated Root CAS need not invalidate a run. Nonempty arbitrary hash-valid JSON is insufficient.'),
 finding('W09-CTRL-03','HIGH','launch.py',[4,18],
 'launch/controller/case_worker import controller_common through normal import before any pin validation; existing pyc can be read despite dont_write_bytecode. Only Controller emits runtime.before/after; the outer launcher and separate case-worker interpreters do not emit their own actual __file__/__cached__/loaded-DLL observations. A shared binary/catalog is not an observation of those processes.',
 'Use a minimal reviewed bootstrap that hashes and raw-compiles the exact common module bytes before use, or explicitly freeze/verify all effective import artifacts before loading. Require actual -I -S -X utf8 and pinned interpreter; record before/after point-time Python/source/cached/OS inputs for each interpreter which owns native calls, retaining the explicit non-lifecycle limitation. Include those records and their inputs in the appropriate outer/worker receipts; do not infer worker runtime from controller runtime.'),
 finding('W09-CTRL-04','HIGH','controller.py',[47,87],
 'run() writes invocation.json only after wrapper validation and output-size inspection. A failing wrapper at line62, a helper exception, or a raw-size postcondition failure bypasses that record. Its finally only runs Ledger.check, which may replace the primary exception. launch.py likewise has no finally around helper invocation; case_worker writes case-owned only after run_owned returns. main preserves only an exception type/message and may lose per-case progress in results when cases raises.',
 'Persist each attempted argv/cwd/env/start/phase and nullable raw native/outer observations in unconditional finally, including wrapper request/result and actual first cause. Save later vector/closure errors separately without replacing the first failure. Retain partial ordered results and explicit NOT_RUN remainder; preserve stdout/stderr even when oversized or cleanup fails. A preflight/native timeout must not become an unrecorded Python failure.'),
 finding('W09-CTRL-05','HIGH','controller.py',[161,190],
 'junction-resource nonzero is labelled HOLD_RESOURCE_UNEXPLAINED_NATIVE_FAILURE but execution then continues through cases; the symlink branch classifies every OSError as expected unavailability. This contradicts first-unexpected-stop and cannot distinguish a permitted missing capability from a malformed request or another preparation defect.',
 'Freeze precise expected-unavailable Windows error classifications and evidence; only those may HOLD the affected four dependent calls while running independent resource-free cases. Unexplained native nonzero, wrong link identity, or other unexpected exceptions must seal the first failure and stop its registered cohort. Preserve original native result; never convert it into successful resource qualification.'),
 finding('W09-CTRL-06','HIGH','seal_readonly.py',[18,43],
 'The sealer validates native invocations found by a glob but does not require the complete stage inventory, each case wrapper request/result, actual grant/authority closure, or every intermediate vector. It accepts any result row marked NOT_RUN_RESOURCE_HOLD without checking that the frozen row actually requires a held resource. The seal manifest excludes its own summary as well as the whole seal directory.',
 'Bind exact completed outer/controller/grant inputs; require all mandatory export/version/env/list/compile/buildinfo stages and actual cases against the roster, including wrappers, cleanup and before/after vectors. Validate row id+selector and resource-HOLD provenance. Include the immutable summary in the final manifest while excluding only the manifest itself. Keep sealing file-only with no SQL or test rerun and no source acceptance claim.')]

debug_review={
 'helper_ref':ref(S/'windows_debug_job_tree.py'),'mode':'DEBUG_PROCESS_NEW_UNEXECUTED_DESCENDANT_CAPTURE',
 'reviewed_static_guards':[
  {'lines':[148,179],'fact':'Caller debug/breakaway flags rejected; finite allowed executable/module pin sets; process budget1..2048; helper itself selects DEBUG_PROCESS.'},
  {'lines':[298,330],'fact':'CREATE_PROCESS/LOAD_DLL must supply a real file handle; held duplicate is hashed under deadline and retained for final hash; module allowlist and primary/child executable image allowlist checked; event hFile closed in finally.'},
  {'lines':[332,423],'fact':'Per-generation actual PID/creation FILETIME/held process handle/Job membership captured; unknown generation/RIP/unsupported events fail; first loader breakpoint assumption is explicit; other exceptions are passed as not handled; received event always continued.'},
  {'lines':[425,450],'fact':'Primary wait/exit plus Job active and total process accounting used; max16 concurrent and finite total cap. No reliance on DEBUG_ONLY_THIS_PROCESS for descendant coverage.'},
  {'lines':[487,518],'fact':'Own suspended process is assigned to exclusive kill-on-close Job before resume; all debug children must be observed in that Job.'},
  {'lines':[525,605],'fact':'Timeout/error terminates only the owned Job (or own never-resumed primary if assignment failed), observes cleanup5s, rehashes held modules with separate25s budget, independently compares each process exit with exit event/continuation, checks create/exit/TotalProcesses equality, closes owned handles.'}
 ],
 'required_before_execution_conditions':[
  'The Git launcher path is cmd/git.exe, but Git calls pass allowed_images=[git] only while allowing up to4 processes. Root must establish a finite actual launcher/descendant executable set (including any Git-for-Windows shim target) and wire it into allowed_images; runtime module membership alone cannot authorize another CREATE_PROCESS image. This review did not execute Git/debugger to discover that set.',
  'Root must freeze actual Python/OS/Git/GoTool images and complete GOROOT/module-cache membership before grant; these inputs are intentionally absent, not proven by old Go3 evidence.',
  'Fixed2048/16 process budgets,131072 events/32768 modules,256MiB per module/128GiB aggregate and cleanup5/finalization25/outer15000 are proposed caps requiring explicit Root scope. File hashing checks deadlines between reads; it does not bound a blocking kernel read. Outer owned Job is the separate hard wall bound.',
  'Observe actual nested Job membership, breakpoint/child event flow and cleanup in finite authorized execution. No behavioral PASS or full lifetime Python attestation is supplied by AST.'
 ],'additional_helper_code_blocker_proven_by_this_static_read':False,'behavioral_qualification':False}
save('debug-tree-static-review.json',debug_review)

canon=[]
for name in ['checkpoint','path_ownership','step_state','commands']:
 p=ROOT/('execution/v2.4/'+name+'.json');q=N/('canonical.after.'+name+'.json');b=p.read_bytes()
 with q.open('xb') as f:f.write(b)
 canon.append({'path':str(p),'before_copy_ref':ref(N/('canonical.before.'+name+'.json')),'after_copy_ref':ref(q),
               'unchanged':(N/('canonical.before.'+name+'.json')).read_bytes()==b})
save('canonical-read-observations.json',{'rows':canon,'canonical_writes':0,'parallel_Root_progress_permitted':True,
 'canonical_is_not_a_candidate_input_vector':'Snapshots are observation only; input43 drift is checked separately.'})
save('tool-diagnostics.json',{'read_only_tool_chunks':[{'chunk_id':x,'actual_outer_exit':0} for x in ['985bdf','1c183c','ba02a0','d7bd57','424909','b4afd1','4669f0','ce65f1','e15fcc']],
 'original_results_retained_in_conversation':True,'b4afd1_output_truncated':True,'bounded_exact_import_source_reads_followed':'4669f0',
 'native_candidate_Dll_helper_Go_SQL_Node_HTTP_MODEL_execution':0,'new_failure_origins':[],
 'prior_author_eeed61_ref':ref(S/'diagnostics/eeed61/origin.json'),'prior_eeed61_not_new_again':True})
save('review.json',{'schema':'researchos.w09.finite-controller-static-review.v1','reviewer':'codex:/root/command_queue_impl',
 'decision':'REQUEST_CHANGES','preparation_review_only':True,'execution_authorized':False,
 'authorship_disclosure':'Reviewer did not author W09 source4, controller bundle or DEBUG_PROCESS descendant extension. Reviewer previously authored reusable6a4 normal Job helper and earlier Go3 helper foundation; this review does not independently requalify those originals or inherit their behavioral acceptance.',
 'handoff_ref':ref(S/'handoff.json'),'manifest_ref':ref(S/'manifest.json'),'spec_ref':ref(S/'spec.json'),
 'source_review_ref':spec['source_review_ref'],'source_commit':spec['source_commit'],'base_commit':spec['base_commit'],
 'verified':{'manifest_members':43,'including_self':44,'hash_mismatches':sum(not x['matches'] for x in after),
 'AST_selected_modules':7,'candidate_imported':False,'source4_current_hashes_match':all(x.get('matches',True) for x in inputs),
 'roster':before['roster'],'counts_are_expected_NOT_RUN':True,'actual_Go_or_cases':0},
 'requested_changes':changes,'debug_review_ref':ref(N/'debug-tree-static-review.json'),
 'evidence_limits':{'new_domain_closedcopy_expected':29,'selected_four_table_driver_JSON_expected':21,'business_JSON_only_expected':8,
 'old_domain_no_closedcopy':6,'adapter_no_DB':14,'SQLite_typeof_or_implicit_rowid_or_all_tables_claim':False,
 'fresh_compile_graph_WORK_archives_exes_actual':False,'fresh_combined_Main_validation':False},
 'read_audit_before_ref':ref(N/'read-audit.before.json'),'read_audit_after_ref':ref(N/'read-audit.after.json'),
 'source_input_refs':ref(N/'read-source-inputs.json'),'canonical_observation_ref':ref(N/'canonical-read-observations.json'),
 'tool_diagnostics_ref':ref(N/'tool-diagnostics.json'),'new_failure_origins':[],
 'source_ready':False,'parent_acceptance':False,'formal_increment':0})
save('handoff.json',{'schema':'researchos.w09.finite-controller-review-handoff.v1','decision':'REQUEST_CHANGES',
 'review_ref':ref(N/'review.json'),'debug_review_ref':ref(N/'debug-tree-static-review.json'),
 'requested_change_ids':[x['id'] for x in changes],'new_failure_origins':[],
 'actual_product_or_controller_execution':False,'source_or_parent_acceptance':False,
 'next':'Source/Root may prepare a new immutable controller revision under a separately assigned receipt scope; no execution grant arises from this review.'})
members=[ref(p) for p in sorted(N.rglob('*')) if p.is_file()]
save('manifest.json',{'count':len(members),'entries':members,'excluded_only':str(N/'manifest.json')})
print(json.dumps({'review':ref(N/'review.json'),'handoff':ref(N/'handoff.json'),'manifest':ref(N/'manifest.json'),'members':len(members)},ensure_ascii=False))
