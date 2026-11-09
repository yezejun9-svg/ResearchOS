import pathlib,json,hashlib,ast
N=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/finite_controller_preparation_revision_codex/b9b9b105f8e74cc4a7b39a0c059914b8')
O=pathlib.Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/finite_controller_v2_static_independent_review_codex/f4250aa50b74415a969b56fca0b177b4')
reads={};checks=[]
def ck(v,n):checks.append({'name':n,'passed':bool(v)})
def read(p):
 p=pathlib.Path(p);b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};ck(str(p) not in reads or reads[str(p)]==r,'stable:'+str(p));reads[str(p)]=r;return b
def verify(r):
 b=read(r['path']);ck(hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes'],'ref:'+r['path']);return b
def doc(p):return json.loads(read(p))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
h=doc(N/'handoff.complete.json');m=doc(N/'manifest.complete.json');s=doc(N/'spec.v2.sealed.json');cat=doc(N/'public-source-catalog.v2.json')
ck(reads[str(N/'handoff.complete.json')]['sha256']=='1bf5df0d4b6c3044c7fdd515a77a87ec5eec2dc0f9a60b499d2b6ab0ac636a49','handoff pin')
ck(reads[str(N/'manifest.complete.json')]['sha256']=='dc19a892766501143a9f340ad9038792a880adf5485e817ed01d91cd21fcf3e3','manifest pin')
ck(m['member_count']==len(m['members'])==77,'manifest77')
for r in m['members']:verify(r)
for k,r in h.items():
 if isinstance(r,dict) and {'path','sha256','bytes'}<=r.keys():verify(r)
for r in h['old_refs']:verify(r)
for r in s['controller_refs']:
 b=verify(r);ast.parse(b);(O/('input.'+pathlib.Path(r['path']).name)).write_bytes(b)
ck(s['authorized'] is False and s['execution_authorized'] is False and s['status']=='PREPARATION_ONLY_NOT_RUN','unexecuted spec')
roster=s['roster'];ck(len(roster)==49,'49selectors');ck(sum(x['new'] for x in roster)==41,'41new');ck(sum(bool(x['requires_resource']) for x in roster)==4,'4resourcecases');ck(len({x['selector'] for x in roster})==49,'unique49');ck(all(x['execution']=='NOT_RUN' for x in roster),'allNOTRUN')
ck(sum(len(x['expected_records']['run_records']) for x in roster)==89,'expected89run');ck(sum(len(x['expected_records']['pass_records']) for x in roster)==89,'expected89pass')
blobs={}
for stem in ['git-public-blobs','git-control-blobs']:
 b=read(N/(stem+'.stdout.raw'));pos=0
 while pos<len(b):
  end=b.index(b'\n',pos);oid,kind,count=b[pos:end].decode('ascii').split();count=int(count);body=b[end+1:end+1+count];pos=end+1+count
  ck(kind=='blob' and len(body)==count and b[pos:pos+1]==b'\n','batch framing:'+oid);pos+=1
  ck(hashlib.sha1(b'blob '+str(count).encode()+b'\0'+body).hexdigest()==oid,'batch Gitblob:'+oid)
  ck(oid not in blobs or blobs[oid]==body,'duplicate object samebytes:'+oid);blobs[oid]=body
 ck(pos==len(b),'batch EOF:'+stem)
ck(cat['file_count']==len(cat['files'])==511,'catalog511')
for r in cat['files']:
 body=blobs.get(r['git_blob']);ck(body is not None,'catalog blobpresent:'+r['path'])
 if body is not None:ck(hashlib.sha256(body).hexdigest()==r['sha256'] and len(body)==r['bytes'],'catalogSHA:'+r['path'])
ck(len(cat['lexical_import_audit']['local_imports'])==21 and cat['lexical_import_audit']['missing_directories']==[],'lexical21noMissing')
ck(cat['actual_compilation_closure'] is None and cat['combined_Main_source_commit'] is None,'no false currentcompile')
# AST structure only; no target function import, exec, or call.
sealer=ast.parse(read(N/'seal_readonly.v2.sealed.py'))
f=next(x for x in sealer.body if isinstance(x,ast.FunctionDef) and x.name=='check_vector')
ck(not any(isinstance(x,ast.Name) and x.id in ['merged','addfiles','final','expected_revision'] for x in ast.walk(f)),'findingcheckvector notbound ledger')
callfacts=[]
for x in ast.walk(sealer):
 if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='check_vector':callfacts.append({'line':x.lineno,'argument_count':len(x.args),'source':ast.unparse(x)})
save('read-audit.json',{'checks':checks,'check_count':len(checks),'failed':[x for x in checks if not x['passed']],'inputs':list(reads.values()),'check_vector_calls':callfacts,'target_imports':0,'product_native_executions':0,'SQL_HTTP_Model_Dll':0,'catalog511bytehash_verified':True,'resource_catalog_runtime_unbound':True})
print(json.dumps({'checks':len(checks),'failed':sum(not x['passed'] for x in checks),'reads':len(reads),'vector_calls':callfacts},ensure_ascii=True))
