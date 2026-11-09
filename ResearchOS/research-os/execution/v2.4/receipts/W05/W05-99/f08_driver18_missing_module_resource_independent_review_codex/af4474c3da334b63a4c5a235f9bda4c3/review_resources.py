import ast,base64,hashlib,json,os,re,stat,zipfile
from pathlib import Path,PurePosixPath
N=Path(__file__).parent
R=N.parent.parent
S=R/'f08_driver18_missing_module_resource_codex/062143fda9fb442fbdbc104f6d865833'
reads={};checks=[]
def check(ok,label):
    checks.append({'check':label,'pass':bool(ok)})
    if not ok:raise RuntimeError(label)
def ref(p,b):return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):
    p=Path(p);b=p.read_bytes();reads[str(p)]=ref(p,b);return b
def pin(p):return ref(Path(p),read(p))
def verify(r):
    b=read(r['path']);check(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'HASH '+r['path']);return b
def doc(p):return json.loads(read(p))
def save(n,v):
    with (N/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
checks0=[('handoff.json','20586c4c7bfa373f414399d64c9244d05e4b5cde003c970091f3bc576fa96f31'),('manifest.json','bd6623f754f7d426e0e0e71df40afff24096ea9031f494b42e4992f93c145cb1'),('acquire.tool-observation.json','5018939c74311de3030ded6ca651da3cc4580067373f2bf8ec41e6f344abca3a')]
for name,sha in checks0:check(pin(S/name)['sha256']==sha,'FIXED_INPUT '+name)
mf=doc(S/'manifest.json');members=mf['members'];check(len(members)==310,'MANIFEST_310')
for r in members:
    check(Path(r['path']).is_relative_to(S),'MANIFEST_BOUNDARY');verify(r)
expected={str(Path(r['path'])) for r in members}|{str(S/'manifest.json'),str(S/'acquire.tool-observation.json')}
actual={str(p) for p in S.rglob('*') if p.is_file()};check(actual==expected,'EXACT_MEMBERS_PLUS_EXPLICIT_SUPPLEMENT')
h=doc(S/'handoff.json');scope=doc(S/'scope.resource.json');ob=doc(S/'acquire.tool-observation.json')
for r in h['input_refs']:verify(r)
sumraw=verify(h['input_refs'][0]);check(h['input_refs'][0]['sha256']=='4b96232886b890be75080078e4638c9e139490a04c8eabe711dc5fbffe051c33','FROZEN_FORK_SUM');sums=sumraw.decode().splitlines()
source=read(S/'acquire-fixed-modules.once.py').decode();ast.parse(source)
check("headers={'User-Agent':'ResearchOS-fixed-public-module-resource/1','Accept-Encoding':'identity'}" in source,'FIXED_NO_KEY_HEADERS')
check('os.environ' not in source and 'getenv' not in source and 'urllib' not in source,'NO_ENV_CREDENTIAL_LOOKUP_OR_REDIRECT_CLIENT')
check("con.request('GET',path" in source and source.count("con.request('GET',path")==1,'ONE_STATIC_GET_CALL_SITE_TWO_MODULE_LOOP')
check(ob['original_tool_object']['exit_code']==0 and 'PythonNativeExit=0' in ob['original_tool_object']['output'],'ACTUAL_OUTER_AND_EXPLICIT_NATIVE_0')
check(h['public_GET_attempts']==2 and not h['failure_origin_refs'],'TWO_REPORTED_REQUESTS_NO_ORIGINS')
cache=Path('D:/作品集/ResearchOS/research-os/.local/gopath/pkg/mod');modules=[];deps=[]
for i,(label,descriptor) in enumerate(zip(['pprof','fileutil'],scope['modules'])):
    leaf=S/label;res=doc(leaf/'result.json');request=doc(leaf/'request.json');headers=doc(leaf/'response.headers.json');lock=doc(leaf/'module.file-lock.json');zrows=doc(leaf/'zip-members.verified.json')
    mod=descriptor['module'];ver=descriptor['version'];prefix=mod+'@'+ver+'/'
    check(res['HTTP_status']==headers['status']==200 and res['public_GET_attempts']==1,'HTTP200_SINGLE '+label)
    check(request['url']==descriptor['url'] and request['method']=='GET' and request['credentials']=='NONE' and request['redirects'] is False,'EXACT_PUBLIC_REQUEST '+label)
    check(not any(k.lower() in ['authorization','proxy-authorization','set-cookie'] for k,v in headers['headers']),'NO_AUTH_COOKIE_RESPONSE '+label)
    actual_rows=[];modecounts={};fold=set();nonregular=[]
    with zipfile.ZipFile(leaf/'response.body') as z:
        infos=z.infolist();check(len(infos)==res['zip_members']<=scope['members_limit'],'ZIP_COUNT '+label)
        for inf in infos:
            name=inf.filename;mode=inf.external_attr>>16;modecounts[str(mode)]=modecounts.get(str(mode),0)+1
            check(name.startswith(prefix) and not PurePosixPath(name).is_absolute(),'ZIP_PREFIX '+name)
            rel=name[len(prefix):];parts=rel.split('/')
            check(rel and not inf.is_dir() and not any(x in ['','.','..'] for x in parts) and not any(c in name for c in '\\:<>|?*\x00\r\n"'),'SAFE_PATH '+name)
            check(all(not x.endswith(('.', ' ')) and x.split('.')[0].upper() not in {'CON','PRN','AUX','NUL',*(f'COM{j}' for j in range(1,10)),*(f'LPT{j}' for j in range(1,10))} for x in parts),'WINDOWS_SAFE '+name)
            check(rel.casefold() not in fold,'CASEFOLD_UNIQUE '+name);fold.add(rel.casefold())
            check(not inf.flag_bits&1 and stat.S_IFMT(mode) in [0,stat.S_IFREG] and not stat.S_ISLNK(mode),'REGULAR_UNENCRYPTED '+name)
            check(inf.file_size<=scope['per_member_limit'],'MEMBER_CAP '+name)
            b=z.read(inf);check(len(b)==inf.file_size,'CRC_AND_BYTES '+name)
            dest=leaf/'module'/Path(*parts)
            check(dest.is_relative_to(leaf/'module') and dest.is_file() and not dest.is_symlink() and not getattr(dest.lstat(),'st_file_attributes',0)&0x400,'EXTRACTED_REGULAR '+name)
            check(read(dest)==b,'ZIP_EQUALS_EXTRACTED '+name)
            actual_rows.append({'relative_path':rel,'zip_name':name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
    check(actual_rows==zrows,'ZIP_ROWS_EXACT '+label)
    check({r['relative_path'] for r in actual_rows}=={p.relative_to(leaf/'module').as_posix() for p in (leaf/'module').rglob('*') if p.is_file()},'NO_EXTRACTED_EXTRAS '+label)
    check(lock['files']==[dict(r,**ref(leaf/'module'/Path(*PurePosixPath(r['relative_path']).parts),read(leaf/'module'/Path(*PurePosixPath(r['relative_path']).parts)))) for r in actual_rows],'LOCK_FULL_ROWS '+label)
    summary=b''.join((r['sha256']+'  '+r['zip_name']+'\n').encode() for r in sorted(actual_rows,key=lambda r:r['zip_name'].encode()))
    h1='h1:'+base64.b64encode(hashlib.sha256(summary).digest()).decode()
    check(h1==res['actual_h1']==res['expected_h1']==descriptor['expected_h1']==lock['h1'],'H1_ALL_EQUAL '+label)
    check(sums.count(mod+' '+ver+' '+h1)==1,'FROZEN_GOSUM_MODULE '+label)
    check(read(leaf/'module.ziphash')==h1.encode('ascii'),'ZIPHASH_EXACT_ASCII '+label)
    gm=read(leaf/'module/go.mod');modh='h1:'+base64.b64encode(hashlib.sha256((hashlib.sha256(gm).hexdigest()+'  go.mod\n').encode()).digest()).decode()
    check(sums.count(mod+' '+ver+'/go.mod '+modh)==1,'GOMOD_H1 '+label)
    check(sum(r['bytes'] for r in actual_rows)==res['expanded_bytes']<=scope['per_expanded_limit'],'EXPANDED_CAP '+label)
    licensefacts=[]
    for lr in res['license_refs']:
        lb=verify(lr);licensefacts.append({'ref':lr,'first_lines':lb.decode('utf8').splitlines()[:8]})
    for dm,dv in re.findall(r'^\s*([a-z0-9][^\s]+/[^\s]+|modernc\.org/[^\s]+)\s+(v[^\s]+)',gm.decode(),re.M):
        dp=cache/(dm+'@'+dv);metaroot=cache/'cache/download'/dm/'@v';metadata=[]
        for ext in ['.mod','.info','.ziphash']:
            p=metaroot/(dv+ext);metadata.append({'path':str(p),'exists':p.is_file(),'ref':pin(p) if p.is_file() else None})
        deps.append({'declared_by':mod,'module':dm,'version':dv,'source_path':str(dp),'source_exists':dp.is_dir(),'download_metadata':metadata,'actual_import_graph_required':None})
    cp=cache/(mod+'@'+ver)
    check(not cp.exists(),'ORIGINAL_MISSING_CACHE_STILL_ABSENT '+label)
    modules.append({'module':mod,'version':ver,'ZIP_ref':res['response_body_ref'],'source_lock_ref':res['source_lock_ref'],'source_root':lock['source_root'],'member_count':len(actual_rows),'expanded_bytes':res['expanded_bytes'],'h1':h1,'go_mod_h1':modh,'zip_mode_histogram':modecounts,'mode_limit':'Archive regular type proven; extraction creates Windows regular files. No claim Unix executable mode preserved or included in Go h1.','license_facts':licensefacts,'HTTP_evidence':{'status':200,'attempts':1,'redirect_handler_absent':True,'public_mirror':True},'authentication':'Matches pre-existing pinned fork go.sum; no independent sumdb signature/tree authentication.'})
oldfacts=doc(S/'inputs.before-after.json');check(not oldfacts['drift'] and oldfacts['before']==oldfacts['after'],'AUTHOR_FROZEN_INPUT_BEFORE_AFTER')
save('module-audit.json',modules);save('declared-dependency-offline-delta.json',deps)
before=list(reads.values());save('inputs.before.json',before)
after=[]
for r in before:
    b=Path(r['path']).read_bytes();n=ref(Path(r['path']),b);check(n==r,'AFTER_HASH '+r['path']);after.append(n)
save('inputs.after.json',after);save('checks.json',checks)
review={'schema':'researchos.driver18-missing-module-independent-resource-review.v1','reviewer':'codex:/root/command_queue_impl','resource_author':'codex:/root','independent_for_this_delivery':True,'disclosed_prior_authorship':'Reviewer authored prior driver18 source/controller and resource-map; this verdict reviews Root two-module acquisition only, not driver correctness or source acceptance.','decision':'RESOURCE_PREPARATION_VERIFIED_WITH_DECLARED_CLOSURE_OPEN','requested_changes':[],'modules':modules,'checks':len(checks),'failed_checks':0,'source_manifest_members':310,'explicit_nonmanifest_supplement_ref':pin(S/'acquire.tool-observation.json'),'source_manifest_ref':pin(S/'manifest.json'),'source_handoff_ref':pin(S/'handoff.json'),'dependency_delta_ref':pin(N/'declared-dependency-offline-delta.json'),'cache_protection_evidence':'Acquirer source writes only owned OUT; original two extracted module paths remain absent; author two fixed input before/after and independent current hashes match. Whole unrelated cache tree was not monitored, so no unsupported whole-cache immutability claim.','limitations':['Public mirror HTTP200 and checksum consistency with frozen go.sum, not independently verified sumdb signature/tree or upstream identity.','No actual Go module/package resolution/compile performed; pprof declares readline/demangle/xsys versions and actual package selection remains OPEN.','No driver18 runtime resource closure, Root gate/grant, I17 closure or source/adoption/formal acceptance granted.'],'actual_review_target_Go_SQL_network_helper_model':0,'new_failure_origins':[],'source_acceptance':False,'formal_increment':0}
save('review.json',review)
print(json.dumps({'review':pin(N/'review.json'),'checks':len(checks),'failed':0,'inputs':len(before),'module_files':[len(zrows) for zrows in [json.loads((S/'pprof/zip-members.verified.json').read_bytes()),json.loads((S/'fileutil/zip-members.verified.json').read_bytes())]],'new_origins':[]},ensure_ascii=False))
