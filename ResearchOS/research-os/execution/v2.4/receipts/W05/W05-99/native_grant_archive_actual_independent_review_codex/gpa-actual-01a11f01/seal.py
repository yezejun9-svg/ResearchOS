from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
def pin(p):
 raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
checks=json.loads((O/'checks.json').read_bytes());assert len(checks)==400 and all(x['passed'] for x in checks)
r=json.loads((O/'review.json').read_bytes());refs=json.loads((O/'initial-pins.json').read_bytes());files=sorted(p for p in O.rglob('*') if p.is_file() and p not in (O/'HDF.json',O/'MF.json',O/'postseal.json'))
save('MF.json',dict(schema='researchos.actual-public-archive-independent-manifest.v1',members=[pin(p) for p in files],member_count=len(files),excludes=['HDF.json','MF.json','postseal.json']))
h=dict(schema='researchos.actual-public-archive-independent-handoff.v1',status=r['status'],archive_manifest_ref=refs[0],request_ref=refs[1],helper_ref=r['helper_ref'],Source_resource_gate_ref=r['source_review_HDF'],manifest_ref=pin(O/'MF.json'),report_ref=pin(O/'report.md'),checks_ref=pin(O/'checks.json'),review_ref=pin(O/'review.json'),raw_equality_ref=pin(O/'raw-equality.json'),input_pins_ref=pin(O/'finite-input-pins.json'),independent_guard_ref=pin(O/'readguard.actual.closed.json'),hold_duration_ref=pin(O/'guard-hold-duration.json'),root_original_io_ref=pin(O/'root-original-tool-io.input.json'),root_original_io_origin_ref=json.loads((O/'root-original-tool-io.pin.json').read_bytes()),checks=400,failed_checks=0,originals_checked=61,archives_checked=61,identical_raw_pairs=61,source_inventory_count=28,target_inventory_count=29,backup_count=1,rehearsal_count=1,cipher_count=2,alias_one_copy=True,actual_archive_guard_entries=70,actual_archive_guard_closed=True,independent_guard_inputs=128,independent_guard_closed=True,TEMP_retained_handles=0,actual_archive_outer_exit=0,actual_archive_python_exit=0,actual_product_native_exit=None,grant_freshness_or_authority_claim=False,Native_migration_pass=False,formal_acceptance=False,full20_to24='OPEN',new_failure_ordinals=[],STOP=True,FINAL=True)
save('HDF.json',h);print(json.dumps(dict(HDF=pin(O/'HDF.json'),MF=pin(O/'MF.json'),status=h['status']),ensure_ascii=False))
