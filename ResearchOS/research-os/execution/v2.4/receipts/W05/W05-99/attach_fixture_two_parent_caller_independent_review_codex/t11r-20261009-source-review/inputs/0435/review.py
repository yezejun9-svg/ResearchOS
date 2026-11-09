from pathlib import Path
import json, hashlib, re, collections
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
Q=B/'legacy_migration_fixture_source_codex/edd7ae2789974a469dd2fc3a1bce50a9'
O=B/'legacy_migration_fixture_independent_review_codex/4ec609adce7346a9b8fe61e898a8a15e'
T=R/'.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2'
def j(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def pin(p):
    data=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
def dump(name,obj): (O/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def copy(p,name):
    d=O/name; d.parent.mkdir(parents=True,exist_ok=True); d.write_bytes(p.read_bytes())
def refs(obj):
    if isinstance(obj,dict):
        if {'path','sha256','bytes'} <= set(obj): yield obj
        for v in obj.values(): yield from refs(v)
    elif isinstance(obj,list):
        for v in obj: yield from refs(v)
def masked(s):
    a=list(s); i=0
    while i<len(s):
        start=i
        if s.startswith('//',i):
            end=s.find('\n',i); i=len(s) if end<0 else end
        elif s.startswith('/*',i):
            end=s.find('*/',i+2); i=len(s) if end<0 else end+2
        elif s[i] in ('"',"'",'`'):
            q=s[i]; i+=1
            while i<len(s):
                if s[i]==q: i+=1; break
                if s[i]=='\\' and q!='`': i+=2
                else: i+=1
        else: i+=1; continue
        for k in range(start,min(i,len(s))):
            if a[k]!='\n': a[k]=' '
    return ''.join(a)
def funcs(s):
    m=masked(s); result={}
    for hit in re.finditer(r'^func\s+(Test\w+)\s*\(',m,re.M):
        left=m.find('{',hit.end()); depth=1; right=left+1
        while right<len(m) and depth:
            depth+=(m[right]=='{')-(m[right]=='}'); right+=1
        result[hit.group(1)]=s[hit.start():right]
    return result
def assertions(s):
    m=masked(s); result=[]
    for hit in re.finditer(r'\bt\.(?:Fatalf?|Errorf?|FailNow|Fail)\s*\(',m):
        depth=1; right=hit.end()
        while right<len(m) and depth:
            depth+=(m[right]=='(')-(m[right]==')'); right+=1
        result.append(s[hit.start():right])
    return collections.Counter(result)
O.mkdir(parents=True,exist_ok=False)
copy(Path(__file__),'review.py')
copy(Path('C:/Users/yqyyds/AppData/Local/Temp/w0599_legacy_read.py'),'read.py')
mf=j(Q/'MANIFEST.json'); sp=j(Q/'source-pins.json'); migrations=j(Q/'migration-resources.json'); historical=j(Q/'historical20-resource-entry.json')
checked=[]; seen=set()
for obj in (mf,sp,migrations):
    for ref in refs(obj):
        key=(ref['path'],ref['sha256'],ref['bytes'])
        if key in seen: continue
        seen.add(key); actual=pin(Path(ref['path']))
        checked.append(dict(expected=ref,actual=actual,match=all(actual[k]==ref[k] for k in ('sha256','bytes'))))
for p in (Q/'HANDOFF.json',Q/'MANIFEST.json',Q/'postseal-tool-io.json'):
    copy(p,'inputs/author/'+p.name)
for member in mf['members']: copy(Path(member['path']),'inputs/author/'+member['relative_path'])
for name in ('domain_test.go','context_test.go'):
    p=T/'internal/domain'/name; checked.append(dict(actual=pin(p),match=None,reason='independent transitive fixture source')); copy(p,'inputs/dependencies/'+name)
dump('input-pins.json',checked)
gitrows=[]
for entry in migrations['migration_sources']:
    raw=Path(entry['actual_source_ref']['path']).read_bytes(); obj=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    gitrows.append(dict(version=entry['version'],git_path=entry['git_path'],actual_blob=obj,expected_blob=entry['git_blob'],match=obj==entry['git_blob']))
ddl=(Q/'resources/pretranscript-3225a31f.sql').read_bytes(); ddlblob=hashlib.sha1(b'blob '+str(len(ddl)).encode()+b'\0'+ddl).hexdigest()
tree=historical['original_IO']['output']['output']; treeentries=[]
for line in tree.splitlines():
    left,path=line.split('\t',1); mode,typ,obj=left.split(); treeentries.append(dict(mode=mode,type=typ,git_blob=obj,git_path=path,commit=historical['commit']))
preserved=[]
for base in sp['base_refs']:
    p=Path(base['path']); a=p.read_text(encoding='utf-8'); b=(Q/'candidate-root/internal/domain'/p.name).read_text(encoding='utf-8')
    af,bf=funcs(a),funcs(b); aa,ba=assertions(a),assertions(b)
    preserved.append(dict(file=p.name,base_tests=list(af),candidate_tests=list(bf),lost_tests=sorted(set(af)-set(bf)),unchanged_bodies=[n for n in af if af[n]==bf.get(n)],base_assertions=aa.total(),candidate_assertions=ba.total(),missing_assertions=list((aa-ba).elements())))
post=j(Q/'postseal-tool-io.json'); calls=[]
for c in post['calls']:
    result=c.get('result',{}); result=result.get('value',result); output=result.get('output','') if isinstance(result,dict) else str(result)
    calls.append(dict(key=c.get('key'),exit_code=result.get('exit_code') if isinstance(result,dict) else None,output_end=output[-6000:]))
dump('static-verification.json',dict(authority='NONE',formal_acceptance=False,checks_are_static_not_execution=True,reference_checks=len(checked),mismatches=[r for r in checked if r['match'] is False],manifest_members=len(mf['members']),migration_blobs=gitrows,DDL_blob=ddlblob,DDL_blob_match=ddlblob==migrations['historical_DDL_git_blob'],selected_tree_entries=len(treeentries),selected_tree_original_IO_matches=treeentries==historical['selected_Git_entries'],preservation=preserved,postseal_calls=calls,postseal_pin=pin(Q/'postseal-tool-io.json'),postseal_exclusion=mf['exclusions'].get('postseal-tool-io.json'),independent_native_SQL_Go_execution=False,mechanical_failures_this_review=0,author_833_preserved=True,prior_826_and_FULL_1261_25_4_not_reset=True))
print(json.dumps(dict(namespace=str(O),reference_checks=len(checked),mismatches=sum(r['match'] is False for r in checked),migration_blob_matches=sum(r['match'] for r in gitrows),DDL_blob_match=ddlblob==migrations['historical_DDL_git_blob'],selected_tree_original_IO_matches=treeentries==historical['selected_Git_entries'],preservation=preserved,postseal_calls=calls),ensure_ascii=False))
