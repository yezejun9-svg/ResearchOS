import pathlib,json,hashlib
O=pathlib.Path(__file__).parent
def r(p):
 b=p.read_bytes();return {'path':str(p).replace('\\','/'),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def w(n,x):
 p=O/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return r(p)
entries=[r(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in ('manifest.final.json','handoff.final.json')]
m=w('manifest.final.json',{'schema':'researchos.public-review-manifest.v1','entry_count':len(entries),'entries':entries,'excludes':['manifest.final.json','handoff.final.json']})
h=w('handoff.final.json',{'decision':'SOURCE_SCOPE_READY_WITH_MANDATORY_SAME_PATH_BOUNDS','source_count':5,'scope_review':r(O/'scope_review.json'),'manifest':m,'read_audit':r(O/'read_audit.json'),'original_fixture':r(O/'old_v2verbs.git.raw'),'source_acceptance':False,'execution_performed':False,'root_CAS_before_implementation':True,'formal_increment':0})
print(json.dumps({'review':r(O/'scope_review.json'),'manifest':m,'handoff':h,'count':len(entries)},ensure_ascii=True))
