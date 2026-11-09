import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path('D:/作品集/ResearchOS/research-os')
HERE=Path(__file__).resolve().parent
CONTROL=HERE/'product-v1-owned-verification-20261104'
BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104'
OUT=BASE/'progress-cp682'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
    temp=p.with_name(p.name+'.cp682.new');assert not temp.exists()
    with temp.open('xb') as f:
        raw=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')
        assert f.write(raw)==len(raw);f.flush();os.fsync(f.fileno())
    os.replace(temp,p)
cpf=ROOT/'execution/v2.4/checkpoint.json';raw=cpf.read_bytes();cp=read(cpf)
assert cp['revision']==681 and cp['current_Main_HEAD']=='998fc6330ba735056cd31f8ebf68dd50a8251c1b'
assert len(cp['failure_counters'])==2617 and not OUT.exists()
leases=read(ROOT/'execution/product-v1/leases.json')
assert not [x for x in leases['source_owners'] if x['status']=='IMPLEMENTING']
r12=read(CONTROL/'runs/product-v1-build-12/RESULT.json')
assert r12['root_exit_code']==1 and r12['stop_proved'] and r12['job_active_zero'] and not r12['input_drift']
assert r12['terminate_job_attempts']==0 and r12['job_total_processes']==18
effective=CONTROL/'scopes/product-v1-build-13-effective-v1.json'
assert sha(effective)=='478fc79a6a70383714fb2f129b8ff1bcf95be2223a991f97e39ba2e227bc0275'
assert (CONTROL/'runs/product-v1-build-13/CONSUMED.json').is_file()
pure={}
for key,scope_id,count in [('controller','product-v1-native-conditional-controller-pure-02',5),('poststop','product-v1-native-conditional-poststop-pure-02',6)]:
    path=CONTROL/'runs'/scope_id/'RESULT.json';r=read(path)
    assert r['root_exit_code']==0 and r['stop_proved'] and r['job_active_zero'] and not r['input_drift'] and not r['errors'] and not r['timed_out'] and r['terminate_job_attempts']==0
    pure[key]=dict(scope_id=scope_id,result_path=str(path),result_sha256=sha(path),passed=count,claim='PURE_VALIDATORS_ONLY_NOT_LIVE_EXECUTION')
diagnostics=[
('native-conditional-controller:windows-canonical-source', 'RESOLVED_CONTROLLER_SOURCE_FIXTURE', 'CTRL-F1 slash spelling differed from actual Shell/Main canonical Windows reply; frozen prep02 canonicalizes fixed literal. Five actual pure tests and independent57b36a review passed; no Task execution.'),
('native-conditional-controller:late-addition-pin-check','RESOLVED_CONTROLLER_SOURCE_FIXTURE','CTRL-F2 moved fixed B3 allowed-addition pins before root creation/App/Task; original prep01 and review retained. This was static source finding, not a consumed model attempt.'),
('native-conditional-poststop:outer-inner-scope-conflation','RESOLVED_POSTSTOP_SOURCE_FIXTURE','POST-F1 distinct outer f13 and inner runner scope pins, exact argv and input binding; original prep01 preserved. Six pure tests passed; no live verifier execution.'),
('native-conditional-poststop:plan-event-json-case','RESOLVED_POSTSTOP_SOURCE_FIXTURE','POST-F2 uses actual lowercase production Plan/Event JSON tags; original uppercase expectation retained in prep01. Finite validator fixtures only.'),
('native-conditional-poststop:nil-slice-wire-encoding','RESOLVED_POSTSTOP_SOURCE_FIXTURE','POST-F3 accepts exact phase-specific null-or-empty Go nil slices while requiring seven actual final results; undefined/nonempty finding codes remain rejected.'),
('root:conditional-controller-pure-registrar-manifest-key','ROOT_TOOL_PREFLIGHT','Root initial registrar expected artifacts key while prep02 uses files. KeyError before scope/output creation; corrected source registered fresh pure02 once. No App/Native/Task execution.'),
('root:desktop-build12-helper-origin-input','ROOT_ACTUAL_BUILD_PREFLIGHT_FAILURE','Actual build12 stopped before producer creation: supplied S helper copy has same4ac bytes but original build receipt binds buildout path. Security source correctly rejected detached input path;18 Job processes stopped without force/drift. Build13 uses original artifact plus separately pinned S copy. No source gate relaxed or build12 replayed.'),
('root:desktop-build12-registration-draft-newline','AUTHOR_TOOL_SOURCE_SYNTAX_DIAGNOSTIC','Preserved draft SHA989f5c89 has valid UTF8 but literal newline escape causes SyntaxError line58; successor fixed and compile-only checked. No registered build used damaged draft.'),
('root:desktop-build12-serial-wrapper-stage','ROOT_STATIC_RECIPE_DIAGNOSTIC','Initial unfrozen wrapper mistakenly surrounded registrar, which cannot carry GOMAXPROCS through f13 clean environment. Corrected before build12 registration to surround actual app builder. Earlier Root readback retained in conversation; no distinct original wrapper file asserted archived.'),
('root:desktop-build13-unconsumed-wrapper-reference','ROOT_PRE_EXECUTION_SCOPE_AMENDMENT','Original registered13 still named serial12 after mechanical derivation. Root verified no runs/13 existed, preserved original scope413a76 and registration, added effective-v1 scope478fc79 with exact13 wrapper before first execution. Original13 scope was never run; no consumed scope overwritten.')]
now=datetime.now(timezone.utc).isoformat();original=list(cp['failure_counters']);known={x.get('origin_key') for x in original}
for origin,classification,detail in diagnostics:
    assert origin not in known
    cp['failure_counters'].append(dict(at=now,attempts=1,counter_reset=False,origin_key=origin,classification=classification,detail=detail));known.add(origin)
