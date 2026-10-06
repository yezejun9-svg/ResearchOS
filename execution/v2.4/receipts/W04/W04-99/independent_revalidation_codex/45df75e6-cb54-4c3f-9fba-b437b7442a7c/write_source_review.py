from datetime import datetime, timezone
import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(p):return json.loads(p.read_bytes())
def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
audit=read(OUT/'audit.json')
wt=ROOT/'.local/worktrees/codex-w0799'
base=wt/'execution/v2.4/receipts/W04/W04-99/executor_revalidation_codex'
scope=ROOT/'execution/v2.4/receipts/W04/W04-99/integration_codex/revalidation-82783db86d8a4a49a287c371c72f156d/scope_registration.json'
review={
 'schema':'researchos.w04.independent-revalidation-collector-source-review.v1',
 'reviewer_id':'codex:/root/w05_merge_review',
 'issued_at':datetime.now(timezone.utc).isoformat(),
 'candidate_commit':'2ab648416690625c3aa65ef6ae2a95a577fde85d',
 'decision':'SOURCE_READY', 'failed':[], 'missing':[],
 'scope':'Only the registered new collector bundle and retained tooling evidence. Ready for exact-byte Root integration and subsequent fresh MAIN preparation; not evidence that current W04 product or native gates passed.',
 'scope_registration_ref':ref(scope),
 'source_refs':[ref(wt/p) for p in read(scope)['executor_source_scope']],
 'audit_ref':ref(OUT/'audit.json'),'audit_raw_ref':ref(OUT/'audit_final.raw'),'audit_actual_exit':0,
 'checks':[
  {'id':'COMMIT_SCOPE','status':'PASS','actual':'All 224 Git blobs were independently read from fixed commit and compared byte-for-byte with clean candidate WT; every change is an addition within executor_revalidation_codex. Exactly nine registered source paths. No old executor/canonical/registry/shared-reader source modification.'},
  {'id':'FROZEN_PACKAGE','status':'PASS','actual':'147 exact PACKAGE_MANIFEST entries plus PACKAGE_MANIFEST itself = 148 files. All hashes and complete file inventory match original package; retaining manifest is required. Five immutable helper/expected files and historical r37 snapshot byte-identical. Legacy entries changes only registry_ref path, preserving full command payload and original SHA.'},
  {'id':'ACTUAL_ACTORS','status':'PASS','actual':'collect.py requires explicit executor/reviewer/root IDs, three casefold-distinct trimmed nonempty strings, exact immutable Root assignment SHA and tuple, assigned_by and executor namespace. Refusal precedes preparation/execution. New run receipts mark verifier assignment as ASSIGNED_NOT_YET_REVIEWED; executor writes no review or Root issuance.'},
  {'id':'ATTEMPT_ISOLATION','status':'PASS','actual':'New UUID run directory uses exclusive creation; receipts/raw use exclusive creation; old 1436-file executor tree inventory is unchanged and current hashes match protected before/after. New namespace current_proof/current_execution pointers may advance; immutable run artifacts are preserved and pointer existence is not acceptance.'},
  {'id':'LOCKED_TOOLS','status':'PASS','actual':'Locked Python/Go hashes checked, actual tool --version exit and exact output enforced before freeze, GOROOT derived from locked Go path, GOTOOLCHAIN=local/GOENV=off and repository module/build cache fixed. Inherited tool overrides/credentials are excluded by allowlisted environment. Actual qualification version raw and locked executable bytes verified.'},
  {'id':'SOURCE_AND_COMPILE_CLOSURE','status':'PASS','actual':'Original enrolled_sources six roots and eight files remains byte-identical in evidence_module. New test_collect.py, actor assignment, locked executable hashes, Go-list dependencies/test/helper/literal embeds and all local-package *.go are explicitly captured as separate auxiliary inputs. Existing files and new local *.go additions rechecked before proof, prepublication and finally; drift refuses collection. No claim that tooling-only test_collect belongs to the frozen eight.'},
  {'id':'UNCHANGED_EXPECTATIONS','status':'PASS','actual':'Frozen expected.json and parent_driver preserve exact Go roster, expected IDs, full package validator, three cases/six case-command bindings/five gates, deterministic FIXTURE mode. New executor changes neither thresholds nor assertion status interpretation.'},
  {'id':'ACTUAL_TOOLING_CONTROLS','status':'PASS','actual':'Latest executor raw shows nine collector and four unchanged bridge tests, each actual exit 0 and no skips. Independent explicit SYNTHETIC_NOT_PRODUCT copies replayed the same nine and four controls with actual exit 0; no actual collect invocation, Go product execution, native eleven dispatches, provider request or private DB access.'},
  {'id':'PROTECTED_READER','status':'PASS','actual':'Main and WT first 51719 bytes of formal_case_index.py hash 92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1. Generic v1 behavior preserved; scope requires extra Root transition ownership checks for the new executor namespace.'}
 ],
 'counts':{'commit_blobs':224,'registered_sources':9,'frozen_manifest_entries':147,'frozen_package_files_including_manifest':148,'remaining_tooling_receipt_blobs':67,'old_executor_files_verified':1436,'preserved_executor_tooling_rounds':3,'latest_collector_tests':9,'latest_bridge_tests':4,'independent_controls_actual_success':13,'current_product_collections':0,'native_dispatches':0},
 'preserved_review_failures':[
  {'origin':'Independent audit first replay copied an incomplete synthetic root: go.mod/go.sum were absent. Actual nine-test process exit 1; one setup FileNotFoundError. This is a reviewer fixture-copy failure, not a candidate failure. Original script/raw retained.', 'audit_ref':ref(OUT/'audit_candidate.py'),'raw_ref':ref(OUT/'audit.raw'),'unit_receipt_ref':ref(OUT/'test_collect.invocation.json')},
  {'origin':'After copying both actual lock files, nine tests actually passed with exit 0. Reviewer raw regex did not normalize CRLF and incorrectly returned audit exit 1. Final audit reads the original successful raw with universal newline handling; those nine tests were not rerun again.', 'audit_ref':ref(OUT/'audit_candidate_attempt2.py'),'raw_ref':ref(OUT/'audit_attempt2.raw'),'actual_success_receipt_ref':ref(OUT/'attempt2/test_collect.invocation.json')}
 ],
 'future_registration_requirements':[
  'Integrate only reviewed source bytes and re-freeze after the final MAIN code/three command entries have settled. The isolated WT lacks the final MAIN composition; this SOURCE_READY result cannot substitute for current capture or GLOBAL/native proof.',
  'Root transition must enforce actual assignment executor/reviewer/root exactly and reject reviewer receipts residing in either old executor_codex or new executor_revalidation_codex (including nested runs/aliases). formal_case_index.py line 756 rejects only the old executor namespace; do not treat that narrow v1 check as adequate new ownership isolation. Verify original actual review delivery, not path labels alone.',
  'Root transition and independent current review must read and bind auxiliary compiled-inputs before/preproof/prepublish/after, actual collector final exit, assignment, exact helper source and tool-version raw. The unchanged v1 formal reader does not independently prove this new auxiliary closure. An emitted proof/pointer from an ultimately failing collection is insufficient.',
  'Fresh current product Go/package assertions, all eleven actual native dispatches, complete body/DB graph, context/vector, independent real acceptance delivery and the reviewed acyclic transition protocol remain required before new W04 CURRENT registration.',
  'Changing command registry or shared captured inputs makes earlier A05 applicability NEEDS_REVALIDATION. Preserve original W07 proof/review and run fresh on the final stable vector; do not patch old proof or reinterpret this collector tooling pass as product acceptance.'
 ],
 'executor_rounds_note':'All three retained candidate tooling rounds have actual exit 0 for their five invocations; intermediate sources remain represented by their original before/after hashes. Historical old executor failures remain in the unchanged old tree. No failed record is rewritten or reclassified as product PASS.',
 'source_edits_by_reviewer':0,'canonical_registry_changes_by_reviewer':0,'formal_acceptance_delta':0,'W04_current_qualified':False
}
save('source_review.json',review)
save('receipt_manifest.json',[ref(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='receipt_manifest.json'])
print(json.dumps({'decision':review['decision'],'review_ref':ref(OUT/'source_review.json'),'audit_ref':ref(OUT/'audit.json'),'collect_ref':ref(base/'collect.py'),'test_collect_ref':ref(base/'test_collect.py'),'manifest_ref':ref(OUT/'receipt_manifest.json')},ensure_ascii=False))
