import pathlib,json,hashlib,subprocess,copy,base64
E=pathlib.Path(__file__).resolve().parent/'verified-boundary'
E.mkdir(exist_ok=False)
P=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-status-combined-5ddc0abb-20261014')
S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-status-repair-20261014')
read=lambda p:json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
sha=lambda raw:hashlib.sha256(raw).hexdigest()
D=read(P/'apps/desktop/resources/client-wire/descriptor.json');exe=P/'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'
assert sha(exe.read_bytes())==D['binary_sha256']=='74ad36a6a49588ff5fb42b9f9549115402bdbf1d710c15e90a4eadd324197fe9'
fixtures=read(S/'tests/contracts/fixtures/client_protocol_v2_fixtures.json')['fixtures'];catalog={r['name']:r['value'] for r in fixtures}
req=copy.deepcopy(catalog['valid_request_session_attach']);req['writer_epoch']=None;req['payload']['request_write_owner']=True
res=copy.deepcopy(catalog['valid_response_session_attach']);res['result']['write_owner_acquired']=True
cases=[('attach-request',req,None,'VALID',''),('attach-completed',req,res,'VALID','')]
ack={k:v for k,v in res.items() if k!='result'};ack['status']='ACKNOWLEDGED';ack['result']={'accepted_at':'2026-10-01T10:00:00Z','operation_id':'synthetic-op','after_sequence':0,'related_resource_ref':None};cases.append(('attach-historical-ack',req,ack,'VALID',''))
for name,key,val,reason in [('foreign-command','command_id','foreign-command','RESPONSE_IDENTITY'),('foreign-session','session_id','foreign-session','RESPONSE_IDENTITY'),('zero-revision','revision',0,'INVALID_RESPONSE_SCHEMA'),('foreign-protocol','protocol_version','other-protocol','INVALID_RESPONSE_SCHEMA')]:
 bad=copy.deepcopy(res);bad[key]=val;cases.append((name,req,bad,'REFUSED',reason))
def decode(v):
 assert isinstance(v,list) and v
 tag=v[0]
 if tag=='object':
  assert len(v)==2 and len({p[0] for p in v[1]})==len(v[1]);return {k:decode(x) for k,x in v[1]}
 if tag=='array':assert len(v)==2;return [decode(x) for x in v[1]]
 if tag=='string':assert len(v)==2 and type(v[1]) is str;return v[1]
 if tag=='bool':assert len(v)==2 and type(v[1]) is bool;return v[1]
 if tag=='null':assert len(v)==1;return None
 if tag=='integer':assert len(v)==3 and int(v[1])==int(v[2]);return int(v[2])
 raise AssertionError('Unexpected typed JSON value tag: '+repr(tag))
results=[]
for index,(name,request,response,expected,reason) in enumerate(cases):
 rb=json.dumps(request,ensure_ascii=False,separators=(',',':')).encode('utf8');sb=json.dumps(response,ensure_ascii=False,separators=(',',':')).encode('utf8') if response else b''
 nonce='12345678-1234-1234-1234-'+str(index).zfill(12)
 packet={'schema':'researchos.desktop.http-validation/1','phase':'RESPONSE' if response else 'REQUEST','nonce':nonce,'http_status':200 if response else None,'request_raw_base64':base64.b64encode(rb).decode(),'response_raw_base64':base64.b64encode(sb).decode() if response else ''}
 raw=json.dumps(packet,separators=(',',':')).encode('utf8');p=subprocess.run([str(exe)],input=raw,capture_output=True,cwd=E,timeout=15)
 for suffix,body in [('stdin.raw',raw),('stdout.raw',p.stdout),('stderr.raw',p.stderr)]:
  with (E/(name+'.'+suffix)).open('xb') as f:f.write(body)
 got=json.loads(p.stdout)
 checks={'native_exit_zero':p.returncode==0,'stderr_empty':p.stderr==b'','exact_reply_keys':set(got)=={'schema','phase','nonce','http_status','request_sha256','response_sha256','schema_sha256_pair','build_input_digest','outcome','reason','value'},'schema':got.get('schema')==packet['schema'],'phase':got.get('phase')==packet['phase'],'nonce':got.get('nonce')==nonce,'http_status':got.get('http_status')==packet['http_status'],'request_hash':got.get('request_sha256')==sha(rb),'response_hash':got.get('response_sha256')==sha(sb),'schema_pair':got.get('schema_sha256_pair')==D['schema_sha256_pair'],'build_binding':got.get('build_input_digest')==D['build_input_digest'],'expected_outcome':got.get('outcome')==expected,'expected_reason':got.get('reason')==reason,'typed_value':decode(got['value'])==response if expected=='VALID' and response else got['value'] is None}
 item={'name':name,'argv':[str(exe)],'cwd':str(E),'native_exit':p.returncode,'stdin_sha256':sha(raw),'stdout_sha256':sha(p.stdout),'stderr_sha256':sha(p.stderr),'checks':checks,'passed':all(checks.values()),'outcome':got['outcome'],'reason':got['reason']};results.append(item)
 with (E/(name+'.process.json')).open('x',encoding='utf8') as f:json.dump(item,f,indent=2)
 assert item['passed'],(name,checks,got)
assert sha(exe.read_bytes())==D['binary_sha256']
with (E/'validator-package-boundary.json').open('x',encoding='utf8') as f:json.dump({'source':'fresh packaged binary native execution with synthetic stdin only','cases':results,'all_passed':all(r['passed'] for r in results),'no_core_server_gui_api_model_or_db':True},f,indent=2)
print(json.dumps({'cases':len(results),'all_passed':True,'build_input_digest':D['build_input_digest']}))
