import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

R=Path('D:/作品集/ResearchOS/research-os')
B=Path(__file__).parent
E=R/'execution/v2.4/receipts/W05/W05-99'
BI=E/'qualification_failure_b_revision02_source_codex/20261015-current-chat'
SI=E/'owned_core_stop_authority_revision04_independent_review_codex/20261015-current-chat'
SA=E/'owned_core_stop_authority_revision04_source_codex/20261015-current-chat'
QI=E/'qualification_boot_supplement_independent_design_review_codex/20261015-current-chat'
BW=R/'.local/worktrees/qualification-failure-b-r2-20261015'
SW=R/'.local/worktrees/owned-core-stop-authority-r4-20261015'
O=B/'continuation-cp521'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
    p=p.resolve()
    v=p.read_bytes()
    return {'path':p.relative_to(R.resolve()).as_posix() if p.is_relative_to(R.resolve()) else str(p),'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)}
def new(p,v):
    with p.open('x',encoding='utf8') as f:
        json.dump(v,f,ensure_ascii=False,indent=2)
        f.write('\n')
def replace(p,b,a):
    assert p.read_bytes()==b
    q=p.with_name(p.name+'.cp521.pending')
    q.write_bytes(a)
    assert p.read_bytes()==b
    os.replace(q,p)
verified={}
def verify(p,v):
    p=p.resolve()
    if str(p) not in verified: verified[str(p)]=ref(p)
    a=verified[str(p)]
    assert a['sha256']==v['sha256'],(a,v)
    if 'bytes' in v: assert a['bytes']==v['bytes'],(a,v)
def nested(v,parent):
    if isinstance(v,dict):
        if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str):
            p=Path(v['path'])
            if not p.is_absolute():
                candidates=[parent/p,R/p,BW/p,SW/p,BI/p,SI/p,QI/p,SA/p]
                matches=[q for q in candidates if q.is_file() and hashlib.sha256(q.read_bytes()).hexdigest()==v['sha256']]
                assert matches, v
                p=matches[0]
            verify(p,v)
        for x in v.values(): nested(x,parent)
    elif isinstance(v,list):
        for x in v: nested(x,parent)
def verify_manifest(p,sha):
    assert ref(p)['sha256']==sha
    m=read(p)
    nested(m,p.parent)
    if isinstance(m.get('files'),dict):
        for name,v in m['files'].items(): verify(p.parent/name,v)
    return m
