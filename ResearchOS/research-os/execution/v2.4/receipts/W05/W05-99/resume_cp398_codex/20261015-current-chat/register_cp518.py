import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
E = R / 'execution/v2.4/receipts/W05/W05-99'
O = B / 'continuation-cp518'
BI = E / 'qualification_failure_b_independent_review_codex/20261015-current-chat'
SI = E / 'owned_core_stop_proof_revision03_independent_review_codex/20261015-current-chat'
QI = E / 'qualification_recovery_boot_supplement_architecture_codex/20261015-current-chat'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def ref(p):
    v = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'sha256': hashlib.sha256(v).hexdigest(), 'bytes': len(v)}


def new(p, v):
    with p.open('x', encoding='utf8') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write('\n')


def replace(p, before, after):
    assert p.read_bytes() == before
    q = p.with_name(p.name + '.cp518.pending')
    with q.open('xb') as f:
        f.write(after)
    assert p.read_bytes() == before
    os.replace(q, p)


assert ref(BI / 'FINAL-manifest.json')['sha256'] == '9f8a27dd579d33179f2ef7b2ca98f87836ae308d75e095605c1276d3deb79e1a'
assert ref(SI / 'evidence-manifest.json')['sha256'] == '7d28a8f61f4a74e528dc571f106b13a7879d16a05880a3d3cb378d8680124d87'
assert ref(QI / 'FINAL-manifest.json')['sha256'] == 'a4237a000b8a73af47cb45514057947f913be6e6b11771f37e0628a3407bbad5'
verified = {}


def verify(p, v):
    p = p.resolve()
    assert p.is_relative_to(R.resolve()), str(p)
    if str(p) not in verified:
        verified[str(p)] = ref(p)
    a = verified[str(p)]
    assert a['sha256'] == v['sha256'] and a['bytes'] == v['bytes'], (a, v)


def nested(v, parent):
    if isinstance(v, dict):
        if all(k in v for k in ('path', 'sha256', 'bytes')):
            p = Path(v['path'])
            if not p.is_absolute():
                p = (parent / p) if (parent / p).exists() else R / p
            verify(p, v)
        for item in v.values():
            nested(item, parent)
    elif isinstance(v, list):
        for item in v:
            nested(item, parent)


for directory, filename in ((BI, 'FINAL-manifest.json'), (SI, 'evidence-manifest.json'), (QI, 'FINAL-manifest.json')):
    m = read(directory / filename)
    nested(m, directory)
    if isinstance(m.get('files'), dict):
        for name, item in m['files'].items():
            verify(directory / name, item)
