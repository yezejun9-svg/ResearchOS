from pathlib import Path
import json,hashlib
own=Path("D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\schema22_public_fixture_bridge_revision_codex\\378a514e11f9417fab091937a9d2421c")
prior=own.parent.parent/'schema22_public_fixture_bridge_source_codex/3d7d237d23244950a6d9008753e3fde9'
failed=Path("D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\schema22_public_fixture_bridge_revision_codex\\27d0db0ad5184a03b3a794e464526f2a")
def ref(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(n,v):
 p=own/n;p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');return ref(p)
old=json.loads((prior/'HDF.json').read_text())
pins=json.loads((own/'base-refs.json').read_text())
assert all(ref(Path(x['path']))==x for x in pins)
source_refs={rel:ref(own/rel) for rel in old['source_refs']}
historical_refs={rel:ref(own/rel) for rel in old['historical22_overlay_refs']}
rel='candidate-root/internal/domain/backup_configuration_upgrade_test.go'
before=Path(old['source_refs'][rel]['path']).read_bytes();after=(own/rel).read_bytes()
line=b'\t"time"\n'
assert before.count(line)==1 and after==before.replace(line,b'',1)
same=[]
for k,v in {**old['source_refs'],**old['historical22_overlay_refs']}.items():
 if k!=rel:
  assert (own/k).read_bytes()==Path(v['path']).read_bytes();same.append(k)
assert len(same)==3
partial={p.relative_to(failed).as_posix():ref(p) for p in sorted(failed.rglob('*')) if p.is_file()}
assert len(partial)==4
for k,v in partial.items():
 assert v['sha256']=={**old['source_refs'],**old['historical22_overlay_refs']}[k]['sha256']
write('failed-partial-namespace.pins.json',{'namespace':str(failed),'status':'UNSEALED_FAILED_CONSTRUCTION_NOT_DELIVERABLE','failure_sequence':783,'members':partial})
static=write('static-evidence.json',{'kind':'BYTE_AND_HASH_CHECKS_ONLY','sole_change':'delete the eight actual LF-terminated bytes of the unused time import','changed_member':rel,'exact_single_deletion':True,'all_other_bytes_in_changed_file_identical':True,'all_other_source_members_byte_identical':same,'input_pins':len(pins),'input_drift_count':0,'tests_executed':0,'Go_build_performed':False,'Root_previous_failure':'build-time unused import; zero tests executed','original_test_suite_and_assertions_retained':True})
members={p.relative_to(own).as_posix():ref(p) for p in sorted(own.rglob('*')) if p.is_file() and p.name not in ['MF.json','HDF.json']}
mf=write('MF.json',{'schema':'researchos.schema22-fixture-bridge-revision-manifest.v1','formal':False,'member_count':len(members),'members':members,'source_refs':source_refs,'historical22_overlay_refs':historical_refs,'base_refs':pins})
h=dict(old)
h.update({'schema':'researchos.schema22-fixture-bridge-revision-handoff.v1','status':'SOURCE_FIXED_PENDING_ROOT_BUILD_REGRESSION_AND_INDEPENDENT_REVIEW','source_root':str(own/'candidate-root'),'source_refs':source_refs,'historical22_overlay_root':str(own/'historical22-overlay'),'historical22_overlay_refs':historical_refs,'manifest_ref':mf,'previous_bridge_source_handoff':ref(prior/'HDF.json'),'previous_bridge_source_manifest':ref(prior/'MF.json'),'contract_ref':ref(own/'CONTRACT.md'),'inherited_contract_ref':ref(prior/'CONTRACT.md'),'build_profile_ref':ref(own/'build-profile.json'),'provenance_ref':ref(own/'revision-delta.json'),'static_evidence_ref':static,'patch_ref':ref(own/'source.patch'),'original_tool_io_ref':ref(own/'original-tool-io.json'),'embedded_input_manifest':ref(own/'historical22-overlay/internal/domain/schema22_bridge_inputs.json'),'failure_origins':[ref(own/'failure-origin.783.json')],'prior_failure_origins_preserved':old['failure_origins'],'failed_partial_namespace_pins':ref(own/'failed-partial-namespace.pins.json'),'input_pin_count':len(pins),'input_drift_count':0,'source_delta':'exactly one unused import line removed, eight LF-terminated bytes; all other bytes unchanged','source_refs_shape':'dictionary keyed by candidate-root-relative member path; each value contains path,sha256,bytes','historical22_overlay_refs_shape':'dictionary keyed by historical22-overlay-relative member path; each value contains path,sha256,bytes','Root_prior_build_test_count':0,'author_accepted':False,'actual_author_execution':{'python_metadata_source_write':True,'go':False,'gofmt':False,'tests':False,'native':False,'SQL':False,'models':False,'DPAPI':False,'production_signing':False,'Git':False,'Main_write':False,'canonical_write':False,'old_source_write':False,'old_root_worktree_write':False},'composition_order':'Same prior composition; replace previous bridge current source_refs with this revision. Historical22 overlay is byte-identical. Do not modify previous sealed sources or old Root worktrees.'})
hdf=write('HDF.json',h)
print(json.dumps({'namespace':str(own),'HDF':hdf,'MF':mf,'members':len(members),'total_files':len(members)+2,'source_refs':source_refs,'historical22_overlay_count':len(historical_refs),'unchanged_source_members':3,'removed_bytes':8,'inputs':len(pins),'new_failure_origin':ref(own/'failure-origin.783.json')},indent=2))

