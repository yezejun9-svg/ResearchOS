import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
E = R / 'execution/v2.4/receipts/W05/W05-99'
O = B / 'continuation-cp517'
BE = E / 'qualification_failure_b_source_codex/20261015-current-chat'
SE = E / 'owned_core_stop_proof_revision03_source_codex/20261015-current-chat/candidate-2816daac-final'
GE = E / 'git_automatic_gc_incident_codex/20261015-current-chat'
FE = E / 'qualification_boot_fence_input_map_codex/20261015-current-chat'
QE = E / 'qualification_recovery_boundary_decision_codex/20261015-current-chat'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def ref(p):
    data = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def new(p, obj):
    with p.open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def replace(p, before, after):
    assert p.read_bytes() == before
    tmp = p.with_name(p.name + '.cp517.pending')
    with tmp.open('xb') as f:
        f.write(after)
    assert p.read_bytes() == before
    os.replace(tmp, p)


assert ref(BE / 'FINAL.json')['sha256'] == 'e9048b3966ea5272775eb3026060c19c0a73175ee7916427d8bc743683ad7638'
assert ref(BE / 'B-evidence-manifest.json')['sha256'] == '111b9e46f84fbb9161b6c589c482e19d6e3cd464d42e7e7a197ab57cc8f844e7'
assert ref(SE / 'manifest.json')['sha256'] == 'a52bcca9a87c9f9693d0f16e5971619537a9b62a5f2bda9ac5f202d994d9b012'
assert ref(GE / 'COLLECTION-manifest.json')['sha256'] == '562e1893fcc36e6e0f5443b2ff02cb5cb823267738d0d5ebf53c8ee269dd3e3a'
assert ref(FE / 'COLLECTION-manifest.json')['sha256'] == '0de611578345548d2b2e65e18d30a258bf14e9fb810d6e5625bb924e93ac79ac'
cp_p, ow_p, hp, sp = [R / ('execution/v2.4/' + name) for name in ('checkpoint.json', 'path_ownership.json', 'HANDOFF_RESUME_PACK.md', 'step_state.json')]
raw = {p: p.read_bytes() for p in (cp_p, ow_p, hp, sp)}
cp, ow = read(cp_p), read(ow_p)
assert cp['revision'] == 516 and ow['revision'] == 302 and len(cp['failure_counters']) == 1738
O.mkdir(exist_ok=False)
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
git_index = []


def git(label, args, cwd=R):
    argv = ['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0'] + args
    recipe = O / (label + '.recipe.json')
    new(recipe, {'argv': argv, 'cwd': str(cwd), 'env_override': {}, 'read_only': True, 'at': now})
    p = subprocess.run(argv, cwd=cwd, capture_output=True)
    out, err = O / (label + '.stdout.raw'), O / (label + '.stderr.raw')
    out.write_bytes(p.stdout)
    err.write_bytes(p.stderr)
    result = {'recipe': ref(recipe), 'stdout': ref(out), 'stderr': ref(err), 'native_exit_code': p.returncode}
    new(O / (label + '.result.json'), result)
    git_index.append(result)
    assert p.returncode == 0, result
    return p.stdout


