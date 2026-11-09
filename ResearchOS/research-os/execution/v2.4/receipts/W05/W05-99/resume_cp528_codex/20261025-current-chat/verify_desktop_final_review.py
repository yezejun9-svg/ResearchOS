import json
from pathlib import Path
from preserve_main_baseline import verify,read,ref,R,N
V=N.parent.parent/'desktop_main7d_independent_review_codex/20261025-current-chat/complete-tree'
refs=[]
for name,sha in [('R3-REVIEW-SEAL.json','2981911af85ea4163389592041a9474f0ed5ed8e027ba5ac131e3912560b939c'),('R3-REVIEW-MANIFEST.json','b2dd5376a2fc18114416bbe12fa0c7b902944baf3d1f7a9a4ea58a37831933f0'),('R3-INDEPENDENT-REVIEW.md','78f88e72560997764e3d74bc96584a4490f201f3650462174607dd15da3c0709')]:
 a=ref(V/name);assert a['sha256']==sha;refs.append(a)
s=read(V/'R3-REVIEW-SEAL.json');assert s['verdict']=='SOURCE_BUILD_REVIEW_PASS_NOT_NATIVE_ACCEPTED' and s['blocking_findings']==0 and s['native_gui_core_starts']==0 and s['formal_increment']==0
for x in read(V/'R3-REVIEW-MANIFEST.json')['files']:
 a=ref(V/x['path']);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'];refs.append(a)
d=read(V/'REVIEW-DIAGNOSTICS.json');assert ref(V/'REVIEW-DIAGNOSTICS.json')['sha256']==s['diagnostics_sha256'] and d['reviewer_nonzero_count']==4
c=read(N/'Desktop-ecc28-candidate-root-verification.json');assert c['candidate_commit']==s['candidate_commit'] and c['candidate_tree']==s['candidate_tree']
for x in c['verified_refs']:
 a=ref(Path(x['path']));assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'];refs.append(a)
out={'schema':'researchos.desktop-independent-final-root-verification.v1','verdict':s['verdict'],'candidate_commit':s['candidate_commit'],'candidate_tree':s['candidate_tree'],'bundle_manifest_sha256':s['bundle_manifest_sha256'],'verified_refs':refs,'reviewer_diagnostics':d['reviewer_nonzero_attempts'],'originals_preserved':verify(),'native_GUI_Core_launched':False,'formal_increment':0}
with(N/'Desktop-independent-final-root-verification.json').open('x',encoding='utf8')as stream:json.dump(out,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'verified_refs':len(refs),'verdict':out['verdict'],'blocking_findings':0,'formal':0}))
