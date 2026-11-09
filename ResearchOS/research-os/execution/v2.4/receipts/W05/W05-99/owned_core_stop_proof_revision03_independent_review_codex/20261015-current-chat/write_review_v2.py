from pathlib import Path
import json, hashlib, datetime, subprocess, collections

r = Path(r'D:\作品集\ResearchOS\research-os')
e = Path(__file__).parent
w = r / '.local/worktrees/owned-core-stop-proof-r3-20261015'

def ref(p):
    p = Path(p)
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def write(name, obj):
    (e / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

captures = []
for cap in sorted((e / 'command-captures').iterdir()):
    if not (cap / 'after.json').exists():
        continue
    b = json.loads((cap / 'before.json').read_text(encoding='utf-8'))
    a = json.loads((cap / 'after.json').read_text(encoding='utf-8'))
    captures.append({'capture': str(cap), 'before': ref(cap / 'before.json'), 'after': ref(cap / 'after.json'), 'stdout': ref(cap / 'stdout.bin'), 'stderr': ref(cap / 'stderr.bin'), 'argv': b['argv'], 'cwd': b['cwd'], 'allowlist_env': b['allowlist_env'], 'native_exit': a['native_exit']})

def capref(label):
    return next(x for x in captures if '-' + label + '-' in Path(x['capture']).name)

cases = [{'artifact': ref(p), 'result': json.loads(p.read_text(encoding='utf-8'))} for p in sorted(e.glob('fixture-e2e-*/case-result.json'))]
finding = {
    'id': 'STOP-R3-F01', 'prior_finding': 'STOP-R2-F03', 'priority': 'P2',
    'title': 'Retained Core/parent image chain accepts unauthorized initial owner/DACL policy',
    'locations': [{'path': 'ops/supervisor/owned_core_handle_windows.go', 'line': n} for n in (111, 119, 156, 369)],
    'impact': 'observeOwnedImageAnchor only requires a valid owner SID and a nonempty DACL, then freezes its SDDL. It never checks the owner against an authorized ownership policy or rejects untrusted write/control ACEs. Actual copied Core and parent processes with Everyone FULL_ACCESS on either image ancestor or final image pass ObserveOwnedCoreReadOnly, OpenOwnedCoreRetained and verifyRetained. This fails the explicit strict owner/DACL boundary in CP516 F03 and CP517. Recording an unsafe initial descriptor and comparing it later does not authorize it.',
    'evidence_level': 'Fresh native Windows own copied executable parent+child, package-private test overlay; two unsafe ACL cases accepted; no production Source edits; no native stop signal',
    'evidence': [capref('independent-unsafe-acl-v2')['stdout'], ref(e / 'independent_owned_core_handle_windows_test_v2.go'), ref(e / 'overlay-v2-lineage.json')],
    'authorized_owner_boundary': 'Source confirms any valid owner is accepted. No foreign-owner or foreign-user runtime test performed. Explicit policy must distinguish authorized operator and justified OS/install owners.',
    'ace_boundary': 'Direct final-image Everyone FULL_ACCESS and OICI ancestor Everyone FULL_ACCESS dynamically accepted. First non-inheritable ancestor setup denied child launch and is retained as a harness diagnostic.',
    'share_boundary': 'Ancestor FILE_SHARE_WRITE allows independently opening a GENERIC_WRITE directory handle during retention. Final-image write sharing and ancestor rename refusal passed fresh tests. No successful namespace replacement or hostile race observed. Directory write sharing alone is not asserted to be an exploit; require deny-write guarantee or a demonstrated equivalent native protection argument.',
    'minimal_fix_paths': ['ops/supervisor/owned_core_handle_windows.go', 'ops/supervisor/owned_core_handle_windows_test.go'],
    'minimal_fix': 'Enforce explicit trusted-owner/ACE policy on every Core/parent image component at acquisition and action boundaries; interpret inherited/inherit-only ACEs correctly; reject untrusted modify/write/delete/control rights without broad ACL relaxation. Preserve retained same-handle hash/ID, nonreparse/hardlink checks and reverse closure. Deny ancestor write where required or demonstrate an equally strong native primitive against relevant path mutation.',
    'required_tests': ['Actual copied parent+child safe ACL positive and direct/inherited Everyone/Users write/control ACE rejection before signal.', 'Authorized-owner policy positive/negative cuts with honest foreign-user limitation.', 'Native writable-directory handle/reparse/rename, final-image write-sharing, hardlink and wrong-parent cuts; no unexecuted hostile race claim.']
}

coverage = [
    {'id': 'F01', 'status': 'FIX_SUPPORTED', 'evidence': 'Fresh own two-grant positive: one native signal, 87-table/35-row matching postflight. Missing worker exit/verifier wait yield preflight STOP_UNAVAILABLE without a STOP grant. Fresh 28 numeric cases pass. Strict seven proof classes unchanged; each validation iteration decodes a fresh receipt. Synthetic fixture receipt is not original OS Wait.'},
    {'id': 'F02', 'status': 'SOURCE_AND_BOUNDARY_FIX_SUPPORTED_WITH_INTEGRATION_LIMIT', 'evidence': 'Caller ctx and earliest deadline flow through Commit to retained native layer. Checks occur before/after durable intent and after prewait. Fresh cancellation/earlier deadline/prewait and consumed-journal tests pass; replay does not enter native path after durable claim.', 'limit': 'No deterministic full live Commit cancel/expiry after its own durable intent. Source plus seam/journal tests are compositional evidence, not an executed integrated cut. No remaining cancellation source defect identified.', 'minimal_next_cut': 'Package-private deterministic full Commit fixture: cancel/expire after durable intent, observe zero signal and UNKNOWN, then independently invoke replay to prove permanent consumption; no production approval switch.'},
    {'id': 'F03', 'status': 'NEEDS_CHANGES', 'finding': 'STOP-R3-F01'},
    {'id': 'COV01', 'status': 'BOUNDED_SYNTHETIC_REENTRY_SUPPORTED', 'evidence': 'Six author claim/BEGIN/intent/postcall/torn-claim/orphan-BEGIN images get real compiled CLI repeat reentry. Third grant on claim; preflight reset refusal on four normal claimed states. Own fresh positive repeat-commit equality.', 'limit': 'Images explicitly synthetic; postcall record is not observed OS Wait. No actual killed grant-aware CLI/powerloss. Not a Cartesian product; torn/orphan reset unexecuted. No new r3 concurrent CLI case; prior concurrency remains historical.'},
    {'id': 'COV02', 'status': 'PARTIAL_F03_BLOCKING', 'evidence': 'Fresh native actual copied parent+child hardlink, reparse, rename, final sharing, wrong parent tests pass; author SID/Host/Owner mismatch denied before attempt.', 'limit': 'Wrong expected SID is not foreign-user execution; hostile race unexecuted; unsafe initial ACL accepted.'},
    {'id': 'COV03', 'status': 'INTEGRATION_LIMIT_RETAINED', 'evidence': 'F02 source and fresh focused boundary/journal tests support zero signal and no refund.', 'limit': 'Full live Commit intent-after cancellation/expiry not executed.'},
    {'id': 'COV04', 'status': 'BOUNDED_TRUE_CLI_DANGER_DENIAL_SUPPORTED', 'evidence': 'Six author true-CLI cases STARTED/UNKNOWN/nonmodel/other run/other dispatch/control request return STALE_PLAN with live fixture. Full baseline compare denies first. Prior PREPARED and safety source inventory reviewed.', 'limit': 'Not each deeper SafetySnapshot branch independently reached. Pending client-command/old-subject variants not added as r3 true-CLI cases.'},
    {'id': 'COV05', 'status': 'BOUNDED_MALFORMED_CLI_SUPPORTED', 'evidence': 'Three malformed compiled-grant classes and two malformed CLI flag classes denied with no operation files, live fixture and readable-data equality. Source loads grant before FS/DB/native work. Own missing receipts and numeric unit cases pass.', 'limit': 'Readable file equality is not universal zero-open tracing; coordinator.lock unreadable and listed. Not all malformed grant fields through CLI.'}
]

nonzero = []
for c in captures:
    if c['native_exit'] == 0:
        continue
    n = Path(c['capture']).name
    if 'independent-unsafe-acl-v2' in n:
        kind = 'EXPECTED_FINDING_REPRODUCTION'
    elif 'independent-unsafe-acl-' in n:
        kind = 'MIXED_FINDING_REPRODUCTION_AND_HARNESS_ERROR'
    elif 'own-temp-cleanup-' in n or '-write-review-' in n:
        kind = 'DIAGNOSTIC_ERROR_RETAINED'
    elif 'preflight-binary-cannot-commit' in n or 'stop-binary-cannot-preflight' in n:
        kind = 'EXPECTED_ACTION_DENIAL'
    else:
        raise RuntimeError('unclassified nonzero: ' + n)
    nonzero.append({**c, 'classification': kind})

gaps = [
    {'id': 'R3-REVIEW-GAP-01', 'kind': 'bootstrap_read_capture', 'details': 'Initial AGENTS/card, memory registry, author matrix/helper/source-card reads occurred before own logger. Four native read commands have raw chat tool outputs but no own-E before/raw/after capture. No Source/actual mutation.'},
    {'id': 'R3-REVIEW-GAP-02', 'kind': 'own_evidence_writer_setup', 'details': 'Own directory/helper setup and script creation for read_candidate, overlays v1/v2, read_ledgers, audit_author, cleanup and initial report writer used visible shell code without separate logger capture of writing portion. Script bytes/derivations retained. First nested-quote report generator failed SyntaxError; missing script invocation exit2 captured. Subsequent report/manifest source files use direct apply_patch. Not complete shell-command coverage.'},
    {'id': 'R3-REVIEW-GAP-03', 'kind': 'embedded_native_exit_masked', 'capture': capref('source-inventory')['capture'], 'details': 'Unquoted HEAD^{tree} through Windows PowerShell rewrote git argv and produced fatal. Outer exit0 after successful reads masks individual native exit, which is not separately known. Corrected Python-argv read captured and asserted exact HEAD/tree/clean state.'},
    {'id': 'R3-REVIEW-GAP-04', 'kind': 'author_bootstrap_root_supplement', 'details': 'Root message confirms author 12:21:24 initial scope read before logger is separate from two post-reset Git read gaps and absent from frozen author ledger. Root will register in next CP. This is a Root-supplied audit supplement, not a Source defect; author files untouched.'},
    {'id': 'R3-REVIEW-GAP-05', 'kind': 'finite_snapshot_tail', 'details': 'Current report-writer and later manifest-seal completion lie after finite ledger snapshot. Complete command captures retained separately. Manifest excludes only its active capture and itself explicitly; no recursive self-hash claim.'}
]
ledger = {'schema': 'researchos.owned-core-stop-r3-independent-diagnostic-ledger.v1', 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'author_new_nonzero': {'total': 80, 'expected_denial': 71, 'diagnostic_errors': 9, 'unique_raw_before_after_verified': True, 'semantic_group_audit': capref('expected-denial-semantic-audit')['stdout'], 'historical63_recounted': False, 'audit': ref(e / 'author-evidence-audit.json')}, 'own_completed_captures': captures, 'own_nonzero': nonzero, 'own_nonzero_counts': dict(collections.Counter(x['classification'] for x in nonzero)), 'own_embedded_diagnostic_not_counted_as_captured_nonzero': 'R3-REVIEW-GAP-03', 'capture_gaps': gaps, 'cleanup': 'Own temporary root removed by cleanup-v2 after exact resolved boundary verification. First cleanup failed before removal due Windows PowerShell no-BOM decoding. Evidence and binaries retained.', 'formal_increment': 0}
write('diagnostic-ledger.json', ledger)

state = {}
for name, args in [('head', ['git', 'rev-parse', 'HEAD']), ('tree', ['git', 'rev-parse', 'HEAD^{tree}']), ('status', ['git', 'status', '--porcelain'])]:
    p = subprocess.run(args, cwd=w, capture_output=True)
    state[name] = {'argv': args, 'native_exit': p.returncode, 'stdout': p.stdout.decode().strip(), 'stderr': p.stderr.decode().strip()}
    assert p.returncode == 0
assert state['head']['stdout'] == '2816daacdb2c08ae8ee1d62c91bcd3f571d40737'
assert state['tree']['stdout'] == '67fc84be0238b724f7d0ec41eb4c8b688b0269f3'
assert state['status']['stdout'] == ''
review = {'schema': 'researchos.owned-core-stop-r3-independent-source-review.v1', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'reviewer': 'codex:/root/owned_core_stop_r3_review', 'model': 'gpt-6-astra', 'reasoning_effort': 'high', 'model_basis': 'CP517 scope and delegation', 'candidate': state['head']['stdout'], 'tree': state['tree']['stdout'], 'main_base': '4f4023c956f84d65743f39ce77d6c8899a21ada1', 'revision_base': 'f5db4a9639f1a50380eb5929ee6295887baeb756', 'whole_candidate_paths': 19, 'revision_paths': 7, 'verdict': 'NEEDS_CHANGES', 'findings': [finding], 'coverage': coverage, 'fresh_cases': cases, 'focused_regression': capref('focused-regression'), 'verified_author_references': 583, 'diagnostic_ledger': ref(e / 'diagnostic-ledger.json'), 'review_md': ref(e / 'review.md'), 'final_candidate_state': state, 'source_edits': False, 'main_edits': False, 'actual_authority': False, 'actual_or_current_root_used': False, 'formal_increment': 0, 'parent_acceptance': False, 'limits': ['Only new owned synthetic fixture processes/data. Historical fixture receipt labels are synthetic, not original product native Wait proof.', 'No Main/current product/actual operation/provider/model/W05 parent/formal case acceptance.', 'Boot recovery outside this card.']}
write('review.json', review)
print(json.dumps({'verdict': 'NEEDS_CHANGES', 'findings': 1, 'own_nonzero_counts': ledger['own_nonzero_counts'], 'review_json': ref(e / 'review.json'), 'review_md': ref(e / 'review.md'), 'ledger': ref(e / 'diagnostic-ledger.json'), 'candidate_final_state': state}, ensure_ascii=False, indent=2))
