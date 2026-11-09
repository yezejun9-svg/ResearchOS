import pathlib,json,hashlib,subprocess,os,time,datetime
E=pathlib.Path(__file__).parent;R=pathlib.Path('D:/作品集/ResearchOS/research-os');S=R/'.local/worktrees/coding-profile-result-20261014';A=R/'execution/v2.4/receipts/W05/W05-99/coding_profile_result_source_codex/20261014-current-chat';C=R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp474/coding-profile-result-source-scope.json';N=pathlib.Path('C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe')
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def git(*a):return subprocess.check_output(['git','-C',str(S),*a])
assert sha(C.read_bytes())=='f7d5ad2626f91f70730c39d48e9062b64e917611eb1b833a7166b492dcb1269c'
assert sha((A/'FINAL-report.json').read_bytes())=='3dae6f571e27e684785cee7f4e2149bfa0ee11746e46dce42f03c5aa0adfc1db'
assert sha((A/'source.patch').read_bytes())=='7d72a74b6b34488c1953fe109fe802bf23a4e2eaa999088e9db8e9d61aef9a12'
assert git('rev-parse','HEAD').decode().strip()=='a070f16d06fee609691992ba57ee046431f8f55f';assert git('rev-parse','HEAD^{tree}').decode().strip()=='cd951533206a6a4545a6e55fec374e62289d2dd4';assert git('rev-parse','HEAD^').decode().strip()=='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2';assert git('status','--porcelain')==b'';assert git('diff','--check','HEAD^','HEAD')==b''
report=read(A/'FINAL-report.json');scope=read(C);assert set(git('diff','--name-only','HEAD^','HEAD').decode().splitlines())==set(scope['paths'])
inputs=[]
def freeze(p,to):
 raw=p.read_bytes();to.parent.mkdir(parents=True,exist_ok=True);to.write_bytes(raw);inputs.append({'path':str(p),'sha256':sha(raw),'bytes':len(raw)})
files=sorted(p for p in A.iterdir() if p.is_file());assert len(files)==16
for p in files:freeze(p,E/'author'/p.name)
freeze(C,E/'scope.json');inputs.append({'path':str(N),'sha256':sha(N.read_bytes()),'bytes':N.stat().st_size});assert inputs[-1]['sha256']==report['node_sha256']
paths=git('ls-files','apps/desktop/main','tests/ui/desktop/coding-authorization-boundary.test.mjs','tests/ui/desktop/desktop-management-boundary.test.mjs','AGENTS.md').decode().splitlines()
for name in paths:
 p=S/name;raw=p.read_bytes();assert raw==git('show','HEAD:'+name),name;freeze(p,E/'source'/name)
for name,want in report['changed_source_sha256'].items():assert sha((S/name).read_bytes())==want
for name in ['internal/domain/client_runtime_coding_windows.go','internal/domain/client_runtime_setup_windows.go','internal/domain/contracts.go','internal/api/contracts/domain.schema.json']:
 raw=git('show','HEAD:'+name);assert raw==git('show','HEAD^:'+name);p=E/'producer-contract'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
(E/'source.patch').write_bytes(git('diff','--binary','HEAD^','HEAD'));assert (E/'source.patch').read_bytes()==(A/'source.patch').read_bytes()
(E/'inputs.before.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(E/'git-status.before.raw').write_bytes(git('status','--short'))
temp=E/'fixture-temp';temp.mkdir();env=os.environ.copy();env.update(TEMP=str(temp),TMP=str(temp))
def run(name,argv):
 started=time.time()
 with (E/(name+'.stdout.raw')).open('xb') as out,(E/(name+'.stderr.raw')).open('xb') as err:proc=subprocess.run(argv,cwd=S,env=env,stdout=out,stderr=err,timeout=150)
 r={'argv':argv,'cwd':str(S),'native_exit':proc.returncode,'seconds':time.time()-started,'TEMP':str(temp),'TMP':str(temp)};(E/(name+'.process.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8');assert proc.returncode==0,r
run('fresh-boundaries',[str(N),'--test','tests/ui/desktop/coding-authorization-boundary.test.mjs','tests/ui/desktop/desktop-management-boundary.test.mjs'])
source=(S/'tests/ui/desktop/coding-authorization-boundary.test.mjs').read_text(encoding='utf8');prefix=source[:source.index("test('")]
prefix=prefix.replace("require('../../../apps/desktop/main/lib/desktop-management.js')",'require('+json.dumps(str(S/'apps/desktop/main/lib/desktop-management.js'))+')').replace("require('../../../apps/desktop/main/lib/ipc.js')",'require('+json.dumps(str(S/'apps/desktop/main/lib/ipc.js'))+')')
extra=r'''
test('independent valid Artifact ID and revision boundaries settle original confirm and status', async () => {
 for (const id of ['a','A_.:-9','a'.repeat(128),'a'.repeat(129),'a'.repeat(160)]) {
  for (const revision of [1,Number.MAX_SAFE_INTEGER]) {
   const f=fixture();try {
    const value={...profileRef(),id,revision};f.setProfileRef(value);await prepare(f);
    const settled=await approve(f);assert.deepEqual(settled.profile_ref,value);
    const status=await f.manager.statusCoding();assert.deepEqual(status.profile_ref,value);
    assert.equal(status.commit_key,settled.commit_key);assert(Object.isFrozen(status.profile_ref));
    assert.throws(()=>{status.profile_ref.id='mutated'},TypeError);
    assert.equal(f.manager.codingIntent.profileRef.id,id);
   } finally {f.close()}
  }
 }
});
test('independent existing result guards remain fail closed with valid Artifact ref', async () => {
 const mutations={state:'EXECUTION_SETTLED',request_id:'foreign',request_hash:'sha256:'+'0'.repeat(64),project_id:'foreign',session_id:'foreign',old_model_config_ref:'foreign',model_config_ref:'bad/ref',runtime_status:'QUALIFIED',model_calls:1,normal_max_model_calls:9,qualification_model_calls:2,qualification_tool_calls:1,scope:{},frozen_checks:[],revision:1.5,config_revision:Number.MAX_SAFE_INTEGER+1};
 for(const [key,value] of Object.entries(mutations)) { const f=fixture();try {
  await prepare(f);const result={...configuredResult(f,profileRef()),[key]:value};
  assert.throws(()=>f.manager.acceptCodingResult(f.manager.codingIntent,result),{code:'CODING_RESULT_INVALID'},key);
  assert.equal(f.manager.codingIntent.state,'AWAITING_CODING_CONFIRMATION');assert.equal(f.manager.codingIntent.profileRef,undefined);
 } finally {f.close()} }
});
'''
(E/'independent-boundaries.test.mjs').write_text(prefix+extra,encoding='utf8');run('independent-boundaries',[str(N),'--test',str(E/'independent-boundaries.test.mjs')])
for p in inputs:
 f=pathlib.Path(p['path']);assert sha(f.read_bytes())==p['sha256'] and f.stat().st_size==p['bytes']
assert git('status','--porcelain')==b'';(E/'git-status.after.raw').write_bytes(git('status','--short'));temp.rmdir()
print(json.dumps({'all_input_hashes_pass':True,'author_files':len(files),'source_read_dependencies':len(paths),'fresh_exit':0,'independent_exit':0,'input_files':len(inputs)},ensure_ascii=True))
