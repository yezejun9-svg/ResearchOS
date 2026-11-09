from pathlib import Path
import hashlib,json,os,subprocess,tarfile

here=Path(__file__).resolve().parent
root=Path('D:/作品集/ResearchOS/research-os')
git=Path('C:/Program Files/Git/cmd/git.exe')
base='29f92310a0bdefefbb7c020c792a3565f7b71504'
target=here/'base-source'
archive=here/'base-source.tar'
assert not target.exists() and not archive.exists(),'Inspect existing stage before retry'
assert hashlib.sha256(git.read_bytes()).hexdigest()=='da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f'
env=os.environ.copy();env['GIT_OPTIONAL_LOCKS']='0'
prefix=[str(git),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(root)]
metadata=subprocess.run(prefix+['ls-tree','-rl',base],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
(here/'base-ls-tree.stderr.raw').write_bytes(metadata.stderr)
assert metadata.returncode==0,'Git base metadata failed'
total=0;count=0
for line in metadata.stdout.splitlines():
    fields=line.split(b'\t',1)[0].split()
    if len(fields)==4 and fields[3]!=b'-':total+=int(fields[3]);count+=1
assert total<=512*1024*1024,'Tracked base exceeds owned C staging budget'
command=prefix+['archive','--format=tar','--output='+str(archive),base]
result=subprocess.run(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
(here/'base-archive.stdout.raw').write_bytes(result.stdout)
(here/'base-archive.stderr.raw').write_bytes(result.stderr)
assert result.returncode==0,'Git archive failed'
target.mkdir()
with tarfile.open(archive) as tf:tf.extractall(target,filter='data')
manifest={'base_head':base,'source_kind':'Git archive of fixed base commit, no history or user files','tracked_blob_count':count,'tracked_blob_bytes':total,'archive_bytes':archive.stat().st_size,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'git_command':command,'exit_code':result.returncode,'target':str(target),'network':False,'source_control_writes':False}
(here/'base-stage.json').write_text(json.dumps(manifest,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:manifest[k] for k in ['tracked_blob_count','tracked_blob_bytes','archive_bytes','archive_sha256','exit_code','target']}))
