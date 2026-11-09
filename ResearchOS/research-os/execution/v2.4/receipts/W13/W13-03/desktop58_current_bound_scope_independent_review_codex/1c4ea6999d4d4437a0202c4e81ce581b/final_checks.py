from pathlib import Path
import hashlib,json,os,ast
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-'+O.name)
def read(p):return json.loads(Path(p).read_bytes())
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
s=read(N/'scope_registration.json');a=read(O/'audit.json');pp=read(O/'path-projection.json');q=read(N/'root-construction.parameters.desktop58.json');r=read(s['resource_catalog_ref']['path']);rt=read(s['runtime_resources_ref']['path']);c=read(s['compiler_resources_ref']['path']);m=read(r['root_membership_ref']['path'])
expected_false=['mandatory runtime basis '+x['original']['path'] for x in pp['runtime_path_only_changes']]+['runtime exact1242+40+8+6','compiler rows preserved current bytes']
ck('all original false predicates accounted exactly',sorted(x['check'] for x in a['failed_checks'])==sorted(expected_false) and all(x['passed'] for x in pp['checks']))
old=read(q['compiler_base_ref']['path']);ck('compiler permutation no byte or path changes',len(old['files'])==len(c['files'])==22138 and {x['path']:(x['sha256'],x['bytes']) for x in old['files']}=={x['path']:(x['sha256'],x['bytes']) for x in c['files']})
union={x['path']:x for x in c['files']+rt['files']+r['images']}
for key in ['electron_dist','web_modules']:
 root=Path(m['membership'][key]['root'])
 union.update({x['path']:x for x in r['files'] if Path(x['path']).is_relative_to(root)})
ck('exact resource union with no unrelated additions',union=={x['path']:x for x in r['files']})
ck('all resource and source byte checks passed',all(x['passed'] for x in a['checks'] if x['check'].startswith('pin ')))
ck('all current public roots membership exact',all(not x['extra'] and not x['missing'] and not x['reparse'] for x in a['membership_results']))
constructor=(N/'construct_root_inputs.desktop58.v3.py').read_text(encoding='utf-8')
ck('constructor actual canonical projection present','resolve(' in constructor and "'files':" in constructor)
observation=read(N/'scope-build.tool-observation.closed.json');summaries={}
def summarize(x):
 if isinstance(x,dict):return {k:summarize(v) for k,v in x.items() if k not in ['cmd','output','original_tool_output','source']}
 if isinstance(x,list):return [summarize(v) for v in x]
 return x
summaries['scope']=summarize(observation)
for name in ['resource-capture.tool-observation.closed.json','binding-pre-review.tool-observation.closed.json']:summaries[name]=summarize(read(N/name))
canonical=read(N/'canonical-before.constructed.json')['entries']
for e in canonical:ck('live canonical final '+e['canonical_path'],(R/e['canonical_path']).read_bytes()==Path(e['ref']['path']).read_bytes())
for k in ['output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root']:ck('fresh final '+k,not os.path.lexists(s[k]))
out={'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'correction':{'original_audit_ref':ref(O/'audit.json'),'projection_ref':ref(O/'path-projection.json'),'static_false_predicate_count':len(a['failed_checks']),'explanation':'Thirty historic Windows hFile path spellings require canonical Path.resolve() projection, preserving every SHA and byte count. Compiler rows have identical unique refs but a different order; consumers require resource membership, not original list order. Original audit and code retained unchanged. Both audit executions exit0, no failure origin.'},'tool_observation_summaries':summaries,'tool_observation_refs':[ref(N/n) for n in ['scope-build.tool-observation.closed.json','resource-capture.tool-observation.closed.json','binding-pre-review.tool-observation.closed.json']],'actual_candidate_calls':0,'new_failure_origins':[]}
with (O/'final-checks.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'checks':len(checks),'failed':out['failed_checks'],'scope_observation_summary':summaries['scope'],'ref':ref(O/'final-checks.json')},ensure_ascii=False))
