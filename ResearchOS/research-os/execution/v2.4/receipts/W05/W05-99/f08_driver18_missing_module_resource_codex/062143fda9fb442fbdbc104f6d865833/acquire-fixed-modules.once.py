"""Root public resource lane: two fixed module ZIP GETs; no target execution."""
import base64, datetime, hashlib, http.client, json, ssl, stat, sys, time, traceback, zipfile
from pathlib import Path, PurePosixPath
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).absolute().parent
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
sys.dont_write_bytecode=True
SUM=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_sqlite_complete_fork_resource_codex/29646a104712459fb211fc6f80545bf0/module/modernc_sqlite_v1_60_1_researchos_innocuous/go.sum'
MAP=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_driver18_resource_map_codex/3c2dd502fd33432d8b1d91cfadc56564/handoff.json'
MODULES=[('pprof','github.com/google/pprof','v0.0.0-20260802141513-ef3492d7dac3','h1:LMLX+LgTNWpfvCBdFebv6EsYotImrt/Ppc5cXIriCSo='),
('fileutil','modernc.org/fileutil','v1.4.0','h1:j6ZzNTftVS054gi281TyLjHPp6CPHr2KCxEXjEbD6SM=')]
CAP=128*1024*1024
def pin(p):
    p=Path(p).absolute(); b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(p,v):
    with Path(p).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8'))
