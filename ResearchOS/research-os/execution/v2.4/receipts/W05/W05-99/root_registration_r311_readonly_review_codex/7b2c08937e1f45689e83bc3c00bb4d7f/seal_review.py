import pathlib,json,hashlib,ast,subprocess,os,datetime
R=pathlib.Path(r'D:/作品集/ResearchOS/research-os'); D=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop-http-exact15-lease-r311'; O=R/'execution/v2.4/receipts/W05/W05-99/root_registration_r311_readonly_review_codex/7b2c08937e1f45689e83bc3c00bb4d7f'
def load(p):return json.loads(p.read_bytes())
def h(b):return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':p.relative_to(R).as_posix(),'sha256':h(b),'bytes':len(b)}
def save(n,v):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
expected={'register.py':'340c618aafd1f5e91b38f1d2045bb60ffed036c3b78248fc4ce5beb848dcd54a','run.py':'99ba49168aa4826da70bab5a2c63ee3b2cf368d231e17bb304a5702d49387b4c','prepared_refs.json':'f996196304da42e60b2fb31346885e7020e1c486f74da55882f0a0514012c265','audit.json':'155ce5300dacbbef0e27cb9a44394a4b40c9794381e6e2a5575eea6d4fc11d69','scope_registration.json':'3595c57c257c097718d5d1debecf219f2707fea9294812c81d7cbfc6a6864a84'}
errors=[]; scriptrefs=[]
for n,want in expected.items():
 p=D/n;raw=p.read_bytes();copy=O/('original-'+n);copy.write_bytes(raw);scriptrefs.append({'original':ref(p),'copy':ref(copy),'matches_expected':h(raw)==want})
 if h(raw)!=want:errors.append('scriptpin:'+n)
 if n.endswith('.py'):ast.parse(raw,filename=str(p))
prepared=load(D/'prepared_refs.json'); scope=load(D/'scope_registration.json'); copies=[]; canon=[]
for i,pin in enumerate(prepared['canonical_before']):
 p=R/pin['path'];raw=p.read_bytes();copy=O/('%02d-'%i+p.name+'.original');copy.write_bytes(raw);copies.append(ref(copy));canon.append({'expected':pin,'actual':ref(p),'copy':ref(copy),'equal':ref(p)==pin})
 if ref(p)!=pin:errors.append('canonical:'+pin['path'])
verified=[]
for pin in prepared['verified_refs']:
 actual=ref(R/pin['path']);eq=all(actual[k]==pin[k] for k in ['path','sha256','bytes']);verified.append({'expected':pin,'actual':actual,'equal':eq})
 if not eq:errors.append('ref:'+pin['path'])
cp=load(O/'00-checkpoint.json.original');ow=load(O/'01-path_ownership.json.original');before_counts=[cp['revision'],ow['revision'],len(cp['failure_counters'])]
if before_counts!=[310,138,384]:errors.append('counts')
lock=load(R/'execution/toolchains/locked.json')['tools'];env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'); git=lock['git']['path']; gitcalls=[]
def gitread(args,cwd=R):
 run=subprocess.run([git]+args,cwd=cwd,env=env,capture_output=True);n=len(gitcalls);(O/('git-%02d.stdout.raw'%n)).write_bytes(run.stdout);(O/('git-%02d.stderr.raw'%n)).write_bytes(run.stderr);gitcalls.append({'argv':[git]+args,'cwd':str(cwd),'actual_native_exit':run.returncode,'stdout':ref(O/('git-%02d.stdout.raw'%n)),'stderr':ref(O/('git-%02d.stderr.raw'%n))});return run
head=gitread(['rev-parse','HEAD']);status=gitread(['status','--porcelain=v1','--untracked-files=no']);index=gitread(['diff','--cached','--name-only'])
if head.returncode or head.stdout.decode().strip()!=prepared['head']:errors.append('HEAD')
if status.returncode or h(status.stdout)!=prepared['git_status_sha256']:errors.append('status')
if index.returncode or index.stdout:errors.append('index')
if len(status.stdout.splitlines())!=13 or sum(x[:2]==b' D' for x in status.stdout.splitlines())!=11:errors.append('13status/11D')
g2=R/'.local/worktrees/codex-w0599-provider-g2-finite-r307';g2head=gitread(['rev-parse','HEAD'],g2);g2status=gitread(['status','--porcelain=v1'],g2)
if g2head.returncode or g2head.stdout.decode().strip()!='9a34aacbaeb775566e524f5af3518ea86a5d41b9' or g2status.returncode or g2status.stdout:errors.append('g2frozen')
source=load(R/scope['path_bounds_ref']['path']);sr=[]
for item in source['paths']:
 p=R/item['path'];actual=ref(p) if p.is_file() else None
 eq=(actual is not None and actual['sha256']==item['sha256'] and actual['bytes']==item['bytes']) if item['exists_before'] else not p.exists()
 sr.append({'expected':item,'actual':actual,'equal':eq})
 if not eq:errors.append('source:'+item['path'])