br, sr, qr = read(BI / 'review.json'), read(SI / 'review.json'), read(QI / 'C-boot-exact-scope.json')
assert br['status'] == sr['verdict'] == 'NEEDS_CHANGES'
assert len(br['findings']) == 3 and len(sr['findings']) == 1
bpaths = br['minimal_repair_paths']
spaths = sr['findings'][0]['minimal_fix_paths']
assert len(bpaths) == 5 and len(spaths) == 2
assert qr['counts']['total'] == 57 and not qr['source_card_issuable_now']
cp_p, ow_p, hp, sp = [R / ('execution/v2.4/' + p) for p in ('checkpoint.json', 'path_ownership.json', 'HANDOFF_RESUME_PACK.md', 'step_state.json')]
raw = {p: p.read_bytes() for p in (cp_p, ow_p, hp, sp)}
cp, ow = read(cp_p), read(ow_p)
assert cp['revision'] == 517 and ow['revision'] == 303 and len(cp['failure_counters']) == 1852
assert subprocess.check_output(['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0', 'rev-parse', 'HEAD'], cwd=R, text=True).strip() == '4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert not subprocess.check_output(['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0', 'diff', '--cached', '--name-only'], cwd=R)
assert len(subprocess.check_output(['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=R).splitlines()) == 20
for item in read(E / 'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    assert ref(R / item['path'])['sha256'] == item['sha256']
assert ref(R / '.git/config')['sha256'] == '1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
O.mkdir(exist_ok=False)
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O / 'root-input-verification.json', {'unique_refs_verified': len(verified), 'refs': list(verified.values()), 'semantic_source_verdicts_adopted': ['B_NEEDS_CHANGES', 'STOP_R3_NEEDS_CHANGES'], 'boot_design_adopted_only': 'Finite resource decision, no Source or mechanism acceptance'})
shared = {'at': now, 'model': 'gpt-6-sol', 'reasoning_effort': 'high', 'model_choice_reason': 'Bounded independently reproduced exact-path repairs; independent astra review required after freeze', 'formal_increment': 0, 'actual_authority': False, 'self_acceptance': False}
bs = dict(shared, schema='researchos.qualification-failure-B-revision02-source.v1', owner='codex:/root/qualification_projection_builder',
    base_commit=br['candidate'], base_tree=br['tree'], base_status='NEEDS_CHANGES_NOT_ACCEPTED',
    worktree=str(R / '.local/worktrees/qualification-failure-b-r2-20261015'), branch='codex/qualification-failure-b-r2-20261015',
    own_receipts=str(E / 'qualification_failure_b_revision02_source_codex/20261015-current-chat'), own_temporary_root=str(R / '.local/qualification-failure-b-r2-20261015-tmp'), source_allowlist=bpaths,
    inputs=[ref(BI / 'FINAL-manifest.json'), ref(BI / 'review.md'), ref(BI / 'review.json'), ref(BI / 'diagnostic-ledger.json'), ref(B / 'continuation-cp512/qualification-failure-B-source-scope.json')],
    copied_findings=br['findings'], copied_coverage=br['coverage'],
    requirements=[
        'Own NEW exactbase75 worktree/branch, exactly5 Source/test paths. Do not edit frozen75/f48/Main/spec/current actualroot/Core/Desktop/Ollama/targetCLI2files/privateconfigs or Source25. Not alone: STOP-r4 Source and readonlyofficialentryresourcecollection run in parallel. Root alone shared checkpoint/ownership/handoff. No historicalC/D/new proof class or model calls. Every Git write including worktreeadd/stage/commit has -c maintenance.auto=false -c gc.auto=0, explicitpaths; NO GC/repack/prune/config/oldlog cleanup.',
        'B-F01 native owner/ACE privacy check for directories AND sourcefile, reject unauthorized explicit/inherited write/delete/WRITE_DAC/WRITE_OWNER, handle INHERIT_ONLY and unknown unsupportedACE failclosed, use precise trustedsubjects per existingprivatecontract. D:P/currentSID substrings insufficient. Open/check/retain native nonreparse no-delete/rename identity guards across create-new/write/flush/read; samefinalnativehandle identity/hash, reverseclose. Do not harden caller unsafepaths to make accepted, no relaxedpermissions. Add real safe ACL positive and protected currentSID+Everyone/Users direct/inherited negatives on write and read, unsafefile/reparse/ancestor/identity cuts and persistence/write/flushfailure conservative UNKNOWN.',
        'B-F02 restore COMPLETE basef48 original runtime_command_queue_windows_test.go content and helpers/semantics (356lines approximately), then APPEND newregistry tests. No delete/Skip/weakening old failures. Run focused original3queue tests with existingfrozenlocalMu bundle/resources; if resource missing report exact and preserve blocked/skip, do not label regressionPASS. Current5path delta must visibly restore every deletedoldtestassertion/helper.',
        'B-F03 bind exact sole MODEL subject/epoch/key/sequence/history, canonical request/request_hash/route/capability/credentialrevision and canonical receipt/receipt_id/provider_response_hash to actualackframe2 and durableHost MODEL fact+responsebytes; sealedproof/marker/plandigest fixall digests. Consumer reloads+recomputes, rejects request/receipt/key/route/history tamper with proof/marker unchanged. Define canonicalobject Hash versus raw frame/source Digest explicitly, never replace rawfacts or collapsemoneyUNKNOWN. PreserveONLINE-onlyprivatevalidatedTx(nohistoricalstub/D productioncaller). Add validbaseline then eachsinglemutation negative, including independentlyreproducedreceipt_id and companionrequesthash/body/route/revision/receiptresponse/history controls, actualOwner-root/grantlineagerevocation.',
        'Fix FirstGateRefusalMatrix valid TOOL arguments map and add unmodifiedvalidpositivecontrol that reachesexactfirstgate. Eachhistory/stage mutant startsvalid and isolates PREPARED/STARTED/CONFIRMED/FAILED/UNKNOWN/compensated/ledger history, subject/lease/technical/marker/route distinctions; secondgate/generic remainUNKNOWN. Never claim late branch coverage from earlier malformedpayload refusal.',
        'Close meaningful B05/06/08/10 gaps withinallowed5paths: persistedreceiptfailure; productionpostdenialsuffix/lateauxMODEL observations and boundeddraintimeout; eachrequirednativecleanup/drained/stopped/output identityfield missing/tampered; enumerate ALL actualtransactionwriters including ImpactLink/domain_refs and trueCOMMITfailure or exact missingprimitive report, everyfailure atomic rollback. Positive full five-version + alltable logical census and unchanged forbidden tables; true completed-marker closure replay calls closeOnlineQualificationFailure branch (not RunAdmitted terminalrefusal), proves0delta; wrongmarker/subject replayrefused. Do not add production authorization switch or broadStore/schema bypass for tests. Fixtures may add own transaction constraints/overlays with provenance but no original DB mutation.',
        'Keep original raw3/ACK2/queue_empty=false/nativeexit facts; FAILED-onlyschema24 exact5versions/uploaded_content1 +enumeratedancillary/runtime_uploads&uses&proofs0, current authenticatedHostauthor/currentOwner-root, rollback/CAS/replay. Task/request/budget/moneyUNKNOWN/failcounts/schema/actualeffects unchanged. Preserve firstcause but extra laterfacts still disqualify. No unrelated broad historical tests once specific checks passed.',
        'All commands recipewritten BEFORE execution; actualargv/cwd/relevantenv/rawstdout/rawstderr/nativeexit/fail/skips/gaps. NewownDtemps/cache/taskfixture, no olddeniedcleanup retries. Gofmt only5paths. Freeze cleancommit/tree, allsourcehashes, exact5deltafrom75 +WHOLEcombined9Bpatchfromf48 and combinedA+Bpathlist; explicitpatchflags/argv. Completeclaim-testmatrix/commandindex/diagnosticledger+FINAL. Preserve original29Brecords and reviewfailures, never reset. Independentastra needed beforeSource/Main/package/actual/formal.'
    ])
ss = dict(shared, schema='researchos.owned-core-stop-authority-revision04-source.v1', owner='codex:/root/owned_core_stop_builder',
    base_commit=sr['candidate'], base_tree=sr['tree'], base_status='NEEDS_CHANGES_NOT_ACCEPTED',
    worktree=str(R / '.local/worktrees/owned-core-stop-authority-r4-20261015'), branch='codex/owned-core-stop-authority-r4-20261015',
    own_receipts=str(E / 'owned_core_stop_authority_revision04_source_codex/20261015-current-chat'), own_temporary_root=str(R / '.local/owned-core-stop-authority-r4-20261015-tmp'), source_allowlist=spaths,
    inputs=[ref(SI / 'evidence-manifest.json'), ref(SI / 'review.md'), ref(SI / 'review.json'), ref(SI / 'diagnostic-ledger.json'), ref(B / 'continuation-cp516/owned-core-stop-proof-revision03-source-scope.json')], copied_findings=sr['findings'], retained_coverage_limits=sr['coverage'],
    requirements=[
        'Own NEW exact2816 worktree/branch, only2supervisorfiles. Not alone: B-r2 Source and readonlyentryresources parallel; Root alone sharedstates. No frozenf5/2816/Main/otherSource/actualCore/Desktop/currentdata/privatesigner/model/bootclass changes. Git EVERYwrite including worktree/stage/commit explicit disablemaintenance.auto+gc.auto andexplicitpaths; noGC/repack/prune/config/logcleanup.',
        'Fix STOP-R3-F01/priorF03 once completely: explicit justified authorizedowner set and nativeACE policy for everyCore+parentimagecomponent. Distinguish currentoperator and trustedOS/installowner correctly; unauthorizedvalidSID not enough. Reject unauthorizedmodify/write/delete/control via direct+inherited ACE, correctly interpretinherit-only/directoryrights/genericmasks andunknownunsupportedtypes failclosed. No broadACLrelaxation or repairing unsafeinputtoaccept. Preserve samefinalretainednativehandle hash/ID, nonreparse/hardlink, ancestoridentityguards and reverseclose.',
        'Ancestor FILE_SHARE_WRITE must be removed where semantics permit OR exactequivalentlystrong nativeprotectionagainst relevantselectedpathmutation mustbeproved with tests and boundedreasoning. Do not claim openingGENERIC_WRITEalone provesrenameexploit; do not freezeunsafeinitialSDDLasauthorization. Native pathowner/ACL continuitycheckedatretainedaction boundary. Avoid blanketpolicy that passesonlysyntheticprivatepathbutrejectsall legitimateOSancestorpaths; validate safe actualcopiedparentchildpositive under supportedWindows and explicitly classifyuntrustedinstallation refusal.',
        'Add independentrepro-derived Everyone/Users direct/inheritedwrite/control negatives for finalimage andancestor, safeACLpositive, ownerpolicy allowed/disallowed cuts, INHERIT_ONLY/malformed/unsupportedACE cuts. True retaineddirectorywrite/reparse/rename/hardlink/finalsharing/wrongparent checks as warranted. Ownfreshcompiledtwo-grantnonemptySQLitepositive stilloneTerminate+numericwait+postflight. Existingmissingfieldnegativesremainpreflightdeny/noSTOPgrant. Nooriginalprocess touched.',
        'F01/F02 priorSource+boundarysupport retained; fullCommitafterownintentcancel, actualforeignuser/hostilerace/powerfail anddeeperSafetySnapshotbranches remainexplicitlimits unlessnewdynamicproof. Do not expand2pathscope to introduceproductionapprovalhook or rerunalloldmatrixwithoutnewconcern. R3author80classified71expected9diagnostic alreadypreserved; Rootseparateinitialscopegap retained. No counterreset/doublecounts.',
        'Recipe/argv/cwd/relevantenv BEFORE EVERYcommand inclbootstrapreads; ownnewDtemp/helpercopiespinned/diffs/rawstdoutstderr/nativeexit/fail/gapledger. Gofmt2paths only; cleanatomicexplicitcommit allowed. Freeze candidatehash/tree, exact2deltafrom2816 andwhole19fromMain4f, sourcepins, meaningfultestmatrix/commandindex/diagnosticledger/manifest. Independentastra Sourceacceptance required beforeMain/package/actual/formal. No bootproofclass changes.'
    ])
rs = {'schema': 'researchos.official-entry-and-backup-readonly-resource-scope.v1', 'at': now, 'owner': 'codex:/root/qualification_boot_design', 'model': 'gpt-6-astra', 'reasoning_effort': 'high', 'model_choice_reason': 'Bounded public source/Windows registration inventory for security-sensitive known mechanism; no implementation', 'actual_authority': False, 'read_only_resource_metadata_authority': True, 'source_edit_authority': False, 'formal_increment': 0,
    'own_receipts': str(E / 'qualification_official_entry_resource_map_codex/20261015-current-chat'),
    'root_parallel_source_receipts': str(E / 'online_backup_source_resource_map_codex/20261015-current-chat'),
    'inputs': [ref(QI / 'FINAL-manifest.json'), ref(QI / 'minimal-resource-package.md'), ref(QI / 'BOOT-C-ARCHITECTURE.md'), ref(E / 'qualification_boot_fence_input_map_codex/20261015-current-chat/COLLECTION-manifest.json')],
    'requirements': [
        'Only one finite resourceclosure for existing OFFICIAL_ENTRY_FILE_DACL_FENCE_V1; no newmechanism/initresearch/Source/codechange/deploy/fence/restart/launch/stop/DB/API/model/privatekey actions. Not alone:2Sourcebuildersinnewworktrees; Root alone sharedstate andonlinebackupSourcecontractread. Yourwriteownership onlyownE, Rootownonlinebackupevidence separate. Do not editfrozenarchitecture. Readscope+AGENT viaownpre-recordedlogger fromfirstcommand, notafter-the-factrecipe; useapply_patchtosetupwrapper ifneeded.',
        'Read exactknown current/old2packages manifests, theirproductlaunchscripts, actualactivationlauncher sources/scopes and knownDesktoppackage/distmain/Coreconfigurationpathlocators, documentedCLI/opsbackup/releasehost/normaldevscripts. Inventory eachOFFICIAL entry surface notallpersonalcode; no broadotherbusinessprivateconfigreads. SameSIDmaliciousarbitrarycopy outsidecontract, but officialrebuild/update/restart/directexe cannotexclude. Sourcefilehash/precisepaths/mandatoryproductexclusivefile and bypass reasoning, unresolveddynamicentryUNKNOWN.',
        'Readonly registrations in exactRun/RunOnce32/64HKCU/HKLM, productmatchingClasses protocol/association, WinlogonandActiveSetupproductmatches; scheduledtasks/actions/principal +servicesandfailureactions onlyproductmatching; current/publicDesktop/StartMenu/Startup shortcut TargetPath/Arguments/WorkingDirectory readonly(noSave/Run). Capturecheckedscopes and0matches, AccessDenied UNKNOWN notempty. Do not print/unnecessarilysealunrelatedregistration/credentials; filterproductexactpaths/names, sanitize anycredentialargument values withflagname+opaquehash and markfullargvbindingUNAVAILABLEifnecessary. NoProcessCommandLine/environment/privatecfgdump.',
        'OSsupportedbuild/architecture/filesystem andwhoami currentSID/groups/priv/elevationmetadata readonly. KnownCore/Desktop imagefiles and productexclusiveproposedtargets plus exactancestors: GetItem attrs/reparse/hardlinks, hash, GetAcl owner/nativeSDDL. Use trustedWindows readonly fsutil queryfileid/volume metadata asauxiliary. Complete128bit/native-samehandle acceptedhelper ifalreadyavailableandindependentlyaccepted; otherwiseidentifyexacttoolgap. Do not executeinventedunreviewednativeC#/Go/PInvoke reader merelytobypassthisgap. Filemetadataonly fororiginaldataRoot/DB/lease, neverreadbusinessDBcontents orkeys. Theseopen/read/close metadataobservations areNOTheldlease/currentnativeclosure/fenceproof.',
        'Output officialsurfaces.json/md, precise file/ancestor/ACL/nativeidentity records, platform/token facts, checkedregistration inventory, pendingresource/toolgap list; decide whetherexistingmechanism potentiallyapplicableorconcretelyinapplicable. Do notdeclarecompletefromtwoPIDs/58membersorquietlyassumeautostartabsent. Where source alone cannotprovecurrentruntimeRestartAppsregistration, markUNKNOWNwithminimalexactneededfutureSource/fixtureevidence. Nohumanapproval/restartask. InputfactcollectionnotdesignacceptanceorSourceauthority.',
        'AllcommandsrecipesBEFORE/raws/nativeexits/relevantenv anddistinctdiagnostic/skips/gaps. RootwillverifyFINALmanifestandthenarrangefiniteindependentdesignrevieworresourcehelperaswarranted, notanothergeneralarchitecturecycle. Rootparallelonlinebackupsourcecontractmap readsproductioncallerswithoutcurrentDB/API; do notduplicateit. Freeze report/JSON/ledger/FINAL andstop.'
    ]}
for name, obj in [('qualification-failure-B-revision02-source-scope.json', bs), ('owned-core-stop-authority-r4-source-scope.json', ss), ('official-entry-readonly-resource-scope.json', rs)]:
    new(O / name, obj)
items = []
bd = read(BI / 'diagnostic-ledger.json')
for item in bd['review_attempts']:
    items.append(('B-review-' + item['id'], 'INDEPENDENT_REVIEW_DIAGNOSTIC_OR_REPRODUCTION_PRESERVED', item, ref(BI / 'diagnostic-ledger.json')))
for item in br['findings']:
    items.append(('B-finding-' + item['id'], 'INDEPENDENT_SOURCE_REVIEW_FINDING_PRESERVED', item, ref(BI / 'review.json')))
assert len(items) == 13
sd = read(SI / 'diagnostic-ledger.json')
for i, item in enumerate(sd['own_nonzero'], 1):
    items.append(('STOP-review-native-' + str(i), 'INDEPENDENT_REVIEW_MIXED_NONZERO_PRESERVED', item, ref(SI / 'diagnostic-ledger.json')))
gaps = {item['id']: item for item in sd['capture_gaps']}
for i in range(4):
    items.append(('STOP-review-bootstrap-read-' + str(i + 1), 'INDEPENDENT_REVIEW_READONLY_CAPTURE_GAP', dict(gaps['R3-REVIEW-GAP-01'], grouped_ordinal=i + 1), ref(SI / 'diagnostic-ledger.json')))
for key in ('R3-REVIEW-GAP-02', 'R3-REVIEW-GAP-03', 'R3-REVIEW-GAP-04'):
    items.append(('STOP-review-' + key, 'INDEPENDENT_REVIEW_CAPTURE_OR_EMBEDDED_NATIVE_DIAGNOSTIC', gaps[key], ref(SI / 'diagnostic-ledger.json')))
items.append(('STOP-source-' + sr['findings'][0]['id'], 'INDEPENDENT_SOURCE_REVIEW_FINDING_PRESERVED', sr['findings'][0], ref(SI / 'review.json')))
assert len(items) == 27
for tag, detail in [('G00', 'InitialAGENT/scopereadrecipe notprewritten'), ('G01', 'Inputhashrecipe savedafterexecution'), ('G02', 'OverbroadRESUMEfieldsfilter/toolpresentationtruncation; fullrawretained'), ('G04', 'NativeGitexit0inraw but wrapperresultfieldnull duechildscope'), ('G05', 'OS206processcreationfailurewhenwritinglongraw; nochildnativeexit')]:
    items.append(('boot-design-' + tag, 'READONLY_DESIGN_DIAGNOSTIC_PRESERVED', {'group': tag, 'detail': detail}, ref(QI / 'diagnostic-gap-ledger.md')))
items.append(('root-oversized-stop-review-display', 'ROOT_READONLY_OUTPUT_CAPTURE_LIMIT', {'tool_chunks': ['50ae57', 'e7a34c'], 'detail': 'Root combined fulllargeledger outputtruncated; correctedselectedJSONreads; diskfilesretained'}, ref(SI / 'diagnostic-ledger.json')))
items.append(('root-backup-source-discovery-recipe-gap', 'ROOT_READONLY_DISCOVERY_CAPTURE_GAP', {'tool_chunk': 'a5c790', 'native_exit': 0, 'detail': 'Bounded sourcebackupfunc rg kepttoolraw but noownprewrittenrecipe; no actualDB/API touched'}, ref(QI / 'minimal-resource-package.md')))
assert len(items) == 34
old = list(cp['failure_counters'])
for suffix, status, detail, er in items:
    origin = '20261015|cp518-' + suffix
    assert not any(x.get('origin_key') == origin for x in old)
    cp['failure_counters'].append({'origin_key': origin, 'attempts': 1, 'status': status, 'detail': detail, 'evidence_ref': er, 'counter_reset': False})
assert cp['failure_counters'][:1852] == old and len(cp['failure_counters']) == 1886
new(O / 'STOP-r3-author-classification-adopted.json', {'source_ledger_ref': ref(SI / 'diagnostic-ledger.json'), 'author_original80_already_registered_cp517': True, 'expected': 71, 'diagnostic': 9, 'new_counter_records_for_classification': 0, 'old63_unchanged': True})
resume = read(B / 'continuation-cp517-retry02/RESUME.current.json')
resume.update(schema='researchos.current-chat-resume.v96', at=now, checkpoint_revision=518, ownership_revision=304, failure_records_preserved=1886,
    B_independent_review_ref=ref(BI / 'FINAL-manifest.json'), B_independent_status='NEEDS_CHANGES', B_r2_source_scope_ref=ref(O / 'qualification-failure-B-revision02-source-scope.json'),
    owned_stop_r3_independent_ref=ref(SI / 'evidence-manifest.json'), owned_stop_r3_independent_status='NEEDS_CHANGES', owned_stop_r4_source_scope_ref=ref(O / 'owned-core-stop-authority-r4-source-scope.json'),
    boot_supplement_design_ref=ref(QI / 'FINAL-manifest.json'), boot_supplement_status='FINITE_RESOURCE_BLOCKED_NOT_SOURCE_AUTHORITY', official_entry_resource_scope_ref=ref(O / 'official-entry-readonly-resource-scope.json'),
    active_source_cards=['CP518 B-r2 exact5from75 repair3findings+meaningfulcuts', 'CP518 STOP-r4 exact2from2816 owner/nativeACE/pathauthority'])
resume['next_command'] = 'Implement isolated B-r2 exact5/STOP-r4 exact2; bothpreviousSourceREJECTED, noMain/actual. One readonlyofficialentryresourceclosure for existingACLfencemechanism, RootseparateonlinebackupSourcecontractmap, noDB/API/nativeoriginalprocessaction. Boot57pathproposalnotSourceauthority,noUserRestartrequest. Main4f/dirty20/protected9/indexempty/config/step_state stable. Formal0/42/all22open.'
new(O / 'RESUME.current.json', resume)
rr = ref(O / 'RESUME.current.json')
cp.update(revision=518, expected_previous_revision=517, updated_at=now, updated_by='codex:/root', next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp518=rr, B_independent_review_ref=ref(BI / 'FINAL-manifest.json'), owned_stop_r3_independent_ref=ref(SI / 'evidence-manifest.json'), boot_supplement_design_ref=ref(QI / 'FINAL-manifest.json'))
cp['evidence_index'].append({'kind': 'B_AND_STOP_R3_REJECTED_REGISTER_EXACT_REPAIRS_AND_FINITE_READONLY_RESOURCES', 'ref': rr, 'formal_increment': 0})
ow.update(revision=304, expected_previous_revision=303, updated_at=now, updated_by='codex:/root')
for key, scope, filename in [('qualification_failure_B_r2_source', bs, 'qualification-failure-B-revision02-source-scope.json'), ('owned_stop_r4_source', ss, 'owned-core-stop-authority-r4-source-scope.json')]:
    ow['special_paths'][key] = {'owner': scope['owner'], 'mode': 'SOURCE_IMPLEMENTATION_ISOLATED', 'state': 'REGISTERED', 'scope_ref': ref(O / filename), 'write_scope': [scope['worktree'], scope['own_receipts'], scope['own_temporary_root']], 'source_allowlist': scope['source_allowlist'], 'actual_authority': False}
for key, er in [('qualification_failure_B_independent_review', ref(BI / 'FINAL-manifest.json')), ('owned_stop_r3_independent_review', ref(SI / 'evidence-manifest.json'))]:
    ow['special_paths'][key].update(state='FROZEN_NEEDS_CHANGES', evidence_ref=er)
ow['special_paths']['qualification_boot_supplement_design'].update(state='FROZEN_FINITE_RESOURCE_BLOCKED_NOT_SOURCE_AUTHORITY', evidence_ref=ref(QI / 'FINAL-manifest.json'))
ow['special_paths']['qualification_official_entry_resource_map'] = {'owner': rs['owner'], 'mode': 'READONLY_PUBLIC_RESOURCE_METADATA', 'state': 'REGISTERED', 'scope_ref': ref(O / 'official-entry-readonly-resource-scope.json'), 'write_scope': [rs['own_receipts']], 'source_edit_authority': False}
ow['special_paths']['online_backup_source_resource_map'] = {'owner': 'codex:/root', 'mode': 'READONLY_SOURCE_CONTRACT_MAP_NO_ACTUAL_DB_API', 'state': 'REGISTERED', 'scope_ref': ref(O / 'official-entry-readonly-resource-scope.json'), 'write_scope': [rs['root_parallel_source_receipts']]}
for key in ('owned_core_stop_source', 'owned_stop_anchor_revision02_source'):
    if key in ow['special_paths']:
        ow['special_paths'][key]['historical_state_before_supersession'] = ow['special_paths'][key].get('state')
        ow['special_paths'][key].update(state='SUPERSEDED_FROZEN_NO_ACTIVE_CONSTRUCTION', superseded_by_scope_ref=ref(O / 'owned-core-stop-authority-r4-source-scope.json'))
for p, name in ((cp_p, 'checkpoint.before.raw.json'), (ow_p, 'ownership.before.raw.json'), (hp, 'handoff.before.raw.md')):
    (O / name).write_bytes(raw[p])
for p, before in raw.items():
    assert p.read_bytes() == before
replace(ow_p, raw[ow_p], (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode())
replace(cp_p, raw[cp_p], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode())
replace(hp, raw[hp], ('# Current verified continuation CP518\n\nRead `' + rr['path'] + '` first. B75 rejected3findings and STOP2816 rejected1ownerACLfinding; bounded B-r2 exact5 and STOP-r4 exact2 Source registered. One finite officialentry/onlinebackup resourceclosure, noSourceC/actual/Restart authority. Formal0/42/all22open; mixedpreservedrecords1886.\n\n').encode() + raw[hp])
assert sp.read_bytes() == raw[sp]
print(json.dumps({'checkpoint': 518, 'ownership': 304, 'mixed_preserved_records': 1886, 'resume': rr, 'verified_refs': len(verified), 'scopes': [ref(O / name) for name in ('qualification-failure-B-revision02-source-scope.json', 'owned-core-stop-authority-r4-source-scope.json', 'official-entry-readonly-resource-scope.json')]}))