assert cp['failure_counters'][:len(original)]==original
OUT.mkdir();(OUT/'checkpoint.before.json').write_bytes(raw)
result13=CONTROL/'runs/product-v1-build-13/RESULT.json'
observed13=read(result13) if result13.exists() else dict(status='RUNNING_FINAL_RESULT_NOT_YET_SAVED',exec_session_id=37185)
progress=dict(checkpoint_revision=682,at=now,status='BUILD13_OWNED_EXECUTION_CONTROLLER_AND_POSTSTOP_PURE_CHECKS_APPROVED',main_head=cp['current_Main_HEAD'],source_pins=67,source_owners=0,source_integrations=['730001fc9de543833190bebcd713c1eb71c80e8f','998fc6330ba735056cd31f8ebf68dd50a8251c1b'],source_lease_close_ref=str((BASE/'source-lease-close-cp681/RESULT.json').relative_to(ROOT)),pure=pure,build12=dict(status=r12['status'],exit=1,original_job_stop_proved=True,reason='ORIGINAL_PREBUILT_HELPER_PATH_REQUIRED_COPY_REJECTED',replay=False),build13=dict(scope_path=str(effective),scope_sha256=sha(effective),original_registered_scope_preserved=True,original_exec_session_id=37185,result_path=str(result13),observed_at_checkpoint=observed13,registration_ref=str((BASE/'build13-scope/registration.effective-v1.json').relative_to(ROOT))),controller_archive_ref=str((BASE/'native-conditional-controller02/ROOT_ARCHIVE.json').relative_to(ROOT)),poststop_archive_ref=str((BASE/'native-conditional-poststop02/ROOT_ARCHIVE.json').relative_to(ROOT)),real_model_requests=1,new_real_model_requests=0,inference='PRIOR_CP647_NOT_CONFIRMED_NO_NEW_NATIVE_MODEL',product_journeys_accepted=0,product_journeys_required=13,legacy_formal_accepted=0,legacy_formal_required=42,historical_records=len(cp['failure_counters']),old_records_reset=False,next='Reconcile original build13 RESULT/session37185, never rerun consumed13 or12. If successful verify complete bundle and exact67source/root/helper/linker provenance, then freeze independently reviewed fresh conditional actual registrar/scope. One NEW synthetic Task and one qualification/RPC/userturn only after all gates; no old Task/echo replay. If build blocked preserve exact failure and continue unaffected source/product branch. No full completion claim.')
put(OUT/'RESUME.json',progress)
sf=ROOT/'execution/product-v1/state.json';sraw=sf.read_bytes();s=read(sf);(OUT/'state.before.json').write_bytes(sraw)
s.update(revision=s['revision']+1,updated_at=now,status=progress['status'],last_progress_ref=str((OUT/'RESUME.json').relative_to(ROOT)),next=progress['next'])
cp.update(revision=682,expected_previous_revision=681,updated_at=now,next_command=progress['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT)))
cp['current_implementation']=dict(status=progress['status'],at=now,resume_ref=str((OUT/'RESUME.json').relative_to(ROOT)),active_construction_owners=[],formal_increment=0)
assert cpf.read_bytes()==raw and sf.read_bytes()==sraw
put(sf,s);put(cpf,cp)
hf=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=hf.read_bytes();(OUT/'handoff.before.md').write_bytes(old)
temp=hf.with_name(hf.name+'.cp682.new');assert not temp.exists();temp.write_bytes(('# Current resume CP682 - BUILD13 OWNED EXECUTION; ACTUAL MODEL NOT RUN\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Build12 known stopped and preserved. Build13 consumed effective-v1 scope may still run: inspect original session/result before any action. Both source fixes integrated; controller5pure/poststop6pure independently approved. No new Task/Native/model, journeys0/13, legacyformal0/42; all old failures/UNKNOWN preserved.\n\n').encode('utf8')+old);os.replace(temp,hf)
(OUT/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(checkpoint=682,head=progress['main_head'],historical_records=progress['historical_records'],new_native_model_calls=0,build13_status=observed13['status'])))
