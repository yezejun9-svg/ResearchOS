import datetime, hashlib, json, pathlib, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[4]
OUT=pathlib.Path(__file__).resolve().parent
AUTHOR=ROOT/'.local/worktrees/jev-protected/execution/receipts/W11/protected/9a616fa5-caf1-4d61-9dc5-deefc50892c5'
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT)
b=load(AUTHOR/'before.json');r=load(AUTHOR/'report.json');checks=[]
def check(id,want,got):checks.append(dict(id=id,expected=want,actual=got,status='PASS' if want==got else 'FAIL'))
for p,h in b['source_manifest'].items():check('SOURCE:'+p,h,sha(git('show',b['code_revision']+':'+p)))
for name,c in r['commands'].items():
 for stream in ['stdout','stderr']:check('RAW:'+name+':'+stream,c[stream+'_sha256'],sha((AUTHOR/(name+'.'+stream+'.txt')).read_bytes()))
native=(AUTHOR/'native-broker-tests.stdout.txt').read_text(encoding='utf-8-sig').splitlines()
check('AUTHOR-NATIVE-INVENTORY',sorted(b['expected_broker_assertions']),sorted(l.split()[1] for l in native if l.startswith('BROKER_ASSERTION ')))
check('AUTHOR-NATIVE-ALL-PASS',True,all(l.split()[2]=='PASS' for l in native if l.startswith('BROKER_ASSERTION ')))
check('AUTHOR-BINARY',b['binary_sha256'],sha(pathlib.Path(b['binary_path']).read_bytes()))
check('AUTHOR-BUILD-CLEAN','',b['build_before_receipt_dirty'])
info=(OUT/'author-binary-build-info.txt').read_text(encoding='utf-8-sig')
check('AUTHOR-BINARY-VCS',True,'vcs.revision='+b['code_revision'] in info and 'vcs.modified=false' in info)
check('AUTHOR-NOT-INSTALLED',{'directory_exists':False,'service_exists':False},r['installation_absent'])
check('AUTHOR-TEST-DELTA-ONLY',['adapters/protectedstore/broker_windows_test.go'],git('diff','--name-only','c7ec0c6','73ecf1e').decode().splitlines())
before=load(OUT/'before.json');after=load(OUT/'after.json');plan=load(OUT/'install-plan.json')
for p,h in before['source_hashes'].items():check('INDEPENDENT-NO-SOURCE-DRIFT:'+p,h.lower(),sha(git('show','c7ec0c6:'+p)).split(':')[1])
for row in load(OUT/'installer-negative-controls.json'):check('INSTALLER-REFUSAL:'+row['scenario'],True,row['refused'])
check('INDEPENDENT-INSTALL-STILL-ABSENT',{'service_exists':False,'install_root_exists':False,'probe_exit':1},after)
check('PLAN-BINARY-HASH',before['binary_hash'].lower(),plan['binary_sha256'])
check('PLAN-NO-ELEVATION',False,plan['elevation_required'])
save(OUT/'author-and-installer-audit.json',dict(checks=checks,count=len(checks),passed=sum(x['status']=='PASS' for x in checks),failed=sum(x['status']=='FAIL' for x in checks)))
assert all(x['status']=='PASS' for x in checks)
raw=OUT/'independent.stdout.txt';assertions=[]
for n,l in enumerate(raw.read_text(encoding='utf-8-sig').splitlines(),1):
 if l.startswith('RV_BROKER_ASSERTION '):
  a=json.loads(l.split(' ',1)[1]);a['raw_evidence']=dict(path=raw.name,line=n,sha256=sha(raw.read_bytes()));assertions.append(a)
assert all(x['status']=='PASS' for x in assertions)
for p in b['source_manifest']:
 target=OUT/'source-snapshot'/(p+'.txt');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(git('show',b['code_revision']+':'+p))
