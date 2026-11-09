from pathlib import Path
import json,hashlib,difflib
own=Path("D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\schema22_public_fixture_bridge_source_codex\\3d7d237d23244950a6d9008753e3fde9")
r=Path(r'D:/作品集/ResearchOS/research-os'); b=r/'execution/v2.4/receipts/W05/W05-99'
prior=b/'prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6'
old=b/'host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a'
def ref(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(name,obj):
 p=own/name;p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8');return ref(p)
pins=json.loads((own/'base-refs.json').read_text(encoding='utf-8'))
drift=[x for x in pins if ref(Path(x['path']))!=x]
assert not drift,drift
childpath=own/'historical22-overlay/internal/domain/configuration_historical22_bridge_test.go'
parentpath=own/'candidate-root/internal/domain/backup_historical22_bridge_test.go'
testpath=own/'candidate-root/internal/domain/backup_configuration_upgrade_test.go'
basepath=prior/'candidate-root/internal/domain/backup_configuration_upgrade_test.go'
child=childpath.read_text(encoding='utf-8');parent=parentpath.read_text(encoding='utf-8')
test=testpath.read_text(encoding='utf-8');base=basepath.read_text(encoding='utf-8')
fa=base.index('func TestConfigurationUpgradeActiveQueueRecovery')
fb=base.index('\nfunc ',fa+5)
ta=test.index('func TestConfigurationUpgradeActiveQueueRecovery')
tb=test.index('\nfunc ',ta+5)
sa=base.index('\tctx := context.Background()',fa);sb=base.index('\tbefore, e := upgradeRows(f.db)',sa)
setup=base[sa:sb]
ca=child.index('\tctx := context.Background()');cb=child.index('\n    versions, err = backupMigrations',ca)
copied=child[ca:cb]
inverse=copied.replace('svc = &ClientService{Doc: historical22ProtocolSchema(t, codeRoot),','svc := &ClientService{Doc: configurationSchema(t),').replace('historical22FixturePort{','configurationUpgradePort{').replace('publicCommand(','configurationPublicCommand(t, f, svc, ')
oldtail=base[sb:fb]
newtail=test[test.index('\tbefore, e := upgradeRows(f.db)',ta):tb].replace('historical.RunID','run.run["id"]').replace('historical.RunEpoch','run.run["lease_epoch"]')
checks={
 'all_506_pinned_inputs_unchanged':len(pins)==506 and not drift,
 'historical_502_manifest_members':len(json.loads((own/'historical22-overlay/internal/domain/schema22_bridge_inputs.json').read_text())['files'])==502,
 'old_public_setup_inverse_normalized_exact':inverse==setup,
 'all_original_recovery_assertions_preserved':newtail==oldtail,
 'all_other_historical_tests_unchanged':test[:ta]==base[:fa] and test[tb:]==base[fb:],
 'only_fixed_test_entry_launched':'-test.run=^TestConfigurationHistorical22FixtureBridge$' in parent,
 'no_current_service_in_parent_bridge':'New(' not in parent and 'svc.Execute' not in parent,
 'actual_old_public_execute_in_child':'svc.Execute(context.Background(), tx, decoded, f.owner)' in child,
 'matched_populated22_old_startup_gate':'f.s, err = New(f.db,' in child and 'historical22 New changed rows' in child,
 'embedded_complete_historical_inputs':'//go:embed schema22_bridge_inputs.json' in child and 'len(seen) != 504' in child,
 'explicit_helper_binary_hash':'Digest(raw) != programSHA' in parent,
 'nine_responses_from_original_idempotency_rows':'len(result.Commands) != 9' in parent and 'SELECT request_hash,body FROM idempotency WHERE principal=? AND project=? AND operation=? AND key=?' in parent,
 'parent_cleanup_registered_before_first_input_or_assertion':'t.Cleanup(func() {' in parent and parent.index('t.Cleanup(func() {')<parent.index('sent := make(chan error, 1)'),
 'bounded_release_wait_and_kill':all(x in parent for x in ['2*time.Second','5*time.Second','cmd.Process.Kill()','cmd.Wait()','context.WithTimeout','150s']),
 'source_db_closed_before_public_result':child.index('f.db.Close()')<child.index('fmt.Println(historical22BridgePrefix'),
 'child_retains_temps_until_parent_release':'decoder.Decode(&release)' in child,
 'owner_not_a_result_field':'Owner string' not in child[child.index('type historical22BridgeResult'):child.index('// All data paths')],
 'owner_not_env_or_command_arg':'request.Owner' in child and '"RESEARCHOS_CONFIGURATION_SCHEMA22_BRIDGE=1"' in parent,
 'old_fixture_phase_label_and_range_retained':'FIXTURE_PHASE' in copied and 'phaseReceipts != 6' in child,
 'no_protocol_implementation_copied':'func (s *ClientService) Execute' not in child and 'func (s *ClientService) dispatch' not in child,
}
assert all(checks.values()),checks
prov=json.loads((own/'fixture-setup-provenance.json').read_text())
prov['construction_source_files']=prov.pop('source_files')
prov['final_source_files']=[ref(childpath),ref(testpath)]
prov['final_setup_inverse_normalized_exact']=inverse==setup
prov['final_original_recovery_assertions_inverse_exact']=newtail==oldtail
write('fixture-setup-provenance.json',prov)
sources={p.relative_to(own).as_posix():ref(p) for p in sorted((own/'candidate-root').rglob('*')) if p.is_file()}
historical={p.relative_to(own).as_posix():ref(p) for p in sorted((own/'historical22-overlay').rglob('*')) if p.is_file()}
assert len(sources)==2 and len(historical)==2
patch=[]
for rel,v in {**sources,**historical}.items():
 p=Path(v['path'])
 prev=basepath if rel.endswith('/backup_configuration_upgrade_test.go') else None
 patch.extend(difflib.unified_diff(prev.read_text().splitlines(keepends=True) if prev else [],p.read_text().splitlines(keepends=True),fromfile=str(prev) if prev else '/dev/null',tofile=rel))
(own/'source.patch').write_text(''.join(patch),encoding='utf-8')
static=write('static-evidence.json',{'kind':'STATIC_TEXT_HASH_PROVENANCE_ONLY_NOT_GO_EXECUTION','checks':checks,'input_count':len(pins),'input_drift':drift,'current_overlay_files':2,'historical_overlay_files':2,'go_test_status':'NOT_RUN'})
members={p.relative_to(own).as_posix():ref(p) for p in sorted(own.rglob('*')) if p.is_file() and p.name not in ['MF.json','HDF.json']}
mf=write('MF.json',{'schema':'researchos.schema22-fixture-bridge-source-manifest.v1','formal':False,'members':members,'member_count':len(members),'source_refs':sources,'historical22_overlay_refs':historical,'base_refs':pins})
hdf=write('HDF.json',{'schema':'researchos.schema22-fixture-bridge-source-handoff.v1','status':'SOURCE_IMPLEMENTED_PENDING_ROOT_BUILD_TEST_AND_INDEPENDENT_REVIEW','sourceStatus':'EXECUTION_REPORTED','formal':False,'production_ready':False,'execution_authority':False,'source_root':str(own/'candidate-root'),'source_file_count':2,'source_refs':sources,'historical22_overlay_root':str(own/'historical22-overlay'),'historical22_overlay_file_count':2,'historical22_overlay_refs':historical,'manifest_ref':mf,'previous_migration_revision_handoff':ref(prior/'HDF.json'),'previous_migration_revision_manifest':ref(prior/'MF.json'),'composition_order':'Apply candidate-root after prior migration revision; historical22-overlay goes ONLY into Root new isolated old22 copy. No prior Source mutation.','historical_source_root':str(old/'frozen_source'),'historical_git_source':ref(old/'git_source.json'),'historical_commit':'396287cc5427eb125aaedb8a2b7fadf63e6b9322','historical_source_file_count':502,'embedded_input_manifest':ref(own/'historical22-overlay/internal/domain/schema22_bridge_inputs.json'),'build_profile_ref':ref(own/'build-profile.json'),'contract_ref':ref(own/'CONTRACT.md'),'provenance_ref':ref(own/'fixture-setup-provenance.json'),'static_evidence_ref':static,'patch_ref':ref(own/'source.patch'),'original_tool_io_ref':ref(own/'original-tool-io.json'),'failure_origins':[ref(own/f'failure-origin.{n}.json') for n in [775,776,778]],'input_pin_count':len(pins),'input_drift_count':0,'actual_author_execution':{'python_metadata_and_source_construction':True,'go':False,'gofmt':False,'native':False,'SQL':False,'provider':False,'DPAPI':False,'Git':False,'Main_write':False,'canonical_write':False,'frozen_source_write':False,'old_revision_write':False},'result_scope':'Historical API fixture only; original FIXTURE_PHASE injection is synthetic phase coverage, never SDK/provider/model/formal execution.','remaining_gates':['Root owned504-file old22copy + actual locked Go helper build and hash','Root current composition and focused historical fixture execution','Full relevant historical regression with matching resources','Independent source/actual-result review','All prior production migration/native/issuer/authorization gates remain']})
print(json.dumps({'HDF':hdf,'MF':mf,'current_source_count':2,'historical_overlay_count':2,'manifest_members':len(members),'total_files':len(members)+2,'static_checks':len(checks),'inputs':len(pins),'drift':0,'failure_origins':[ref(own/f'failure-origin.{n}.json') for n in [775,776,778]]},indent=2))

