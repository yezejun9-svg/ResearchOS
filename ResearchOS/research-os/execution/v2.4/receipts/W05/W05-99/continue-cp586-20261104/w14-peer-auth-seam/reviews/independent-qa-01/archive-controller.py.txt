from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parent
RUN=ROOT/'run-01'
MAIN=Path('D:/作品集/ResearchOS/research-os')
CANDIDATE=MAIN/'.local/worktrees/w14-peer-auth-seam-20261104'
RECEIPT=MAIN/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/w14-peer-auth-seam'
ARCHIVE=RECEIPT/'reviews/independent-qa-01'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
result=json.loads((RUN/'result.json').read_bytes())
assert result['status']=='PRECONDITION_SEAM_QA_PASSED_NOT_HANDOFF_ACCEPTANCE'
assert result['frozen_source_unchanged'] and all(r['exit_code']==0 and r['source_unchanged'] for r in result['results'])
manifest=RECEIPT/'author/source-manifest.json'
assert sha(manifest)=='2628e7d22108bc481d0efd1a1f40de5f7da82a3b4614cb67b3fef5b79390c6c7'
assert all(sha(CANDIDATE/name)==digest for name,digest in result['source_sha256'].items())
ARCHIVE.mkdir(parents=True,exist_ok=False)
inventory={}
for base,prefix in ((RUN,Path()),(ROOT/'harness-attempt-01',Path('harness-attempt-01'))):
 for path in sorted(base.rglob('*')):
  relative=path.relative_to(base)
  if not path.is_file() or 'private' in relative.parts:continue
  target=ARCHIVE/prefix/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
  assert sha(path)==sha(target)
  inventory[str(prefix/relative).replace('\\','/')]={'sha256':sha(target),'bytes':target.stat().st_size}
tools=json.loads((MAIN/'execution/toolchains/locked.json').read_bytes())['tools']
git=tools['git']['path'];assert sha(git)==tools['git']['sha256']
env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
git_results={}
for name,args in [('head',['rev-parse','HEAD']),('status',['status','--porcelain=v1','--untracked-files=all']),('index',['diff','--cached','--name-only'])]:
 argv=[git,'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(CANDIDATE)]+args
 proc=subprocess.run(argv,capture_output=True,env=env,timeout=30)
 (ARCHIVE/('git-'+name+'.stdout.raw')).write_bytes(proc.stdout)
 (ARCHIVE/('git-'+name+'.stderr.raw')).write_bytes(proc.stderr)
 git_results[name]={'argv':argv,'exit_code':proc.returncode}
 assert proc.returncode==0
 if name=='head':assert proc.stdout.decode('ascii').strip()=='ebc340ef35cfdbf4449642ed559a05e5cdbaaee6'
 if name=='index':assert not proc.stdout.strip()
 if name=='status':
  lines=proc.stdout.decode('utf-8').splitlines()
  # Keep status-leading spaces; stripping them previously corrupted metadata.
  assert {line[3:] for line in lines}==set(result['source_sha256'])
  assert all(line[:2] in (' M','??') for line in lines)
  git_results['raw_status_lines']=lines
record={'status':'RAW_SOURCE_INPUT_RESULT_EVIDENCE_ARCHIVED_BEFORE_CACHE_CLEANUP','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':str(ARCHIVE),'source_manifest_sha256':sha(manifest),'source_sha256':result['source_sha256'],'independent_results':result['results'],'git_readback':git_results,'files':inventory,'module_inputs_and_buildcache_not_archived_or_deleted_here':True,'disk_before_cleanup':shutil.disk_usage(ROOT)._asdict(),'formal_increment':0}
target=ARCHIVE/'archive-manifest.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(record,stream,indent=2,ensure_ascii=False);stream.write('\n')
shutil.copyfile(Path(__file__),ARCHIVE/'archive-controller.py.txt')
print(json.dumps({'manifest':str(target),'sha256':sha(target),'status':record['status']},ensure_ascii=False))
