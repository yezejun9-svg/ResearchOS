import pathlib,json,re,hashlib,subprocess,shlex
root=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees');ev=root/'attach-exact6-independent-evidence-20261013';work=root/'attach-exact6-independent-20261013';candidate=root/'attach-synchronous-completion-20261012';base='91218bdd3901bae94a2c1c90521a4d133c59026d';head='b955c8665281193d5cbf90a146f936c9212c7940'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(work),*a])
author=json.loads((ev/'final-author-manifest.json').read_text(encoding="utf-8"));paths=[x['path'] for x in author['source_paths']]
sources=[]
for x in author['source_paths']:
 p=x['path'];b=(work/p).read_bytes();c=(candidate/p).read_bytes();committed=git('show',head+':'+p)
 sources.append({'path':p,'sha256':sha(b),'author_match':sha(b)==x['sha256'],'candidate_match':b==c,'commit_match':b==committed})
# Existing functions are anchored by next top-level func, retaining exact text for body comparison.
def funcs(raw):
 s=raw.decode("utf-8");starts=list(re.finditer(r'^func ',s,re.M));return {s[m.start():s.find('{',m.start())].strip():s[m.start():starts[i+1].start() if i+1<len(starts) else len(s)].rstrip() for i,m in enumerate(starts)}
protected={}
for p,excludes in [('internal/domain/client_protocol_atomic_test.go',[]),('internal/domain/client_protocol_control_windows_test.go',['TestClientSameWriterRenewsExpiredLease']),('internal/api/v2_sessions_test.go',['TestW14SessionWriterLeaseHandoff'])]:
 old=funcs(git('show',base+':'+p));new=funcs(git('show',head+':'+p));items=[]
 for sig,body in old.items():
  if any(n in sig for n in excludes):continue
  # Added function comments before the next declaration are excluded by trimming before final closing brace.
  b=body[:body.rfind('}')+1];n=new.get(sig,'');n=n[:n.rfind('}')+1]
  items.append({'function':sig,'unchanged':b==n,'base_sha256':sha(b.encode()),'candidate_sha256':sha(n.encode())})
 protected[p]=items
scope={'base':base,'head':git('rev-parse','HEAD').decode().strip(),'tree':git('rev-parse','HEAD^{tree}').decode().strip(),'changed_paths':git('diff','--name-only',base,head).decode().splitlines(),'source_checks':sources,'protected_functions':protected,'status':git('status','--short').decode(),'author_manifest_sha256':sha((root/'attach-synchronous-completion-evidence-20261012/final-author-manifest.json').read_bytes()),'diff_check_exit':subprocess.run(['git','-C',str(work),'diff','--check',base,head],capture_output=True).returncode}
(ev/'resume-source-audit.json').write_text(json.dumps(scope,indent=2))
raw=(ev/'independent-native.stderr.raw').read_text(encoding="utf-8");build=raw.splitlines()[0].split('=',1)[1];commands=[];files={};missing=[]
for lineno,line in enumerate(raw.splitlines(),1):
 if 'compile.exe' not in line or ' -pack ' not in line:continue
 tokens=re.findall(r'"(?:[^"\\]|\\.)*"|\S+',line)
 decoded=[json.loads(t) if t.startswith('"') else t for t in tokens]
 package=decoded[decoded.index('-p')+1] if '-p' in decoded else ''
 inputs=[]
 for token in decoded:
  if not token.endswith('.go'):continue
  token=token.replace('$WORK',build);p=pathlib.Path(token)
  if not p.is_absolute():p=work/p
  inputs.append(str(p))
  if p.exists():files[str(p)]={'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
  else:missing.append(str(p))
 commands.append({'raw_line':lineno,'package':package,'argv':decoded,'go_inputs':inputs})
census={'basis':'ACTUAL compile.exe invocations from native -work -x stderr; does not count cached or go-list-only files as compiled','raw_sha256':sha((ev/'independent-native.stderr.raw').read_bytes()),'work':build,'compile_command_count':len(commands),'unique_go_file_count':len(files),'missing':sorted(set(missing)),'commands':commands,'files':list(files.values()),'exact_six_in_actual_compile':{p:str(work/p) in files for p in paths}}
(ev/'resume-actual-compiler-census.json').write_text(json.dumps(census,indent=2))
print(json.dumps({'source_checks':sources,'protected_total':sum(map(len,protected.values())),'protected_differences':[i for a in protected.values() for i in a if not i['unchanged']],'census_summary':{k:v for k,v in census.items() if k not in ['commands','files']}}))

