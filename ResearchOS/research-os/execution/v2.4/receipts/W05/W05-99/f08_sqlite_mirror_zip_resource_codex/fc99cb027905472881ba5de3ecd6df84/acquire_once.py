from pathlib import Path, PurePosixPath
import base64, datetime, hashlib, http.client, json, ssl, stat, time, traceback, zipfile

ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'execution/v2.4/receipts/W05/W05-99/f08_sqlite_complete_fork_resource_codex/29646a104712459fb211fc6f80545bf0'
URL='https://goproxy.cn/modernc.org/sqlite/@v/v1.60.1.zip'
CAP=128*1024*1024
INPUTS=[]

def save(n,d):
    with (OUT/n).open('xb') as f:
        f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))

def pinned(p):
    raw=p.read_bytes()
    return {'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def read(p):
    pre=p.stat();raw=p.read_bytes();post=p.stat()
    if (pre.st_ino,pre.st_size,pre.st_mtime_ns)!=(post.st_ino,post.st_size,post.st_mtime_ns):
        raise ValueError('source read changed: '+str(p))
    r={'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    INPUTS.append(r)
    return raw

result={'schema':'researchos.fixed-mirror-zip-acquisition.v1','actor':'codex:/root/command_queue_impl','url':URL,'route':'http://127.0.0.1:57777','route_implementation':'HTTPSConnection explicit CONNECT to public target; no environment proxy lookup or authentication headers','different_input_from_prior':'goproxy.cn mirror host and explicit existing localhost route replace proxy.golang.org direct route','public_GET_attempts':0,'HTTP_status':None,'headers':None,'body_bytes':0,'first_error':None,'status':'STARTED','native_exit':None,'retry':False,'sumdb_signature_verification':False,'source_adoption':False,'SQL24_permission':False,'target_execution':0}
connection=None;response=None;started=time.monotonic()
try:
    before_raw=read(SOURCE/'module.before.json')
    if hashlib.sha256(before_raw).hexdigest()!='65a5d09890f5462015f640d1a70f03c5dea38905c3dc6d40fca432f036f5e5fc':
        raise ValueError('original1899 inventory pin')
    original=json.loads(before_raw);expected={r['relative_path']:r for r in original['files']}
    if len(expected)!=1899:raise ValueError('original1899 cardinality')
    handoff=read(SOURCE/'handoff.json')
    if hashlib.sha256(handoff).hexdigest()!='1db1cedbb28d1615ff9d6125346eb1b2e4e767c3411168aab883ce2fa3d5e3fe':
        raise ValueError('source handoff pin')
    save('request.json',{'url':URL,'route':result['route'],'method':'GET','redirects_allowed':False,'public_GET_limit':1,'body_limit':CAP,'deadline_seconds':120,'credential_source':'NONE','environment_proxy':'NONE','request_headers':{'User-Agent':'ResearchOS-public-module-resource-audit/1','Accept-Encoding':'identity'},'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    started=time.monotonic()
    connection=http.client.HTTPSConnection('127.0.0.1',57777,timeout=30,context=ssl.create_default_context())
    connection.set_tunnel('goproxy.cn',443)
    connection.connect()
    def remaining():
        left=120-(time.monotonic()-started)
        if left<=0:raise TimeoutError('120s request deadline')
        connection.sock.settimeout(left)
    remaining()
    result['public_GET_attempts']=1
    connection.request('GET','/modernc.org/sqlite/@v/v1.60.1.zip',headers={'User-Agent':'ResearchOS-public-module-resource-audit/1','Accept-Encoding':'identity'})
    remaining();response=connection.getresponse()
    result['HTTP_status']=response.status
    result['headers']=[list(x) for x in response.getheaders()]
    save('response.headers.json',{'status':response.status,'reason':response.reason,'headers':result['headers']})
    length=response.getheader('Content-Length')
    if length is not None and int(length)>CAP:raise ValueError('Content-Length exceeds128MiB')
    body=OUT/'response.body';digest=hashlib.sha256()
    with body.open('xb') as f:
        while True:
            remaining()
            if result['body_bytes']>=CAP:raise ValueError('response cap reached; no extra read')
            chunk=response.read(min(65536,CAP-result['body_bytes']))
            if not chunk:break
            f.write(chunk);digest.update(chunk);result['body_bytes']+=len(chunk)
    result['response_body_ref']={'path':body.as_posix(),'sha256':digest.hexdigest(),'bytes':result['body_bytes']}
    result['request_elapsed_seconds']=time.monotonic()-started
    response.close();response=None;connection.close();connection=None
    if result['HTTP_status']!=200:
        raise ValueError('HTTP '+str(result['HTTP_status'])+'; no redirect/retry/bypass')
    rows=[];seen=set();prefix='modernc.org/sqlite@v1.60.1/'
    with zipfile.ZipFile(body) as z:
        infos=z.infolist()
        result['actual_zip_member_count']=len(infos)
        result['actual_zip_uncompressed_bytes']=sum(i.file_size for i in infos)
        if len(infos)!=1899 or sum(i.file_size for i in infos)!=150427576:
            raise ValueError('mirror ZIP cardinality/size differs from frozen original')
        for info in infos:
            n=info.filename;mode=info.external_attr>>16
            if not n.startswith(prefix) or PurePosixPath(n).is_absolute() or any(x in ('','.','..') for x in n.split('/')) or any(c in n for c in '\\\r\n:') or n.casefold() in seen or info.is_dir() or stat.S_ISLNK(mode) or info.flag_bits&1:
                raise ValueError('unsafe ZIP member: '+n)
            seen.add(n.casefold());rel=n[len(prefix):]
            if rel not in expected or info.file_size!=expected[rel]['bytes']:
                raise ValueError('ZIP member mismatch: '+rel)
            h=hashlib.sha256();size=0
            with z.open(info) as f:
                while True:
                    chunk=f.read(65536)
                    if not chunk:break
                    size+=len(chunk)
                    if size>expected[rel]['bytes']:raise ValueError('expanded member bound')
                    h.update(chunk)
            sha=h.hexdigest()
            if sha!=expected[rel]['sha256'] or size!=expected[rel]['bytes']:
                raise ValueError('ZIP bytes differ from original: '+rel)
            raw=read(Path(expected[rel]['path']))
            if hashlib.sha256(raw).hexdigest()!=sha or len(raw)!=size:
                raise ValueError('original cache drift: '+rel)
            rows.append({'relative_path':rel,'zip_name':n,'sha256':sha,'bytes':size})
    summary=''.join(r['sha256']+'  '+r['zip_name']+'\n' for r in sorted(rows,key=lambda r:r['zip_name'].encode('utf-8'))).encode('utf-8')
    h1='h1:'+base64.b64encode(hashlib.sha256(summary).digest()).decode('ascii')
    result['zip_h1']=h1
    if h1!='h1:/blz53O951KWFOso4QQvEs/Fq6cDBKLtMVrYNSeJVKw=':raise ValueError('zip h1 mismatch')
    save('zip-members.verified.json',rows)
    result['status']='PUBLIC_MIRROR_ZIP_MATCHES_FROZEN_ORIGINAL_NOT_UPSTREAM_AUTHENTICATION'
except BaseException as exc:
    result['status']='MIRROR_RESOURCE_BRANCH_STOPPED_OPEN'
    result['first_error']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
finally:
    if response is not None:response.close()
    if connection is not None:connection.close()
    if (OUT/'response.body').exists():result['response_body_ref']=pinned(OUT/'response.body')
    result.setdefault('request_elapsed_seconds',time.monotonic()-started)
    result['input_drift']=[]
    for r in INPUTS:
        if pinned(Path(r['path']))!=r:result['input_drift'].append(r['path'])
    if result['input_drift']:result['status']='MIRROR_RESOURCE_BRANCH_STOPPED_OPEN'
    save('inputs.before-after.json',{'files':INPUTS,'drift':result['input_drift']})
    save('audit.json',result)
    print(json.dumps({'status':result['status'],'HTTP_status':result['HTTP_status'],'body_bytes':result['body_bytes'],'first_error':result['first_error'],'public_GET_attempts':result['public_GET_attempts']},ensure_ascii=False))
