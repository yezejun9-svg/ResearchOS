from pathlib import Path
import ast,hashlib,json,subprocess,os,datetime
R=Path('D:/作品集/ResearchOS/research-os');N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/parallel-source-and-go3-r320';O=R/'execution/v2.4/receipts/W05/W05-99/root_registration_r320_readonly_review_codex/720240f461ab4fd888837d9d3ba3f72d'
checks=[];reads={};inv=[]
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def ref(p,relative=False):
 p=path(p);b=p.read_bytes();v=dict(path=p.relative_to(R).as_posix() if relative else str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b));reads[str(p)]=v;return v
def doc(p):ref(p);return json.loads(path(p).read_bytes())
def ck(n,b):checks.append(dict(check=n,passed=bool(b)))
def put(n,x):
 with (O/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
 return ref(O/n,True)
pins={'register.py':'4e9bd9c73ac33de9036b17ab8650fbbc138395e7b8211b22bb6eef5f3b8759fa','run.py':'39f89b09e1fd3f8360b3d5c7b39148c40ffde8bb52676c64cad133c1bda0e4e6','prepared_refs.json':'a3b0e8352e0fd657c6b143a21f89a53d835410c309c1a9337d7205ab5b27286f','audit.json':'26a32cf4933df63ce25bda0d65aa5bcb27dd0301aa3337666b48ac3dcf4debfe','scope_registration.json':'db21964ee73dc3316af2ff68be47613a290a3f0f31f60dca3af5d375ec31628f','seal.py':'3575bb614b43990e6f5b924b94ad0694b2f3e6e92e660c4db2d245fe3eb73917'}
for n,h in pins.items():ck('supplied '+n,ref(N/n)['sha256']==h)
for n in ['register.py','run.py','seal.py']:
 b=(N/n).read_bytes();ast.parse(b);ck('AST '+n,True)
 with (O/(n+'.original')).open('xb') as f:f.write(b)
p=doc(N/'prepared_refs.json');a=doc(N/'audit.json');copies=[];before=[]
for idx,x in enumerate(p['canonical_before']):
 b=path(x['path']).read_bytes();ck('canonical pin '+x['path'],hashlib.sha256(b).hexdigest()==x['sha256'] and len(b)==x['bytes']);q=O/(str(idx+1)+'-'+Path(x['path']).name)
 with q.open('xb') as f:f.write(b)
 copies.append(ref(q,True));before.append(b)
ck('ordered canonical4',[x['path'] for x in p['canonical_before']]==['execution/v2.4/'+x for x in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']])
cp,ow=[json.loads(b) for b in before[:2]];ck('actual319/147/413',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[319,147,413])
for x in p['verified_refs']:
 v=ref(x['path']);ck('verified ref '+x['path'],v['sha256']==x['sha256'] and v['bytes']==x['bytes'])
ck('audit counters',a['expected_before']==[319,147,413] and a['expected_after']==[320,148,417])
oldkeys={x.get('origin_key') for x in cp['failure_counters']};origins=p['origins'];ck('four unique new origins',len(origins)==len({x['origin_key'] for x in origins})==4 and not oldkeys.intersection(x['origin_key'] for x in origins))
def contains(x,target):
 if isinstance(x,dict):return x==target or any(contains(v,target) for v in x.values())
 if isinstance(x,list):return any(contains(v,target) for v in x)
 return False
for i,x in enumerate(origins):
 raw=doc(x['evidence_ref']['path']);ck('original nested payload '+x['origin_key'],contains(raw,x['original_payload']));ck('tool normalized outer '+x['origin_key'],x['actual_outer_exit']==1 and x['product_cases_run']==0)
ck('nullable native preserved',[x['actual_native_exit'] for x in origins]==[None,1,None,None]);ck('audit cut equals prepared',a['new_origins']==origins)
w=doc(N/'w09_source_scope.json');g=doc(N/'go3_execution_scope.json');spec=doc(p['pins']['go3_spec']['path']);prop=doc(p['pins']['w09_proposal']['path'])
ck('w09 exact4',w['source_paths']==[x['path'] for x in prop['exact_source_paths']]);ck('w09 noexec',all(w[k]==0 for k in ['Go_compile','Go_test','SQL','HTTP']));ck('fmt3x30',w['formatting']['maximum_invocations']==3 and w['formatting']['timeout_seconds']==30)
for k in ['source_commit','selectors','test_exe','caps','python_flags','new_output_root']:ck('Go3 exact spec '+k,g[k]==spec[k])
ck('new outputs absent',not path(w['worktree_root']).exists() and not path(g['new_output_root']).exists())
lock=doc(R/'execution/toolchains/locked.json')['tools']
for k in ['python','git']:ck('locked '+k,ref(lock[k]['path'])['sha256']==lock[k]['sha256'])
env={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')};env.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='nul')
def git(args,label,cwd=R):
 argv=[lock['git']['path'],'-C',str(cwd)]+args;r=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 for ext,b in [('stdout.raw',r.stdout),('stderr.raw',r.stderr)]:
  with (O/(label+'.'+ext)).open('xb') as f:f.write(b)
 inv.append(dict(argv=argv,actual_exit=r.returncode,stdout_ref=ref(O/(label+'.stdout.raw'),True),stderr_ref=ref(O/(label+'.stderr.raw'),True)));ck(label+' actual0',r.returncode==0);return r.stdout
head=git(['rev-parse','HEAD'],'head').decode().strip();status=git(['status','--porcelain=v1','--untracked-files=no'],'status');index=git(['diff','--cached','--name-only'],'index')
ck('Main head',head==p['head']==cp['head']=='2cdb0d43d5a600eef13c8f1735946a9adf52d079');ck('13status11D',hashlib.sha256(status).hexdigest()==p['git_status_sha256'] and len(status.splitlines())==13 and sum(x[:2]==b' D' for x in status.splitlines())==11);ck('index empty',index==b'')
g2=R/'.local/worktrees/codex-w0599-provider-g2-finite-r307';ck('G2 head',git(['rev-parse','HEAD'],'g2head',g2).decode().strip()=='9a34aacbaeb775566e524f5af3518ea86a5d41b9');ck('G2 clean',git(['status','--porcelain=v1'],'g2status',g2)==b'')
for name,h in [('runtime_coordinator_windows_test.go','a3f6ccfa16a3ea5d3770802eeb376789988bfcbd7b0b9b745e01c2821c4cacd8'),('runtime_provider_binding_windows_test.go','df176f5252e1b7eb6ac6f997052844b3af3f98997f7c2ac232eddb5307eaa8c4')]:ck('G2source '+name,ref(g2/'internal/domain'/name)['sha256']==h)
for x,b in zip(p['canonical_before'],before):ck('after canonical '+x['path'],path(x['path']).read_bytes()==b)
for n,h in pins.items():ck('after draft '+n,ref(N/n)['sha256']==h)
put('git-invocations.json',inv)
aud=put('read-audit.json',dict(checks=checks,refs=list(reads.values()),known_static_finding_not_execution=True,new_nonzero_origins=[]))
finding=dict(id='R320-SEAL-01',priority='P1',path=str(N/'seal.py'),expression="prepared['pins']['runner_review']",fact='The actual pins mapping has go3_review and w09_review but no runner_review. After successful canonical registration the sealer reaches this expression while constructing registration-audit.json and raises KeyError before writing that audit/manifest.',required_change='Preserve draft. Publish a new immutable sealer using the actual go3_review pin and a separate w09_review pin, or explicitly bind a verified alias in a new immutable prepared/register/wrapper set. Bind the replacement sealer actual bytes in the reviewed final execution plan. Do not execute the current sealer.',actual_execution=False)
changes=[finding]+[x for x in checks if not x['passed']]
review=put('review.json',dict(schema='researchos.root-registration-source-review.v1',reviewer='codex:/root/w05_merge_review',decision='REQUEST_CHANGES',requested_changes=changes,actual_registration_executed=False,expected_before=[319,147,413],expected_after=[320,148,417],register_sha256=pins['register.py'],wrapper_sha256=pins['run.py'],prepared_refs_sha256=pins['prepared_refs.json'],audit_sha256=pins['audit.json'],seal_sha256=pins['seal.py'],canonical_before=p['canonical_before'],copied_canonical_before_refs=copies,audit_ref=aud,source_acceptance=False,formal_increment=0,verified_static_guards=['Wrapper checks review identity/hash/four ordered copied canonical bytes/current original bytes and all four draft hashes before launch.','Register pins locked Python/Git, original4/HEAD/status/index/G2 and all prepared refs. Cached original reads rechecked before publication; desired2 and intent are written before mutation.','Every replace checks all4 current expected bytes and HEAD/status; own READS updated after replace; original413 prefix and formal state preserved; failure journal forward-only, no rollback.','Only new W09 test-source lease and Root receipt-only once Go3 scope. Existing319 Root14 is neither relaunched nor accepted; source/Main/formal remain false.','Four actual tool origins map to their original per-file/nested JSON payloads, native [null,1,null,null], not synthetic product failures.'],new_failure_origins=[],note='All listed byte/static checks ran successfully; one source-level sealer defect prevents approval. Root registration and sealer were not executed.'))
mf=put('manifest.json',dict(entries=[ref(f,True) for f in sorted(O.iterdir()) if f.is_file()],self_excluded=True));ho=put('handoff.json',dict(decision='REQUEST_CHANGES',review_ref=review,manifest_ref=mf,actual_registration_executed=False,new_failure_origins=[]))
print(json.dumps(dict(review=review,manifest=mf,handoff=ho,checks=len(checks),failed_checks=[x for x in checks if not x['passed']]),ensure_ascii=False))