from pathlib import Path, PurePosixPath
import base64, datetime, hashlib, json, stat, time, traceback
import urllib.request, urllib.error, urllib.parse, zipfile

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
SOURCE = ROOT/'execution/v2.4/receipts/W05/W05-99/f08_sqlite_complete_fork_resource_codex/29646a104712459fb211fc6f80545bf0'
MAX_BODY = 256 * 1024 * 1024
TOTAL = 0
COUNT = 1  # Prior web.open .info tool attempt is conservatively charged.
RECORDS = []
INPUTS = []

def save(name, obj):
    raw = (json.dumps(obj, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    with (OUT/name).open('xb') as f:
        f.write(raw)

def pin(p):
    raw = p.read_bytes()
    return {'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def read_input(p):
    before = p.stat()
    raw = p.read_bytes()
    after = p.stat()
    if (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):
        raise ValueError('input changed during read: '+str(p))
    INPUTS.append({'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
    return raw

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

def fetch(url, label):
    global COUNT,TOTAL
    for hop in range(4):
        u = urllib.parse.urlsplit(url)
        if u.scheme!='https' or u.hostname not in ('proxy.golang.org','storage.googleapis.com') or u.username or u.password or u.fragment:
            raise ValueError('public HTTPS redirect outside exact allowlist')
        if COUNT>=8:
            raise ValueError('GET count exhausted')
        COUNT+=1
        name=label+'-request-'+str(COUNT)
        rec={'url':url,'method':'GET','credential_source':'NONE','environment_proxy_used':False,'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':None,'native_exit':None,'outer_exit':None,'body_bytes':0,'error':None}
        RECORDS.append(rec)
        save(name+'.request.json',dict(rec))
        start=time.monotonic(); response=None; status=None
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'ResearchOS-public-module-resource-audit/1','Accept-Encoding':'identity'})
            try:
                response=OPENER.open(req,timeout=180)
            except urllib.error.HTTPError as exc:
                response=exc
            status=response.status
            rec['status']=status
            rec['headers']=[[k,v] for k,v in response.headers.items()]
            body=OUT/(name+'.body')
            sha=hashlib.sha256()
            with body.open('xb') as f:
                while True:
                    remaining=180-(time.monotonic()-start)
                    if remaining<=0:
                        raise TimeoutError('per-request180s deadline')
                    sock=getattr(getattr(getattr(response,'fp',None),'raw',None),'_sock',None)
                    if sock is not None:
                        sock.settimeout(remaining)
                    if TOTAL>=MAX_BODY:
                        raise ValueError('cumulative response body cap reached; no further read')
                    block=response.read(min(65536,MAX_BODY-TOTAL))
                    if not block:
                        break
                    f.write(block);sha.update(block);TOTAL+=len(block);rec['body_bytes']+=len(block)
                    if TOTAL>MAX_BODY:
                        raise ValueError('cumulative response body cap exceeded')
            rec['body_ref']={'path':body.as_posix(),'sha256':sha.hexdigest(),'bytes':rec['body_bytes']}
            if status in (301,302,303,307,308):
                location=response.headers.get('Location')
                if not location:
                    raise ValueError('redirect lacks Location')
                url=urllib.parse.urljoin(url,location)
            elif status!=200:
                raise ValueError('HTTP status '+str(status)+'; branch stopped without retry')
            else:
                return body
        except BaseException as exc:
            rec['error']={'type':type(exc).__name__,'message':str(exc)}
            rec['traceback']=traceback.format_exc()
            partial=OUT/(name+'.body')
            if partial.exists():
                rec['body_ref']=pin(partial)
            raise
        finally:
            if response is not None:
                response.close()
            rec['elapsed_seconds']=time.monotonic()-start
            rec['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
            save(name+'.response.json',rec)
    raise ValueError('redirect bound exhausted')

result={'schema':'researchos.sqlite-upstream-zip-acquisition-audit.v1','actor':'codex:/root/command_queue_impl','status':'STARTED','product_execution':0,'source_adoption':False,'SQL24_permission':False,'actual_native_exit':None,'retry':False,'counter_reset':False,'sumdb_signature_or_tree_verification':False,'first_error':None}
try:
    before=json.loads(read_input(SOURCE/'module.before.json'))
    handoff=json.loads(read_input(SOURCE/'handoff.json'))
    expected={r['relative_path']:r for r in before['files']}
    if len(expected)!=1899:
        raise ValueError('original inventory count')
    body=fetch('https://proxy.golang.org/modernc.org/sqlite/@v/v1.60.1.zip','upstream-zip')
    result['zip_ref']=pin(body)
    rows=[];seen=set();names=set();prefix='modernc.org/sqlite@v1.60.1/'
    with zipfile.ZipFile(body,'r') as z:
        infos=z.infolist()
        if len(infos)!=1899 or sum(i.file_size for i in infos)!=150427576:
            raise ValueError('ZIP full member count or expanded size differs from frozen1899 inventory')
        for info in infos:
            n=info.filename;p=PurePosixPath(n)
            mode=info.external_attr>>16
            if n in seen or n.casefold() in names or not n.startswith(prefix) or p.is_absolute() or any(x in ('..','.','') for x in n.split('/')) or '\\' in n or ':' in n or '\n' in n or '\r' in n or info.is_dir() or stat.S_ISLNK(mode) or info.flag_bits&1:
                raise ValueError('unsafe/duplicate/non-file ZIP member: '+n)
            seen.add(n);names.add(n.casefold())
            rel=n[len(prefix):]
            if rel not in expected or info.file_size!=expected[rel]['bytes']:
                raise ValueError('ZIP member differs from original inventory: '+rel)
            h=hashlib.sha256();count=0
            with z.open(info,'r') as f:
                while True:
                    block=f.read(65536)
                    if not block:break
                    count+=len(block)
                    if count>expected[rel]['bytes']:raise ValueError('expanded member size exceeded')
                    h.update(block)
            actual=h.hexdigest()
            if count!=expected[rel]['bytes'] or actual!=expected[rel]['sha256']:
                raise ValueError('ZIP content does not match cached original: '+rel)
            cached=read_input(Path(expected[rel]['path']))
            if hashlib.sha256(cached).hexdigest()!=actual or len(cached)!=count:
                raise ValueError('current cached file changed: '+rel)
            rows.append({'relative_path':rel,'zip_name':n,'sha256':actual,'bytes':count})
    summary=''.join(r['sha256']+'  '+r['zip_name']+'\n' for r in sorted(rows,key=lambda r:r['zip_name'].encode('utf-8'))).encode('utf-8')
    archive_h1='h1:'+base64.b64encode(hashlib.sha256(summary).digest()).decode('ascii')
    if archive_h1!='h1:/blz53O951KWFOso4QQvEs/Fq6cDBKLtMVrYNSeJVKw=':
        raise ValueError('downloaded archive h1 mismatch')
    save('zip-members.json',rows)
    result['zip_h1']=archive_h1
    result['member_count']=len(rows)
    result['cached_file_content_comparison']='ALL1899_EXACT'
    mod=fetch('https://proxy.golang.org/modernc.org/sqlite/@v/v1.60.1.mod','upstream-mod')
    expected_mod=read_input(Path(handoff['source_module'])/'go.mod')
    if mod.read_bytes()!=expected_mod:
        raise ValueError('public .mod differs from frozen directory go.mod')
    result['public_mod_ref']=pin(mod)
    result['status']='PUBLIC_PROXY_ZIP_AND_MOD_MATCH_FROZEN_CONTENT'
except BaseException as exc:
    result['status']='RESOURCE_BRANCH_STOPPED_OPEN'
    result['first_error']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
finally:
    result['count_including_prior_web_attempt']=COUNT
    result['captured_response_body_bytes']=TOTAL
    result['requests']=RECORDS
    result['no_extraction_or_code_execution']=True
    result['info_tool_branch']='Earlier web.info inaccessible; HTTP status unknown; no retry'
    save('inputs.actual.json',INPUTS)
    save('audit.json',result)
    print(json.dumps({'status':result['status'],'first_error':result['first_error'],'requests':COUNT,'body_bytes':TOTAL},ensure_ascii=False))