if [x['path'] for x in source['paths']]!=scope['exact_paths'] or len(scope['exact_paths'])!=15 or pathlib.Path(scope['worktree']).exists():errors.append('exact15/worktree')
checks=[{'check':'registration boundaries','verdict':'VERIFIED_STATIC','source':'register.py:79-99','detail':'Only DesktopW13 work_in_progress lease + W13-03 new subtask + revision/time/evidence/integrity/nextcommand metadata; original W05 scopes preserved. SourceReady false; noMainintegration; worktree creation deferred.'},{'check':'384 failure origins','verdict':'VERIFIED_STATIC_AND_CURRENT','source':'register.py:76-77,138','detail':'Original full list preserved with zero additions; exact384 count and prefix afterwrite.'},{'check':'original/desired/intent ordering','verdict':'VERIFIED_STATIC','source':'register.py:100-123','detail':'Four raw originals plus Gitstatus, two desireds and intent all persist before canonical temp/replaces. xb outputs prevent automatic overwrites/retry.'},{'check':'perreplace fourfile and Git CAS','verdict':'VERIFIED_STATIC','source':'register.py:125-141','detail':'Each replacement compares allfour to expected_live and HEAD/status; own replacement updates both expected_live and READS, preserving canonical ST/commands original bytes.'},{'check':'failure behavior','verdict':'VERIFIED_STATIC','source':'register.py:146-150','detail':'Inside write phase preserves actualexception/stage/currenthash; no rollback/retry. Failures before write phase still stop and are wrapper stderr/nativeexit; intent/originals remain when produced. No claim transactional multi-file atomicity.'},{'check':'review gating','verdict':'VERIFIED_STATIC','source':'run.py:14-53','detail':'Requires actual reviewsha/schema/identity/positivedecision/emptychanges/beforeafter/4scriptpins/canonicalbefore+sameorder four copied originals underreview namespace and actualcanonicalequal; tools/Git guards precede subprocess.'},{'check':'guardoptimization','verdict':'VERIFIED_STATIC','source':'register.py:9-10;run.py:9-10','detail':'-O explicitly refused before assert-based guards; no assertion bypass under optimization.'},{'check':'Desktop scope','verdict':'VERIFIED_SCOPE_ONLY','source':'scope_registration.json','detail':'15exact includingv2.js;159+7 max386loopback andpreflightfail0;finalsixkeys,compiled/allWORK,captureactualchildclose,noPIDkill;Host1MiB/native/Web/install/formalheld. No source/product acceptance.'}]
# Re-read only the pinned canonical and fixed draft input bytes after inspection.
after=[]
for item in canon:
 actual=ref(R/item['expected']['path']);eq=actual==item['expected'];after.append({'expected':item['expected'],'actual':actual,'equal':eq})
 if not eq:errors.append('aftercanonical:'+item['expected']['path'])
for row in scriptrefs:
 if ref(R/row['original']['path'])!=row['original']:errors.append('afterdraft:'+row['original']['path'])
save('audit.json',{'scriptpins':scriptrefs,'verified_refs':verified,'canonical':canon,'canonical_after':after,'current_counts':before_counts,'source15':sr,'Git':gitcalls,'checks':checks,'errors':errors,'registration_executed':False,'actual_product_invocations':0})
save('tool_origins.json',{'read_tools':[{'ref':'176aed','outer_exit':0},{'ref':'a24b49','outer_exit':0}],'readonly_Git_calls':gitcalls,'new_nonzero_origins':[x for x in gitcalls if x['actual_native_exit']!=0],'locator_branch':'STOPPED; only supplied exactrefs used','register_run_import_execution':0,'product_Go_SQL_Node_HTTP_MODEL':0})
save('review.json',{'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/command_queue_impl','decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' if not errors else 'REQUEST_CHANGES','requested_changes':errors,'actual_registration_executed':False,'expected_before':[310,138,384],'expected_after':[311,139,384],'register_sha256':expected['register.py'],'wrapper_sha256':expected['run.py'],'prepared_refs_sha256':expected['prepared_refs.json'],'audit_sha256':expected['audit.json'],'canonical_before':prepared['canonical_before'],'copied_canonical_before_refs':copies,'review_scope':'Root registration mechanics and exact Desktop source lease only; no product/source acceptance','independence':'Registration scripts authored byRoot, reviewer didnot implement these scripts or Desktop product15. Prior scope review is referenced as scope only.','checks_ref':ref(O/'audit.json'),'source_acceptance':False,'formal_increment':0,'new_failure_count':sum(x['actual_native_exit']!=0 for x in gitcalls)})
save('handoff.json',{'review_ref':ref(O/'review.json'),'decision':load(O/'review.json')['decision'],'audit_ref':ref(O/'audit.json'),'tool_origins_ref':ref(O/'tool_origins.json'),'actual_registration_executed':False,'new_failure_count':sum(x['actual_native_exit']!=0 for x in gitcalls),'current_counts':before_counts,'fixed_refs_verified':len(verified),'forward_only_no_automatic_retry':True})
allfiles=sorted(p for p in O.iterdir() if p.is_file() and p.name!='manifest.json');save('manifest.json',{'files':[ref(p) for p in allfiles],'listed_count':len(allfiles),'self_excluded':True})
print(json.dumps({'errors':errors,'refs':{n:ref(O/n) for n in ['review.json','manifest.json','handoff.json']}},ensure_ascii=True))
