from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def write(name,v):
 with (H/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
v=json.loads((H/'verified-input-pins.json').read_bytes());review=json.loads((H/'review.json').read_bytes())
for r in v['references']:assert pin(r['path'])==r
assert v['count']==4163 and review['copied_public_evidence_count']==53
for pair in review['copies']:
 a=pin(pair['original_ref']['path']);b=pin(pair['copied_ref']['path'])
 assert a==pair['original_ref'] and b==pair['copied_ref'] and a['sha256']==b['sha256'] and a['bytes']==b['bytes']
members={p.relative_to(H).as_posix():pin(p) for p in sorted(H.rglob('*')) if p.is_file()}
write('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=members,base_refs=v['references'],copied_public_evidence_count=53,drift_count=0))
handoff=dict(schema='researchos.independent-review-handoff.v1',decision=review['decision'],manifest_ref=pin(H/'MF.json'),review_ref=pin(H/'review.json'),report_ref=pin(H/'report.md'),
 counts=dict(members=len(members),files=len(members)+2,base_refs=v['count'],copied_public_files=53),
 source_count=43,unchanged_baseline_files=42,compile_jobs_closed=7,isolation_jobs_closed=5,compile_guard_groups_closed=5,isolation_guard_groups_closed=2,
 package_count=364,build_input_count=3793,product_inventory_count=599,embed_occurrences=38,compiler_tools=8,
 compiler_guard_set_exact=True,GoRef_VERSION_explicitly_guarded=True,canonical_pre_run_persisted=True,canonical_current_exact=True,
 Root_compile_full_tool_objects_persisted=True,Root_isolation_final_full_tool_object_persisted=False,Root_isolation_final_metadata_only=True,
 unit_execution=False,native_case_execution=False,new_unit_pass_count=0,issuer_signatures_created=0,new_mechanical_errors=0,
 authority='NONE',Main_adopted=False,native_acceptance=False,Owner_acceptance=False,formal_acceptance=False,stop=True)
write('HDF.json',handoff)
for r in members.values():assert pin(r['path'])==r
print(json.dumps(dict(HDF=pin(H/'HDF.json'),MF=pin(H/'MF.json'),counts=handoff['counts'],decision=review['decision']),ensure_ascii=True))

