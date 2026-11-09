import pathlib,json,hashlib,subprocess,datetime,base64,copy,os
EV=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/attach-desktop-package-review-20261014')
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os');SOURCE=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/attach-synchronous-completion-20261012')
FORMAL=ROOT/'execution/v2.4/receipts/W05/W05-99/approved_attach_combined_desktop_build_codex/20261014-current-chat';MP=FORMAL/'FINAL-manifest.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def save(name,x):
 with (EV/name).open('x',encoding='utf8') as f:json.dump(x,f,indent=2,ensure_ascii=True)
def record(p):
 p=pathlib.Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}

PACKAGE=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-attach-combined-c465d135-20261014')
bound='8b05bba2053fa3085a6243728b4997ff457951089f60f9817f77be4797a49d8a'
# Execute packaged validator only, against synthetic private packets; no Core server or real DB.
fixtures=read(SOURCE/'tests/contracts/fixtures/client_protocol_v2_fixtures.json')['fixtures'];catalog={r['name']:r['value'] for r in fixtures};request=copy.deepcopy(catalog['valid_request_session_attach']);request['writer_epoch']=None;request['payload']['request_write_owner']=True
response=copy.deepcopy(catalog['valid_response_session_attach']);response['result']['write_owner_acquired']=True
cases=[('attach-request',request,None,'VALID'),('attach-completed',request,response,'VALID')]
ack={k:v for k,v in response.items() if k!='result'};ack['status']='ACKNOWLEDGED';ack['result']={'accepted_at':'2026-10-01T10:00:00Z','operation_id':'synthetic-op','after_sequence':0,'related_resource_ref':None};cases.append(('attach-historical-ack',request,ack,'VALID'))
bad=copy.deepcopy(response);bad['command_id']='foreign-command';cases.append(('foreign-command',request,bad,'REFUSED'))
bad=copy.deepcopy(response);bad['revision']=0;cases.append(('zero-revision',request,bad,'REFUSED'))
results=[]
for name,req,res,expect in cases:
 rb=json.dumps(req,separators=(',',':')).encode();sb=json.dumps(res,separators=(',',':')).encode() if res else b''
 packet={'schema':'researchos.desktop.http-validation/1','phase':'RESPONSE' if res else 'REQUEST','nonce':'12345678-1234-1234-1234-123456789abc','http_status':200 if res else None,'request_raw_base64':base64.b64encode(rb).decode(),'response_raw_base64':base64.b64encode(sb).decode() if res else ''};pb=json.dumps(packet,separators=(',',':')).encode();exe=PACKAGE/'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'
 r=subprocess.run([str(exe)],input=pb,capture_output=True,cwd=EV,timeout=15);(EV/(name+'.stdin.raw')).write_bytes(pb);(EV/(name+'.stdout.raw')).write_bytes(r.stdout);(EV/(name+'.stderr.raw')).write_bytes(r.stderr);got=json.loads(r.stdout);result={'name':name,'argv':[str(exe)],'cwd':str(EV),'exit':r.returncode,'expected':expect,'actual':got,'input_sha256':sha(pb),'bound':got['build_input_digest']==bound,'passes':r.returncode==0 and got['outcome']==expect and got['build_input_digest']==bound};results.append(result)
save('validator-package-boundary.json',results);assert all(r['passes'] for r in results)

print(json.dumps({'boundary_count':len(results),'all_pass':all(r['passes'] for r in results)}))
