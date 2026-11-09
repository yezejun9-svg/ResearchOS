from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def write(name,value):
 with (H/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
v=json.loads((H/'verified-input-pins.json').read_bytes())
for r in v['references']:assert pin(r['path'])==r
review=json.loads((H/'review.json').read_bytes());assert review['new_mechanical_errors']==0 and review['stop']
members={p.name:pin(p) for p in sorted(H.iterdir()) if p.is_file()}
write('MF.json',dict(schema='researchos.independent-review-manifest.v1',members=members,base_refs=v['references'],drift_count=0))
handoff=dict(schema='researchos.independent-review-handoff.v1',decision=review['decision'],manifest_ref=pin(H/'MF.json'),review_ref=pin(H/'review.json'),report_ref=pin(H/'report.md'),
 counts=dict(members=len(members),files=len(members)+2,base_refs=len(v['references'])),checkpoint_ref=review['canonical_checkpoint_ref'],
 old815prefix_preserved=True,registered_failures=823,highest_registered_ordinal=825,pending826_excluded=True,guard_entries_closed=155,
 new_mechanical_errors=0,authority='NONE',formal_acceptance=False,native_acceptance=False,Owner_or_original_business_acceptance=False,stop=True)
write('HDF.json',handoff)
for r in members.values():assert pin(r['path'])==r
print(json.dumps(dict(HDF=pin(H/'HDF.json'),MF=pin(H/'MF.json'),counts=handoff['counts'],decision=review['decision']),ensure_ascii=True))