(OUT/'independent_review_test.go.txt').write_bytes((ROOT/'.local/w11-broker-preinstall/review_test.go').read_bytes())
review=dict(schema='W11_BROKER_PREINSTALL_INDEPENDENT_REVIEW_V1',reviewer='codex:/root/orchestration_verifier',verdict='PASS_IN_PREINSTALL_SCOPE',reviewed_source=b['code_revision'],independent_test_source=before['source_revision'],test_delta_only=True,source_hashes=b['source_manifest'],author_receipt='execution/receipts/W11/protected/9a616fa5-caf1-4d61-9dc5-deefc50892c5',author_binary_sha256=b['binary_sha256'],independent_binary_sha256='sha256:'+before['binary_hash'].lower(),binary_difference='Embedded VCS revision differs: independent c7ec0c6 versus author 73ecf1e; product broker/service/installer code is identical.',assertion_count=len(assertions),pass_count=len(assertions),audit_count=len(checks),assertions=assertions,findings=[],installed=False,installed_boundary_verdict='NOT_RUN_PENDING_EXPLICIT_AUTHORIZED_UAC',formal_G04='BLOCKED',formal_A08='BLOCKED',formal_holdout_count=0,real_provider_called=False,maximum_mode='ADVISORY',automatic_authority='NONE',stage_advanced=False,source_review=['Installer creates fixed directory atomically with protected Administrators owner and explicit ACL; executable/manifest administrator-owned, reader only read/execute, data parent service/admin only; private root and files exact service token SID owner/ACL.','Windows service entry requires SCM, exact virtual-account token user and fixed executable path. Developer gets only SCM config/status query rights. SeChangeNotifyPrivilege is the only configured required service privilege.','Pipe uses first-instance guard, rejects remote clients, grants reader exact FILE_READ_DATA|FILE_WRITE_DATA|SYNCHRONIZE (no FILE_CREATE_PIPE_INSTANCE), client requests SECURITY_IDENTIFICATION, binds actual server PID to SCM PID before and after exchange.','Only summary-v1 is accepted. No arbitrary file path, process, provider URL, proxy, credential or evaluation request interface exists in this revision. Response is validated SafeSummary; file ACL/hash/body rechecked on every request.','Public probe returns within 3 seconds; overlapped request/read/ack has absolute deadline. Same-user native silent-server test proves I/O timeout. Installed SCM/token/PID/ACL persistence is not yet dynamically proven.','Uninstall targets fixed service plus exact four canaries, verifies configuration/hash, refuses unknown files and uses no recursive deletion.'],installed_required=['Run unelevated developer access probes: all four existing input/label/detail/log files return ERROR_ACCESS_DENIED, not missing-file success; exact service account/PID/aggregate roundtrip; binary write/WRITE_DAC denied with Administrators owner.','Also verify service control/change-config/write-owner denied and exact installed root/data/private owners/DACL under privileged verifier; candidate AppContainer direct-path read/write denied with current-input positive control.','Perform controlled service restart in the same authorized administrator session, then repeat unelevated probes to prove persistence; reject any ACL, binary, config or private-body drift.','Validate actual SCM-authenticated server-PID mismatch rejection and pipe-squatting/extra-instance denial with synthetic probes. Same-user protocol tests are not substitutes.'],formal_route='minimal-route.md',known_unrelated_test='Root reported W12 retention loopback readiness failure; not used as broker evidence and not reclassified here.',references=[{'url':'https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights','supports':'Specific read/write rights exclude FILE_CREATE_PIPE_INSTANCE, unlike generic write.'}])
save(OUT/'review.json',review)
files={str(p.relative_to(OUT)).replace('\\','/'):sha(p.read_bytes()) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='evidence-index.json'}
save(OUT/'evidence-index.json',dict(files=files))
print(json.dumps(dict(verdict=review['verdict'],assertions=len(assertions),audit_count=len(checks),review_sha256=sha((OUT/'review.json').read_bytes()),index_sha256=sha((OUT/'evidence-index.json').read_bytes()))))
