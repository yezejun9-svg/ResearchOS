from pathlib import Path
import hashlib,json,subprocess
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent;E=N.parent.parent
P=E/'qualification_maintenance_c57_codex/20261025-current-chat'
V=E/'qualification_maintenance_c57_independent_review_codex/20261025-current-chat'
B=E/'qualification_recovery_boundary_boot6_codex/20261025-current-chat'
W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
verified={}
def verify(base,x):
 p=Path(x.get('path',x.get('name',x.get('file',''))));assert str(p)!='.'
 p=p if p.is_absolute() else base/p;a=ref(p)
 assert a['sha256']==x['sha256'],str(p)
 if 'bytes'in x:assert a['bytes']==x['bytes'],str(p)
 verified[a['path']]=a;return a
def seal(base,name,sha,key,count):
 verify(base,{'path':name,'sha256':sha});d=read(base/name);assert len(d[key])==count
 for x in d[key]:verify(base,x)
 return d
reviews=[]
for name,sha,count in [
 ('PHASE1-parent51-static-review-seal.json','89ce92686cc716ca2bd0d1d867e341bad85b9a4a3992d3d3961a6ba272ee9fbb',117),
 ('PHASE1-parent51-nine-table-addendum-seal.json','ca6c8a439fdadbdfc4a2d3c5f156b1498824efa523fed361832acc014c04e76b',36),
 ('PHASE1-parent51-r2-targeted-review-seal.json','96d404ee96d31d6e9ea5bef4848bb64f4c40996d7ec674c82efde1ce113ca0f5',47)]:
 d=seal(V,name,sha,'files',count);assert not d['candidate_tests_run'];reviews.append({'seal':ref(V/name),'status':d['status'],'refs':count})
history=seal(B,'historical-v7-v9-additive-seal.json','621d129b9e93b6d0f1c4a18e58b497e7e4a63adb785c46c400d29ccb484b8b84','files',136)
v10=seal(B,'final-v10-additive-seal.json','c34640058479fd5ed1ac7532037d2f0eb9a7ee9f2b4910ee6f923bbb1b9755fe','evidence',28)
index=read(B/'historical-v7-v9-capture-index.json');events=[]
assert len(index['captures'])==33
for c in index['captures']:
 for x in c['originals'].values():verify(B,x)
 x=c['originals']['native_exit'];native=int((B/x['file']).read_text(encoding='utf-8-sig').strip());assert native==c['native_exit']
 if native or c['category']!='EXIT0_PASS_OR_PROBE':events.append(c)
assert sum(c['native_exit']!=0 for c in index['captures'])==7
parent=[]
for rev,sha,inc in [
 ('R2','f76ac75feffbbe174c6268f505512a49447296953868f7d914889663c008525a','FINAL'),
 ('R3','73dd30e430f8c2114b05327df1f4ae28105468f3465c4bbf499c367207b32f5b','INCREMENT'),
 ('R4','fdb59f3f6385b77b97c58d9fe55d0abb5ed0b2115ffdfedd21f523a6176bdba2','INCREMENT')]:
 freeze=P/f'C51-{rev}-SOURCEFREEZE.json';verify(P,{'path':freeze.name,'sha256':sha});d=read(freeze);assert len(d['owned_files'])==51 and d['inherited_pin_count']==40
 q=P/f'C51-{rev}-{inc}.json';a=ref(q);verified[a['path']]=a;i=read(q)
 verify(P,{'path':f'C51-{rev}-DELTA.patch','sha256':i['delta_sha256'],'bytes':i['delta_bytes']})
 for x in i['test_receipts']:verify(P,x)
 parent.append({'revision':rev,'freeze':ref(freeze),'increment':ref(q),'changes':i['changed_paths'],'receipt_count':len(i['test_receipts'])})
current=read(P/'C51-R4-SOURCEFREEZE.json')
for x in current['owned_files']:verify(W,x)
scope=read(N/'continuation-cp533/C57-source-scope.json')
for x in scope['inherited43_other_paths_must_remain_exact']:verify(W,x)
native_receipts=[]
for q in sorted(P.glob('*.native-exit.txt')):
 name=q.name;number=int(name.removeprefix('combined-').split('-')[0]) if name.removeprefix('combined-').split('-')[0].isdigit() else -1
 if 55<=number<=78:
  stem=name.removesuffix('.native-exit.txt');parts=[]
  for suffix in ['.recipe.txt','.stdout.raw','.stderr.raw','.native-exit.txt']:
   z=P/(stem+suffix)
   if z.exists():a=ref(z);verified[a['path']]=a;parts.append(a)
  native_receipts.append({'id':stem,'native_exit':int(q.read_text(encoding='utf-8-sig').strip()),'refs':parts,'recipe_file_present':(P/(stem+'.recipe.txt')).exists()})
assert all(x['native_exit']==0 for x in native_receipts if x['id'].split('-')[0]in ['058','061','071','073','074','076'])
assert [x['id']for x in native_receipts if x['native_exit']!=0]==['070-domain-lease-isolate','075-linux-selective-build','combined-065-domain','combined-067-boot','combined-069-linux-build']
out={'schema':'researchos.c57-new-increments-root-verification.v1','reviews':reviews,'parent_revisions':parent,'current_parent51_exact':True,'inherited40_exact':True,'historical_boot_index':ref(B/'historical-v7-v9-capture-index.json'),'historical_boot_events':events,'historical_boot_gaps':index['unknown_capture_gaps'],'boot_v10_seal':ref(B/'final-v10-additive-seal.json'),'boot_v10_is_current':False,'parent_native_receipts':native_receipts,'verified_refs':list(verified.values()),'independent_candidate_acceptance':False,'formal_increment':0,'limits':['Historical R2/R3 source manifests are verified as historical evidence, not compared to mutable current bytes.','v10 author tests predate C inherited environment combined067 failure; v11 required.','Linux076 selected supported packages does not establish whole Linux product build.','Some author diagnostics have no separate recipe file; preserve reported capture boundaries.']}
with(N/'C57-new-increments-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'unique_refs':len(verified),'reviews':[x['refs']for x in reviews],'current_parent_files':51,'pins':40,'boot_history_captures':33,'boot_history_nonzero':7,'parent_native_commands':len(native_receipts),'parent_native_nonzero':5,'formal_increment':0},ensure_ascii=False))
