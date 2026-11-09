"""One-use physical public dependency copy. No install/build/model/GUI."""
from datetime import datetime,timezone
import hashlib,json,os,shutil,stat
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=Path('D:/作品集/ResearchOS/research-os/apps/web/node_modules')
TARGET=Path('D:/作品集/ResearchOS/research-os/.local/product-v1-build-inputs-20261104')
WEB=TARGET/'web-node_modules'
REPARSE=getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400)
phase='not-started'
def now():return datetime.now(timezone.utc).isoformat()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def canonical(v):return (json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
def save(p,v):
    with p.open('xb') as f:f.write(canonical(v));f.flush();os.fsync(f.fileno())
def journal(event,**values):
    row={'at':now(),'event':event,**values}
    with (HERE/'JOURNAL.jsonl').open('ab') as f:f.write(canonical(row));f.flush();os.fsync(f.fileno())
def check(p,directory=False):
    s=p.lstat()
    if p.is_symlink() or s.st_file_attributes&REPARSE:raise ValueError('reparse refused: '+str(p))
    if directory and not stat.S_ISDIR(s.st_mode):raise ValueError('directory required: '+str(p))
    if not directory and not stat.S_ISREG(s.st_mode):raise ValueError('regular file required: '+str(p))
    return s
def ancestors(p):
    for part in reversed([p,*p.parents]):check(part,True)
    if p.resolve()!=p.absolute():raise ValueError('resolved alias refused: '+str(p))
def tree(root,hashes):
    ancestors(root)
    dirs=[];files=[];pending=[root]
    while pending:
        current=pending.pop()
        with os.scandir(current) as entries:
            for entry in sorted(entries,key=lambda v:v.name):
                p=Path(entry.path);s=entry.stat(follow_symlinks=False)
                if entry.is_symlink() or s.st_file_attributes&REPARSE:raise ValueError('tree reparse refused: '+str(p))
                rel=p.relative_to(root).as_posix()
                if stat.S_ISDIR(s.st_mode):dirs.append(rel);pending.append(p)
                elif stat.S_ISREG(s.st_mode):
                    row={'path':rel,'bytes':s.st_size}
                    if hashes:row['sha256']=digest(p)
                    files.append(row)
                else:raise ValueError('nonregular tree entry: '+str(p))
    files.sort(key=lambda r:r['path']);dirs.sort()
    return {'directories':dirs,'files':files,'file_count':len(files),'logical_bytes':sum(r['bytes'] for r in files)}
def main():
    global phase
    scope=json.loads((HERE/'SCOPE.json').read_bytes())
    scope_pin=digest(HERE/'SCOPE.json')
    assert scope['source']==SOURCE.as_posix() and scope['target_root']==TARGET.as_posix()
    assert scope['target_web_relative']=='web-node_modules'
    if not (HERE/'JOURNAL.jsonl').is_file():raise RuntimeError('C scope journal must already exist')
    initial=json.loads((HERE/'JOURNAL.jsonl').read_bytes().splitlines()[0])
    if initial['event']!='scope-registered-before-D-mkdir' or initial['scope_sha256']!=scope_pin or initial['copy_script_sha256']!=digest(Path(__file__)):
        raise RuntimeError('C scope/script journal binding differs')
    if (HERE/'COPY-STARTED.json').exists():raise RuntimeError('Consumed copy: readback only, no replay')
    save(HERE/'COPY-STARTED.json',{'at':now(),'scope_sha256':scope_pin,'status':'CONSUMED_NO_D_DIRECTORY_YET'})
    journal('copy-started',scope_sha256=scope_pin)
    phase='preflight-paths'
    ancestors(TARGET.parent)
    if TARGET.exists():raise FileExistsError('Target already exists; never overwrite')
    phase='preflight-size-reparse'
    meta=tree(SOURCE,False)
    free_before=shutil.disk_usage(TARGET.parent).free
    required=meta['logical_bytes']+meta['file_count']*scope['allocation_slack_per_file_bytes']+scope['free_space_margin_bytes']
    save(HERE/'SPACE.before.json',{'at':now(),'free_bytes':free_before,'source_logical_bytes':meta['logical_bytes'],
        'source_files':meta['file_count'],'required_with_slack_and_margin':required,'adequate':free_before>=required})
    if free_before<required:raise OSError('Insufficient destination space; no user files cleaned')
    phase='hash-source-before'
    before=tree(SOURCE,True)
    assert before['logical_bytes']==meta['logical_bytes'] and before['file_count']==meta['file_count']
    before_pin=hashlib.sha256(canonical(before)).hexdigest()
    save(HERE/'SOURCE.before.json',before)
    journal('preflight-complete-before-D-mkdir',files=before['file_count'],logical_bytes=before['logical_bytes'],
        source_manifest_sha256=before_pin,free_bytes=free_before,required_bytes=required)
    print(json.dumps({'stage':'PREFLIGHT_OK_NO_D_WRITES_YET','files':before['file_count'],'bytes':before['logical_bytes'],'free_bytes':free_before}),flush=True)
    phase='mkdir-new-target'
    TARGET.mkdir();WEB.mkdir()
    for relative in before['directories']:
        p=WEB/relative
        assert p.absolute().is_relative_to(WEB.absolute())
        p.mkdir(parents=True,exist_ok=True)
    journal('fresh-target-created',target=str(TARGET))
    phase='physical-copy'
    for i,row in enumerate(before['files'],1):
        src=SOURCE/row['path'];dst=WEB/row['path']
        check(src)
        assert not dst.exists() and dst.absolute().is_relative_to(WEB.absolute())
        with src.open('rb') as source,dst.open('xb') as target:
            shutil.copyfileobj(source,target,1024*1024)
        if dst.stat().st_size!=row['bytes'] or digest(dst)!=row['sha256']:raise RuntimeError('Target per-file hash mismatch: '+row['path'])
        if i%250==0:
            journal('copy-progress',copied_files=i,total_files=before['file_count'])
            print(json.dumps({'stage':'COPY_PROGRESS','files':i,'total':before['file_count']}),flush=True)
    phase='hash-source-after-and-target'
    after=tree(SOURCE,True);target=tree(WEB,True)
    save(HERE/'SOURCE.after.json',after);save(HERE/'TARGET.readback.json',target)
    if after!=before or target!=before:raise RuntimeError('Source/target tree drift; retain branch blocked')
    free_after=shutil.disk_usage(TARGET).free
    result={'schema':'researchos.product-v1-public-build-inputs.v1','status':'WEB_MODULES_PHYSICALLY_COPIED_HASH_VERIFIED',
        'at':now(),'scope_sha256':scope_pin,'source':str(SOURCE),'target_root':str(TARGET),'web_modules':str(WEB),
        'files':before['file_count'],'directories':len(before['directories']),'logical_bytes':before['logical_bytes'],
        'source_before_sha256':before_pin,'source_after_sha256':hashlib.sha256(canonical(after)).hexdigest(),
        'target_readback_sha256':hashlib.sha256(canonical(target)).hexdigest(),'all3_equal':True,
        'source_opened_readonly':True,'physical_copy_only':True,'reparse_count':0,'old_cache_rename_delete_or_write':0,
        'D_free_before':free_before,'D_free_after':free_after,'required_bytes':required,
        'Electron_copied':False,'GOMODCACHE_copied':False,'builds':0,'GUI_or_model_calls':0,'installs':0,'formal_increment':0}
    phase='seal-inputs'
    save(HERE/'INPUTS.json',result);save(TARGET/'INPUTS.json',result)
    journal('copy-complete',inputs_sha256=digest(HERE/'INPUTS.json'),files=before['file_count'],free_bytes=free_after)
    print(json.dumps({'stage':'COPY_VERIFIED','inputs_sha256':digest(HERE/'INPUTS.json'),**result}),flush=True)

if __name__=='__main__':
    try:main()
    except BaseException as error:
        failure={'at':now(),'status':'COPY_BRANCH_BLOCKED_NO_RETRY','phase':phase,'type':type(error).__name__,
            'errno':getattr(error,'errno',None),'winerror':getattr(error,'winerror',None),'reason':str(error),
            'partial_new_target_retained':TARGET.exists(),'old_cache_writes':0,'automatic_retry':False}
        if not (HERE/'FAILURE.json').exists():save(HERE/'FAILURE.json',failure)
        journal('copy-failed',**failure)
        print(json.dumps(failure),flush=True)
        raise SystemExit(1)
