import json,os,shutil
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=Path(__file__).parent
names=['owned-core-stop-effect-state-r5-20261015-tmp','online-backup-fixture-qualification-20261015-tmp','qualification-failure-b-r2-20261015-tmp']
def size(p):
 total=0;count=0;skips=[];stack=[p]
 while stack:
  q=stack.pop()
  try:
   for e in os.scandir(q):
    if e.is_symlink():skips.append(e.path);continue
    if e.is_dir(follow_symlinks=False):
     st=e.stat(follow_symlinks=False)
     if getattr(st,'st_file_attributes',0)&0x400:skips.append(e.path);continue
     stack.append(Path(e.path))
    elif e.is_file(follow_symlinks=False):total+=e.stat(follow_symlinks=False).st_size;count+=1
  except OSError as ex:skips.append({'path':str(q),'error':str(ex)})
 return {'bytes':total,'file_count':count,'skipped':skips}
out={'drives':{d:dict(zip(['total','used','free'],shutil.disk_usage(d)))for d in ['C:/','D:/']},'candidates':[],'authority':'READONLY_TASK_OWNED_METADATA_NO_DELETE_NO_ORIGINAL_ROOT'}
for name in names:
 p=R/'.local'/name
 if not p.exists():out['candidates'].append({'path':str(p),'exists':False});continue
 v={'path':str(p),'exists':True,'children':[]}
 for c in sorted(p.iterdir()):
  if c.is_dir()and not c.is_symlink():v['children'].append({'name':c.name,'resolved':str(c.resolve()),**size(c)})
  elif c.is_file():v['children'].append({'name':c.name,'bytes':c.stat().st_size,'file_count':1})
 out['candidates'].append(v)
p=B/'completed-task-cache-intake-cp522.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(out,ensure_ascii=False))
