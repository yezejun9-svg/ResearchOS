import pathlib,json,hashlib,subprocess,sys,datetime
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
OUT=pathlib.Path(__file__).parent
V5=ROOT/'execution/v2.4/receipts/W05/W05-99/cancel_finalization_closed_contract_revision_v5_codex/669a7381fd594e88b8570b67a507596a'
def sha(b): return hashlib.sha256(b).hexdigest()
def save(n,v):
 p=OUT/n
 if p.exists(): raise RuntimeError('immutable output exists '+n)
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if sys.argv[1]=='capture':
 paths={p.relative_to(ROOT).as_posix() for p in V5.rglob('*') if p.is_file()}
 proposal=json.loads((V5/'scope_proposal.json').read_text(encoding='utf-8'))
 paths.update(x['path'] for x in proposal['scope'])
 paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'internal/domain').glob('*.go'))
 paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'migrations/sqlite').glob('*.sql'))
 paths.update(['internal/store/store.go','AGENTS.md','go.mod','go.sum'])
 rows=[]
 for rel in sorted(paths):
  p=ROOT/rel
  if p.exists():
   b=p.read_bytes(); rows.append({'path':rel,'bytes':len(b),'sha256':sha(b)})
  else: rows.append({'path':rel,'absent':True})
 save('inputs.before.json',rows)
 h=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True)
 save('capture.invocation.json',{'argv':sys.argv,'cwd':str(ROOT),'git_argv':['git','rev-parse','HEAD'],'git_exit':h.returncode,'git_stdout':h.stdout,'git_stderr':h.stderr,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'policy':'public bytes only; no SQL/Go/Node/tests/HTTP/model'})
 print(len(rows),'public inputs captured')
elif sys.argv[1]=='read':
 rel=sys.argv[2]; p=V5/rel[3:] if rel.startswith('v5:') else ROOT/rel
 lines=p.read_text(encoding='utf-8').splitlines(); start=int(sys.argv[3]) if len(sys.argv)>3 else 1; end=int(sys.argv[4]) if len(sys.argv)>4 else len(lines)
 print(str(p)); print('\n'.join(f'{i}: {s}' for i,s in enumerate(lines,1) if start<=i<=end))
