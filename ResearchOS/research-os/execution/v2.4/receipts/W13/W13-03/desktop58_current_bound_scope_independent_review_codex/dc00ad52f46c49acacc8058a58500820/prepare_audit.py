from pathlib import Path
import json,hashlib,ast
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os')
old=R/'execution/v2.4/receipts/W13/W13-03/desktop58_current_bound_scope_independent_review_codex/1c4ea6999d4d4437a0202c4e81ce581b/audit.py'
text=old.read_text(encoding='utf-8');changes=[]
def replace(a,b):
 global text
 n=text.count(a);changes.append({'old':a,'new':b,'occurrences':n})
 if n==1:text=text.replace(a,b,1)
replace("q=doc(N/'root-construction.parameters.desktop58.json');ri=doc(N/'root-inputs.desktop58.pre-review.json')", "q=doc(N/'input_capture_v2/root-construction.parameters.desktop58.json');ri=doc(N/'input_capture_v2/root-inputs.desktop58.pre-review.json')")
replace('864913475e250e8363f628578df084eab8e93ebe3b769a4cf31164b9b5acd3de','9c91d99e92192ee5e21183d2a1a064d0f765aa3afacd36556191566d8b906f0a')
replace('[335,163,553]','[335,163,564]')
replace("len(cut['origins'])==21", "len(cut['origins'])==32")
replace("ck('all21 unique',len(newsha)==21)","ck('all32 unique',len(newsha)==32)")
replace("rt={x['path']:x for x in runtime['files']};base=doc(q['runtime_base_ref']['path'])['files'];corr=doc(q['mandatory_correction_ref']['path'])['missing_Windows_refs']", "canonical_row=lambda x:dict(x,path=str(path(x['path']).resolve()));rt={canonical_row(x)['path']:canonical_row(x) for x in runtime['files']};base=[canonical_row(x) for x in doc(q['runtime_base_ref']['path'])['files']];corr=[canonical_row(x) for x in doc(q['mandatory_correction_ref']['path'])['missing_Windows_refs']]")
replace("runtimewanted={x['path']:x for x in base+corr+q['metadata_code_refs']+[s[k] for k in codekeys]}","runtimewanted={canonical_row(x)['path']:canonical_row(x) for x in base+corr+q['metadata_code_refs']+[s[k] for k in codekeys]}")
replace("compiler['files']==oldcompiler['files']","{x['path']:(x['sha256'],x['bytes']) for x in compiler['files']}=={x['path']:(x['sha256'],x['bytes']) for x in oldcompiler['files']}")
start=text.index(" for obsname in ['resource-capture.tool-observation.closed.json'")
end=text.index(" for item in before:ck('final four",start)
replacement=""" observation=doc(N/'tool-observations.resource-capture.closed.json')
 ck('actual resource capture observation retained',isinstance(observation,dict))
 source_review=doc(R/'execution/v2.4/receipts/W13/W13-03/desktop58_cli_root_closure_adapter_independent_source_review_codex/5ae97e98de0568903e5d77af5169ffc5/review.json')
 ck('new v3 adapter independent source no requests',source_review['requested_changes']==[])
 qnew=qual['evidence_refs'];rootmf=doc(qnew['root_closed_manifest_ref']['path']);scan(rootmf)
 rootcompletion=doc(qnew['root_completion_ref']['path']);closureq=doc(rootcompletion['closure_request_ref']['path']);scan(closureq)
 ck('actual CLI2 aggregate schema169',rootmf['schema']=='researchos.root-launch-closure-manifest.v2' and len(rootmf['members'])==169 and rootcompletion['source_commit']==s['source_commit'])
 union={x['path']:x for x in compiler['files']+runtime['files']+resource['images']}
 for key in ['electron_dist','web_modules']:
  root=Path(groups[key]['root']);union.update({x['path']:x for x in resource['files'] if Path(x['path']).is_relative_to(root)})
 ck('exact resource union no unrelated files',union==files)
"""
changes.append({'old':'original observation/source-review block','new':'actual dc observations, v3 source review, actual169 aggregate and exact union','occurrences':1});text=text[:start]+replacement+text[end:]
with (O/'audit-derivation.json').open('xb') as f:f.write((json.dumps({'prior_source':{'path':str(old),'sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'bytes':old.stat().st_size},'changes':changes,'all_replacements_unique':all(x['occurrences']==1 for x in changes)},ensure_ascii=False,indent=2)+'\n').encode())
if all(x['occurrences']==1 for x in changes):
 ast.parse(text)
 with (O/'audit.py').open('xb') as f:f.write(text.encode('utf-8'))
print(json.dumps({'generated':all(x['occurrences']==1 for x in changes),'replacement_counts':[x['occurrences'] for x in changes]},ensure_ascii=False))
