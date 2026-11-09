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
assert sha(MP.read_bytes())=='b9e835d51d321193913f56a7a388745b94157e5ec5d82cbe479502040d443870'
M=read(MP);PACKAGE=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-attach-combined-c465d135-20261014');OLD=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-readlane-combined-91218bdd-20261012')
COMP=read(FORMAL/'composition.json');D=read(PACKAGE/'apps/desktop/resources/client-wire/descriptor.json');RAW=pathlib.Path(M['build']['raw_receipts']);checked={};errors=[]
def references(x):
 if isinstance(x,dict):
  if all(k in x for k in ('path','bytes','sha256')) and pathlib.Path(x['path']).is_absolute():
   p=pathlib.Path(x['path'])
   if str(p) not in checked:
    try:actual=record(p);checked[str(p)]={**actual,'expected_sha256':x['sha256'],'match':actual['sha256']==x['sha256'] and actual['bytes']==x['bytes']}
    except Exception as e:checked[str(p)]={'path':str(p),'error':str(e),'match':False}
   if not checked[str(p)]['match']:errors.append(str(p))
  for v in x.values():references(v)
 elif isinstance(x,list):
  for v in x:references(v)
references(M);references(D)
files=[]
for row in COMP['package_files']:
 actual=record(PACKAGE/row['path']);r={**row,'actual':actual,'matches_composition':actual['sha256']==row['sha256'] and actual['bytes']==row['bytes']}
 if row.get('source'):r['matches_build_or_source']=sha(pathlib.Path(row['source']).read_bytes())==actual['sha256']
 if row.get('component') in ['REBUILT_UI_EQUAL_OLD','REBUILT_REACT_EQUAL_OLD','PUBLIC_SOURCE_EQUAL_OLD'] or 'runtime/' in row['path']:
  r['matches_old']=sha((OLD/row['path']).read_bytes())==actual['sha256']
 if row['path'].startswith(('apps/desktop/main/','apps/desktop/preload/','internal/api/contracts/','migrations/','spec/')):r['matches_candidate_source']=sha((SOURCE/row['path']).read_bytes())==actual['sha256']
 files.append(r)
actual_members=sorted(p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*') if p.is_file());expected_members=sorted(r['path'] for r in files)
inputs=read(RAW/'inputs.before.json');after=read(RAW/'inputs.after.json');bound=sha(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode());input_bad=[]
for r in inputs:
 p=pathlib.Path(r['path']);a=record(p)
 if a['sha256']!=r['sha256'] or a['bytes']!=r['bytes']:input_bad.append({'expected':r,'actual':a})
archive=read(RAW/'compiler-work-archive.json');references(archive)
def git(cwd,*argv):return subprocess.check_output(['git','-C',str(cwd),*argv]).decode('utf8').strip()
source={'candidate_head':git(SOURCE,'rev-parse','HEAD'),'candidate_tree':git(SOURCE,'rev-parse','HEAD^{tree}'),'candidate_status':git(SOURCE,'status','--short'),'main_head':git(ROOT,'rev-parse','HEAD'),'main_tree':git(ROOT,'rev-parse','HEAD^{tree}'),'unchanged_UI_vs_old_source':git(SOURCE,'diff','--name-only','070e6cda24ec2fadca104873534febcedfb7ddc0','b955c8665281193d5cbf90a146f936c9212c7940','--','apps/desktop','apps/web','spec/v2.0/contracts','migrations','internal/api/contracts')}
for name,relative in [('control','apps/desktop/resources/control/researchos-control.exe'),('runtime-verifier','apps/desktop/resources/control/runtime-verifier.exe'),('validator','apps/desktop/resources/client-wire/researchos-client-wire-validator.exe')]:
 cmd=[str(ROOT/'.local/tools/go1.27.1/go/bin/go.exe'),'version','-m',str(PACKAGE/relative)];r=subprocess.run(cmd,capture_output=True);(EV/(name+'-version-m-attempt02.stdout.raw')).write_bytes(r.stdout);(EV/(name+'-version-m-attempt02.stderr.raw')).write_bytes(r.stderr);save(name+'-version-m-attempt02.process.json',{'argv':cmd,'cwd':str(EV),'exit':r.returncode,'binary':record(PACKAGE/relative)})
 text=r.stdout.decode('utf8');assert r.returncode==0 and 'vcs.revision=b955c8665281193d5cbf90a146f936c9212c7940' in text and 'vcs.modified=false' in text
 if name=='validator':assert bound in text
installer=read(PACKAGE/'apps/desktop/resources/control/runtime-verifier-installation.json');expected_verifier=(PACKAGE/'apps/desktop/resources/control/runtime-verifier.exe').resolve();assert pathlib.Path(installer['executable']).resolve()==expected_verifier and installer['source_commit']=='b955c8665281193d5cbf90a146f936c9212c7940' and installer['executable_hash']=='sha256:'+sha(expected_verifier.read_bytes())
check={'author_final_manifest':record(MP),'source':source,'referenced_files_checked':len(checked),'reference_mismatches':sorted(set(errors)),'reference_files':list(checked.values()),'package_members':len(actual_members),'member_sets_equal':actual_members==expected_members,'package_files':files,'input_count':len(inputs),'input_digest':bound,'descriptor_digest_equal':bound==D['build_input_digest']==COMP['bound_full_input_digest'],'input_drift':input_bad,'before_after_manifest_consistent':all(r['sha256']==r['current_sha256'] for r in after) and [{k:r[k] for k in ['path','sha256','bytes']} for r in after]==inputs,'descriptor_binary_hash_equal':D['binary_sha256']==sha((PACKAGE/'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe').read_bytes()),'descriptor_module_count':len(D['exact_module_source_inventory']),'descriptor_react_count':len(D['compiled_React_asset_inventory']),'installer':installer}
save('package-audit.json',check)
assert not errors and len(actual_members)==58 and actual_members==expected_members and not input_bad and check['descriptor_digest_equal'] and check['before_after_manifest_consistent']
assert all(all(v for k,v in r.items() if k.startswith('matches_')) for r in files)
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
print(json.dumps({'members':len(actual_members),'input_count':len(inputs),'input_digest':bound,'references_checked':len(checked),'mismatches':errors,'boundary_cases':len(results),'all_boundary_pass':all(r['passes'] for r in results),'source':source},ensure_ascii=True))

