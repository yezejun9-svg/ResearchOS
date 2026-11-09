import datetime,hashlib,json,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
s=read(N/'continuation-cp533/C57-source-scope.json');sub=read(N/'continuation-cp538/C57-boot6-source-subscope.json');w=Path(s['worktree'])
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];g=lambda *a:subprocess.check_output(git+list(a),cwd=w)
head=g('rev-parse','HEAD').decode().strip();assert head==s['base_commit'];assert not g('diff','--cached','--name-only')
parts=lambda b:[]if not b else b.decode('utf8').strip(chr(0)).split(chr(0))
tracked=parts(g('diff','--name-only','-z'));untracked=parts(g('ls-files','--others','--exclude-standard','-z'))
outside=sorted((set(tracked)|set(untracked))-set(s['source_allowlist']));assert not outside,outside
protected=[]
for x in s['inherited43_other_paths_must_remain_exact']:
 a=ref(w/x['path']);assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];protected.append(a)
assert len(protected)==40
out={'schema':'researchos.C57-live-scope-preservation.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'MUTABLE_SCOPE_AND_INHERITED40_VERIFIED_NOT_ACCEPTANCE','base_commit':head,'tracked_changed_paths':tracked,'new_untracked_source_paths':untracked,'outside57_paths':outside,'protected40_refs':protected,'boot6_present':{p:(w/p).is_file()for p in sub['source_allowlist']},'scope_counts':{'parent51':51,'boot6':6,'total57':57},'candidate_frozen':False,'source_acceptance':False,'formal_increment':0}
with(N/'C57-live-scope-preservation-cp540.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':out['status'],'base_commit':head,'tracked_changed':len(tracked),'new_untracked':len(untracked),'outside57':len(outside),'inherited40_exact':len(protected),'boot6_present':sum(out['boot6_present'].values()),'formal_increment':0},ensure_ascii=False))