verify_manifest(QI/'FINAL-manifest.json','97a51cd59fd3a7336ecfb1148a41c657dd5d87650bbb27b568a361cf91219bf7')
verify_manifest(SI/'FINAL-manifest.json','90099eff1b269ac9fa898191472c5b8111928762a91d7ccd2447cd88a316ef92')
assert ref(BI/'FINAL-manifest.json')['sha256']=='1aca112dd1d8c963da7ea1cd7a9db6b012048426515aff439ccb420aca689bda'
assert ref(BI/'capture-gap-and-skip-supplement.json')['sha256']=='ac0cefe372782a305f7defac572ca8350c0a187d5f21c817ab9e785cfb4ad028'
assert ref(SA/'scope-deviation-supplement.json')['sha256']=='0857e6fafbe2d0cf5bbff12d954c583b8d555fe30da779d331560434177eac3a'
bp=B/'continuation-cp521-inputs-retry02/B-r2-root-input-verification.json'
assert ref(bp)['sha256']=='370ccca470e0a0d6082a262189a88b29f8babe0039563dafcb62e0932d40a4a8'
nested(read(bp),bp.parent)
srp=B/'continuation-cp520/root-r4-command-capture-verification.json'
assert ref(srp)['sha256']=='136d9977524898fddc9947589192ab809c32250483672b08136e77b910a8c922'
nested(read(srp),srp.parent)
bm,br,bd,qr,sr,sd=[read(p) for p in [BI/'FINAL-manifest.json',BI/'capture-gap-and-skip-supplement.json',BI/'diagnostic-ledger.json',QI/'design-review.json',SI/'review.json',SI/'diagnostic-ledger.json']]
assert qr['verdict']=='CONDITIONAL_IMPLEMENTABLE_SOURCE_PROPOSAL' and not qr['source_card_issuable_now']
assert len(qr['source_paths'])==57 and len(qr['findings'])==9
assert sr['verdict']=='NEEDS_CHANGES' and len(sr['findings'])==1 and sr['findings'][0]['id']=='STOP-R4-F01'
assert len(bd['native_nonzero'])==16 and len(br['pre_execution_malformed_recipe_attempts'])==4 and len(br['skips_and_empty_success'])==2
assert sd['reviewer_nonzero_command_records']==9 and sd['reviewer_shell_capture_gap_count']==1
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x) for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
raw={p:p.read_bytes() for p in [cp_p,ow_p,hp,sp]}
cp,ow=read(cp_p),read(ow_p)
assert cp['revision']==520 and ow['revision']==306 and len(cp['failure_counters'])==1924
git=['git','-c','maintenance.auto=false','-c','gc.auto=0']
assert subprocess.check_output(git+['rev-parse','HEAD'],cwd=R,text=True).strip()=='4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert not subprocess.check_output(git+['diff','--cached','--name-only'],cwd=R)
assert len(subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=no'],cwd=R).splitlines())==20
for item in read(E/'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    assert ref(R/item['path'])['sha256']==item['sha256']
assert ref(R/'.git/config')['sha256']=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
assert not subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all'],cwd=BW)
assert subprocess.check_output(git+['rev-parse','HEAD'],cwd=BW,text=True).strip()==bm['commit']
O.mkdir(exist_ok=False)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O/'root-input-verification.json',{'refs_verified':len(verified),'refs':list(verified.values()),'B_r2_candidate_provenance':ref(bp),'STOP_r4_capture_supplement':ref(srp),'B_source_semantic_acceptance':False,'STOP_r4_semantic_verdict_adopted':'NEEDS_CHANGES','boot_design_adopted_only':'Conditional implementation proposal + exact9 refinements; no Source/actual authority, no new operational proof accepted'})
new(O/'boot-proposal-adopted-limits.json',{'design_review':ref(QI/'FINAL-manifest.json'),'verdict':qr['verdict'],'findings_required':qr['findings'],'source57':qr['source_paths'],'gates':qr['gates'],'root_decision':'After independent B-r2 acceptance and exact composite baseline, author a concrete Source57 proposal for C-only POST_RESTART_CURRENT_QUIESCENCE_V1; existing STOP classes unchanged. This is not Source implementation/semantic or actual acceptance.','actual_authority':False,'source_card_issued':False,'formal_increment':0})
common={'at':now,'actual_authority':False,'formal_increment':0,'self_acceptance':False}
bs=dict(common,schema='researchos.qualification-failure-B-r2-independent-review.v1',owner='codex:/root/qualification_failure_b_r2_review',model='gpt-6-astra',reasoning_effort='high',model_choice_reason='Full9 independent native security/proof/transaction review after three reproduced priorP1 repairs',worktree=str(BW),source_commit=bm['commit'],source_tree=bm['tree'],source_allowlist_readonly=bm['combined_source_paths'],r2_delta_paths_readonly=bm['source_allowlist'],source_edit_authority=False,own_receipts=str(E/'qualification_failure_b_revision02_independent_review_codex/20261015-current-chat'),own_temporary_root=str(R/'.local/qualification-failure-b-r2-independent-review-20261015-tmp'),
 inputs=[ref(BI/'FINAL-manifest.json'),ref(BI/'FINAL.md'),ref(BI/'diagnostic-ledger.json'),ref(BI/'capture-gap-and-skip-supplement.json'),ref(BI/'claim-test-matrix.json'),ref(bp),ref(E/'qualification_failure_b_independent_review_codex/20261015-current-chat/FINAL-manifest.json'),ref(E/'qualification_failure_b_independent_review_codex/20261015-current-chat/review.json'),ref(B/'continuation-cp518/qualification-failure-B-revision02-source-scope.json'),ref(E/'qualification_projection_a_revision02_independent_review_codex/20261015-current-chat/evidence-manifest.json')],
 requirements=[
  'Full9 Source from accepted A f48fca0e plus exact5r2 from75, frozen1d3cc504/be0c58 readonly. Verify full integration/production callers, all3 priorP1 repairs and meaningful original covergaps. Root verified134captures/670files/Git9/source5delta/whole9 clean; this is provenance only, not semantic acceptance. Do not edit Source/frozenauthor artifacts. OwnE new tests via copied Gooverlay allowed, pinned/diffed. Not alone: STOP-r5 Source and onlinebackup freshqualification separate; Root owns sharedstate. No original liveRoot/Core/Desktop/DB/API/provider/model/keys/worker, historicalC/newbootproof/SourceD or actual/formal actions.',
  'B-F01 native owner/ACE privacy on sourcefile/directories AND retained identity/reparse/no-delete guard: protected currentSID+EveryoneFull must refuse, final unsafefile and inherited write/control refusal, safeACLtruepositive. Check INHERIT_ONLY/unknown/genericrights/OStrustedowner and samefile nativehandle hash/write/flush/read continuity plus close error/failurepaths. Conservative failure leaves UNKNOWN. No ACL change to shared ancestors/originalpaths; own new fixture nativeACL changes permitted. Determine exact whether nativeguard actually protects selected namespace/bytes acrossaction, do not equate savedSDDL/strings with authorization.',
  'B-F02 complete base-f48 ordinary queue tests/helper assertions restored before appended registry tests. Inspect actual originalcontent/body, do not accept count or authorclaim alone. Run original3ordinaryMuqueue/cancel/claim groups with existing frozenlocalMu bundle, 0SKIP; sourceA accepted limited reference retained, no globalnormalcostgate. Fail/skip distinctly; no unrelated suite expansion once fixed regression verified.',
  'B-F03 sealed proof + marker bind exact sole MODEL threephase subject/epoch/effect_key/sequence/history, canonicalrequest/hash/route/capability/credentialrevision, canonicalreceipt/id/providerresponsehash to raw ACK2/model frame and durableHost MODELrequest/responsefact. Define canonical Hash vs raw Digest. Consumer reloads/recomputes from nativeprotectedfiles+currentDB in actualTx, rejects independentreceipt_id/requestbody/hash/route/key/history/credential/Hostfact/response tamper with marker/proofunchanged. Review rawarrays/bodyshape/canonicalization and crossphase/sourcebinding; a hash of callerdata alone is not provenance. CurrentOwner-root/grantdeletion/revocation, scheduler-root and all marker namespace/lineage checks matter.',
  'Production B path: valid firstgate rejection before prepareTOOL, trueLIVE controlledloopback raw3/ACK2/rejected1/queue_emptyfalse, onenativeworker stopped/drained/cleanup/copied, brokerregistry closed+suffix reread+boundeddrain currentplan/heartbeatCAS, preserves firstcause while lateextra observations disqualify. No fake ACK/no TOOL effect/modelrepeat; rawcostUNKNOWN remainsunknown. Blocked MODEL and late suffix are separate from still-unproven15s brokerdrain timeout; sourceanalysis may support conservativebranch but do not label dynamictimeoutPASS. Generic/secondgate/uncertaincasesremainUNKNOWN.',
  'PrivatevalidatedTx realcompletedclosure branch: exact fiveversiondifferences/oneuploadedcontent/enumeratedallowedancillary runtime_uploads/uses/proofs0 plus alltablelogicalcensus. Verify 20writerfaults including ImpactLink/ref/Artifactref and true deferredFK Commit failure rollback, exactcompletedmarker replay0delta and wrongmarker/subject refusal; publicRunAdmittedterminalrefusal alone is insufficient replayproof. Positive firstgate seed reachesrealgate before eachisolated24mutation. Nativecleanup fields eachmissing/null/tampered genuinecuts, rawHostfile/seal drift. Freshownfocusedtests+atleastmeaningfulnegative viaGooverlay; do not rely onlyauthorPASS.',
  'Classify16authornative/unavailable +4preexecseparate +SKIPcommand4lines +emptytest +unloggedreadonlywrongcwd +bootstrapencodinglimit once; Rootalreadyimports24mixedgroups, oldB29/review13 no recount/reset. Sourcecandidate clean must remain. Everycommand incl first AGENTS/scope prewrittenrecipe/argv/cwd/relevantenv/rawstdoutstderr/nativeexit, capturesupplementonlynotSourcehooks. D uniqueTMP/TEMP/GOTMPDIR/GOCACHE, localGo/modulecache/Mu resources only; no installs/oldpolicydeniedcleanup.',
  'Freeze finite review.md/json candidate/tree/full9/5delta/verdict/findings/minimalfixpaths/coverage+exactlimits, commandindex/diagnosticledger/FINALmanifest. Check B final privateAPI consumption implications for future C but no Cimplementation or newarchitectureloop. Root alone may adopt limitedSourceacceptance; no self or actual/formal acceptance.'
 ])
ss=dict(common,schema='researchos.owned-core-stop-effect-state-r5-source.v1',owner='codex:/root/owned_core_stop_builder',model='gpt-6-sol',reasoning_effort='high',model_choice_reason='Narrow independently reproduced SQLite NULL semantics fix in two exact store paths',base_commit=sr['source_commit'],base_tree=sr['source_tree'],base_status='NEEDS_CHANGES',worktree=str(R/'.local/worktrees/owned-core-stop-effect-state-r5-20261015'),branch='codex/owned-core-stop-effect-state-r5-20261015',source_allowlist=sr['findings'][0]['minimal_fix_paths'],own_receipts=str(E/'owned_core_stop_effect_state_revision05_source_codex/20261015-current-chat'),own_temporary_root=str(R/'.local/owned-core-stop-effect-state-r5-20261015-tmp'),approved_c_image_fixture_root='C:/Users/yqyyds/.codex/researchos-fixture-cache/owned-core-stop-effect-state-r5-20261015',
 inputs=[ref(SI/'FINAL-manifest.json'),ref(SI/'review.md'),ref(SI/'review.json'),ref(SI/'diagnostic-ledger.json'),ref(SA/'candidate-ab308912-final2/manifest.json'),ref(SA/'scope-deviation-supplement.json')],copied_finding=sr['findings'][0],retained_limits=sr['limits'],
 requirements=[
  'New exactab308912 worktree/branch, only2storeSource/testpaths. No SourceMain/frozenab/otherSource edits, no actualCore/Desktop/RootDB/API/privatekey/model/bootnewclass action. Not alone: fullB-r2 independentreview+onlinebackupfreshfixtures run in parallel; Root alone sharedcheckpoint/ownership/handoff. EVERYGitwrite includingworktree/stage/commit explicit-cmaintenance.auto=false-cgc.auto=0 withpaths. NoGC/repack/prune/config/reset/clean/oldlogcleanup.',
  'Fix reproducedSTOP-R4-F01: latest same-subject extraMODEL missing/null state must countunsafe or refuse. Preserve latest-sequence/effect_key/project/run binding, uniqueoneCONFIRMEDMODEL and prior normalknownstates, abnormalJSONtypes/unknownenum/capabilitynullreject. Do not silently reinterpret earlierhistory overriddenbylatest ascurrenteffect; currentlatestsemantics and deeperhistoryresiduallimit remainexplicit. No schema/datarewrite, no guardrelaxation, no stringdefaultCONFIRMED or coercion ofmissingtozero. Use existingfinite16matrix validcontrol+alltypes/latest/historyproportionalchecks.',
  'New productiontests startvalid then add exactextraeffect missing/null atbaseline, realschema24/reservedSQLitebarrier mustrefuse. Genuine compiled PREFLIGHT_ONLY CLI eachbadbaseline beforecensus/plan mustSTOP_UNAVAILABLE or earlierdeny,0STOPgrant/0nativesignal/Corealiveuntilfixturegracefulcleanup. Never manufactureSTOPgrant afterdenial. OwnfreshvalidnonemptySQLite realtwocompiledgrantspositive stilloneTerminateProcess/originalretainedhandlenumericwait/postflightstable/replay. Authoroldbadbaselinepositiveisfailedsourceevidence, do not modify.',
  'Use reviewer Ddata/operation harnesslineage instead of oldauthorCdata/journalplacement. C resource ONLYnewexactapprovedimages/parenthelper/supportscripts; SQLiteDB/dataRoot/STOPoperation/journals/keys/TMP/build/cache/Source/officialreceipts remain taskDroots. Pin Ccopies toDbuild+nativeACLbeforeuse. Do not run oldunapprovedC:/Users/yqyyds/ResearchOS-STOP-r4-20261015-tmp or oldpolicydeniedtargets, do not rewriteD/shared/homeACL. SupportedCimagepositiveanduntrustedDimageinstallationlimits unchanged. This resourcepermission is not retrospectiveapprovalofr4Cdata/journaldeviation.',
  'Prior r4ownerACE/nativeimage fix independentlySUPPORTED, requirednativefields/ctxcuts have boundedproof; do not rerunalloldmatriceswithoutnewconcern or edittheirSource. FullCommitafterownintentcancel/foreignSID/hostilerace/powerfail/deeperSnapshotbranches remain explicit limits. ExistingSTOPsevenproofclasses unchanged, no bootclass authorization. No extra production authorization/testhooks.',
  'RecipebeforeeverycommandinclAGENTS/scope, argv/cwd/relevantenv/rawstdoutstderr/nativeexit/sourcehelpercopyhash/diff. OwnDuniqueTMP/TEMP/GOTMPDIR/GOCACHE, pinnedlocalGo/modulecache only. Gofmt2paths, exactatomiccommit/tree, cleanworktree. Freeze exact2deltafromab+whole19fromMain4f withexplicitbinaryfullindexpatchargv/hash, source19pins, finiteclaimtestmatrix/rawcommandindex/failureledger+FINAL. Preserveallold20author/22Root/thisreviewrecordswithoutdoublecount/reset; newerrors/skips/gapsdistinct. IndependentreviewneededbeforeSource/Main/package/actual/formal.'
 ])
assert len(ss['source_allowlist'])==2
new(O/'qualification-failure-B-r2-independent-review-scope.json',bs)
new(O/'owned-core-stop-effect-state-r5-source-scope.json',ss)
items=[]
for item in bd['native_nonzero']: items.append(('B-native-'+item['tag'],'AUTHOR_NATIVE_NONZERO_OR_UNAVAILABLE_PRESERVED',item,ref(BI/'diagnostic-ledger.json')))
for item in br['pre_execution_malformed_recipe_attempts']: items.append(('B-preexec-'+item['tag'],'AUTHOR_PREEXEC_RECIPE_FAILURE_WITH_RAW_GAP_PRESERVED',item,ref(BI/'capture-gap-and-skip-supplement.json')))
for item in br['skips_and_empty_success']: items.append(('B-native0-'+item['tag'],'AUTHOR_SKIP_OR_ZERO_ASSERTION_PRESERVED',item,ref(BI/'capture-gap-and-skip-supplement.json')))
items.append(('B-unlogged-readonly','AUTHOR_READONLY_CAPTURE_GAP_PRESERVED',br['shell_logging_audit']['unlogged_shell_gap'],ref(BI/'capture-gap-and-skip-supplement.json')))
items.append(('B-bootstrap-encoding','AUTHOR_READONLY_CAPTURE_ENCODING_LIMIT',br['shell_logging_audit']['first_scope_and_agents_read'],ref(BI/'capture-gap-and-skip-supplement.json')))
assert len(items)==24
for tag,detail in [('R01','Get-FileHash unavailable native1; prewrittenfirstreadfailed'),('R07-warning','Python invalidescape SyntaxWarning retained'),('R04-display','Ownfullraw retained, tooldisplaytruncated'),('R05-display','Ownfullraw retained, tooldisplaytruncated'),('R07-display','Ownfullraw retained, tooldisplaytruncated'),('R08-display','Ownfullraw retained, tooldisplaytruncated'),('R10-display','Ownfullraw retained, tooldisplaytruncated'),('W03-filter','Mistyped site filter; thirdpartyresultsnotused, Microsoftprimaryonly'),('API-display-aggregate','Official API page opens toolpresentationlimited; evidencefullypreserved, noemptyabsenceclaim')]:
    items.append(('boot-design-'+tag,'INDEPENDENT_DESIGN_DIAGNOSTIC_OR_CAPTURE_LIMIT_PRESERVED',{'detail':detail},ref(QI/'diagnostic-ledger.md')))
for item in qr['findings']: items.append(('boot-refinement-'+item['id'],'CONDITIONAL_DESIGN_REFINEMENT_REQUIRED_NOT_SOURCE_FINDING_ACCEPTANCE',item,ref(QI/'design-review.json')))
assert len(items)==42
for item in sd['records']: items.append(('STOP-review-native-'+str(item['ordinal']),'INDEPENDENT_REVIEW_MIXED_NONZERO_PRESERVED',item,ref(SI/'diagnostic-ledger.json')))
items.append(('STOP-review-shell-launch-gap','INDEPENDENT_REVIEW_SHELL_CAPTURE_GAP_PRESERVED',sd['reviewer_extra_shell_launch_records'],ref(SI/'diagnostic-ledger.json')))
items.append(('STOP-review-bootstrap-encoding','INDEPENDENT_REVIEW_READONLY_CAPTURE_ENCODING_LIMIT',{'detail':sd['other_notes'][0]},ref(SI/'diagnostic-ledger.json')))
items.append(('STOP-finding-STOP-R4-F01','INDEPENDENT_SOURCE_FINDING_REPRODUCED',sr['findings'][0],ref(SI/'review.json')))
items.append(('STOP-author-Cdata-operation','AUTHOR_C_FIXTURE_SUPPORT_SCOPE_AMBIGUITY_OR_DEVIATION_PRESERVED',{'supplement':ref(SA/'scope-deviation-supplement.json'),'detail':'C fixture SQLite/data/operation/journal exceeded explicit images-only interpretation; no retrospective authorization. Prior wrongE/earlyoutsideC alreadycp520, no recount.'},ref(SA/'scope-deviation-supplement.json')))
items.append(('root-stop-index-shape','ROOT_READONLY_JSON_SHAPE_DIAGNOSTIC_PRESERVED',{'tool':'8511f4','native_exit':1,'detail':'Treated flat command-index list asobject; corrected selectedread and584fileverify'},ref(B/'read-stop-r4-command-index-shape.recipe.result.json')))
items.append(('root-B-result-shape','ROOT_PROVENANCE_READER_SCHEMA_DIAGNOSTIC_PRESERVED',{'tool':'8212dc','native_exit':1,'detail':'Assumed argv in result rather thancommand.json; immutablefailurepreserved, retry02all134/670verified'},ref(B/'verify-B-r2-frozen-inputs.recipe.result.json')))
assert len(items)==57
new(O/'new-records-ledger.json',{'distinct_mixed_records':len(items),'records':[{'id':i,'status':s,'detail':d,'evidence':e} for i,s,d,e in items],'not_product_failure_count':True})
old=list(cp['failure_counters'])
for suffix,status,detail,er in items:
    key='20261015|cp521-'+suffix
    assert not any(v.get('origin_key')==key for v in old)
    cp['failure_counters'].append({'origin_key':key,'attempts':1,'status':status,'detail':detail,'evidence_ref':er,'counter_reset':False})
assert cp['failure_counters'][:1924]==old and len(cp['failure_counters'])==1981
new(O/'STOP-r4-author-classification-adopted.json',{'original20_already_cp520':True,'review_ref':ref(SI/'review.json'),'expected_denial':4,'retained_diagnostic':16,'additional_counter_records_for_classification':0,'earlierwrongEandCoutofscope_already_cp520':True,'newCdataoperationambiguity_only_one_new_group':True})
resume=read(B/'continuation-cp520/RESUME.current.json')
resume.update(schema='researchos.current-chat-resume.v99',at=now,checkpoint_revision=521,ownership_revision=307,failure_records_preserved=1981,B_r2_source_manifest_ref=ref(BI/'FINAL-manifest.json'),B_r2_status='AUTHOR_FROZEN_NOT_ACCEPTED_REVIEW_REGISTERED',B_r2_independent_review_scope_ref=ref(O/'qualification-failure-B-r2-independent-review-scope.json'),owned_stop_r4_independent_manifest_ref=ref(SI/'FINAL-manifest.json'),owned_stop_r4_independent_status='NEEDS_CHANGES_STORE_STATE_NULL',owned_stop_r5_source_scope_ref=ref(O/'owned-core-stop-effect-state-r5-source-scope.json'),boot_supplement_independent_design_ref=ref(QI/'FINAL-manifest.json'),boot_supplement_root_decision_ref=ref(O/'boot-proposal-adopted-limits.json'),boot_supplement_status='CONDITIONAL_SOURCE_PROPOSAL_AFTER_B_ACCEPTED_NOT_SOURCE_OR_ACTUAL_AUTHORITY',online_backup_fixture_status='ACTIVE_UNCHANGED_SOURCE_FRESH_FIXTURES_Q01Q02_LOCALPASS_Q03_INPROGRESS_NOT_ACCEPTED',owned_stop_r4_capture_verification_supplement_ref=ref(srp),owned_stop_r4_scope_deviation_supplement_ref=ref(SA/'scope-deviation-supplement.json'),active_source_cards=['CP521 STOP-r5 exact2store missing/null latest state fix'])
resume['next_command']='Independentlyreview frozenB-r2 full9/5delta; implementSTOP-r5 exact2store nullstatefix fromrejectedab; unchangedSource onlinebackupfixtureQ01Q02localpass/Q03inprogress. Boot57conditionalproposal9refinementsadoptedonly, SourceCnotissuedbeforeBaccepted+exactcomposite. Main4f/dirty20/protected9/indexempty/config/step_state stable. No originalroot/backup/STOP/fence/restart/model authority. Formal0/42/all22open.'
new(O/'RESUME.current.json',resume)
rr=ref(O/'RESUME.current.json')
cp.update(revision=521,expected_previous_revision=520,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp521=rr,B_r2_independent_scope_ref=ref(O/'qualification-failure-B-r2-independent-review-scope.json'),owned_stop_r5_scope_ref=ref(O/'owned-core-stop-effect-state-r5-source-scope.json'),boot_design_conditional_adoption_ref=ref(O/'boot-proposal-adopted-limits.json'))
cp['evidence_index'].append({'kind':'B_R2_FROZEN_REVIEW_REGISTER_STOP_R4_REJECTED_MINIMAL_R5_BOOT_CONDITIONAL_DESIGN_ADOPTED_NO_ACTUAL','ref':rr,'formal_increment':0})
ow.update(revision=307,expected_previous_revision=306,updated_at=now,updated_by='codex:/root')
ow['special_paths']['qualification_failure_B_r2_source'].update(state='AUTHOR_FROZEN_NOT_ACCEPTED',evidence_ref=ref(BI/'FINAL-manifest.json'))
ow['special_paths']['owned_stop_r4_independent_review'].update(state='FROZEN_NEEDS_CHANGES',evidence_ref=ref(SI/'FINAL-manifest.json'))
ow['special_paths']['boot_supplement_independent_design_review'].update(state='FROZEN_CONDITIONAL_IMPLEMENTATION_PROPOSAL_NO_SOURCE_AUTHORITY',evidence_ref=ref(QI/'FINAL-manifest.json'))
ow['special_paths']['online_backup_fixture_qualification'].update(state='ACTIVE_FRESH_FIXTURE_QUALIFICATION_NOT_ACCEPTED')
ow['special_paths']['qualification_failure_B_r2_independent_review']={'owner':bs['owner'],'mode':'INDEPENDENT_FULL9_SOURCE_NATIVE_FIXTURE_REVIEW','state':'REGISTERED','scope_ref':ref(O/'qualification-failure-B-r2-independent-review-scope.json'),'write_scope':[bs['own_receipts'],bs['own_temporary_root']],'source_edit_authority':False,'actual_authority':False}
ow['special_paths']['owned_stop_r5_source']={'owner':ss['owner'],'mode':'SOURCE_IMPLEMENTATION_ISOLATED','state':'REGISTERED','scope_ref':ref(O/'owned-core-stop-effect-state-r5-source-scope.json'),'write_scope':[ss['worktree'],ss['own_receipts'],ss['own_temporary_root'],ss['approved_c_image_fixture_root']],'source_allowlist':ss['source_allowlist'],'actual_authority':False}
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]: (O/name).write_bytes(raw[p])
for p,b in raw.items(): assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode())
replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode())
replace(hp,raw[hp],('# Current verified continuation CP521\n\nRead `'+rr['path']+'` first. B-r2 1d3cc504 frozen full9/5delta independentreview registered. STOPab rejectedoneP2 latestMODELstate missing/null; minimal2store r5 Source registered. Boot57 conditionaldesign9refinements adoptedonly; noSourceC beforeBacceptance/composite. Backup unchangedSource freshfixtures active, notactualaccepted. Formal0/42/all22open; mixedpreservedrecords1981.\n\n').encode()+raw[hp])
assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':521,'ownership':307,'mixed_preserved_records':1981,'resume':rr,'verified_refs':len(verified),'B_review_scope':ref(O/'qualification-failure-B-r2-independent-review-scope.json'),'STOP_r5_scope':ref(O/'owned-core-stop-effect-state-r5-source-scope.json')},ensure_ascii=False))
