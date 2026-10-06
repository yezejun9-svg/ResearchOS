import pathlib,subprocess,json,hashlib,gzip
D=pathlib.Path(__file__).resolve().parent; R=D.parents[6]
def save(n,v):
 with (D/n).open('x',encoding='utf8',newline='\n') as f: json.dump(v,f,indent=2,ensure_ascii=False); f.write('\n')
def sha(b): return hashlib.sha256(b).hexdigest()
m=json.loads((D/'commit_manifest.json').read_text(encoding='utf8'))
for row in m['files']: assert sha((R/row['path']).read_bytes())==row['sha256']
# Preserve the exact failed broad check's diagnostic bytes once without printing
# tens of megabytes of public raw fixture diff. No evidence is normalized.
argv=['git','diff','--cached','--check']; p=subprocess.run(argv,cwd=R,capture_output=True)
(D/'broad-check.stdout.gz').write_bytes(gzip.compress(p.stdout,mtime=0)); (D/'broad-check.stderr.gz').write_bytes(gzip.compress(p.stderr,mtime=0))
save('commit_check_failure.json',{'original_tool_chunk':'7d206c','original_wrapper_exit':1,'actualargv':argv,'exit':p.returncode,'cwd':str(R),'stdout_sha256':sha(p.stdout),'stdout_bytes':len(p.stdout),'stdout_gzip':'broad-check.stdout.gz','stderr_sha256':sha(p.stderr),'stderr_gzip':'broad-check.stderr.gz','cause':'Broad whitespace check includes immutable original CRLF receipts and raw fixture payloads; no source/test failure and no raw rewriting.','replacement_check':['git','diff','--cached','--check','--',*m['source_paths']]})
q=subprocess.run(['git','diff','--cached','--check','--',*m['source_paths']],cwd=R,capture_output=True)
save('source_check.json',{'exit':q.returncode,'stdout':q.stdout.decode(),'stderr':q.stderr.decode()}); assert q.returncode==0
files=sorted(set([r['path'] for r in m['files']]+[p.relative_to(R).as_posix() for p in D.rglob('*') if p.is_file()]))
save('commit_manifest.final.json',{'files':[{'path':n,'sha256':sha((R/n).read_bytes())} for n in files],'source_paths':m['source_paths'],'commit_check_failure_ref':'commit_check_failure.json','preserve_original_manifest':True})
files.append((D/'commit_manifest.final.json').relative_to(R).as_posix())
subprocess.run(['git','-c','core.longpaths=true','add','--pathspec-from-file=-','--pathspec-file-nul'],cwd=R,input=b'\0'.join(x.encode() for x in files)+b'\0',capture_output=True,check=True)
staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=R).decode().strip('\0').split('\0'); assert set(staged)==set(files)
p=subprocess.run(['git','commit','-m','fix(runtime): match SDK signed-zero tool index identity'],cwd=R,capture_output=True); print('commit exit',p.returncode); assert p.returncode==0,p.stderr.decode()
print('candidate',subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()); print('files',len(files)); print('commit_manifest.final_sha256',sha((D/'commit_manifest.final.json').read_bytes()))
