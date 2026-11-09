import json,hashlib
from pathlib import Path
from preserve_main_baseline import verify,read,ref,R,N
E=N.parent.parent;A=E/'desktop_main7d_native_codex/20261025-current-chat';V=E/'desktop_main7d_independent_review_codex/20261025-current-chat';W=R/'.local/worktrees/desktop-main7d-native-20261025'
preserved=verify();refs=[]
seal=V/'REVIEW-SEAL.json';assert ref(seal)['sha256']=='b436bec91308f70702d8cba6414dc06ca9adbf06c241d7bd7f01f973c00b3647';s=read(seal);refs.append(ref(seal))
for p,k in [(V/'REVIEW-MANIFEST.json','manifest_sha256'),(V/'DESKTOP-MAIN7D-INDEPENDENT-REVIEW.md','report_sha256')]:
 a=ref(p);assert a['sha256']==s[k];refs.append(a)
for x in read(V/'REVIEW-MANIFEST.json')['files']:
 a=ref(V/x['path']);assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'];refs.append(a)
assert s['native_nonzero']==s['gui_core_launches']==s['source_edits']==s['formal_increment']==0
b=read(A/'build-evidence-manifest.json');refs.append(ref(A/'build-evidence-manifest.json'))
assert b['builder_native_exit']==0 and b['builder_result_status']=='BUILT_NOT_TESTED' and not b['source_acceptance'] and b['input_drift_count']==0 and b['subinvocation_nonzero_count']==0 and b['subinvocations']==9
for x in b['copies']:
 for key in ['origin','canonical']:
  a=ref(Path(x[key]));assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'];refs.append(a)
internal=Path(b['internal_receipt_root']);before=read(internal/'inputs.before.json');after=read(internal/'inputs.after.json');assert len(before)==len(after)==b['input_count']==6449
for old,new in zip(before,after):
 assert new=={**old,'current_sha256':old['sha256']}
 p=Path(old['path'])
 if p.is_relative_to(W) and not p.is_relative_to(W/'.local'):
  a=ref(p);assert a['sha256']==old['sha256'] and a['bytes']==old['bytes']
for x in b['tools']:
 a=ref(Path(x['path']));assert a['sha256']==x['sha256'] and a['bytes']==x['bytes'];refs.append(a)
output=Path(b['output_root']);missing=[str(p.relative_to(output))for p in [output/'apps/desktop/resources/control/researchos-control.exe',output/'apps/desktop/resources/control/runtime-verifier-installation.json',output/'apps/desktop/resources/control/runtime',output/'migrations/sqlite']if not p.exists()];assert len(missing)==4
v={'schema':'researchos.desktop-main7d-build-root-verification.v1','source_head':b['source_head'],'verified_refs':refs,'source_bound_build':'BUILT_NOT_TESTED','input_count':6449,'input_drift':0,'builder_exit':0,'child_commands_exit0':9,'react_assets':3,'first_management_start_blocker':'INSTALLED_RESOURCE_UNAVAILABLE','missing_generated_resources':missing,'independent_review_blockers':['D01 resources missing','D02 ambient data/discovery isolation','D03 actual frozen smoke code false positive and missing successful shutdown evidence'],'native_GUI_Core_launched':False,'originals_preservation':preserved,'formal_increment':0}
with (N/'Desktop-Main7d-build-root-verification.json').open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'verified_refs':len(refs),'build':'BUILT_NOT_TESTED','input_count':6449,'drift':0,'review_blockers':3,'formal':0},ensure_ascii=False))
