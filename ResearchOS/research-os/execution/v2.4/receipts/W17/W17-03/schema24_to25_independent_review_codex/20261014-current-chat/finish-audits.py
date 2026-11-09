import pathlib,json,subprocess,hashlib,datetime
E=pathlib.Path(__file__).parent
A=E.parents[1]/'schema24_to25_source_codex'/'20261014-current-chat'
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def census(p):
 events=[json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip().startswith('{')]
 passed={(e['Package'],e['Test']) for e in events if e.get('Action')=='pass' and 'Test' in e}
 return dict(top=sum('/' not in n for _,n in passed),leaf=sum(not any(q==p and t.startswith(n+'/') for q,t in passed) for p,n in passed),all_pass_events=len(passed),fail=[e for e in events if e.get('Action')=='fail'],skip=[e for e in events if e.get('Action')=='skip'],packages=[e['Package'] for e in events if e.get('Action')=='pass' and 'Test' not in e])
r={'fresh_tests':census(E/'fresh-source-tests.stdout.jsonl'),'compiler_coverage':{},'binaries':[]}
assert not r['fresh_tests']['fail']
for role in ['source24','target25-r3']:
 d=A/(role+'-build-inputs');pins=read(d/'compiler-inputs.json'); names={str(pathlib.Path(x['path']).resolve()).lower() for x in pins['inputs']}
 raw=(d/'go-list.stdout.raw').read_text(encoding='utf8');dec=json.JSONDecoder();pkgs=[];offset=0
 while raw[offset:].strip():
  offset+=len(raw[offset:])-len(raw[offset:].lstrip());p,n=dec.raw_decode(raw,offset);offset=n;pkgs.append(p)
 inputs=set()
 for p in pkgs:
  for key in ['GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','EmbedFiles']:
   for n in p.get(key,[]):inputs.add(str((pathlib.Path(p['Dir'])/n).resolve()).lower())
 missing=sorted(inputs-names);assert not missing,missing
 r['compiler_coverage'][role]={'package_count':len(pkgs),'selected_source_and_embed_files':len(inputs),'pinned_files':len(names),'missing':missing}
pins=read(E/'author-manifest.json')['program_pins']
for role in ['SourceBackupProgram','RootProgram','ControlProgram','BackupProgram','EnrollmentProgram']:
 p=pins[role];argv=[str(ROOT/'.local/tools/go1.27.1/go/bin/go.exe'),'version','-m',p['path']]
 run=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE);out=run.stdout.decode('utf8');assert run.returncode==0
 expected='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2' if role=='SourceBackupProgram' else '1b5ec5d049db7811f6e0d8b143659ea5e2f0836b'
 assert 'go1.27.1' in out and 'vcs.modified=false' in out and 'vcs.revision='+expected in out
 (E/(role+'.go-version-m.stdout.raw')).write_bytes(run.stdout);(E/(role+'.go-version-m.stderr.raw')).write_bytes(run.stderr)
 r['binaries'].append({'role':role,'argv':argv,'native_exit':run.returncode,'sha256':hashlib.sha256(pathlib.Path(p['path']).read_bytes()).hexdigest(),'expected_commit':expected,'modified':False})
(E/'additional-integrity-audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(r,ensure_ascii=False))
