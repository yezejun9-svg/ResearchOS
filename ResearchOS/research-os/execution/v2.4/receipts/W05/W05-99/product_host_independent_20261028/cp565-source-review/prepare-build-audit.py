from pathlib import Path
E=Path(__file__).resolve().parent
s=(E.parent/'final-448af-review/audit-build04.py').read_text(encoding='utf8')
s=s.replace("A=AUTH/'marker-fixture-cp563/build-04';B=W/'.local/product-layout-cp558-20261028-04'","A=AUTH/'asar-repair-cp565/build-05';B=W/'.local/product-layout-cp558-20261028-05'")
s=s.replace("HEAD='448af57c208a3f29199d10e0fa9d9c7311776fad';TREE='c4c9a19b5dce33a390620cb460e5b1c88d28cfc2';BASE='9361c1b63fa658251f730771bc12633ff5f12c08'","HEAD='5c4c94022bd92da68ef544f2779527bfe065c428';TREE='133c6fdee17e1ad2f7758689c55c1486e778cec0';BASE='448af57c208a3f29199d10e0fa9d9c7311776fad'")
s=s.replace("req(changed==['tests/ui/desktop/product-host.test.mjs'],'exact1')","req(changed==['apps/desktop/main/main.js','tests/ui/desktop/product-host.test.mjs'],'exact2')")
s=s.replace("E/'exact1.diff'","E/'build-source.diff'")
s=s.replace("E.parent/'build03-review/DEPENDENCY-RECHECK.json'","E.parent/'final-448af-review/DEPENDENCY-DELTA.json'")
s=s[:s.index('node_before=read(')]
s+='''
for ref in refs:req(sha(ref['path'])==ref['sha256'],'review input drift')
req(git('rev-parse','HEAD')==HEAD and not git('status','--porcelain'),'git drift')
put('BUILD05-INPUTS.json',refs)
summary={'status':'BUILD05_BOUND_MANIFEST_AND_CLOSURES_VERIFIED','head':HEAD,'tree':TREE,'parent':BASE,'exact_delta':changed,'marker_sha256':sha(B/'installed-product.json'),'installation_id':marker['installation_id'],'inventory_files_rehashed':133,'electron_runtime_files':sum(x.startswith('runtime/electron/') for x in names),'closures':closures,'unique_dependency_records':len(checks),'changed_dependency_records_rehashed':sum(x['verification']=='CURRENT_HASH' for x in checks),'behavior_reruns_by_reviewer':0,'formal_increment':0}
put('BUILD05-REVIEW.json',summary);print(json.dumps(summary))
'''
s=s.replace("put('DEPENDENCY-DELTA.json',checks)","put('BUILD05-DEPENDENCY-DELTA.json',checks)")
with (E/'audit-build05.py').open('x',encoding='utf8') as f:f.write(s)