assert git('main-head', ['rev-parse', 'HEAD']).decode().strip() == '4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert not git('main-index', ['diff', '--cached', '--name-only'])
assert len(git('main-dirty', ['status', '--porcelain=v1', '--untracked-files=no']).splitlines()) == 20
for item in read(E / 'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    assert ref(R / item['path'])['sha256'] == item['sha256']
assert ref(R / '.git/config')['sha256'] == '1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
bm, sm = read(BE / 'B-evidence-manifest.json'), read(SE / 'manifest.json')
verified = {}


def verify(p, item):
    p = p.resolve()
    assert p.is_relative_to(R.resolve()), str(p)
    key = str(p)
    if key not in verified:
        verified[key] = ref(p)
    actual = verified[key]
    assert actual['sha256'] == item['sha256'] and actual['bytes'] == item['bytes'], (actual, item)


def nested(obj):
    if isinstance(obj, dict):
        if all(k in obj for k in ('path', 'sha256', 'bytes')):
            p = Path(obj['path'])
            if not p.is_absolute():
                p = R / p
            verify(p, obj)
        for value in obj.values():
            nested(value)
    elif isinstance(obj, list):
        for value in obj:
            nested(value)


for name, item in read(BE / 'FINAL.json')['files'].items():
    verify(BE / name, item)
for item in bm['command_ledger']:
    name = item['id']
    verify(BE / (name + '.recipe.json'), item['recipe'])
    result = read(BE / (name + '.result.json'))
    assert result['native_exit'] == item['native_exit']
    for stream in ('stdout', 'stderr'):
        verify(BE / (name + '.' + stream + '.raw'), {'sha256': item[stream + '_sha256'], 'bytes': result[stream + '_bytes']})
for name, item in bm['source'].items():
    verify(Path(bm['worktree']) / name, item)
    blob = git('B-source-' + str(len(git_index)), ['show', bm['candidate_commit'] + ':' + name])
    assert hashlib.sha256(blob).hexdigest() == item['sha256']
bp = git('B-full-patch', ['diff', '--binary', bm['base_commit'], bm['candidate_commit']])
assert bp == (BE / 'B-whole-source.patch').read_bytes()
bpaths = git('B-full-paths', ['diff', '--name-only', bm['base_commit'], bm['candidate_commit']]).decode().splitlines()
assert sorted(bpaths) == sorted(bm['source']) and len(bpaths) == 9
assert not git('B-clean', ['status', '--porcelain=v1', '--untracked-files=no'], Path(bm['worktree']))
nested(sm)
nested(read(Path(sm['command_capture_index']['path'])))
nested(read(GE / 'COLLECTION-manifest.json'))
nested(read(FE / 'COLLECTION-manifest.json'))
assert len(sm['source_files']) == 19 and len(sm['case_rows']) == 22
assert len(git('STOP-r3-paths', ['diff', '--name-only', sm['base_commit'], sm['commit']]).splitlines()) == 7
assert len(git('STOP-whole-paths', ['diff', '--name-only', sm['main_base'], sm['commit']]).splitlines()) == 19
assert git('STOP-r3-patch', ['diff', '--binary', sm['base_commit'], sm['commit']]) == Path(sm['delta_patch']['path']).read_bytes()
assert git('STOP-whole-patch', ['diff', '--binary', sm['main_base'], sm['commit']]) == Path(sm['whole19_patch']['path']).read_bytes()
assert not git('STOP-clean', ['status', '--porcelain=v1', '--untracked-files=no'], Path(sm['worktree']))
new(O / 'root-input-verification.json', {'verified_unique_files': len(verified), 'files': list(verified.values()), 'B_paths': bpaths, 'STOP_r3_paths': 7, 'STOP_whole_paths': 19, 'STOP_case_rows': 22, 'semantic_acceptance': False})
new(O / 'git-command-index.json', git_index)

common = {'at': now, 'model': 'gpt-6-astra', 'reasoning_effort': 'high', 'formal_increment': 0, 'actual_authority': False, 'source_edit_authority': False}
bs = dict(common, schema='researchos.qualification-failure-B-independent-source-review.v1', owner='codex:/root/qualification_failure_b_review',
    model_choice_reason='Security and transaction/concurrency proof needs independent architecture review', candidate=bm['candidate_commit'], tree=bm['candidate_tree'], base=bm['base_commit'],
    worktree=bm['worktree'], own_receipts=str(E / 'qualification_failure_b_independent_review_codex/20261015-current-chat'), own_temporary_root=str(R / '.local/qualification-failure-b-independent-review-20261015'),
    inputs=[ref(BE / 'FINAL.json'), ref(BE / 'B-evidence-manifest.json'), ref(BE / 'B-author-report.md'), ref(BE / 'B-diagnostic-ledger.md'), ref(B / 'continuation-cp512/qualification-failure-B-source-scope.json'), ref(GE / 'COLLECTION-manifest.json')],
    requirements=[
        'Read complete CP512 B scope, its frozen architecture/testcut/classification/accepted-A inputs, complete9path diff and production callers. No Source/Main/shared/actual data/native current process/private config changes. You are not alone: STOP-r3 review and readonly boot supplement design run independently. Only own evidence/test overlay/temp writes. Any Git write must disable both automatic maintenance and GC per invocation; no GC/repack/prune/config/old log cleanup.',
        'Verify actual typed first dispatchGate constructor before prepareEffectTx, all subject/marker/profile/hash/known-route/frame3 bindings and zero rejected-key effect/ledger histories; no text matching/secondgate/generic conversion. Receipt create-new/private/nonreparse ancestor/flush and persistence failure UNKNOWN. Inspect TOCTOU and single resourceWriteLock boundary.',
        'Review broker registry admission fence/cancel/join every admitted broker exactly once, bounded wait and duplicate/missing/extra suffix handling. Actual pending broker/suffix must disqualify derived FAILED. Heartbeat cancellation/join must precede frozen CAS. Check ordinary generic path regressions and goroutine lifetime; first cause retention cannot hide later disqualifying facts. Raw ACK2/frame3/queue_empty=false remains unchanged.',
        'Review source-bound raw native stopped/drained/cleanup/output evidence and all domain effect/queue/control/checkpoint census. FAILED-only transaction exact version/row shape with real authenticated Host author, sealed uploaded_content1 vs runtime_uploads/artifact_uses/proofs0, replay0 and atomic rollback at every actual writer. Preserve Task/requests/budget/costUNKNOWN/schema/native facts. Review real private validatedQualificationFailureTx consumer against all tamper/revocation paths, especially current Owner-root revocation which author explicitly did not test separately. No stub C/D historical authority.',
        'Run fresh focused local domain+adapter tests and at least one meaningful independent negative addressing an unresolved production concern; use task-owned overlay of copied allowed test file if package-private access needed, never modify frozen Source/fixtures. Native local loopback permitted only owned fresh fixtures, external/current model/Ollama calls0. Do not call live original root/process/status wrappers. Respect b75 orphan and old denied cleanup paths; no unrelated full historical test reruns.',
        'Audit B01-12 mapping and classify missing tests versus actual defects. Verify authorraw recipes/results; 22nonzero/unavailable +3preexec +aggregate uncapturedreads+b82stderr+b91GC deviation already preserved by Root; do not reset/recount as productfailures. Owner-root earlier tested claim was overstatement corrected by author. Root containment proves selected object/header availability only, historical missing62 remains. Independent namespace is not protected holdout.',
        'Freeze review.md/review.json with LIMITED_SOURCE_ACCEPTED or NEEDS_CHANGES, exact findings/line numbers/minimal paths/coverage limits and test evidence, diagnostic/failure/gap ledger + manifest. No author self-acceptance/Main/package/actual/formal acceptance. If defects found, report early then freeze finite review rather than fix Source yourself.'
    ])
ss = dict(common, schema='researchos.owned-core-stop-r3-independent-source-review.v1', owner='codex:/root/owned_core_stop_r3_review',
    model_choice_reason='Independent native authority/proof/cancellation/path protection review', candidate=sm['commit'], tree=sm['tree'], base=sm['base_commit'], main_base=sm['main_base'], worktree=sm['worktree'],
    own_receipts=str(E / 'owned_core_stop_proof_revision03_independent_review_codex/20261015-current-chat'), own_temporary_root=str(R / '.local/owned-core-stop-r3-independent-review-20261015'),
    inputs=[ref(SE / 'manifest.json'), ref(Path(sm['claim_to_test_matrix']['path'])), ref(Path(sm['failure_and_gap_ledger']['path'])), ref(B / 'continuation-cp516/owned-core-stop-proof-revision03-source-scope.json'), ref(E / 'owned_core_stop_anchor_revision02_independent_review_codex/20261015-current-chat/evidence-manifest.json')],
    requirements=[
        'Review entire19path candidate fromMain4f and7deltafrom rejectedf5, CP516 exactscope and r2 independent3findings/5coveragegaps. NoSource/Main/shared/actualprocess/currentroot/otherauthor evidence changes. Own E/temp/owncopiedharness/fixturebinary only. OtherBreview+bootdesign run independently. Git writes per-command disableautomaticmaintenance+gc; noGC/repack/prune/config/logcleanup.',
        'F01 native receipt fields bothworker/verifier presence-awareuint32/missing/null/0/nonzero/wait explicit WAIT_OBJECT_0; numericmalformed/crossclass preservedstrict. Independently run fresh true compiled two-grant/nonemptySQLite positive and targeted missing/nativefield negative; preflight refusal correctly means noSTOPgrant minted. No syntheticfactpresentedasoriginalWait.',
        'F02 earliestdeadline/callerctx carried to exact retainednative boundary and checked beforeintent, afterdurableintent, afterprewait and beforeoneTerminate. Expiry/cancelafterintent zero-signal permanentconsumption. Carefully assess new callback/boundaryunit tests versus untested fullCommit afterintent cancellation; productionpath evidence must suffice or identifyminimal necessary gap. No test-only production approval switch.',
        'F03 retainedCore+parentimageancestorhandles strictnonreparseowner/DACL/identity/denywrite/delete acrossopen/action; samefinalretainedimagehash andID, reverseclose. Review nativeACL inheritedpermission behavior on realWindows, actualsource code not EvalSymlinks assertion. Fresh own copiedimage/junction/hardlink/sharing tests as necessary; foreignexpectedSID is not genuineforeign-user process, and sequentialmutation is not an observedhostilerace.',
        'COV01-05 durable oneintent reentry/crashgrammar/thirdgrant/preflightreset/concurrency/S209inventory/malformedcompiledgrant all meaningful; synthetic journal images honestly labeled and not actualpowerfailure. Classify author80newnonzero71expected9diagnostic plus actual gaps, do not duplicateold63 or harnesssummary. Scopebootstrapreadgap clarification may arrive separately. Distinguish materialdefects from unexercised nativeassumptions; retain all limits.',
        'Own commandrecipes BEFORE execution/raws/nativeexits/failures/gaps, Dtemps. Can copy pinned authorrun_logged/fixture_e2e_r3 helpers into ownE, change ONLY own ROOT/WORKTREE/FIXTURE/temp/cache constants and pin derivation; build OWNfixture from candidate. No privatekey/originalCore/currentDB/model/OSrestart. For additionalpackageprivatetests use ownGooverlay withoutmutating Source. Freeze finite review.md/json +diagnostic ledger +manifest, verdictLIMITED_SOURCE_ACCEPTEDorNEEDS_CHANGES withexactminimalfixpaths. Newbootclass outsidecard; noactual/formalincrement.'
    ])
qs = dict(common, schema='researchos.qualification-recovery-boot-supplement-design.v1', owner='codex:/root/qualification_boot_design',
    model_choice_reason='Security-sensitive recovery startup/fence authority must be concrete before any new Source or actual action',
    own_receipts=str(E / 'qualification_recovery_boot_supplement_architecture_codex/20261015-current-chat'),
    inputs=[ref(QE / 'FINAL-manifest.json'), ref(QE / 'boundary-decision.md'), ref(QE / 'boundary-decision.json'), ref(FE / 'COLLECTION-manifest.json'), ref(FE / 'INPUT-MAP.json'), ref(B / 'continuation-cp513/RESUME.current.json'), ref(E / 'qualification_failure_revision02_architecture_codex/20261015-current-chat/C-ARCHITECTURE.md'), ref(E / 'qualification_failure_revision02_architecture_codex/20261015-current-chat/C-exact-scope.json'), ref(BE / 'FINAL.json')],
    query_group_limit=12,
    requirements=[
        'Readonly finite design supplement after adopted bounded decision; do not repeat initsemantic/globalarchitecture search. Max12 grouped reads/spec/officialAPIqueries afterinputintake. NoSource/testcode/actualOSprobes/currentDB/API/privatekey/model/nativefence/deployment/restart/launch/stop actions. BSourceandSTOPreviewsparallel. Main4f and actualresource inventories are inputs only, notloadedbytes/completeentrycoverage proof.',
        'Read frozen decision, actualpublicpackage/knownimage inputmap, C51 sourcecontract and BprivatevalidatedTx current75 candidate. Produce complete specific C+bootSource card proposal: C startup/journal/maintenance integration plus six newbootmodule/CLI paths, exact paths/versions and testcuts, no broadunbounded expansion. B remainsunaccepted: proposed Cbase depends acceptedB; noSourceauthority now.',
        'Resolve cycle onlineprephase cannot take rootexclusivelease, needs separatelyacceptedusableconsistentonlinebackup and productidentities beforearm; existingold/current binaries willignore newjournal. Concrete persistent externalWindows/launcher fence must cover actual installedlegacy/currentCore/verifier/Desktop/CLI/restart/autostart documentedlaunchsurfaces and survive userFullRestart. Define inputinventory completeness/exactnativeimageIDs+hashes/ancestorretention/ACLownership/readback/anti-swap, failure/recovery/unfence authority and noaccidentalpermanentlockout. Do not silently assume two observedPIDs equalsallentrycoverage or DACL-writealone proves prevention.',
        'Choose smallest supportable mechanism for actualentryfence. If oldentry/rootACL/nativeprimitive cannot be proved within boundedfacts, return an explicitfinite noimplementablecardwithminimalmissingresource instead of another speculative architecture loop. No universalOSnoeffect or historicalwaitcompletion claim. UsermalicioussameSID/rootadmin assumptions explicit without weakening actualproductcontracts.',
        'Define pre/post trustedwitness samehost/SID/root/DBfile immutableidentity with postnativeuptimelesspre +LastBootcorroboration, stale/replay/tamper/freshness, supportedWindows/noVMrollbackassumption; userexplicitFullRestart resource lateronly. Afterfenceverifiedandnewbootobserved, acquire/retainrealrootlease, currentcensusandCown-operationpermit; rejectexternalUNKNOWN and existingnarrowB/Host/effectrequirements unchanged. OldrawACK/Wait/cost/failurehistoryunchanged. ExistingstrictSTOPproofclasses unchanged;bootclassonlyseparateaccepted Cauthority later.',
        'Deliver BOOT-C-ARCHITECTURE.md, C-boot-exact-scope.json, C-boot-test-cuts.json, actual-deployment-plan-reviewable.md or finiteblockeddecision, preciseBAPIcompatibilitynotes, diagnostic/rawcommand/gapledger andFINAL-manifest. All proposedclassNOT_IMPLEMENTED_NOT_ACCEPTED, actual_authorityfalse, noUserRestartrequest. Noauthoracceptance; independentdesignreview requiredbeforeSource. Make result reviewable, finite and implementation-specific.'
    ])
for name, obj in [('qualification-failure-B-independent-review-scope.json', bs), ('owned-core-stop-r3-independent-review-scope.json', ss), ('qualification-boot-supplement-design-scope.json', qs)]:
    new(O / name, obj)

old = list(cp['failure_counters'])
items = []
for item in bm['command_ledger']:
    if item['native_exit'] != 0:
        items.append(('B-' + item['id'], 'SOURCE_AUTHOR_NONZERO_OR_UNAVAILABLE_NATIVE_PRESERVED', item, ref(BE / 'B-evidence-manifest.json')))
assert len(items) == 22
for tag in ('b09', 'b15', 'b20'):
    items.append(('B-recipe-' + tag, 'SOURCE_AUTHOR_PREEXECUTION_RECIPE_ERROR', {'id': tag, 'native_process_executed': False}, ref(BE / 'B-diagnostic-ledger.md')))
items += [
    ('B-uncaptured-read-aggregate', 'SOURCE_AUTHOR_READONLY_CAPTURE_GAP_AGGREGATE', {'individual_count_unavailable': True}, ref(BE / 'B-diagnostic-ledger.md')),
    ('B-b82-nonterminating-cleanup-error', 'SOURCE_AUTHOR_STDERR_ERROR_NATIVE_ZERO', {'command': 'b82', 'native_exit': 0}, ref(BE / 'B-diagnostic-ledger.md')),
    ('B-b91-automatic-gc-deviation', 'SOURCE_AUTHOR_GIT_EXECUTION_DEVIATION_AUTOMATIC_GC_FAILED', {'command': 'b91', 'native_exit': 0, 'root_containment_ref': ref(GE / 'COLLECTION-manifest.json'), 'history_not_repaired': True}, ref(BE / 'FINAL.json')),
    ('B-owner-root-test-overstatement', 'SOURCE_AUTHOR_COVERAGE_OVERSTATEMENT_CORRECTED', {'actual': 'Current Owner-root revocation was not separately injected; use narrower frozen report'}, ref(BE / 'B-author-report.md')),
    ('root-input-directory-display-truncated', 'ROOT_READONLY_OUTPUT_CAPTURE_LIMIT', {'tool_chunk': '4cb00f', 'detail': 'Unnecessarily large filename listing; corrected to bounded selected JSON; no file mutation'}, ref(GE / 'COLLECTION-manifest.json')),
    ('root-gc-check-missing-parent', 'ROOT_HELPER_SETUP_FAILURE_PRESERVED', {'native_exit': 1, 'result_ref': ref(B / 'check-git-gc-incident.result.json'), 'detail': 'Evidence mkdir initially omitted parents=True; second invocation succeeded, originals retained'}, ref(B / 'check-git-gc-incident.stderr.raw')),
]
assert len(items) == 31
sl = read(Path(sm['failure_and_gap_ledger']['path']))
assert len(sl['root_command_nonzero']) == 80
for i, item in enumerate(sl['root_command_nonzero'], 1):
    items.append(('STOP-r3-native-' + str(i), 'SOURCE_AUTHOR_MIXED_NONZERO_REQUIRES_INDEPENDENT_CLASSIFICATION', item, ref(Path(sm['failure_and_gap_ledger']['path']))))
for i in range(2):
    items.append(('STOP-r3-readonly-git-capture-gap-' + str(i + 1), 'SOURCE_AUTHOR_READONLY_COMMAND_CAPTURE_GAP', {'detail': sl['capture_gaps'][0], 'group_ordinal': i + 1}, ref(Path(sm['failure_and_gap_ledger']['path']))))
assert len(items) == 113
for suffix, status, detail, er in items:
    origin = '20261015|cp517-' + suffix
    assert not any(x.get('origin_key') == origin for x in old)
    cp['failure_counters'].append({'origin_key': origin, 'attempts': 1, 'status': status, 'detail': detail, 'evidence_ref': er, 'counter_reset': False})
assert cp['failure_counters'][:1738] == old and len(cp['failure_counters']) == 1851
resume = read(B / 'continuation-cp516/RESUME.current.json')
resume.update(schema='researchos.current-chat-resume.v95', at=now, checkpoint_revision=517, ownership_revision=303, failure_records_preserved=1851,
    B_source_final_ref=ref(BE / 'FINAL.json'), B_source_status='FROZEN_NOT_INDEPENDENTLY_ACCEPTED', B_independent_review_scope_ref=ref(O / 'qualification-failure-B-independent-review-scope.json'),
    owned_stop_r3_source_final_ref=ref(SE / 'manifest.json'), owned_stop_r3_source_status='FROZEN_NOT_INDEPENDENTLY_ACCEPTED', owned_stop_r3_review_scope_ref=ref(O / 'owned-core-stop-r3-independent-review-scope.json'),
    git_automatic_gc_incident_ref=ref(GE / 'COLLECTION-manifest.json'), boot_fence_input_map_ref=ref(FE / 'COLLECTION-manifest.json'), boot_supplement_design_scope_ref=ref(O / 'qualification-boot-supplement-design-scope.json'), active_source_cards=[])
resume['next_command'] = 'Independent astra review frozen B75 exact9 and STOP2816 full19/r3delta7; finite readonly Cboot implementation-specific design supplement max12queries. NoSourceC or actualRestart/fence/stop/model authority. Gitb91 automaticGCdeviation preserved; currentMain/A/B selectedtreeheaders available,064d alreadyoldmissing62, nohistoryrepair. Main4f/dirty20/protected9/indexempty/config/step_state unchanged. Formal0/42/all22open.'
new(O / 'RESUME.current.json', resume)
rr = ref(O / 'RESUME.current.json')
cp.update(revision=517, expected_previous_revision=516, updated_at=now, updated_by='codex:/root', next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp517=rr, B_source_final_ref=ref(BE / 'FINAL.json'), owned_stop_r3_source_final_ref=ref(SE / 'manifest.json'), git_automatic_gc_incident_ref=ref(GE / 'COLLECTION-manifest.json'))
cp['evidence_index'].append({'kind': 'B_AND_STOP_R3_FROZEN_REGISTER_TWO_REVIEWS_AND_READONLY_BOOT_DESIGN_GIT_INCIDENT_PRESERVED', 'ref': rr, 'formal_increment': 0})
ow.update(revision=303, expected_previous_revision=302, updated_at=now, updated_by='codex:/root')
ow['special_paths']['owned_stop_r3_source'].update(state='FROZEN_REQUIRES_INDEPENDENT_REVIEW', evidence_ref=ref(SE / 'manifest.json'))
for key, scope, filename, mode in [('qualification_failure_B_independent_review', bs, 'qualification-failure-B-independent-review-scope.json', 'READONLY_SOURCE_REVIEW_OWN_FIXTURES'), ('owned_stop_r3_independent_review', ss, 'owned-core-stop-r3-independent-review-scope.json', 'READONLY_SOURCE_REVIEW_OWN_FIXTURES'), ('qualification_boot_supplement_design', qs, 'qualification-boot-supplement-design-scope.json', 'READONLY_BOUNDED_DESIGN')]:
    ow['special_paths'][key] = {'owner': scope['owner'], 'mode': mode, 'state': 'REGISTERED', 'scope_ref': ref(O / filename), 'write_scope': [scope['own_receipts']] + ([scope['own_temporary_root']] if 'own_temporary_root' in scope else []), 'actual_authority': False, 'source_edit_authority': False}
for key, value in ow['special_paths'].items():
    if isinstance(value, dict) and value.get('owner') == 'codex:/root/qualification_projection_builder' and value.get('state') in ('REGISTERED', 'ACTIVE'):
        value.update(state='FROZEN_REQUIRES_INDEPENDENT_REVIEW', evidence_ref=ref(BE / 'FINAL.json'))
for p, filename in ((cp_p, 'checkpoint.before.raw.json'), (ow_p, 'ownership.before.raw.json'), (hp, 'handoff.before.raw.md')):
    (O / filename).write_bytes(raw[p])
for p, data in raw.items():
    assert p.read_bytes() == data
replace(ow_p, raw[ow_p], (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode())
replace(cp_p, raw[cp_p], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode())
replace(hp, raw[hp], ('# Current verified continuation CP517\n\nRead `' + rr['path'] + '` first. B75 and STOP2816 frozen, two independent reviews and finite readonly boot supplement design registered. Git GC execution deviation preserved and selected current trees remain available; no history repair. Formal0/42/all22open; mixed preserved records1851. No actual/new SourceC authority.\n\n').encode() + raw[hp])
assert sp.read_bytes() == raw[sp]
print(json.dumps({'checkpoint': 517, 'ownership': 303, 'preserved_mixed_records': 1851, 'resume': rr, 'verified_unique_files': len(verified), 'scopes': [ref(O / p) for p in ('qualification-failure-B-independent-review-scope.json', 'owned-core-stop-r3-independent-review-scope.json', 'qualification-boot-supplement-design-scope.json')]}))
