import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

R=Path('D:/作品集/ResearchOS/research-os')
B=Path(__file__).parent
E=R/'execution/v2.4/receipts/W05/W05-99'
S=E/'owned_core_stop_authority_revision04_source_codex/20261015-current-chat'
F=S/'candidate-ab308912-final2'
W=R/'.local/worktrees/owned-core-stop-authority-r4-20261015'
O=B/'continuation-cp520'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
    v=p.read_bytes()
    return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p),'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)}
def new(p,v):
    with p.open('x',encoding='utf8') as f:
        json.dump(v,f,ensure_ascii=False,indent=2)
        f.write('\n')
def replace(p,b,a):
    assert p.read_bytes()==b
    q=p.with_name(p.name+'.cp520.pending')
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
                candidates=[parent/p,S/p,R/p]
                found=[q for q in candidates if q.is_file()]
                assert found, v
                p=found[0]
            verify(p,v)
        for x in v.values(): nested(x,parent)
    elif isinstance(v,list):
        for x in v: nested(x,parent)
assert ref(F/'manifest.json')['sha256']=='9b210bb5dcf65dc34cb21743fc1e5ff8b4209e601b17bc82bf54b9590869516b'
m=read(F/'manifest.json')
nested(m,F)
ci=read(F/'command-index.json')
nested(ci,F)
fl=read(F/'failure-ledger.json')
assert m['source_commit']=='ab308912117dac59cadd5aa2e75b46a418e41b6b' and m['source_tree']=='c45e5bd0a1890c6789ddb590e57d9d7db0f67521'
assert len(m['changed_paths'])==2 and len(m['whole19_paths'])==19 and len(m['source_pins'])==19
assert fl['total_nonzero']==20 and fl['expected_negative_cli']==4 and fl['diagnostics']==16 and fl['known_unlogged_shell_reads']==0
git=['git','-c','maintenance.auto=false','-c','gc.auto=0']
assert subprocess.check_output(git+['rev-parse','HEAD'],cwd=W,text=True).strip()==m['source_commit']
assert not subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all'],cwd=W)
assert set(subprocess.check_output(git+['diff','--name-only',m['source_base_commit'],m['source_commit']],cwd=W,text=True).splitlines())==set(m['changed_paths'])
assert set(subprocess.check_output(git+['diff','--name-only',m['main_base_commit'],m['source_commit']],cwd=W,text=True).splitlines())==set(m['whole19_paths'])
for path,v in m['source_pins'].items():
    raw_blob=subprocess.check_output(git+['show',m['source_commit']+':'+path],cwd=W)
    assert hashlib.sha256(raw_blob).hexdigest()==v['sha256'] and len(raw_blob)==v['bytes'],path
    assert ref(W/path)['sha256']==v['sha256'],path
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x) for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
raw={p:p.read_bytes() for p in [cp_p,ow_p,hp,sp]}
cp,ow=read(cp_p),read(ow_p)
assert cp['revision']==519 and ow['revision']==305 and len(cp['failure_counters'])==1902
assert subprocess.check_output(git+['rev-parse','HEAD'],cwd=R,text=True).strip()=='4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert not subprocess.check_output(git+['diff','--cached','--name-only'],cwd=R)
assert len(subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=no'],cwd=R).splitlines())==20
for item in read(E/'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    assert ref(R/item['path'])['sha256']==item['sha256']
assert ref(R/'.git/config')['sha256']=='1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'
O.mkdir(exist_ok=False)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O/'root-r4-input-verification.json',{'verified_refs':len(verified),'refs':list(verified.values()),'git_source_pins':m['source_pins'],'clean_candidate':m['source_commit'],'source_semantic_acceptance':False,'author_claimed_nonzero_classification_not_independent':{'expected_negative':4,'diagnostic':16}})
scope={
 'schema':'researchos.owned-core-stop-authority-r4-independent-review.v1','at':now,'owner':'codex:/root/owned_core_stop_r4_review','model':'gpt-6-astra','reasoning_effort':'high','model_choice_reason':'Independent security/native proof review of full19 and minimal2-path owner/ACE repair',
 'source_commit':m['source_commit'],'source_tree':m['source_tree'],'worktree':str(W),'own_receipts':str(E/'owned_core_stop_authority_revision04_independent_review_codex/20261015-current-chat'),'own_temporary_root':str(R/'.local/owned-core-stop-r4-independent-review-20261015-tmp'),
 'approved_c_fixture_root':'C:/Users/yqyyds/.codex/researchos-fixture-cache/owned-core-stop-r4-independent-review-20261015',
 'source_allowlist_readonly':m['whole19_paths'],'delta_paths_readonly':m['changed_paths'],'actual_authority':False,'source_edit_authority':False,'formal_increment':0,'self_acceptance':False,
 'inputs':[ref(F/'manifest.json'),ref(F/'failure-ledger.json'),ref(F/'test-matrix.json'),ref(F/'command-index.json'),ref(S/'selected-image-path-threat-model.md'),ref(B/'continuation-cp518/owned-core-stop-authority-r4-source-scope.json'),ref(B/'continuation-cp518/owned-stop-r4-fixture-location-amendment01.json'),ref(E/'owned_core_stop_proof_revision03_independent_review_codex/20261015-current-chat/evidence-manifest.json'),ref(E/'owned_core_stop_proof_revision03_independent_review_codex/20261015-current-chat/review.json')],
 'requirements':[
  'Review the FULL19 from Main4f and r4exact2 from2816, frozen ab308912 cleanworktree readonly. Independent semantic review, not hashes alone. Not alone: B-r2 Source and finite boot design review in separate scopes; Root owns sharedstate. No Source edits, actual original processes/root/DB/API/keys/STOP/restart/fence/model or new proofclass. Write only ownE/newTMP/new approved C fixture subtree. Never edit frozen author receipts/helpers; copy/pin before adapting own test driver.',
  'Resolve R3-F01 and complete prior F03: exact trusted owner set currentoperator/System/Admin/TrustedInstaller; native ACE/masks/INHERIT_ONLY/unsupported/malformed/direct/inherited rights, generic mapping/directory semantics. Check relevant untrusted file write/delete/securitycontrol and directory add/deletechild/rename boundaries under actual Windows APIs; saved ACL alone is insufficient authority. Validate trusted OS ancestors without waiving untrusted D installation refusal. Final and every selected ancestor native handles hash/ID/ACL continuity and closing on every failed branch.',
  'Review author equivalently strong selected-path argument with directory GENERIC_WRITE OPENED fact preserved. Do retained no-delete-share handles + rejecting unauthorized FILE_DELETE_CHILD + final no-write-share block relevant selected mutations? Special isolated FILE_ADD_SUBDIRECTORY allowance must not grant selectedpath replacement/reparse/hardlink/ACL bypass. Distinguish unauthorized untrusted actor from explicitly trusted operator/elevatedOS; trusted actor ACL drift must still be rechecked before action. Do not infer hostile race exhaustiveness from a few refused calls. Find/reproduce actual bug if any; otherwise retain exact residual limits.',
  'Fresh own real native copied parent+child ACL positive and at least reproduced protected currentSID+Everyone/Users final and inherited ancestor unsafe negatives; wrongowner/unsupported/inheritonly cuts as justified. Use real native APIs and task C installation. D AU Modify source install remains negative, no modifying shared D/root/home/old actual ACL. C fixture contains ONLY own copied/built helper/images and supportscripts; Source/build/cache/TMP/receipts remain D. Pin copiedCbytes to own D build, read native ACL before positive. New own C subtree only, do not use author unapproved C:/Users/yqyyds/ResearchOS-STOP-r4-20261015-tmp or any previous policy-denied paths.',
  'Fresh own compiled two grant CLI path + nonempty SQLite: build own fixture from frozen Source, pin harness copy and exact edits. Safe C native parent/helper may be copied from author pinned helper Source and rebuilt, no production validator seam. Real preflight compilegrant execute then STOP compilegrant execute, exactly1native TerminateProcess, originalhandle numericwait and postflight/stable inspect; no currentoriginal process. Existing missingworkerexit/verifierwait can rerun one targeted refusal if useful, must deny before preflight grant/noSTOPgrant, never fabricate authority after refusal. Keep observed facts separate from synthetic historical native receipts.',
  'Prior required-field/callerctx r3 fixes remain reviewed full19. Test proportional focused suite + own meaningful negative, do not rerun all old matrices without concern. Full Commit cancellation after its own durableintent, actualforeignSID/hostilerace/powerfailure/deeperbarriers remain limits unless genuinely new proof. No production test hook. Classify 20 authornonzeros (4expected/16diagnostic claimed) and capture/scope deviations once; old counters not reset or relabeled away. Adjacent receipt root misplacement and early unapproved Croot remain explicit even if Source correct.',
  'Prewrite all command recipes incl initial reads, argv/cwd/relevantenv/rawstdoutstderr/nativeexit, copy/source/overlay hashes and diffs. Existing local tools no install. TMP/TEMP/GOTMPDIR/GOCACHE unique D root. Finite review.md/json with candidate/tree/full19/2delta hashes/verdict/findings/minimalfixpaths/coverage/limits, diagnostic ledger/commandindex/FINALmanifest. Root alone adopts acceptance. No actual/formal completion.'
 ]}
new(O/'owned-core-stop-r4-independent-review-scope.json',scope)
items=[('author-nonzero-'+str(i),'AUTHOR_NATIVE_NONZERO_UNCLASSIFIED_PRESERVED',v,ref(F/'failure-ledger.json')) for i,v in enumerate(fl['failures'],1)]
items += [('author-bootstrap-location','AUTHOR_EVIDENCE_LOCATION_DEVIATION_PRESERVED',{'detail':fl['bootstrap_capture_location_deviation'],'not_native_copy_collision_recount':True},ref(F/'failure-ledger.json'))]
supp=S/'scope-deviation-supplement.json'
if supp.is_file():
    items.append(('author-C-fixture-location','AUTHOR_FIXTURE_LOCATION_SCOPE_DEVIATION_PRESERVED',read(supp),ref(supp)))
else:
    items.append(('author-C-fixture-location','AUTHOR_FIXTURE_LOCATION_SCOPE_DEVIATION_PRESERVED',{'reported_by_author':'C:/Users/yqyyds/ResearchOS-STOP-r4-20261015-tmp created before approved subtree, stopped using, retained; exact capture supplement pending','amendment_not_retroactive':True},ref(B/'continuation-cp518/owned-stop-r4-fixture-location-amendment01.json')))
old=list(cp['failure_counters'])
for suffix,status,detail,er in items:
    key='20261015|cp520-'+suffix
    assert not any(v.get('origin_key')==key for v in old)
    cp['failure_counters'].append({'origin_key':key,'attempts':1,'status':status,'detail':detail,'evidence_ref':er,'counter_reset':False})
assert len(items)==22 and cp['failure_counters'][:1902]==old and len(cp['failure_counters'])==1924
resume=read(B/'continuation-cp519/RESUME.current.json')
resume.update(schema='researchos.current-chat-resume.v98',at=now,checkpoint_revision=520,ownership_revision=306,failure_records_preserved=1924,owned_stop_r4_frozen_source_manifest_ref=ref(F/'manifest.json'),owned_stop_r4_status='AUTHOR_FROZEN_NOT_ACCEPTED_INDEPENDENT_REVIEW_REGISTERED',owned_stop_r4_independent_review_scope_ref=ref(O/'owned-core-stop-r4-independent-review-scope.json'),active_source_cards=['CP518 B-r2 exact5from75 repair3findings+meaningfulcuts'])
resume['next_command']='B-r2 Source continues; STOP-r4 ab308912 frozenonlynotaccepted full19/2delta independent review registered. Finite boot design review active; unchangedSource online backup fixture qualification pending slot. Main4f/dirty20/protected9/indexempty/config/step_state unchanged. No originalroot/backup/STOP/fence/restart/model authority. Formal0/42/all22open.'
new(O/'RESUME.current.json',resume)
rr=ref(O/'RESUME.current.json')
cp.update(revision=520,expected_previous_revision=519,updated_at=now,updated_by='codex:/root',next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp520=rr,owned_stop_r4_frozen_manifest_ref=ref(F/'manifest.json'),owned_stop_r4_independent_review_scope_ref=ref(O/'owned-core-stop-r4-independent-review-scope.json'))
cp['evidence_index'].append({'kind':'STOP_R4_AUTHOR_FROZEN_FULL19_REGISTER_INDEPENDENT_REVIEW_NO_ACTUAL','ref':rr,'formal_increment':0})
ow.update(revision=306,expected_previous_revision=305,updated_at=now,updated_by='codex:/root')
ow['special_paths']['owned_stop_r4_source'].update(state='AUTHOR_FROZEN_NOT_ACCEPTED',evidence_ref=ref(F/'manifest.json'))
ow['special_paths']['owned_stop_r4_independent_review']={'owner':scope['owner'],'mode':'INDEPENDENT_FULL19_SOURCE_NATIVE_FIXTURE_REVIEW','state':'REGISTERED','scope_ref':ref(O/'owned-core-stop-r4-independent-review-scope.json'),'write_scope':[scope['own_receipts'],scope['own_temporary_root'],scope['approved_c_fixture_root']],'source_edit_authority':False,'actual_authority':False}
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]: (O/name).write_bytes(raw[p])
for p,b in raw.items(): assert p.read_bytes()==b
replace(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode())
replace(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode())
replace(hp,raw[hp],('# Current verified continuation CP520\n\nRead `'+rr['path']+'` first. STOP ab308912 authorfrozen full19/2delta independentreview registered; B-r2 Source continues. Boot finite independentdesign active, backup unchangedSource fixture qualification pending slot. No actual/root/STOP/backup/fence/Restart/model authority; formal0/42/all22open; mixed preserved records1924.\n\n').encode()+raw[hp])
assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':520,'ownership':306,'mixed_preserved_records':1924,'resume':rr,'verified_refs':len(verified),'review_scope':ref(O/'owned-core-stop-r4-independent-review-scope.json')},ensure_ascii=False))
