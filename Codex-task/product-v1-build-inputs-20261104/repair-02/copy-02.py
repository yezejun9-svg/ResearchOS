"""Fresh node_modules basename copy. Does not install or build Desktop."""
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
SOURCE=Path('D:/作品集/ResearchOS/research-os/apps/web/node_modules')
TARGET=Path('D:/作品集/ResearchOS/research-os/.local/product-v1-build-inputs-20261104/web-node_modules-02')
MODULES=TARGET/'node_modules'
OLD=TARGET.parent/'web-node_modules'
LIB=HERE.parent/'copy_public_web.py'
assert hashlib.sha256(LIB.read_bytes()).hexdigest()=='71d671c387dd82b4b1982c1c45f6f77645249ff9872d6aef82208b833bc941c0'
spec=importlib.util.spec_from_file_location('_readonly_copy_helpers',LIB)
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
save,tree,digest,canonical=lib.save,lib.tree,lib.digest,lib.canonical
phase='not-started'
def journal(event,**values):
    with (HERE/'JOURNAL.jsonl').open('ab') as f:
        f.write(canonical({'at':datetime.now(timezone.utc).isoformat(),'event':event,**values}));f.flush();os.fsync(f.fileno())
def main():
    global phase
    scope=json.loads((HERE/'SCOPE.json').read_bytes())
    first=json.loads((HERE/'JOURNAL.jsonl').read_bytes().splitlines()[0])
    assert first['scope_sha256']==digest(HERE/'SCOPE.json') and first['copy_script_sha256']==digest(Path(__file__))
    if (HERE/'COPY-CONSUMED.json').exists():raise RuntimeError('Consumed: no replay')
    save(HERE/'COPY-CONSUMED.json',{'scope_sha256':digest(HERE/'SCOPE.json'),'status':'CONSUMED_BEFORE_D_MKDIR'})
    graph=json.loads((HERE/'SOURCE.resolution-02.json').read_bytes())
    assert graph['phase']=='original-source' and graph['package_code_executed'] is False
    # Actual Node resolution found all18 in the existing public subtree. Do
    # not expand this diagnosis into copying an unrelated hoisted cache.
    for pkg in graph['nodes']:
        root=Path(pkg['source_root']);assert root.is_relative_to(SOURCE)
        assert digest(root/'package.json')==pkg['package_sha256']
    phase='preflight';lib.ancestors(TARGET.parent)
    if TARGET.exists():raise FileExistsError('New target must not exist')
    meta=tree(SOURCE,False);before_free=shutil.disk_usage(TARGET.parent).free
    required=meta['logical_bytes']+meta['file_count']*scope['slack_per_file_bytes']+scope['space_margin_bytes']
    save(HERE/'SPACE.before.json',{'free_bytes':before_free,'files':meta['file_count'],'logical_bytes':meta['logical_bytes'],'required_bytes':required})
    if before_free<required:raise OSError('Insufficient space; no cleanup allowed')
    before=tree(SOURCE,True);old_before=tree(OLD,True)
    assert digest(TARGET.parent/'INPUTS.json')=='87856127688f28e6d3b3cb24addbefbb1b6bfb3630690be8b76085d16113ddff'
    save(HERE/'SOURCE.before.json',before);save(HERE/'OLD01.before.json',old_before)
    journal('preflight-complete-before-D-mkdir',files=before['file_count'],bytes=before['logical_bytes'],free_bytes=before_free,
        required_bytes=required,resolution_sha256=digest(HERE/'SOURCE.resolution-02.json'))
    print(json.dumps({'stage':'PREFLIGHT_OK_NO_D_WRITE','files':before['file_count'],'bytes':before['logical_bytes']}),flush=True)
    phase='copy';TARGET.mkdir();MODULES.mkdir()
    for rel in before['directories']:(MODULES/rel).mkdir(parents=True,exist_ok=True)
    for i,row in enumerate(before['files'],1):
        source=SOURCE/row['path'];target=MODULES/row['path'];lib.check(source)
        assert target.absolute().is_relative_to(MODULES.absolute()) and not target.exists()
        with source.open('rb') as a,target.open('xb') as b:shutil.copyfileobj(a,b,1024*1024)
        if digest(target)!=row['sha256'] or target.stat().st_size!=row['bytes']:raise RuntimeError('Target mismatch '+row['path'])
        if i%250==0:journal('copy-progress',files=i)
    phase='readback';after=tree(SOURCE,True);readback=tree(MODULES,True);old_after=tree(OLD,True)
    save(HERE/'SOURCE.after.json',after);save(HERE/'TARGET.readback.json',readback);save(HERE/'OLD01.after.json',old_after)
    if before!=after or before!=readback or old_before!=old_after:raise RuntimeError('Source/target/old01 drift')
    assert digest(TARGET.parent/'INPUTS.json')=='87856127688f28e6d3b3cb24addbefbb1b6bfb3630690be8b76085d16113ddff'
    result={'status':'PHYSICAL_COPY_VERIFIED_AWAITING_MINIMAL_IMPORT_BUILD_CHECK','origin':scope['origin'],
        'target_root':str(TARGET),'web_modules':str(MODULES),'files':before['file_count'],'logical_bytes':before['logical_bytes'],
        'directories':len(before['directories']),'tree_sha256':digest(HERE/'SOURCE.before.json'),
        'source_after_sha256':digest(HERE/'SOURCE.after.json'),'target_readback_sha256':digest(HERE/'TARGET.readback.json'),
        'old01_unchanged':True,'old01_tree_sha256':digest(HERE/'OLD01.before.json'),
        'old01_inputs_sha256':digest(TARGET.parent/'INPUTS.json'),'D_free_before':before_free,'D_free_after':shutil.disk_usage(TARGET).free,
        'required_bytes':required,'reparse_count':0,'additional_hoisted_packages_copied':0,'installs':0,'D_Desktop_builds':0,'GUI_or_model_calls':0}
    save(HERE/'COPY-RESULT.json',result);journal('copy-complete',copy_result_sha256=digest(HERE/'COPY-RESULT.json'))
    print(json.dumps(result),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as e:
        failure={'status':'RESOURCE_REPAIR_COPY_BLOCKED','phase':phase,'type':type(e).__name__,'reason':str(e),
            'errno':getattr(e,'errno',None),'winerror':getattr(e,'winerror',None),'partial_target_retained':TARGET.exists(),'automatic_retry':False}
        if not (HERE/'COPY-FAILURE.json').exists():save(HERE/'COPY-FAILURE.json',failure)
        journal('copy-failure',**failure);print(json.dumps(failure),flush=True);raise SystemExit(1)