inputs=[pin(SUM),pin(MAP)]
assert inputs[0]['sha256']=='4b96232886b890be75080078e4638c9e139490a04c8eabe711dc5fbffe051c33'
assert inputs[1]['sha256']=='ab64a244ca3e2510f4587b051094cb42fa2b84125baf99e50a681f84b1e99a15'
sum_lines=SUM.read_text(encoding='utf8').splitlines()
assert [(x['module'],x['version']) for x in json.loads(MAP.read_bytes())['missing']]==[(m,v) for _,m,v,_ in MODULES]
for _,m,v,h in MODULES:assert sum_lines.count(m+' '+v+' '+h)==1
save(OUT/'scope.resource.json',{'schema':'researchos.root-fixed-public-module-acquisition-scope.v1','actor':'codex:/root',
'modules':[{'module':m,'version':v,'expected_h1':h,'url':'https://goproxy.cn/'+m+'/@v/'+v+'.zip'} for _,m,v,h in MODULES],
'public_GET_limit':2,'per_body_limit':CAP,'per_expanded_limit':CAP,'members_limit':10000,'per_member_limit':32*1024*1024,
'per_request_deadline_seconds':120,'route':'http://127.0.0.1:57777','redirects_allowed':False,
'retry':False,'credential_source':'NONE','SDK_Model_external_paid':0,'target_helper_Go_SQL_calls':0,
'canonical_writes':0,'old_cache_writes':0,'source_adoption':False,'sumdb_signature_verification':False,
'input_refs':inputs,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
reports=[]; failures=[]
for label,mod,ver,expected in MODULES:
    leaf=OUT/label; leaf.mkdir()
    con=None; response=None
    r={'module':mod,'version':ver,'expected_h1':expected,'HTTP_status':None,'public_GET_attempts':0,
       'status':'STARTED','body_bytes':0,'first_cause':None,'actual_stage_native_exit':None,'retry':False,
       'source_adoption':False,'target_execution':0,'sumdb_signature_verification':False}
    start=time.monotonic()
    try:
        path='/'+mod+'/@v/'+ver+'.zip'
        save(leaf/'request.json',{'method':'GET','url':'https://goproxy.cn'+path,'route':'http://127.0.0.1:57777',
           'credentials':'NONE','redirects':False,'timeout_seconds':120,'body_cap':CAP})
        con=http.client.HTTPSConnection('127.0.0.1',57777,timeout=30,context=ssl.create_default_context())
        con.set_tunnel('goproxy.cn',443); con.connect()
        def remaining():
            seconds=120-(time.monotonic()-start)
            if seconds<=0:raise TimeoutError('RESOURCE_REQUEST_DEADLINE')
            con.sock.settimeout(seconds)
        remaining(); r['public_GET_attempts']=1
        con.request('GET',path,headers={'User-Agent':'ResearchOS-fixed-public-module-resource/1','Accept-Encoding':'identity'})
        remaining(); response=con.getresponse(); r['HTTP_status']=response.status
        save(leaf/'response.headers.json',{'status':response.status,'reason':response.reason,'headers':[list(x) for x in response.getheaders()]})
        length=response.getheader('Content-Length')
        if length is not None and int(length)>CAP:raise ValueError('RESOURCE_CONTENT_LENGTH_CAP')
        body=leaf/'response.body'
        with body.open('xb') as f:
            while True:
                remaining()
                if r['body_bytes']>=CAP:raise ValueError('RESOURCE_BODY_CAP')
                b=response.read(min(65536,CAP-r['body_bytes']))
                if not b:break
                f.write(b); r['body_bytes']+=len(b)
        response.close(); response=None; con.close(); con=None
        if r['HTTP_status']!=200:raise ValueError('RESOURCE_HTTP_STATUS_'+str(r['HTTP_status']))
        prefix=mod+'@'+ver+'/'; rows=[]; seen=set()
        with zipfile.ZipFile(body) as archive:
            infos=archive.infolist()
            if not infos or len(infos)>10000 or sum(i.file_size for i in infos)>CAP:raise ValueError('RESOURCE_ZIP_LIMIT')
            for i in infos:
                n=i.filename; parts=n.split('/'); mode=i.external_attr>>16
                if not n.startswith(prefix) or PurePosixPath(n).is_absolute() or any(x in ('','.','..') for x in parts) or any(c in n for c in '\\:<>|?*\x00\r\n"') or i.is_dir() or stat.S_ISLNK(mode) or i.flag_bits&1 or i.file_size>32*1024*1024:
                    raise ValueError('UNSAFE_MODULE_MEMBER '+n)
                rp=n[len(prefix):]
                if not rp or rp.casefold() in seen or any(p.endswith(('.', ' ')) for p in rp.split('/')):raise ValueError('MODULE_MEMBER_COLLISION_OR_WINDOWS_PATH '+rp)
                seen.add(rp.casefold())
                b=archive.read(i)
                if len(b)!=i.file_size:raise ValueError('RESOURCE_MEMBER_LENGTH')
                rows.append({'relative_path':rp,'zip_name':n,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
            summary=''.join(x['sha256']+'  '+x['zip_name']+'\n' for x in sorted(rows,key=lambda x:x['zip_name'].encode('utf8'))).encode('utf8')
            actual='h1:'+base64.b64encode(hashlib.sha256(summary).digest()).decode('ascii')
            if actual!=expected:raise ValueError('MODULE_H1_MISMATCH '+actual)
            r['actual_h1']=actual; r['zip_members']=len(rows); r['expanded_bytes']=sum(x['bytes'] for x in rows)
            source=leaf/'module'; source.mkdir()
            locks=[]
            for row in rows:
                target=source/Path(*PurePosixPath(row['relative_path']).parts)
                if not target.absolute().is_relative_to(source.absolute()):raise ValueError('MODULE_EXTRACTION_BOUNDARY')
                target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('xb') as f:f.write(archive.read(row['zip_name']))
                actual_ref=pin(target)
                if (actual_ref['sha256'],actual_ref['bytes'])!=(row['sha256'],row['bytes']):raise ValueError('EXTRACTED_MEMBER_PIN')
                locks.append(dict(row,**actual_ref))
        save(leaf/'zip-members.verified.json',rows)
        save(leaf/'module.file-lock.json',{'module':mod,'version':ver,'source_root':str(source),'files':locks,'h1':actual})
        with (leaf/'module.ziphash').open('xb') as f:f.write(actual.encode('ascii'))
        r['source_lock_ref']=pin(leaf/'module.file-lock.json');r['ziphash_ref']=pin(leaf/'module.ziphash')
        r['license_refs']=[pin(source/Path(*PurePosixPath(x['relative_path']).parts)) for x in rows if PurePosixPath(x['relative_path']).name.upper().startswith(('LICENSE','COPYING','NOTICE'))]
        r['status']='PUBLIC_MODULE_BYTES_MATCH_FROZEN_GO_SUM'
    except BaseException as e:
        r['status']='RESOURCE_BRANCH_OPEN'
        r['first_cause']={'stage':'PUBLIC_FIXED_MODULE_RESOURCE','error':repr(e),'traceback':traceback.format_exc(),
                         'actual_stage_native_exit':None,'automatic_retry':False,'counter_reset':False}
        save(leaf/'failure.origin.json',r['first_cause']); failures.append(pin(leaf/'failure.origin.json'))
    finally:
        if response is not None:response.close()
        if con is not None:con.close()
        if (leaf/'response.body').is_file():r['response_body_ref']=pin(leaf/'response.body')
        r['elapsed_seconds']=time.monotonic()-start
        save(leaf/'result.json',r); reports.append(pin(leaf/'result.json'))
drift=[a for a in inputs if pin(a['path'])!=a]
save(OUT/'inputs.before-after.json',{'before':inputs,'after':[pin(a['path']) for a in inputs],'drift':drift})
if drift:raise RuntimeError('FROZEN_INPUT_DRIFT')
save(OUT/'handoff.json',{'schema':'researchos.root-fixed-module-resource-handoff.v1','actor':'codex:/root','reports':reports,
'failure_origin_refs':failures,'input_refs':inputs,'public_GET_attempts':sum(json.loads(Path(r['path']).read_bytes())['public_GET_attempts'] for r in reports),
'status':'RESOURCES_PREPARED_PENDING_NONAUTHOR_REVIEW' if not failures else 'RESOURCE_BRANCHES_REPORTED_WITH_OPEN_FAILURES',
'formal_increment':0,'canonical_writes':0,'old_cache_writes':0,'source_adoption':False,'target_execution':0,'retry':False})
save(OUT/'manifest.json',{'members':[pin(p) for p in sorted(OUT.rglob('*')) if p.is_file()],'self_excluded':True})
print(json.dumps({'handoff_ref':pin(OUT/'handoff.json'),'manifest_ref':pin(OUT/'manifest.json'),'failures':failures},ensure_ascii=False))
sys.exit(1 if failures else 0)
