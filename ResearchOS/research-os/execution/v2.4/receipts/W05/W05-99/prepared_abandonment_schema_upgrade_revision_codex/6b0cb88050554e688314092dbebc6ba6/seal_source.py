from pathlib import Path
import json,hashlib,difflib
own=Path("D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\prepared_abandonment_schema_upgrade_revision_codex\\6b0cb88050554e688314092dbebc6ba6")
root=Path(r'D:/作品集/ResearchOS/research-os')
old=root/'execution/v2.4/receipts/W05/W05-99/prepared_abandonment_schema_upgrade_source_codex/e841e7fcddaa45ecb115f84df9827af2'
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,obj):
 p=own/name;p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8');return ref(p)
pins=json.loads((own/'base-refs.json').read_text(encoding='utf-8'))
drift=[x for x in pins if ref(Path(x['path']))!=x]
assert not drift,drift
sources=sorted(p for p in (own/'candidate-root').rglob('*') if p.is_file())
assert len(sources)==12
oldrefs=json.loads((old/'HDF.json').read_text(encoding='utf-8'))['source_refs']
refs={};patch=[];same=[];changed=[]
for p in sources:
 rel=p.relative_to(own).as_posix()
 prev=old/rel
 main=root/p.relative_to(own/'candidate-root')
 base=prev if prev.is_file() else main if main.is_file() else None
 refs[rel]={**ref(p),'base_ref':ref(base) if base else None}
 before=base.read_text(encoding='utf-8') if base else ''
 after=p.read_text(encoding='utf-8')
 if prev.is_file() and prev.read_bytes()==p.read_bytes():same.append(rel)
 else:changed.append(rel)
 patch.extend(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile=str(base) if base else '/dev/null',tofile=rel))
assert len(same)==9 and len(changed)==3
(own/'revision.patch').write_text(''.join(patch),encoding='utf-8')
test=(own/'candidate-root/internal/domain/backup_configuration_upgrade_test.go').read_text(encoding='utf-8')
part=test[test.index('func TestConfigurationUpgradeFreshAndAdditiveGuard'):]
hist=(own/'candidate-root/internal/domain/backup_upgrade_test.go').read_text(encoding='utf-8')
prov=json.loads((own/'historical14-method-provenance.json').read_text(encoding='utf-8'))
checks={
 'same_nine_prior_source_files':len(same)==9,
 'fresh_historical_root23':'root := configurationUpgradeReleaseFixture(t, 23)' in part,
 'fresh_bootstrap_historical_root':'store.Bootstrap(ctx, db, filepath.Join(root, "migrations/sqlite/0001_bootstrap.sql"))' in part,
 'fresh_new_historical_root':'New(db, filepath.Join(root, "spec/v2.0/contracts"), filepath.Join(root, "migrations/sqlite/0002_domain.sql"))' in part,
 'historical14_only_branch':'if version == 14 {' in hist,
 'three_original_resume_calls_retargeted':hist.count('resume(ctx, token, f.project')==3,
 'other_versions_keep_current_method':'resume := svc.ResumeCheckpoint' in hist,
 'exact_schema14_validation_before_method':'upgradeHistoricalFixtureService(t, db, opt.TargetRoot, 14, true)\n\t\t\treturn svc.upgradeHistorical14ResumeCheckpoint' in hist,
 'copied_historical_body_exact_inverse':prov['method_body_exact_after_name_inverse'] is True,
}
# Compare the complete original ActiveQueueRecovery function, not a prefix.
def func(s,name):
 a=s.index('func '+name+'(');b=s.find('\nfunc ',a+5);return s[a:] if b<0 else s[a:b]
checks['schema22_test_not_replaced']=func(test,'TestConfigurationUpgradeActiveQueueRecovery')==func((old/'candidate-root/internal/domain/backup_configuration_upgrade_test.go').read_text(encoding='utf-8'),'TestConfigurationUpgradeActiveQueueRecovery')
assert all(checks.values()),checks
static=write('static-evidence.json',{'kind':'STATIC_TEXT_HASH_ONLY_NOT_GO_TESTS','checks':checks,'source_file_count':len(sources),'input_pin_count':len(pins),'drift':drift,'prior_sources_byte_identical':same,'changed_or_added_test_files':changed})
members={p.relative_to(own).as_posix():ref(p) for p in sorted(own.rglob('*')) if p.is_file() and p.name not in ['MF.json','HDF.json']}
mf=write('MF.json',{'schema':'researchos.source-manifest.v1','formal':False,'members':members,'member_count':len(members),'source_refs':refs,'base_refs':pins})
hdf=write('HDF.json',{'schema':'researchos.prepared-abandonment-schema-upgrade-revision-handoff.v1','status':'SOURCE_IMPLEMENTED_PENDING_ROOT_TESTS_AND_INDEPENDENT_REVIEW','sourceStatus':'EXECUTION_REPORTED','formal':False,'production_ready':False,'execution_authority':False,'source_root':str(own/'candidate-root'),'source_file_count':12,'source_refs':refs,'manifest_ref':mf,'previous_source_handoff':ref(old/'HDF.json'),'previous_source_manifest':ref(old/'MF.json'),'inherited_product_contract':ref(old/'CONTRACT.md'),'contract_ref':ref(own/'CONTRACT.md'),'diagnosis_ref':ref(own/'diagnosis.json'),'patch_ref':ref(own/'revision.patch'),'static_evidence_ref':static,'original_tool_io_ref':ref(own/'original-tool-io.json'),'failure_origins':[ref(own/'failure-origin.770.json'),ref(own/'failure-origin.771.json')],'root768_preserved_not_recounted':True,'source_fix_count':2,'open_schema22_fixture_boundary':True,'root_resource_wiring_cases':3,'historical_method_provenance':ref(own/'historical14-method-provenance.json'),'input_pin_count':len(pins),'input_drift_count':0,'actual_author_execution':{'python_metadata_source_writes':True,'go':False,'gofmt':False,'tests':False,'native':False,'sql':False,'provider':False,'git':False,'Main_write':False,'canonical_write':False},'composition_note':'Use exact Source roots pinned by Root. This revision changes no migration/native API. The newest native-authority package is separately owned and must not be inferred from this prior Source dependency.','remaining_gates':['Root format/build/focused and historical tests','source22 historical public execution boundary','Root matched frozen source22/target23/schema14 and locked Go resources','independent Source and actual-result review','all previous schema23-to24 production, issuer, matching backup/rehearsal and original-root authorization gates']})
print(json.dumps({'HDF':hdf,'MF':mf,'source_files':12,'members':len(members),'total_files':len(members)+2,'checks':len(checks),'inputs':len(pins),'drift':0,'failure_origins':[ref(own/'failure-origin.770.json'),ref(own/'failure-origin.771.json')]},indent=2))

