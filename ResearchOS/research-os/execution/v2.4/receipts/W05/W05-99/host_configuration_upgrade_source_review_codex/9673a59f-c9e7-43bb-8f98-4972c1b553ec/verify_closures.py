exec((__import__('pathlib').Path(__file__).with_name('prepare_final.py')).read_text(encoding='utf-8-sig').split('checks=[]')[0])
import collections
N=W/P if False else W/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex'
changed={}
for c in ['125ea34ca0878f18c4dce47f9259ab5e9e77c2eb',C]:
 for line in git('diff-tree','--no-commit-id','--name-only','-r',c).decode().splitlines():changed[line]=c
proc=subprocess.Popen(['git','--no-replace-objects','-C',str(W),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE);blobs=[]
for path,c in changed.items():
 proc.stdin.write((c+':'+path+'\n').encode());proc.stdin.flush();head=proc.stdout.readline().decode().split();size=int(head[2]);b=proc.stdout.read(size);proc.stdout.read(1);actual=(W/path).read_bytes();assert b==actual
 blobs.append({'path':path,'commit':c,'sha256':sha(b),'bytes':len(b)})
proc.stdin.close();proc.wait();save('all_candidate_blobs.json',blobs)
# Inspect each build/execution vector and hash current public input bytes.
V=N/'closure-6e184bfb0e35426ab6f38707d3eeb5eb';before=json.loads((V/'source_before.json').read_text(encoding='utf-8-sig'));after=json.loads((V/'source_after.json').read_text(encoding='utf-8-sig'));assert before==after
prefix=collections.Counter(k.split(':',1)[0] for k in before);bad=[];unknown=[]
for key,h in before.items():
 kind,name=key.split(':',1)
 if kind=='main':p=R/name
 elif kind=='absolute':p=Path(name)
 elif kind in ['worktree','repo']:p=W/name
 else:unknown.append(key);continue
 if not p.is_file() or sha(p.read_bytes())!=h:bad.append({'path':str(p),'expected':h,'actual':sha(p.read_bytes()) if p.is_file() else None})
save('author_current_vector_audit.json',{'prefixes':dict(prefix),'count':len(before),'before_after_equal':before==after,'current_drift':bad,'unresolved':unknown})
# old22 public build vector and native program hash chain, no execution.
B=N/'old22-build-40e94f3f6e53442fa07068089c0de64a';refs=[]
for n in ['result.json','git_source.json','old22-control.exe.build.invocation.json','old22-control.exe.build.stdout','old22-control.exe.build.stderr','old22-backup.exe.build.invocation.json','source_before.json','source_after.json']:
 p=B/n;refs.append({'path':str(p),'sha256':sha(p.read_bytes())})
a=json.loads((B/'source_before.json').read_text(encoding='utf-8-sig'));z=json.loads((B/'source_after.json').read_text(encoding='utf-8-sig'));assert a==z
save('external_build_bindings.json',{'old22_vector_equal':True,'count':len(a),'refs':refs,'source_record':json.loads((B/'git_source.json').read_text(encoding='utf-8-sig')),'build_invocation':json.loads((B/'old22-control.exe.build.invocation.json').read_text(encoding='utf-8-sig')),'limit':'External source/build provenance; binary does not attest its own source. No universal version-probing API claimed.'})
print(json.dumps({'candidate_blobs':len(blobs),'vector_count':len(before),'prefixes':dict(prefix),'drift':len(bad),'unknown':len(unknown)}))
