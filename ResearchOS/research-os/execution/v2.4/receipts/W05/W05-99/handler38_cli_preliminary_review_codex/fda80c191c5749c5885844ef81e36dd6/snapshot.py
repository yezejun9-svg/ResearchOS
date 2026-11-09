import pathlib,json,hashlib,datetime,difflib
R=pathlib.Path('D:/作品集/ResearchOS/research-os'); W=R/'.local/worktrees/codex-w0599-host-configuration-handler'; N=pathlib.Path(__file__).parent
H=lambda b:hashlib.sha256(b).hexdigest()
def save(n,v):
 p=N/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
rels=['apps/cli/cli_contract.go','apps/cli/cli_v2.go','apps/cli/cli_stream.go','apps/cli/cli_model_configuration_test.go','apps/cli/cli_model_configuration_windows_test.go','internal/domain/contracts.go','internal/domain/client_protocol_schema.go','internal/domain/client_protocol_configuration.go','internal/domain/client_protocol_sessions.go','internal/api/contracts/client.protocol.schema.json','internal/domain/contracts/client.protocol.schema.json','go.mod','go.sum']
paths=[(W/x,'worktree/'+x) for x in rels]
paths += [(R/'execution/toolchains/locked.json','public_tools/locked.json'),(R/'.local/tools/go1.27.1/go/src/encoding/json/jsontext/value.go','public_tools/jsontext_value.go')]
for f in ['validator.go','util.go','schema.go']:
 paths.append((R/'.local/gopath/pkg/mod/github.com/santhosh-tekuri/jsonschema/v6@v6.0.3'/f,'public_tools/jsonschema/'+f))
rows=[]
for p,dst in paths:
 b=p.read_bytes(); q=N/'public_inputs'/dst;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 rows.append({'path':str(p),'snapshot':q.relative_to(N).as_posix(),'sha256':H(b),'bytes':len(b)})
save('inputs.before.json',rows)
old=R/'execution/v2.4/receipts/W05/W05-99/handler38_cli_preliminary_review_codex/acf3406cef3a4fe8b20e0ee340bafc55'
comparisons=[]
for x in rels:
 p=old/'public_inputs'/x
 if not p.exists():continue
 a=p.read_bytes();b=(W/x).read_bytes();comparisons.append({'path':x,'prior_snapshot_sha256':H(a),'current_sha256':H(b),'same_bytes':a==b})
 if a!=b:
  dst=N/'diffs'/(''.join(c if c.isalnum() else '_' for c in x)+'.diff');dst.parent.mkdir(exist_ok=True);dst.write_bytes(''.join(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='prior/'+x,tofile='current/'+x)).encode())
save('prior_comparison.json',comparisons)
print(json.dumps({'namespace':str(N),'inputs':len(rows),'comparisons':comparisons},ensure_ascii=False))